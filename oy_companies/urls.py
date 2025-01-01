from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from core import views
from django.conf import settings
from django.conf.urls.static import static

# Non-translated URLs
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# Translated URLs
urlpatterns += i18n_patterns(
    # Admin
    path('admin/', admin.site.urls),

    # Main pages
    path('', views.home, name='home'),
    path('inventory/', views.inventory, name='inventory'),
    path('reports/', views.reports, name='reports'),
    path('move-forward/', views.move_forward, name='move_forward'),

    # Daily Entries
    path('save-shoe-entry/', views.save_shoe_entry, name='save_shoe_entry'),
    path('save-barber-entry/', views.save_barber_entry, name='save_barber_entry'),
    path('save-meatball-entry/', views.save_meatball_entry, name='save_meatball_entry'),

    # Inventory Management
    path('add-inventory-item/', views.add_inventory_item, name='add_inventory_item'),
    path('edit-inventory-item/<int:item_id>/', views.edit_inventory_item, name='edit_inventory_item'),
    path('delete-inventory-item/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('set-inventory/', views.set_inventory, name='set_inventory'),
    path('view-inventory-report/<int:year>/<int:week>/', views.view_inventory_report, name='view_inventory_report'),
    path('inventory-report/', views.inventory_report, name='inventory_report'),
    path('inventory-report-ajax/', views.inventory_report_ajax, name='inventory_report_ajax'),
    # Task Management
    path('add-task/', views.add_task, name='add_task'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('add-subtask/<int:task_id>/', views.add_subtask, name='add_subtask'),
    path('task-diagram/', views.task_diagram, name='task_diagram'),
    # Account Management
    path('add-account/', views.add_account, name='add_account'),
    path('edit-account/<int:account_id>/', views.edit_account, name='edit_account'),
    path('delete-account/<int:account_id>/', views.delete_account, name='delete_account'),
    path('update-account-balance/<int:account_id>/', views.update_account_balance, name='update_account_balance'),

    prefix_default_language=False,
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)