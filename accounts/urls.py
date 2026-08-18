from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='accounts_index'),
    path('login/', views.login_view, name='login'),
    path('signup-success/', views.signup_success, name='signup_success'),
]