# food/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Restaurant, Review, Dish, DishReview, UserProfile
from search.models import Province
from django.db.models import Prefetch
from cooperate.models import Cooperation, Dish as CooperateDish


def home(request):
    categories = [
        {"name": "Cơm tấm",     "icon": "food/img/comtam.jpg"},
        {"name": "Bánh mì",     "icon": "food/img/banhmi.jpg"},
        {"name": "Phở",         "icon": "food/img/pho1.jpg"},
        {"name": "Lẩu",         "icon": "food/img/lau.jpg"},
        {"name": "Đồ nướng",    "icon": "food/img/donuong.avif"},
        {"name": "Tráng miệng", "icon": "food/img/trangmieng.jpg"},
    ]

    restaurants = Restaurant.objects.all()
    provinces = Province.objects.all()

    favorite_ids = []
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        favorite_ids = list(profile.favorites.values_list('id', flat=True))

    return render(request, 'food/home.html', {
        'restaurants': restaurants,
        'categories': categories,
        'provinces': provinces,
        'favorite_ids': favorite_ids,
    })


def search(request):
    """
    (Nếu còn dùng search của app food) – search đơn giản theo tên / địa chỉ.
    Bây giờ bạn đang dùng search bên app `search` là chính rồi, nên cái này
    không bắt buộc phải dùng.
    """
    query = request.GET.get('q', '').strip()

    if query:
        restaurants = Restaurant.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(cuisine_type__icontains=query)
        )
    else:
        restaurants = Restaurant.objects.all()

    return render(request, 'food/search_results.html', {
        'restaurants': restaurants,
        'query': query,
    })


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, id=pk)
    root_reviews = (
    Review.objects.filter(restaurant=restaurant, parent__isnull=True)
    .select_related("user")
    .prefetch_related(
        Prefetch("replies", queryset=Review.objects.select_related("user").order_by("created_at"))
    )
    )

    # Lấy món ăn từ cả 2 nguồn
    # 1. Món từ food.Dish (FK -> Restaurant)
    dishes_from_food = list(restaurant.dishes.all().order_by('category', 'name'))
    
    # 2. Món từ cooperate.Dish (tìm Cooperation với tên giống Restaurant)
    cooperation = Cooperation.objects.filter(
        restaurant_name=restaurant.name,
        is_approved=True
    ).first()
    
    dishes_from_cooperate = []
    if cooperation:
        dishes_from_cooperate = list(cooperation.dishes.filter(is_available=True))
    
    # Gộp cả 2 danh sách
    dishes = dishes_from_food + dishes_from_cooperate

    # lấy review kèm user + profile để show avatar
    reviews = restaurant.reviews.select_related('user__profile').all()

    # gán thêm thuộc tính reviewer_level + total_reviews cho từng review
    for rv in reviews:
        if rv.user:
            total = rv.user.restaurant_reviews.count() + rv.user.dish_reviews.count()
            if total >= 50:
                level = "Master reviewer"
            elif total >= 20:
                level = "Chuyên gia"
            elif total >= 5:
                level = "Thành viên tích cực"
            else:
                level = "Người mới"
        else:
            total = 0
            level = "Ẩn danh"

        rv.reviewer_level = level
        rv.total_reviews = total

    return render(request, 'food/restaurant_detail.html', {
        'restaurant': restaurant,
        'dishes': dishes,
        'reviews': reviews,  # 👈 dùng cái này ở template
    })
def restaurant_search(request):
    category = request.GET.get('category')
    q = request.GET.get('q')

    restaurants = Restaurant.objects.all()

    # --- Filter theo category (thực ra là cuisine_type) ---
    if category:
        restaurants = restaurants.filter(cuisine_type__icontains=category)

    # --- Filter theo keyword ---
    if q:
        restaurants = restaurants.filter(name__icontains=q)

    return render(request, 'food/restaurant_search.html', {
        'restaurants': restaurants,
        'category': category,
        'q': q,
    })


@login_required(login_url='login')   # hoặc 'accounts:login' nếu bạn đặt tên vậy
def review_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        comment = request.POST.get('comment', '').strip()

        Review.objects.create(
            restaurant=restaurant,
            user=request.user,          # 👈 QUAN TRỌNG
            stars=stars,
            comment=comment,
        )

        # cập nhật rating trung bình
        avg_rating = restaurant.reviews.aggregate(Avg('stars'))['stars__avg']
        restaurant.rating = round(avg_rating, 1) if avg_rating else 0
        restaurant.save()

        return redirect('food:restaurant_detail', pk=restaurant.id)

    return render(request, 'food/review.html', {'restaurant': restaurant})

