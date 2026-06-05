import logging
from collections import defaultdict
from django.conf import settings
from contextlib import ExitStack
from django.db import connections
from .trackers import NPlus1QueryWrapper, get_query_data, clear_query_data

logger = logging.getLogger("django_nplus1_hunter")

class NPlus1HunterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuration defaults
        # We only enable it if DEBUG is True to prevent production catastrophes.
        self.enabled = getattr(settings, "DEBUG", False)
        # How many times the same line of code must generate a query to be considered N+1
        self.nplus1_threshold = getattr(settings, "NPLUS1_HUNTER_THRESHOLD", 3)
        # Warn if the total query count per request exceeds this
        self.total_query_threshold = getattr(settings, "NPLUS1_HUNTER_TOTAL_THRESHOLD", 50)
        # Paths to completely ignore
        self.ignore_paths = getattr(settings, "NPLUS1_HUNTER_IGNORE_PATHS", [])

    def __call__(self, request):
        if not self.enabled or any(request.path.startswith(p) for p in self.ignore_paths):
            return self.get_response(request)

        # Clear any stale data from previous requests on this thread
        clear_query_data()
        
        # Wrap all database executions for the duration of the request
        with ExitStack() as stack:
            for conn in connections.all():
                stack.enter_context(conn.execute_wrapper(NPlus1QueryWrapper()))
            response = self.get_response(request)
            
        # Analysis Engine
        self.analyze_queries(request)
        
        # Cleanup memory
        clear_query_data()
        
        return response

    def analyze_queries(self, request):
        queries = get_query_data()
        total_queries = len(queries)
        
        if total_queries >= self.total_query_threshold:
            logger.warning(
                f"\n[N+1 Hunter] HIGH QUERY COUNT DETECTED: {total_queries} queries "
                f"executed on {request.path}"
            )
            
        # Detect N+1 patterns by grouping queries by the exact line of user code
        # that generated them. If a loop is executing queries, the same line will
        # trigger multiple queries.
        frame_counts = defaultdict(list)
        for q in queries:
            if q["frame"]:
                key = f"{q['frame'].filename}:{q['frame'].lineno}"
                frame_counts[key].append(q)
                
        for frame_key, q_list in frame_counts.items():
            if len(q_list) >= self.nplus1_threshold:
                sample_sql = q_list[0]["sql"]
                if len(sample_sql) > 100:
                    sample_sql = sample_sql[:100] + "..."
                    
                logger.warning(
                    f"\n[N+1 Hunter] N+1 QUERY DETECTED: {len(q_list)} queries originated from "
                    f"{frame_key}.\n"
                    f"Sample SQL: {sample_sql}\n"
                )
