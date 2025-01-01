from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import DailyEntry, Task, Account, InventoryItem, WeeklyInventory


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'entry_type', 'value', 'created_at')
    list_filter = ('entry_type', 'date')
    search_fields = ('date', 'entry_type')
    ordering = ('-date', 'entry_type')
    date_hierarchy = 'date'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'deadline', 'completed', 'parent_task', 'created_at')
    list_filter = ('completed', 'deadline')
    search_fields = ('name', 'description')
    ordering = ('deadline', '-created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'goal', 'progress_percentage', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    def progress_percentage(self, obj):
        return f"{obj.progress_percentage():.1f}%"

    progress_percentage.short_description = _('Progress')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WeeklyInventory)
class WeeklyInventoryAdmin(admin.ModelAdmin):
    list_display = ('item', 'week_number', 'year', 'inventory_type', 'quantity')
    list_filter = ('inventory_type', 'year', 'week_number')
    search_fields = ('item__name',)
    ordering = ('-year', '-week_number', 'item')
    readonly_fields = ('created_at', 'updated_at')