from django.urls import path
from . import views

app_name = 'cooperate'

urlpatterns = [
    path('partner/', views.cooperate_view, name='partner_form'),
    path('success/', views.success_view, name='success'),
    path('my-restaurants/', views.my_restaurants, name='my_restaurants'),
    path('from-restaurant/<int:restaurant_id>/', views.from_food_restaurant, name='from_food_restaurant'),
    path('dashboard/<int:restaurant_id>/', views.restaurant_dashboard, name='restaurant_dashboard'),
    path('dashboard/<int:restaurant_id>/add-dish/', views.add_dish, name='add_dish'),
    path('dashboard/<int:restaurant_id>/edit-dish/<int:dish_id>/', views.edit_dish, name='edit_dish'),
    path('dashboard/<int:restaurant_id>/delete-dish/<int:dish_id>/', views.delete_dish, name='delete_dish'),
    path('dish/<int:dish_id>/', views.cooperate_dish_detail, name='cooperate_dish_detail'),
    path('dish/<int:dish_id>/review/', views.cooperate_dish_review, name='cooperate_dish_review'),
]