Task Tracker: Django N+1 Hunter
Phase 1: Setup & Foundation
[x] 1.1 Project Initialization
[x] Initialize project with hatch (or manually create pyproject.toml and src/ layout).
[x] Set up .gitignore.
[x] 1.2 Tooling Configuration
[x] Configure Ruff in pyproject.toml.
[x] Configure pytest and pytest-django.
[x] Set up tox for multi-environment testing.
[x] 1.3 CI/CD Pipeline
[x] Create GitHub Actions workflow (.github/workflows/test.yml).
[x] 1.4 Test Project Setup
[x] Create tests/test_project/.
[x] Configure minimal manage.py, settings.py, and urls.py.
[x] Create dummy models/views for testing.
Phase 2: Core Logic & Tracking
[x] 2.1 Query Tracker
[x] Implement ExecuteWrapper to capture SQL, time, and raw traceback.
[x] Write tests to confirm interception.
[x] 2.2 Traceback Filtering
[x] Implement logic to filter Django/Python internal frames.
[x] Isolate user code lines originating the query.
[x] 2.3 Thread-Local Storage
[x] Implement threading.local() or contextvars to store per-request queries.
Phase 3: Middleware & Developer Experience
[x] 3.1 Django Middleware
[x] Create middleware class.
[x] Enable tracking on process_request.
[x] Process data on process_response.
[x] 3.2 Analysis Engine
[x] Detect N+1 patterns (consecutive similar queries).
[x] Detect total query threshold violations.
[x] 3.3 Reporting Interface
[x] Output structured warnings showing the offending file and line.
[x] 3.4 AppConfig Safety
[x] Create apps.py with checks for settings.DEBUG to prevent production execution.
Phase 4: Polish & Documentation
[x] 4.1 Configuration Options
[x] Define customizable thresholds and ignored URLs in settings.py.
[x] 4.2 README & Docs
[x] Write comprehensive documentation.
[x] 4.3 Test Coverage
[x] Ensure high test coverage for all modules.
[x] 4.4 PyPI Publish Setup
[x] Configure GitHub Actions for PyPI deployment (publish.yml).