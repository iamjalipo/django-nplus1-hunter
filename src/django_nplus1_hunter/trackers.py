import time
import traceback
from contextvars import ContextVar

# Context-local storage for queries during a request, safe for async/ASGI
_query_data: ContextVar[list] = ContextVar("query_data")

def get_query_data():
    """Retrieve the query data for the current context."""
    try:
        return _query_data.get()
    except LookupError:
        data = []
        _query_data.set(data)
        return data

def clear_query_data():
    """Clear the query data for the current context."""
    _query_data.set([])

def filter_traceback(tb_list):
    """
    Filter the traceback to find the first frame that is NOT from django internals
    or this package. This helps pinpoint the exact line of user code that triggered the query.
    """
    # Start from the bottom of the stack (most recent call) and work backwards
    for tb in reversed(tb_list):
        filename = tb.filename
        normalized_path = filename.replace('\\', '/')
        
        # Ignore Django framework internals
        if normalized_path.startswith('django/') or '/django/' in normalized_path:
            continue
            
        # Ignore frames from this package
        if 'django_nplus1_hunter' in normalized_path:
            continue
        
        return tb
        
    return tb_list[-1] if tb_list else None

class NPlus1QueryWrapper:
    """
    A callable that wraps database executions to capture query data and tracebacks.
    Designed to be used with Django's connection.execute_wrapper().
    """
    def __call__(self, execute, sql, params, many, context):
        start_time = time.time()
        try:
            return execute(sql, params, many, context)
        finally:
            duration = time.time() - start_time
            
            # Capture the current call stack
            # extract_stack() returns a list of FrameSummary objects
            tb = traceback.extract_stack()
            
            # Remove the last few frames which belong to this wrapper and traceback module itself
            # Typically: traceback.extract_stack(), __call__(), etc.
            tb = tb[:-2]
            
            user_frame = filter_traceback(tb)
            
            query_info = {
                'sql': sql,
                'params': params,
                'duration': duration,
                'frame': user_frame,
            }
            
            get_query_data().append(query_info)
