from django.contrib import admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "chinese", "pinyin", "translation", "topic", "hsk_level", "created_at")
    search_fields = ("chinese", "pinyin", "translation", "topic")
    list_filter = ("hsk_level", "topic")