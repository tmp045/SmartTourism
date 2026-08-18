from django.contrib import admin
from django.utils.html import format_html
from .models import Cooperation

from food.models import Restaurant


@admin.register(Cooperation)
class CooperationAdmin(admin.ModelAdmin):
    list_display = ('restaurant_name', 'phone', 'email', 'image_thumbnail', 'is_approved', 'created_at')
    search_fields = ('restaurant_name', 'email')
    list_filter = ('is_approved', 'created_at')
    readonly_fields = ('image_preview', 'created_at')
    actions = ['approve_and_sync']  # ✅ đổi tên rõ hơn

    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('restaurant_name', 'phone', 'email', 'is_approved')
        }),
        ('Địa chỉ & Mô tả', {
            'fields': ('address', 'description', 'opening_hours')
        }),
        ('Hình ảnh', {
            'fields': ('image', 'image_preview')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # =========================
    #  UI image helpers
    # =========================
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:5px;" />',
                obj.image.url
            )
        return "❌"
    image_thumbnail.short_description = "Ảnh"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:400px;max-height:400px;border-radius:8px;" />',
                obj.image.url
            )
        return "Chưa có ảnh"
    image_preview.short_description = "Preview Ảnh"

    # =========================
    #  CORE: sync to Restaurant
    # =========================
    def sync_to_restaurant(self, coop: Cooperation):
        """
        Đồng bộ Cooperation -> Restaurant
        - update_or_create để luôn cập nhật data mới
        - nếu Restaurant không có field nào đó thì xóa key tương ứng
        """
        defaults = {
            "address": coop.address,
            "description": coop.description or "",
            "image": coop.image,
            "rating": 0,
        }

        # Nếu Restaurant của bạn có opening_hours / phone... thì mở thêm:
        if hasattr(Restaurant, "opening_hours"):
            defaults["opening_hours"] = coop.opening_hours or ""
        if hasattr(Restaurant, "phone"):
            defaults["phone"] = coop.phone
        if hasattr(Restaurant, "email"):
            defaults["email"] = coop.email

        # Nếu Cooperation có lat/lng và Restaurant có lat/lng:
        if hasattr(coop, "latitude") and hasattr(Restaurant, "latitude"):
            defaults["latitude"] = coop.latitude
        if hasattr(coop, "longitude") and hasattr(Restaurant, "longitude"):
            defaults["longitude"] = coop.longitude

        # Nếu Restaurant có cuisine_type thì set mặc định
        if hasattr(Restaurant, "cuisine_type"):
            defaults["cuisine_type"] = getattr(coop, "cuisine_type", "") or "Chưa xác định"

        # ✅ Key để tìm restaurant
        # Nếu Restaurant có email -> dùng email sẽ chắc nhất
        if hasattr(Restaurant, "email") and coop.email:
            Restaurant.objects.update_or_create(
                email=coop.email,
                defaults={**defaults, "name": coop.restaurant_name},
            )
        else:
            # fallback theo name
            Restaurant.objects.update_or_create(
                name=coop.restaurant_name,
                defaults=defaults,
            )

    # =========================
    #  1) SAVE: tick duyệt rồi save cũng sync
    # =========================
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_approved:
            self.sync_to_restaurant(obj)

    # =========================
    #  2) ACTION: duyệt hàng loạt + sync
    # =========================
    def approve_and_sync(self, request, queryset):
        count = 0
        for coop in queryset:
            coop.is_approved = True
            coop.save()
            self.sync_to_restaurant(coop)
            count += 1
        self.message_user(request, f"✅ Đã duyệt và đồng bộ {count} quán sang Restaurants")

    approve_and_sync.short_description = "✅ Approve & Sync to Restaurants"
