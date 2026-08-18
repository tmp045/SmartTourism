from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RestaurantPartnerForm, DishForm
from .models import Cooperation, Dish
from food.models import Restaurant, DishReview
from search.models import Province
import logging

logger = logging.getLogger(__name__)

def cooperate_view(request):
    if request.method == 'POST':
        form = RestaurantPartnerForm(request.POST, request.FILES)  # ← Dùng RestaurantPartnerForm
        if form.is_valid():
            cooperation = form.save(commit=False)
            
            # Lấy tất cả các khung giờ từ POST data
            times = []
            i = 0
            while f'opening_time_{i}' in request.POST:
                opening = request.POST.get(f'opening_time_{i}')
                closing = request.POST.get(f'closing_time_{i}')
                if opening and closing:
                    times.append(f"{opening} - {closing}")
                i += 1
            
            cooperation.opening_hours = ', '.join(times) if times else ''
            cooperation.save()
            
            return redirect('cooperate:success')
    else:
        form = RestaurantPartnerForm()  # ← Dùng RestaurantPartnerForm
        
    provinces = Province.objects.all()
    return render(request, 'cooperate/cooperate_form.html', {'form': form, "provinces": provinces,})

def success_view(request):
    return render(request, 'cooperate/success.html')

def my_restaurants(request):
    """Hiển thị các quán ăn của chủ sở hữu (chỉ những quán đã được duyệt)"""
    email = request.GET.get('email', '')
    
    if not email:
        messages.warning(request, '⚠️ Vui lòng nhập email để xem quán của bạn')
        return render(request, 'food/my_restaurant.html', {'restaurants': []})  # ← Đổi thành food/my_restaurant.html
    
    restaurants = Cooperation.objects.filter(email=email, is_approved=True)
    
    if not restaurants.exists():
        messages.info(request, 'ℹ️ Không tìm thấy quán nào được duyệt')
    
    return render(request, 'food/my_restaurant.html', {  # ← Đổi thành food/my_restaurant.html
        'restaurants': restaurants,
        'email': email
    })

def from_food_restaurant(request, restaurant_id):
    """Chuyển từ food_restaurant sang cooperate dashboard"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    print(f"🔍 Restaurant name: {restaurant.name}")
    
    # Tìm Cooperation với tên nhà hàng giống
    cooperation = Cooperation.objects.filter(
        restaurant_name=restaurant.name
    ).first()
    
    print(f"✅ Cooperation tìm được: {cooperation}")
    
    if not cooperation:
        messages.error(request, f'❌ Quán "{restaurant.name}" chưa được đăng ký hợp tác')
        return redirect('food:home')
    
    messages.success(request, f'✅ Vào dashboard: {cooperation.restaurant_name}')
    return redirect('cooperate:dashboard', cooperation_id=cooperation.id)

def restaurant_dashboard(request, restaurant_id):
    """Trang quản lý quán ăn - dùng Cooperation ID"""
    cooperation = get_object_or_404(Cooperation, id=restaurant_id)
    
    # Lưu cooperation_id vào session
    request.session['cooperation_id'] = restaurant_id
    
    if not cooperation.is_approved:
        messages.warning(request, f'⚠️ Quán "{cooperation.restaurant_name}" chưa được duyệt')
        return redirect('food:home')
    
    dishes = cooperation.dishes.all()
    
    return render(request, 'cooperate/dashboard.html', {
        'cooperation': cooperation,
        'dishes': dishes,
        'restaurant_id': restaurant_id
    })

def add_dish(request, restaurant_id):
    """Thêm món ăn mới"""
    cooperation = get_object_or_404(Cooperation, id=restaurant_id)
    
    if not cooperation.is_approved:
        messages.error(request, f'❌ Quán "{cooperation.restaurant_name}" chưa được duyệt')
        return redirect('food:home')
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.cooperation = cooperation
            dish.save()
            messages.success(request, '✅ Thêm món ăn thành công!')
            return redirect('cooperate:restaurant_dashboard', restaurant_id=restaurant_id)
        else:
            # Debug: hiển thị lỗi form
            logger.error(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Lỗi {field}: {error}")
    else:
        form = DishForm()
    
    return render(request, 'cooperate/add_dish.html', {
        'form': form,
        'cooperation': cooperation,
        'restaurant_id': restaurant_id  # ← Thêm dòng này
    })

def edit_dish(request, restaurant_id, dish_id):
    """Chỉnh sửa món ăn"""
    dish = get_object_or_404(Dish, id=dish_id)
    
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cập nhật món ăn thành công!')
            return redirect('cooperate:restaurant_dashboard', restaurant_id=restaurant_id)
    else:
        form = DishForm(instance=dish)
    
    return render(request, 'cooperate/edit_dish.html', {
        'form': form,
        'dish': dish,
        'restaurant_id': restaurant_id
    })

def delete_dish(request, restaurant_id, dish_id):
    """Xóa món ăn"""
    dish = get_object_or_404(Dish, id=dish_id)
    
    if request.method == 'POST':
        dish.delete()
        messages.success(request, '✅ Xóa món ăn thành công!')
    
    return redirect('cooperate:restaurant_dashboard', restaurant_id=restaurant_id)

def cooperate_dish_detail(request, dish_id):
    """
    Trang chi tiết món ăn từ cooperate.Dish
    """
    dish = get_object_or_404(Dish, id=dish_id)
    cooperation = dish.cooperation
    reviews = DishReview.objects.filter(cooperate_dish=dish).select_related('user')
    
    return render(request, 'cooperate/dish_detail.html', {
        'dish': dish,
        'cooperation': cooperation,
        'reviews': reviews,
    })

@login_required
def cooperate_dish_review(request, dish_id):
    """
    Thêm review cho cooperate.Dish
    """
    dish = get_object_or_404(Dish, id=dish_id)
    
    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        comment = request.POST.get('comment', '').strip()
        
        DishReview.objects.create(
            cooperate_dish=dish,
            user=request.user,
            stars=stars,
            comment=comment,
        )
        
        return redirect('cooperate:cooperate_dish_detail', dish_id=dish.id)
    
    return render(request, 'cooperate/dish_review.html', {'dish': dish})
