from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # loại ẩm thực (fastfood, lẩu, cơm…)
    cuisine_type = models.CharField(max_length=100, blank=True)

    # trạng thái & tiện ích
    has_parking = models.BooleanField(default=False)  # dùng chung nếu muốn
    has_bike_parking = models.BooleanField(default=False)
    has_car_parking = models.BooleanField(default=False)
    has_seating = models.BooleanField(default=True)
    can_take_away = models.BooleanField(default=True)

    # flag fallback nếu chưa cấu hình giờ mở cửa
    is_open = models.BooleanField(default=True)

    rating = models.FloatField(default=0)

    # giá & độ phổ biến (phục vụ sort / map)
    avg_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    popularity = models.IntegerField(default=0)

    # toạ độ cho map (có cũng được, không có thì bỏ qua)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # mã tỉnh/phường (nếu muốn filter theo Province/Ward)
    province_code = models.CharField(max_length=10, blank=True)
    ward_code = models.CharField(max_length=20, blank=True)

    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)

    # ===== GIỜ MỞ CỬA =====
    # Ca 1 (ví dụ sáng / trưa)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    # Ca 2 (ví dụ chiều / tối)
    opening_time_2 = models.TimeField(null=True, blank=True)
    closing_time_2 = models.TimeField(null=True, blank=True)

    def update_avg_price(self):
        avg = self.dishes.aggregate(avg=Avg("price"))["avg"]
        self.avg_price = avg
        self.save(update_fields=["avg_price"])
        
    def __str__(self):
        return self.name

    @property
    def is_open_now(self):
        """
        Tự tính đang mở hay đóng dựa vào 1 hoặc 2 khung giờ.
        - Nếu chưa set KHUNG GIỜ NÀO → fallback dùng field is_open (tick tay).
        - Hỗ trợ cả khung giờ qua 0h (vd 18:00 -> 02:00).
        """

        def in_range(start, end, now_time):
            if not start or not end:
                return False

            if start < end:
                # cùng 1 ngày, vd 08:00–22:00
                return start <= now_time <= end
            else:
                # qua 0h, vd 18:00–02:00
                return now_time >= start or now_time <= end

        # Nếu không cấu hình gì thì dùng is_open
        if not (self.opening_time or self.closing_time or
                self.opening_time_2 or self.closing_time_2):
            return self.is_open

        now = timezone.localtime().time()

        # mở nếu rơi vào 1 trong 2 khung giờ
        if in_range(self.opening_time, self.closing_time, now):
            return True
        if in_range(self.opening_time_2, self.closing_time_2, now):
            return True
        return False

class Dish(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='dishes'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=255, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_specialty = models.BooleanField(default=False)

    image = models.ImageField(
        upload_to='restaurants/dishes/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"

    # ===============================
    # 🔥 AUTO UPDATE AVG PRICE
    # ===============================
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.restaurant:
            avg = self.restaurant.dishes.aggregate(
                avg=Avg("price")
            )["avg"]

            self.restaurant.avg_price = avg
            self.restaurant.save(update_fields=["avg_price"])

    def delete(self, *args, **kwargs):
        restaurant = self.restaurant
        super().delete(*args, **kwargs)

        if restaurant:
            avg = restaurant.dishes.aggregate(
                avg=Avg("price")
            )["avg"]

            restaurant.avg_price = avg
            restaurant.save(update_fields=["avg_price"])

class DishReview(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    cooperate_dish = models.ForeignKey(
        'cooperate.Dish',
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dish_reviews'
    )
    stars = models.IntegerField(choices=[(i, f'{i} sao') for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        dish_name = self.dish.name if self.dish else (self.cooperate_dish.name if self.cooperate_dish else 'Unknown')
        return f"{dish_name} - {self.stars} sao"


class Review(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_reviews'
    )

    # reply support
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies"
    )

    # ⭐ stars: cho phép null để reply không cần chấm sao
    stars = models.IntegerField(
        choices=[(i, f'{i} sao') for i in range(1, 6)],
        null=True,
        blank=True
    )

    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_reply(self):
        return self.parent_id is not None

    def __str__(self):
        return f"{self.restaurant.name} - {self.stars or '-'} sao"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    province = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    favorites = models.ManyToManyField(
        Restaurant,
        blank=True,
        related_name='favorited_by'
    )

    def __str__(self):
        return f"Profile of {self.user.username}"
