from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('food.urls')),
    path('accounts/', include('allauth.urls')),
    path('search/', include('search.urls')),
    path('cooperate/', include('cooperate.urls')),
]

# ← THÊM ĐOẠN NÀY
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Browser reload support
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]