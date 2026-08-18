from django.contrib import admin
from .models import SearchHistory, Province, Ward


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'keyword', 'timestamp')
    list_filter = ('user',)
    search_fields = ('keyword',)


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'province')
    search_fields = ('code', 'name', 'province__name')
    list_filter = ('province',)
