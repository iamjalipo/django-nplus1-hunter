from django.http import HttpResponse
from .models import Book

def test_n_plus_one_view(request):
    books = Book.objects.all()
    # Trigger N+1
    titles_with_authors = [f"{book.title} by {book.author.name}" for book in books]
    return HttpResponse("\n".join(titles_with_authors))

def test_ok_view(request):
    books = Book.objects.select_related('author').all()
    # No N+1
    titles_with_authors = [f"{book.title} by {book.author.name}" for book in books]
    return HttpResponse("\n".join(titles_with_authors))