@login_required
def review_submit(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == "POST":
        comment = (request.POST.get("comment") or "").strip()
        stars = request.POST.get("stars")  # chỉ có khi là comment gốc
        parent_id = request.POST.get("parent_id")  # có khi reply

        parent = None
        if parent_id:
            parent = Review.objects.filter(id=parent_id, restaurant=restaurant).first()

        # Nếu là REPLY: không cần stars (hoặc set mặc định)
        if parent:
            Review.objects.create(
                restaurant=restaurant,
                user=request.user,
                parent=parent,
                stars=0,          # hoặc 0 nếu bạn đổi model cho phép null
                comment=comment,
            )
        else:
            # COMMENT GỐC: bắt buộc stars
            Review.objects.create(
                restaurant=restaurant,
                user=request.user,
                parent=None,
                stars=int(stars),
                comment=comment,
            )

    return redirect("food:restaurant_detail", restaurant_id=restaurant.id)

def dish_detail(request, dish_id):
    """
    Trang chi tiết + list bình luận cho MÓN ĂN.
    """
    dish = get_object_or_404(Dish, id=dish_id)
    restaurant = dish.restaurant
    reviews = dish.reviews.all()  # related_name='reviews' ở model DishReview

    return render(request, 'food/dish_detail.html', {
        'dish': dish,
        'restaurant': restaurant,
        'reviews': reviews,
    })


@login_required(login_url='login')
def dish_review_view(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)

    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        comment = request.POST.get('comment', '').strip()

        DishReview.objects.create(
            dish=dish,
            user=request.user,          # 👈 QUAN TRỌNG
            stars=stars,
            comment=comment,
        )

        return redirect('food:dish_detail', dish_id=dish.id)

    return render(request, 'food/dish_review.html', {'dish': dish})


def delete_dish_review(request, review_id):
    """
    Xóa 1 review của món ăn, rồi quay lại trang chi tiết món.
    """
    review = get_object_or_404(DishReview, id=review_id)
    dish_id = review.dish.id if review.dish else None
    cooperate_dish_id = review.cooperate_dish.id if review.cooperate_dish else None

    if request.method == "POST":
        # Chỉ cho phép user xóa review của chính mình hoặc admin
        if request.user == review.user or request.user.is_staff:
            review.delete()

    if dish_id:
        return redirect('food:dish_detail', dish_id=dish_id)
    elif cooperate_dish_id:
        return redirect('cooperate:cooperate_dish_detail', dish_id=cooperate_dish_id)
    else:
        return redirect('food:home')

def delete_restaurant_review(request, review_id):
    """
    Xóa review của nhà hàng
    """
    review = get_object_or_404(Review, id=review_id)
    restaurant_id = review.restaurant.id
    
    if request.method == "POST":
        # Chỉ cho phép user xóa review của chính mình hoặc admin
        if request.user == review.user or request.user.is_staff:
            review.delete()
    
    return redirect('food:restaurant_detail', pk=restaurant_id)


@login_required
def profile(request):
    """
    Trang hồ sơ người dùng + danh sách quán yêu thích.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    favorites = profile.favorites.all()

    if request.method == 'POST':
        # Cập nhật thông tin User
        request.user.first_name = request.POST.get('first_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Cập nhật UserProfile
        profile.phone = request.POST.get('phone', '')
        profile.province = request.POST.get('province', '')
        profile.gender = request.POST.get('gender', '')
        
        # Xử lý ngày sinh
        birth_date = request.POST.get('birth_date', '')
        if birth_date:
            profile.birth_date = birth_date
        
        # Xử lý avatar
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, '✅ Cập nhật thông tin thành công!')
        return redirect('food:profile')

    context = {
        'favorites': favorites,
        'profile': profile,
    }
    return render(request, 'food/edit_profile.html', context)


@login_required
def toggle_favorite(request, restaurant_id):
    """
    Thêm / bỏ quán khỏi danh sách yêu thích (AJAX).
    """
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if restaurant in profile.favorites.all():
            profile.favorites.remove(restaurant)
            is_favorite = False
        else:
            profile.favorites.add(restaurant)
            is_favorite = True

        return JsonResponse({'is_favorite': is_favorite})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def logout_view(request):
    """Đăng xuất rồi quay về trang chủ."""
    logout(request)
    return redirect('food:home')


@login_required
def add_review_or_reply(request, restaurant_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    content = (request.POST.get("content") or "").strip()
    parent_id = request.POST.get("parent_id")  # optional

    if not content:
        return HttpResponseBadRequest("Empty content")

    parent = None
    if parent_id:
        parent = get_object_or_404(Review, id=parent_id, restaurant=restaurant, parent__isnull=True)

    Review.objects.create(
        restaurant=restaurant,
        user=request.user,
        content=content,
        parent=parent,
        rating=0 if parent else float(request.POST.get("rating") or 0),  # reply không cần rating
    )

    return redirect("food:restaurant_detail", restaurant_id)