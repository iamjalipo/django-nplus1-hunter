import pytest
from django.test import Client
from tests.test_project.models import Author, Book

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def setup_data():
    author1 = Author.objects.create(name="Author 1")
    author2 = Author.objects.create(name="Author 2")
    Book.objects.create(title="Book 1", author=author1)
    Book.objects.create(title="Book 2", author=author2)
    Book.objects.create(title="Book 3", author=author1)
    Book.objects.create(title="Book 4", author=author2)

@pytest.mark.django_db
def test_n_plus_one_view(client, setup_data, caplog):
    # Call the view that triggers N+1
    response = client.get('/test-n-plus-one/')
    assert response.status_code == 200
    
    # Check that our middleware logged an N+1 warning
    assert "N+1 QUERY DETECTED" in caplog.text
    assert "queries originated from" in caplog.text

@pytest.mark.django_db
def test_ok_view(client, setup_data, caplog):
    # Call the view that does NOT trigger N+1
    response = client.get('/test-ok/')
    assert response.status_code == 200
    
    # Check that our middleware did NOT log an N+1 warning
    assert "N+1 QUERY DETECTED" not in caplog.text
