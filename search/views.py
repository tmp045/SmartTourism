# search/views.py
from django.shortcuts import render
from django.http import JsonResponse
import json
import math

from .models import SearchHistory, Province, Ward
from food.models import Dish, Restaurant, UserProfile
from .services import basic_search_dish, basic_search_restaurant, fuzzy_filter


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def search_view(request):
    query = (request.GET.get('q') or '').strip()

    # --------- FILTER CƠ BẢN ----------
    scope = request.GET.get('scope') or ''          # nearby / province / ''
    province = request.GET.get('province') or ''
    ward = request.GET.get('ward') or ''

    # --------- FILTER Ở TRANG KẾT QUẢ ----------
    category = request.GET.get('category') or ''
    price_sort = request.GET.get('price_sort') or ''     # asc / desc
    dine_option = request.GET.get('dine_option') or ''   # dine_in / take_away
    has_parking = request.GET.get('has_parking') or ''   # bike / car / both
    specialty = request.GET.get('specialty') == '1'

    # ưu tiên sort
    pri1 = request.GET.get('pri1') or ''
    pri2 = request.GET.get('pri2') or ''
    pri3 = request.GET.get('pri3') or ''

    dish_results = []
    restaurant_results = []

    # giữ lat/lng để template xài (tránh request.GET.lat bị “lúc được lúc không”)
    user_lat_raw = request.GET.get('lat', '')
    user_lng_raw = request.GET.get('lng', '')

    def sort_restaurants_with_priority(restaurants):
        def get_key(r, key):
            if key == 'rating':
                return -(getattr(r, 'rating', 0) or 0)
            if key == 'distance':
                # distance sort đã set khi scope=nearby
                return getattr(r, '_distance_sort', 10**9)
            if key == 'price':
                return getattr(r, 'avg_price', 10**9)
            if key == 'popularity':
                return -(getattr(r, 'popularity', 0) or 0)
            return 0

        priorities = [p for p in [pri1, pri2, pri3] if p]
        if not priorities:
            return restaurants

        restaurants.sort(key=lambda r: tuple(get_key(r, p) for p in priorities))
        return restaurants

    # =====================================================
    #                    SEARCH LOGIC
    # =====================================================
    if query:
        # --- LƯU LỊCH SỬ ---
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, keyword=query)

            qs = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')
            if qs.count() > 64:
                old_ids = list(qs.values_list('id', flat=True)[64:])
                SearchHistory.objects.filter(id__in=old_ids).delete()

        # --- BASIC SEARCH ---
        dish_results = list(basic_search_dish(Dish, query))
        restaurant_results = list(basic_search_restaurant(Restaurant, query))

        # --- FUZZY nếu ít món ---
        if len(dish_results) < 10:
            fuzzy_candidates = Dish.objects.all()[:300]
            fuzzy_added = fuzzy_filter(fuzzy_candidates, 'name', query)
            for d in fuzzy_added:
                if d not in dish_results:
                    dish_results.append(d)

        # --- FILTER CATEGORY ---
        if category:
            dish_results = [
                d for d in dish_results
                if (getattr(d, 'category', '') or '').lower() == category.lower()
            ]

        # --- FILTER ĐẶC SẢN ---
        if specialty:
            dish_results = [d for d in dish_results if getattr(d, 'is_specialty', False)]

        # --- FILTER HÌNH THỨC ĂN ---
        if dine_option:
            if dine_option == 'dine_in':
                dish_results = [d for d in dish_results if getattr(d.restaurant, 'has_seating', False)]
            elif dine_option == 'take_away':
                dish_results = [d for d in dish_results if getattr(d.restaurant, 'can_take_away', False)]

        # --- FILTER PARKING ---
        if has_parking:
            def match_parking(r):
                if has_parking == 'bike':
                    return getattr(r, 'has_bike_parking', False)
                if has_parking == 'car':
                    return getattr(r, 'has_car_parking', False)
                if has_parking == 'both':
                    return getattr(r, 'has_bike_parking', False) and getattr(r, 'has_car_parking', False)
                return True

            restaurant_results = [r for r in restaurant_results if match_parking(r)]
            allowed = {r.id for r in restaurant_results}
            dish_results = [d for d in dish_results if d.restaurant_id in allowed]

        # --- FILTER VỊ TRÍ ---
        if scope == 'nearby' and user_lat_raw and user_lng_raw:
            user_lat = float(user_lat_raw)
            user_lng = float(user_lng_raw)

            def dist_km(r):
                if r.latitude is None or r.longitude is None:
                    return 10**9
                return haversine_km(user_lat, user_lng, float(r.latitude), float(r.longitude))

            for r in restaurant_results:
                r.distance_km = round(dist_km(r), 2)   # show UI
                r._distance_sort = r.distance_km       # sort

            restaurant_results.sort(key=lambda r: getattr(r, '_distance_sort', 10**9))
            restaurant_results = restaurant_results[:10]

            allowed = {r.id for r in restaurant_results}
            dish_results = [d for d in dish_results if d.restaurant_id in allowed]

        elif scope == 'province' and province and ward:
            restaurant_results = [
                r for r in restaurant_results
                if getattr(r, 'province_code', '') == province and getattr(r, 'ward_code', '') == ward
            ]
            allowed = {r.id for r in restaurant_results}
            dish_results = [d for d in dish_results if d.restaurant_id in allowed]

        # --- SORT GIÁ ---
        if price_sort == 'asc':
            dish_results.sort(key=lambda x: x.price)
        elif price_sort == 'desc':
            dish_results.sort(key=lambda x: x.price, reverse=True)

        # --- SORT ƯU TIÊN ---
        restaurant_results = sort_restaurants_with_priority(restaurant_results)

        # ===== GẮN 3 MÓN LIÊN QUAN CHO TỪNG NHÀ HÀNG (LUÔN CÓ) =====
        rest_map = {r.id: r for r in restaurant_results}
        for r in restaurant_results:
            r.match_dishes = []

        q_lower = (query or "").lower()

        # 1) ưu tiên món có chứa keyword (từ dish_results đã search)
        for d in dish_results:
            r = rest_map.get(d.restaurant_id)
            if not r:
                continue
            if len(r.match_dishes) >= 3:
                continue
            if q_lower and q_lower not in (d.name or "").lower():
                continue
            r.match_dishes.append(d)

        # 2) bù cho đủ 3: nếu không có món match keyword thì lấy món bất kỳ của quán
        for r in restaurant_results:
            if len(r.match_dishes) >= 3:
                continue

            need = 3 - len(r.match_dishes)
            existing_ids = {d.id for d in r.match_dishes}

            # ưu tiên món có keyword trước
            fillers = list(
                Dish.objects.filter(restaurant_id=r.id)
                .exclude(id__in=existing_ids)
                .filter(name__icontains=query)[:need]
            )

            # nếu vẫn thiếu -> lấy bất kỳ món nào của quán để đủ 3
            if len(fillers) < need:
                more_need = need - len(fillers)
                more = list(
                    Dish.objects.filter(restaurant_id=r.id)
                    .exclude(id__in=existing_ids)
                    .exclude(id__in=[x.id for x in fillers])[:more_need]
                )
                fillers += more

            r.match_dishes.extend(fillers)

    # =====================================================
    #   PHẦN DƯỚI LUÔN CHẠY
    # =====================================================
    provinces = Province.objects.all()

    # map json
    restaurant_map_data = []
    for r in restaurant_results:
        if not (getattr(r, "latitude", None) and getattr(r, "longitude", None)):
            continue
        try:
            lat_val = float(r.latitude)
            lng_val = float(r.longitude)
        except:
            continue

        avg_price = getattr(r, "avg_price", None)
        try:
            price_val = float(avg_price) if avg_price not in (None, "") else None
        except:
             price_val = None

        rating_val = float(getattr(r, "rating", 0) or 0)

        restaurant_map_data.append({
            "id": r.id,
            "name": r.name,
            "lat": lat_val,
            "lng": lng_val,
            "price": price_val,
            "rating": rating_val,
            "is_open": r.is_open_now,
            "address": r.address,
            "image": r.image.url if getattr(r, "image", None) else "",
        })

    # favorites
    favorite_ids = set()
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        favorite_ids = set(profile.favorites.values_list("id", flat=True))

    return render(request, 'search/results.html', {
        'query': query,
        'dish_results': dish_results,
        'restaurant_results': restaurant_results,

        'favorite_ids': favorite_ids,

        # filter
        'scope': scope,
        'province': province,
        'ward': ward,

        # giữ lat/lng ổn định cho form ưu tiên
        'user_lat': user_lat_raw,
        'user_lng': user_lng_raw,

        # filter trang kết quả
        'category': category,
        'price_sort': price_sort,
        'dine_option': dine_option,
        'has_parking': has_parking,
        'specialty': specialty,
        'provinces': provinces,

        # ưu tiên
        'pri1': pri1,
        'pri2': pri2,
        'pri3': pri3,

        # map json
        'restaurant_map_json': json.dumps(restaurant_map_data, ensure_ascii=False),
    })


def autocomplete(request):
    query = request.GET.get("q", "").strip()
    suggestions = []
    if query:
        dishes = Dish.objects.filter(name__icontains=query).values_list('name', flat=True)[:10]
        restaurants = Restaurant.objects.filter(name__icontains=query).values_list('name', flat=True)[:10]
        suggestions = list(dishes) + list(restaurants)
    return JsonResponse({"suggestions": suggestions})


def get_wards(request):
    province_code = request.GET.get("province", "").strip()
    wards_qs = Ward.objects.none()

    if province_code:
        wards_qs = Ward.objects.filter(province__code=province_code).order_by("name")

    wards = [{"code": w.code, "name": w.name} for w in wards_qs]
    return JsonResponse({"wards": wards})
