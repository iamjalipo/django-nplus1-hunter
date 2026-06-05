import json
import logging
import os
import time
from collections import defaultdict
from contextlib import ExitStack

from django.conf import settings
from django.db import connections

from .trackers import NPlus1QueryWrapper, clear_query_data, get_query_data


class HighQueryCountDetectedError(Exception):
    pass


class NPlus1QueryDetectedError(Exception):
    pass


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
        self.total_query_threshold = getattr(
            settings, "NPLUS1_HUNTER_TOTAL_THRESHOLD", 50
        )
        # Paths to completely ignore
        self.ignore_paths = getattr(settings, "NPLUS1_HUNTER_IGNORE_PATHS", [])
        # Raise exceptions instead of just logging a warning (useful for CI/Tests)
        self.raise_exception = getattr(settings, "NPLUS1_HUNTER_RAISE_EXCEPTION", False)
        # Enable writing JSON lines to a log file for IDE integration (e.g. VS Code)
        self.vscode_integration = getattr(settings, "NPLUS1_HUNTER_VSCODE_INTEGRATION", True)
        self.log_file = getattr(
            settings, "NPLUS1_HUNTER_LOG_FILE",
            os.path.join(getattr(settings, "BASE_DIR", os.getcwd()), ".nplus1-hunter.jsonl")
        )

    def __call__(self, request):
        if not self.enabled or any(
            request.path.startswith(p) for p in self.ignore_paths
        ):
            return self.get_response(request)

        # Clear any stale data from previous requests on this thread
        clear_query_data()

        try:
            # Wrap all database executions for the duration of the request
            with ExitStack() as stack:
                for conn in connections.all():
                    stack.enter_context(conn.execute_wrapper(NPlus1QueryWrapper()))
                response = self.get_response(request)

            # Analysis Engine
            self.analyze_queries(request)

            return response
        finally:
            # Cleanup memory
            clear_query_data()

    def analyze_queries(self, request):
        queries = get_query_data()
        total_queries = len(queries)

        if total_queries >= self.total_query_threshold:
            msg = (
                f"\n[N+1 Hunter] HIGH QUERY COUNT DETECTED: {total_queries} queries "
                f"executed on {request.path}"
            )
            logger.warning(msg)
            if self.raise_exception:
                raise HighQueryCountDetectedError(msg)

        # Detect N+1 patterns by grouping queries by the exact line of user code
        # that generated them. If a loop is executing queries, the same line will
        # trigger multiple queries.
        frame_counts = defaultdict(list)
        for q in queries:
            if q["frame"]:
                key = (q["frame"].filename, q["frame"].lineno, q["frame"].name)
                frame_counts[key].append(q)

        for frame_key, q_list in frame_counts.items():
            if len(q_list) >= self.nplus1_threshold:
                sample_sql = q_list[0]["sql"]
                if len(sample_sql) > 100:
                    sample_sql = sample_sql[:100] + "..."

                total_duration = sum(q.get("duration", 0) for q in q_list)
                filename, lineno, func_name = frame_key
                hunted_ascii = r"""
  _    _ _   _ _   _ _______ ______ _____  
 | |  | | | | | \ | |__   __|  ____|  __ \ 
 | |__| | | | |  \| |  | |  | |__  | |  | |
 |  __  | | | | . ` |  | |  |  __| | |  | |
 | |  | | |_| | |\  |  | |  | |____| |__| |
 |_|  |_|\___/|_| \_|  |_|  |______|_____/ 
"""
                
                import linecache
                source_code = linecache.getline(filename, lineno).strip()
                source_display = f"Code snippet: `{source_code}`\n" if source_code else ""
                
                tip = (
                    "💡 Tip: To optimize this, consider using `select_related()` (for ForeignKey/OneToOne) "
                    "or `prefetch_related()` (for ManyToMany/Reverse relations) on the initial QuerySet."
                )

                msg = (
                    f"\n{hunted_ascii}"
                    f"\n[N+1 Hunter] N+1 QUERY DETECTED: {len(q_list)} queries (taking {total_duration:.4f}s total) "
                    f"originated from {filename}:{lineno} in {func_name}.\n"
                    f"{source_display}"
                    f"Sample SQL: {sample_sql}\n"
                    f"\n{tip}\n"
                )
                logger.warning(msg)

                if self.vscode_integration:
                    try:
                        payload = {
                            "timestamp": time.time(),
                            "file": filename,
                            "line": lineno,
                            "function": func_name,
                            "count": len(q_list),
                            "duration": total_duration,
                            "sql": sample_sql,
                            "tip": tip
                        }
                        with open(self.log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps(payload) + "\n")
                    except Exception as e:
                        logger.error(f"[N+1 Hunter] Failed to write event to {self.log_file}: {e}")

                if self.raise_exception:
                    raise NPlus1QueryDetectedError(msg)
