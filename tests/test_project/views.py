from django.http import HttpResponse
from django.shortcuts import render

from .models import Book, TaggedItem


def test_n_plus_one_view(request):
    books = Book.objects.all()
    # Trigger N+1
    titles_with_authors = [f"{book.title} by {book.author.name}" for book in books]
    return HttpResponse("\n".join(titles_with_authors))


def test_ok_view(request):
    books = Book.objects.select_related("author").all()
    # No N+1
    titles_with_authors = [f"{book.title} by {book.author.name}" for book in books]
    return HttpResponse("\n".join(titles_with_authors))


def test_template_view(request):
    books = Book.objects.all()
    return render(request, "books.html", {"books": books})


def test_generic_relation_n_plus_one_view(request):
    items = TaggedItem.objects.all()
    # Trigger N+1 by accessing content_object on each item
    details = [f"{item.tag}: {item.content_object}" for item in items]
    return HttpResponse("\n".join(details))


def test_generic_relation_ok_view(request):
    # Avoid N+1 by prefetching content_object
    items = TaggedItem.objects.prefetch_related("content_object").all()
    details = [f"{item.tag}: {item.content_object}" for item in items]
    return HttpResponse("\n".join(details))


def test_deferred_fields_n_plus_one_view(request):
    # Fetch books but defer the 'title' field
    books = Book.objects.defer("title").all()
    # Accessing 'title' in a loop will trigger an N+1 query for the deferred field
    titles = [book.title for book in books]
    return HttpResponse("\n".join(titles))


def test_multi_db_n_plus_one_view(request):
    # Fetch books from the secondary database
    books = Book.objects.using("secondary").all()
    # Accessing authors will trigger N+1 on the secondary database
    titles_with_authors = [f"{book.title} by {book.author.name}" for book in books]
    return HttpResponse("\n".join(titles_with_authors))


def test_complex_n_plus_one_view(request):
    # Complex scenario: Generic Relations + Deferred Fields + Standard Relations
    # Fetch TaggedItems from 'default', defer 'tag' field
    items = TaggedItem.objects.defer("tag").all()

    output = []
    # Loop over items
    for item in items:
        # Trigger 1: Access deferred 'tag'
        tag = item.tag
        # Trigger 2: Access GenericForeignKey (content_object)
        content = item.content_object

        # Trigger 3: If content is Book, access ForeignKey (author)
        if isinstance(content, Book):
            author_name = content.author.name
            output.append(f"Tag: {tag}, Book: {content.title}, Author: {author_name}")
        else:
            output.append(f"Tag: {tag}, Object: {content}")

    return HttpResponse("\n".join(output))
