import pytest
from django.db import connection

from django_nplus1_hunter.trackers import (
    NPlus1QueryWrapper,
    clear_query_data,
    get_query_data,
)
from tests.test_project.models import Author


@pytest.mark.django_db
def test_query_interception():
    clear_query_data()

    with connection.execute_wrapper(NPlus1QueryWrapper()):
        Author.objects.create(name="Test Author")
        list(Author.objects.all())

    data = get_query_data()
    assert len(data) >= 2

    # Check that SQL was captured
    assert any("INSERT INTO" in item["sql"] for item in data)
    assert any("SELECT" in item["sql"] for item in data)

    # Check that frame was captured
    assert all(item["frame"] is not None for item in data)
    # The frame filename should ideally be this test file
    assert any("test_trackers.py" in item["frame"].filename for item in data)
