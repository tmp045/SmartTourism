from django.urls import path
from . import views

app_name = 'food'

urlpatterns = [
    path('', views.home, name='home'),

    # --- Search ---
    path('restaurants/', views.restaurant_search, name='restaurant_search'),  # ✅ THÊM DÒNG NÀY

    # --- Nhà hàng ---
    path('restaurant/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurant/<int:restaurant_id>/review/', views.review_view, name='add_review'),
    path('restaurant/<int:restaurant_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('restaurant-review/<int:review_id>/delete/', views.delete_restaurant_review, name='delete_restaurant_review'),

    # --- Profile ---
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile, name='edit_profile'),

    # --- Món ăn ---
    path('dish/<int:dish_id>/', views.dish_detail, name='dish_detail'),
    path('dish/<int:dish_id>/review/', views.dish_review_view, name='add_dish_review'),

    # ❗️ ROUTE ĐỂ XÓA REVIEW MÓN ĂN
    path('dish-review/<int:review_id>/delete/', views.delete_dish_review, name='delete_dish_review'),

    # --- Logout ---
    path('logout/', views.logout_view, name='logout'),

    # submit review ngay trong trang detail
    path("restaurant/<int:restaurant_id>/review/", views.review_submit, name="review_submit"),
    path("restaurant/<int:restaurant_id>/comment/", views.add_review_or_reply, name="add_review_or_reply"),
    
    
]
