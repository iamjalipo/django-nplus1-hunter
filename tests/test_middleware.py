import pytest
from django.test import Client

from django_nplus1_hunter.middleware import NPlus1QueryDetectedError
from tests.test_project.models import Author, Book, TaggedItem


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def setup_data():
    author1 = Author.objects.create(name="Author 1")
    author2 = Author.objects.create(name="Author 2")
    book1 = Book.objects.create(title="Book 1", author=author1)
    book2 = Book.objects.create(title="Book 2", author=author2)
    book3 = Book.objects.create(title="Book 3", author=author1)
    book4 = Book.objects.create(title="Book 4", author=author2)

    # Create books in secondary database
    author1_sec = Author.objects.using("secondary").create(name="Author 1")
    author2_sec = Author.objects.using("secondary").create(name="Author 2")
    Book.objects.using("secondary").create(title="Book 1", author=author1_sec)
    Book.objects.using("secondary").create(title="Book 2", author=author2_sec)
    Book.objects.using("secondary").create(title="Book 3", author=author1_sec)
    Book.objects.using("secondary").create(title="Book 4", author=author2_sec)

    # Generic relation setups: tag different Book instances (single content type)
    TaggedItem.objects.create(tag="tag1", content_object=book1)
    TaggedItem.objects.create(tag="tag2", content_object=book2)
    TaggedItem.objects.create(tag="tag3", content_object=book3)
    TaggedItem.objects.create(tag="tag4", content_object=book4)


@pytest.mark.django_db(databases=["default", "secondary"])
def test_n_plus_one_view(client, setup_data, caplog, settings):
    settings.DEBUG = True
    # Call the view that triggers N+1
    response = client.get("/test-n-plus-one/")
    assert response.status_code == 200

    # Check that our middleware logged an N+1 warning
    assert "N+1 QUERY DETECTED" in caplog.text
    assert "queries (taking" in caplog.text
    assert "originated from" in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_ok_view(client, setup_data, caplog, settings):
    settings.DEBUG = True
    # Call the view that does NOT trigger N+1
    response = client.get("/test-ok/")
    assert response.status_code == 200

    # Check that our middleware did NOT log an N+1 warning
    assert "N+1 QUERY DETECTED" not in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_raise_exception(client, setup_data, settings):
    settings.DEBUG = True
    settings.NPLUS1_HUNTER_RAISE_EXCEPTION = True

    with pytest.raises(NPlus1QueryDetectedError) as exc_info:
        client.get("/test-n-plus-one/")

    assert "N+1 QUERY DETECTED" in str(exc_info.value)


@pytest.mark.django_db(databases=["default", "secondary"])
def test_template_view_traceback_fallback(client, setup_data, caplog, settings):
    settings.DEBUG = True
    response = client.get("/test-template/")
    assert response.status_code == 200

    # Verify that the traceback correctly fell back to the view rendering the template
    assert "N+1 QUERY DETECTED" in caplog.text
    # Ensure it identified the origin as views.py (the user view) rather than Django's template engine
    assert "views.py" in caplog.text
    assert "django/template" not in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_generic_relation_n_plus_one(client, setup_data, caplog, settings):
    settings.DEBUG = True
    # Call the view that triggers N+1 via GenericForeignKey
    response = client.get("/test-generic-n-plus-one/")
    assert response.status_code == 200

    # Check that our middleware logged an N+1 warning for generic relations
    assert "N+1 QUERY DETECTED" in caplog.text
    assert "views.py" in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_generic_relation_ok(client, setup_data, caplog, settings):
    settings.DEBUG = True
    # Call the view that avoids N+1 via prefetch_related
    response = client.get("/test-generic-ok/")
    assert response.status_code == 200

    # Check that our middleware did NOT log any warning
    assert "N+1 QUERY DETECTED" not in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_deferred_fields_n_plus_one(client, setup_data, caplog, settings):
    settings.DEBUG = True
    response = client.get("/test-deferred/")
    assert response.status_code == 200

    # Check that deferred fields triggered an N+1 warning
    assert "N+1 QUERY DETECTED" in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_multi_db_n_plus_one(client, setup_data, caplog, settings):
    settings.DEBUG = True
    response = client.get("/test-multi-db/")
    assert response.status_code == 200

    # Check that N+1 warning correctly catches the queries sent to the secondary database
    assert "N+1 QUERY DETECTED" in caplog.text


@pytest.mark.django_db(databases=["default", "secondary"])
def test_complex_n_plus_one(client, setup_data, caplog, settings):
    settings.DEBUG = True
    response = client.get("/test-complex/")
    assert response.status_code == 200

    # Because of deferred fields and relationships, it should trigger N+1
    assert "N+1 QUERY DETECTED" in caplog.text

    # Print the caplog output to show the complex N+1 warning details
    print("\n--- N+1 Hunter Output ---")
    print(caplog.text)
    print("-------------------------\n")


@pytest.mark.django_db(databases=["default", "secondary"])
def test_vscode_integration_jsonl_output(client, setup_data, settings, tmp_path):
    import json
    
    settings.DEBUG = True
    settings.NPLUS1_HUNTER_VSCODE_INTEGRATION = True
    
    # Use a temporary file for the log
    log_file_path = tmp_path / ".nplus1-hunter-test.jsonl"
    settings.NPLUS1_HUNTER_LOG_FILE = str(log_file_path)
    
    # Call a view that triggers N+1
    response = client.get("/test-n-plus-one/")
    assert response.status_code == 200
    
    # Verify the JSONL file was created
    assert log_file_path.exists()
    
    # Read and parse the file
    lines = log_file_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    
    # Check the payload schema
    payload = json.loads(lines[-1])
    assert "timestamp" in payload
    assert "file" in payload
    assert "line" in payload
    assert "function" in payload
    assert "count" in payload
    assert "duration" in payload
    assert "sql" in payload
    assert "tip" in payload
    
    # Verify payload content
    assert payload["count"] >= 3
    assert "SELECT" in payload["sql"].upper()
    assert payload["duration"] >= 0
    assert payload["function"] == "test_n_plus_one_view" # Or whatever the view function name is

