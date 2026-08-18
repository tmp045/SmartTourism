from django.db import models
from search.models import Province , Ward
class Cooperation(models.Model):
    restaurant_name = models.CharField(max_length=255, verbose_name="Tên quán")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(verbose_name="Email")
    address = models.TextField(verbose_name="Địa chỉ")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    opening_hours = models.TextField(blank=True, null=True, verbose_name="Giờ hoạt động")
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    image = models.ImageField(
        upload_to='cooperations/',
        blank=True,
        null=True,
        verbose_name="Hình ảnh quán"
    )
    
    is_approved = models.BooleanField(default=False, verbose_name="Đã duyệt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Cooperate"  # Đổi từ "Hợp tác" thành "Cooperate"
        verbose_name_plural = "Cooperates"  # Đổi từ "Danh sách hợp tác" thành "Cooperates"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.restaurant_name


class Dish(models.Model):
    cooperation = models.ForeignKey(Cooperation, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='dish_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.cooperation.restaurant_name}"


