from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='search'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('get-wards/', views.get_wards, name='get_wards'),
]
