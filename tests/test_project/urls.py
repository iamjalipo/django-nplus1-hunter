from django.urls import path
from . import views

urlpatterns = [
    path('test-n-plus-one/', views.test_n_plus_one_view, name='test_n_plus_one'),
    path('test-ok/', views.test_ok_view, name='test_ok'),
    path('test-template/', views.test_template_view, name='test_template'),
    path('test-generic-n-plus-one/', views.test_generic_relation_n_plus_one_view, name='test_generic_n_plus_one'),
    path('test-generic-ok/', views.test_generic_relation_ok_view, name='test_generic_ok'),
    path('test-deferred/', views.test_deferred_fields_n_plus_one_view, name='test_deferred'),
    path('test-multi-db/', views.test_multi_db_n_plus_one_view, name='test_multi_db'),
    path('test-complex/', views.test_complex_n_plus_one_view, name='test_complex'),
]

