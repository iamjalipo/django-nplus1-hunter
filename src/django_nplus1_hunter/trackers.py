import time
import traceback
from threading import local

# Thread-local storage for queries during a request
_thread_locals = local()

def get_query_data():
    """Retrieve the query data for the current thread."""
    if not hasattr(_thread_locals, 'query_data'):
        _thread_locals.query_data = []
    return _thread_locals.query_data

def clear_query_data():
    """Clear the query data for the current thread."""
    if hasattr(_thread_locals, 'query_data'):
        del _thread_locals.query_data

def filter_traceback(tb_list):
    """
    Filter the traceback to find the first frame that is NOT from django internals.
    This helps pinpoint the exact line of user code that triggered the query.
    """
    # Start from the bottom of the stack (most recent call) and work backwards
    for tb in reversed(tb_list):
        filename = tb.filename
        
        # Ignore Django internal database frames
        if 'django/db/' in filename.replace('\\', '/'):
            continue
            
        # Ignore Python standard library or test runner internals if needed here
        
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
