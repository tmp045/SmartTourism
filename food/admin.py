from django.contrib import admin
from .models import Restaurant, Dish, Review


# ----- RESTAURANT -----
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    readonly_fields = ("avg_price",)
    list_display = ('name', 'address', 'cuisine_type', 'rating', 'is_open')
    search_fields = ('name', 'address')
    list_filter = ('cuisine_type', 'is_open', 'has_parking')
    list_editable = ('rating', 'is_open')


# ----- DISH -----
@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'category', 'is_specialty')
    list_filter = ('category', 'is_specialty', 'restaurant')
    search_fields = ('name', 'restaurant__name')


# ----- REVIEW -----
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'stars', 'created_at')
    search_fields = ('restaurant__name',)
    list_filter = ('stars', 'created_at')
