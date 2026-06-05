from django.urls import path
from . import views

urlpatterns = [
    path('test-n-plus-one/', views.test_n_plus_one_view, name='test_n_plus_one'),
    path('test-ok/', views.test_ok_view, name='test_ok'),
]
