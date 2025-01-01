
from .models import (
    DailyEntry, Task, Account, InventoryItem, WeeklyInventory
)
from .forms import (
    ShoeShopForm, BarberShopForm, MeatballStandForm,
    TaskForm, AccountForm, InventoryItemForm,
    WeeklyInventoryForm, DateRangeForm
)

from decimal import Decimal, InvalidOperation
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg, F, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Avg, F, Q, Case, When, Value, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime
from decimal import Decimal


def home(request):
    # Get date range - default to today
    selected_date = request.GET.get('start_date', timezone.now().date())
    end_date = request.GET.get('end_date', selected_date)

    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Calculate number of days
    days = Decimal((end_date - selected_date).days + 1)

    # Barber Shop Profits
    barber_profits = (
        DailyEntry.objects
        .filter(
            entry_type__in=['BARBER_ADULT', 'BARBER_CHILD'],
            date__gte=selected_date,
            date__lte=end_date
        )
        .aggregate(
            total=Coalesce(
                Sum(
                    Case(
                        When(entry_type='BARBER_ADULT',
                             then=F('value') * Value(Decimal('120'))),
                        When(entry_type='BARBER_CHILD',
                             then=F('value') * Value(Decimal('100'))),
                        default=Value(Decimal('0')),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                Value(Decimal('0'))
            )
        )
    )
    barber_profit = Decimal(barber_profits['total']) / 2 - (Decimal('260') * days)

    # Shoe Shop Profits
    shoe_profits = (
        DailyEntry.objects
        .filter(
            entry_type='SHOE_REVENUE',
            date__gte=selected_date,
            date__lte=end_date
        )
        .aggregate(
            total=Coalesce(
                Sum('value'),
                Value(Decimal('0'))
            )
        )
    )
    shoe_profit = shoe_profits['total'] - (Decimal('110') * days)  # Changed from division by 2

    # Meatball Stand Profits
    meatball_profits = (
        DailyEntry.objects
        .filter(
            entry_type__in=['MEATBALL_SALES', 'MEATBALL_SALAD'],
            date__gte=selected_date,
            date__lte=end_date
        )
        .aggregate(
            sales=Coalesce(
                Sum('value', filter=Q(entry_type='MEATBALL_SALES')),
                Value(Decimal('0'))
            ),
            salad_cost=Coalesce(
                Sum('value', filter=Q(entry_type='MEATBALL_SALAD')),
                Value(Decimal('0'))
            )
        )
    )
    meatball_profit = (Decimal(meatball_profits['sales']) / 2 -
                       Decimal(meatball_profits['salad_cost']) -
                       (Decimal('200') * days))

    # Calculate total profit
    total_profit = barber_profit + shoe_profit + meatball_profit

    context = {
        'barber_form': BarberShopForm(initial={'date': timezone.now().date()}),
        'shoe_form': ShoeShopForm(initial={'date': timezone.now().date()}),
        'meatball_form': MeatballStandForm(initial={'date': timezone.now().date()}),
        'selected_date': selected_date,
        'end_date': end_date,
        'profits': {
            'barber': barber_profit,
            'shoe': shoe_profit,
            'meatball': meatball_profit,
            'total': total_profit
        }
    }

    return render(request, 'core/home.html', context)


@require_http_methods(["POST"])
def save_shoe_entry(request):
    form = ShoeShopForm(request.POST)
    if form.is_valid():
        try:
            DailyEntry.objects.update_or_create(
                date=form.cleaned_data['date'],
                entry_type='SHOE_REVENUE',
                defaults={'value': form.cleaned_data['revenue']}
            )
            messages.success(request, _('Shoe shop entry saved successfully!'))
        except Exception as e:
            messages.error(request, str(e))
    else:
        messages.error(request, _('Error saving shoe shop entry.'))
    return redirect('home')


@require_http_methods(["POST"])
def save_barber_entry(request):
    form = BarberShopForm(request.POST)
    if form.is_valid():
        try:
            date = form.cleaned_data['date']
            entries = [
                ('BARBER_ADULT', form.cleaned_data['adult_haircuts']),
                ('BARBER_CHILD', form.cleaned_data['child_haircuts']),
                ('BARBER_FREE', form.cleaned_data['free_haircuts']),
            ]

            for entry_type, value in entries:
                DailyEntry.objects.update_or_create(
                    date=date,
                    entry_type=entry_type,
                    defaults={'value': value}
                )
            messages.success(request, _('Barber shop entry saved successfully!'))
        except Exception as e:
            messages.error(request, str(e))
    else:
        messages.error(request, _('Error saving barber shop entry.'))
    return redirect('home')


@require_http_methods(["POST"])
def save_meatball_entry(request):
    form = MeatballStandForm(request.POST)
    if form.is_valid():
        try:
            date = form.cleaned_data['date']
            entries = [
                ('MEATBALL_SALES', form.cleaned_data['sales']),
                ('MEATBALL_SALAD', form.cleaned_data['salad_cost']),
            ]

            for entry_type, value in entries:
                DailyEntry.objects.update_or_create(
                    date=date,
                    entry_type=entry_type,
                    defaults={'value': value}
                )
            messages.success(request, _('Meatball stand entry saved successfully!'))
        except Exception as e:
            messages.error(request, str(e))
    else:
        messages.error(request, _('Error saving meatball stand entry.'))
    return redirect('home')


def inventory(request):
    if request.method == 'POST':
        if 'add_item' in request.POST:
            form = InventoryItemForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Inventory item added successfully!'))
                return redirect('inventory')
        elif 'set_inventory' in request.POST:
            form = WeeklyInventoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Inventory count saved successfully!'))
                return redirect('inventory')
    else:
        item_form = InventoryItemForm()
        inventory_form = WeeklyInventoryForm()

    items = InventoryItem.objects.all()
    weekly_counts = WeeklyInventory.get_completed_weeks()

    context = {
        'item_form': item_form,
        'inventory_form': inventory_form,
        'items': items,
    }
    return render(request, 'core/inventory.html', context)

def view_inventory_report(request, year, week):
    try:
        report_data = WeeklyInventory.generate_report(year, week)
        context = {
            'report_data': report_data,
            'year': year,
            'week': week
        }
        return render(request, 'core/inventory_report.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('inventory')


# @require_http_methods(["POST"])
# def set_inventory(request):
#     try:
#         date = request.POST.get('date')
#         inventory_type = request.POST.get('inventory_type')
#
#         if not date or not inventory_type:
#             messages.error(request, _('Date and inventory type are required.'))
#             return redirect('inventory')
#
#         # Convert date string to date object
#         date_obj = datetime.strptime(date, '%Y-%m-%d').date()
#
#         # Validate day of week
#         if inventory_type == 'START' and date_obj.weekday() != 0:  # Monday is 0
#             messages.error(request, _('Start of week inventory must be set on Monday'))
#             return redirect('inventory')
#         elif inventory_type == 'END' and date_obj.weekday() != 6:  # Sunday is 6
#             messages.error(request, _('End of week inventory must be set on Sunday'))
#             return redirect('inventory')
#
#         # Get week number and year
#         week_number = date_obj.isocalendar()[1]
#         year = date_obj.year
#
#         # Save inventory entries
#         for key, value in request.POST.items():
#             if key.startswith('quantity_'):
#                 item_id = int(key.split('_')[1])
#                 quantity = int(value)
#
#                 WeeklyInventory.objects.update_or_create(
#                     item_id=item_id,
#                     week_number=week_number,
#                     year=year,
#                     inventory_type=inventory_type,
#                     defaults={'quantity': quantity}
#                 )
#
#         messages.success(request, _('Inventory saved successfully!'))
#     except Exception as e:
#         messages.error(request, str(e))
#
#     return redirect('inventory')
@require_http_methods(["POST"])
def set_inventory(request):
    try:
        date = request.POST.get('date')
        inventory_type = request.POST.get('inventory_type')

        if not date or not inventory_type:
            messages.error(request, _('Date and inventory type are required.'))
            return redirect('inventory')

        # Convert date string to date object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Validate day of week
        if inventory_type == 'START' and date_obj.weekday() != 0:  # Monday is 0
            messages.error(request, _('Start of week inventory must be set on Monday'))
            return redirect('inventory')
        elif inventory_type == 'END' and date_obj.weekday() != 6:  # Sunday is 6
            messages.error(request, _('End of week inventory must be set on Sunday'))
            return redirect('inventory')

        # Get week number and year
        week_number = date_obj.isocalendar()[1]
        year = date_obj.year

        # Save inventory entries
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = int(key.split('_')[1])

                # Validate quantity
                try:
                    quantity = int(value)
                    if quantity < 0:
                        raise ValueError("Quantity cannot be negative")
                except ValueError:
                    messages.error(request, _('Invalid quantity for item'))
                    return redirect('inventory')

                # Update or create inventory entry
                WeeklyInventory.objects.update_or_create(
                    item_id=item_id,
                    week_number=week_number,
                    year=year,
                    inventory_type=inventory_type,
                    defaults={'quantity': quantity}
                )

        messages.success(request, _('Inventory saved successfully!'))
    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory')

@require_http_methods(["POST"])
def add_inventory_item(request):
    form = InventoryItemForm(request.POST)
    if form.is_valid():
        try:
            item = form.save()
            messages.success(request, _('Inventory item added successfully!'))
            return redirect('inventory')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('inventory')
    else:
        messages.error(request, _('Error adding inventory item.'))
        return redirect('inventory')

@require_http_methods(["POST"])
def edit_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    form = InventoryItemForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, _('Item updated successfully!'))
    else:
        messages.error(request, _('Error updating item.'))
    return redirect('inventory')

@require_http_methods(["POST"])
def delete_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    item.delete()
    return JsonResponse({'status': 'success'})




# def inventory_report(request):
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     report_data = None
#
#     if start_date and end_date:
#         # Convert strings to dates
#         start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#         end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
#
#         # Get week numbers
#         start_week = start_date.isocalendar()[1]
#         end_week = end_date.isocalendar()[1]
#         year = start_date.year
#
#         # Get inventory data
#         start_inventories = WeeklyInventory.objects.filter(
#             inventory_type='START',
#             week_number__gte=start_week,
#             week_number__lte=end_week,
#             year=year
#         ).select_related('item')
#
#         end_inventories = WeeklyInventory.objects.filter(
#             inventory_type='END',
#             week_number__gte=start_week,
#             week_number__lte=end_week,
#             year=year
#         ).select_related('item')
#
#         # Get sales data
#         sales = DailyEntry.objects.filter(
#             entry_type='MEATBALL_SALES',
#             date__range=[start_date, end_date]
#         ).aggregate(total_sales=Sum('value'))['total_sales'] or 0
#
#         # Get salad cost
#         salad_costs = DailyEntry.objects.filter(
#             entry_type='MEATBALL_SALAD',
#             date__range=[start_date, end_date]
#         ).aggregate(total_cost=Sum('value'))['total_cost'] or 0
#
#         # Calculate usage and costs
#         items_report = []
#         total_cost = 0
#
#         for start_inv in start_inventories:
#             end_inv = end_inventories.filter(item=start_inv.item).first()
#             if end_inv:
#                 units_used = start_inv.quantity - end_inv.quantity
#                 cost_of_used = units_used * start_inv.item.cost
#                 total_cost += cost_of_used
#
#                 items_report.append({
#                     'name': start_inv.item.name,
#                     'price': start_inv.item.cost,
#                     'units_used': units_used,
#                     'cost_of_used': cost_of_used,
#                     'salad_cost': salad_costs,
#                     'revenue': sales,
#                     'profit': sales - (cost_of_used + salad_costs)
#                 })
#
#         report_data = {
#             'items': items_report,
#             'totals': {
#                 'total_cost': total_cost,
#                 'total_salad': salad_costs,
#                 'total_revenue': sales,
#                 'total_profit': sales - (total_cost + salad_costs)
#             }
#         }
#
#     context = {
#         'start_date': start_date,
#         'end_date': end_date,
#         'report_data': report_data
#     }
#
#     return render(request, 'core/inventory_report.html', context)
# def inventory_report(request):
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     report_data = None
#     report_error = None
#
#     if start_date and end_date:
#         try:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
#
#             # Use isocalendar to get the correct week number
#             start_week = start_date.isocalendar()[1]
#             end_week = end_date.isocalendar()[1]
#             year = end_date.year  # Use end date's year
#
#             # Check for END inventory entries
#             end_inventories = WeeklyInventory.objects.filter(
#                 inventory_type='END',
#                 year=year,
#                 week_number=end_week
#             )
#
#             # If no END inventory, return error
#             if not end_inventories.exists():
#                 report_error = _("No ending inventory found for the selected week. Please set end of week inventory before generating the report.")
#                 return render(request, 'core/inventory_report.html', {
#                     'start_date': start_date,
#                     'end_date': end_date,
#                     'report_error': report_error
#                 })
#
#             # Collect sales and salad costs
#             meatball_sales = DailyEntry.objects.filter(
#                 entry_type='MEATBALL_SALES',
#                 date__range=[start_date, end_date]
#             ).aggregate(total_sales=Coalesce(Sum('value'), Value(Decimal('0'))))['total_sales']
#
#             salad_costs = DailyEntry.objects.filter(
#                 entry_type='MEATBALL_SALAD',
#                 date__range=[start_date, end_date]
#             ).aggregate(total_cost=Coalesce(Sum('value'), Value(Decimal('0'))))['total_cost']
#
#             # Prepare report items
#             items_report = []
#
#             # Get all inventory items
#             for item in InventoryItem.objects.all():
#                 # Find the END inventory for the week
#                 end_inv = WeeklyInventory.objects.filter(
#                     item=item,
#                     inventory_type='END',
#                     year=year,
#                     week_number=end_week
#                 ).first()
#
#                 # Find the START inventory from the previous week
#                 previous_week = end_week - 1 if end_week > 1 else 52
#                 previous_year = year if end_week > 1 else year - 1
#
#                 start_inv = WeeklyInventory.objects.filter(
#                     item=item,
#                     inventory_type='START',
#                     year=previous_year,
#                     week_number=previous_week
#                 ).first()
#
#                 # Calculate units used
#                 if start_inv and end_inv:
#                     units_used = start_inv.quantity - end_inv.quantity
#                     cost_of_used = Decimal(units_used) * item.cost
#                 else:
#                     # If no previous START inventory, assume all current inventory was used
#                     units_used = end_inv.quantity if end_inv else Decimal('0')
#                     cost_of_used = units_used * item.cost
#
#                 # Profit calculation
#                 item_profit = meatball_sales - (cost_of_used + salad_costs)
#
#                 items_report.append({
#                     'name': item.name,
#                     'price': item.cost,
#                     'units_used': units_used,
#                     'cost_of_used': cost_of_used,
#                     'salad_cost': salad_costs,
#                     'revenue': meatball_sales,
#                     'profit': item_profit
#                 })
#
#             # Calculate totals
#             report_data = {
#                 'items': items_report,
#                 'totals': {
#                     'total_cost': sum(item['cost_of_used'] for item in items_report),
#                     'total_salad': salad_costs,
#                     'total_revenue': meatball_sales,
#                     'total_profit': meatball_sales - sum(item['cost_of_used'] for item in items_report) - salad_costs
#                 }
#             }
#
#         except Exception as e:
#             report_error = f"Error generating report: {str(e)}"
#
#     context = {
#         'start_date': start_date,
#         'end_date': end_date,
#         'report_data': report_data,
#         'report_error': report_error
#     }
#
#     return render(request, 'core/inventory_report.html', context)
def inventory_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_data = None
    report_error = None

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get total revenue and salad cost for the period ONCE
            revenue = DailyEntry.objects.filter(
                entry_type='MEATBALL_SALES',
                date__range=[start_date, end_date]
            ).aggregate(total_sales=Coalesce(Sum('value'), Value(Decimal('0'))))['total_sales']

            salad_costs = DailyEntry.objects.filter(
                entry_type='MEATBALL_SALAD',
                date__range=[start_date, end_date]
            ).aggregate(total_cost=Coalesce(Sum('value'), Value(Decimal('0'))))['total_cost']

            items_report = []
            total_inventory_cost = Decimal('0.00')

            for item in InventoryItem.objects.all():
                # Fetch START inventory: Closest inventory before the start_date
                start_inv = WeeklyInventory.objects.filter(
                    item=item,
                    inventory_type='START',
                    year__lte=start_date.year,
                    week_number__lte=start_date.isocalendar()[1]
                ).order_by('-year', '-week_number').first()

                # Fetch END inventory: Closest inventory for the end_date
                end_inv = WeeklyInventory.objects.filter(
                    item=item,
                    inventory_type='END',
                    year__lte=end_date.year,
                    week_number__lte=end_date.isocalendar()[1]
                ).order_by('-year', '-week_number').first()

                # Calculate inventory metrics
                start_qty = start_inv.quantity if start_inv else 0
                end_qty = end_inv.quantity if end_inv else 0
                units_used = max(0, start_qty - end_qty)
                cost_of_used = Decimal(units_used) * item.cost
                total_inventory_cost += cost_of_used

                # Add item data without profit calculation
                items_report.append({
                    'name': item.name,
                    'price': item.cost,
                    'units_used': units_used,
                    'cost_of_used': cost_of_used,
                    'salad_cost': None,  # Remove individual salad cost
                    'revenue': None,      # Remove individual revenue
                    'profit': None        # Remove individual profit
                })

            # Calculate total profit for the entire operation
            total_profit = revenue - (total_inventory_cost + salad_costs)

            # Prepare report data
            report_data = {
                'items': items_report,
                'totals': {
                    'total_cost': total_inventory_cost,
                    'total_salad_cost': salad_costs,
                    'total_revenue': revenue,
                    'total_profit': total_profit,
                },
            }

        except Exception as e:
            report_error = f"Error generating report: {str(e)}"

    return render(request, 'core/inventory_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'report_data': report_data,
        'report_error': report_error
    })



def inventory_report_ajax(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_data = None
    report_error = None

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Use isocalendar to get the correct week number
            start_week = start_date.isocalendar()[1]
            end_week = end_date.isocalendar()[1]
            year = end_date.year  # Use end date's year

            # Check for END inventory
            end_inventories = WeeklyInventory.objects.filter(
                inventory_type='END',
                year=year,
                week_number=end_week
            )

            if not end_inventories.exists():
                report_error = _("No ending inventory found for the selected week. Please set end of week inventory before generating the report.")
                return render(request, 'core/inventory_report_ajax.html', {
                    'start_date': start_date,
                    'end_date': end_date,
                    'report_error': report_error
                })

            # Collect sales and salad costs
            meatball_sales = DailyEntry.objects.filter(
                entry_type='MEATBALL_SALES',
                date__range=[start_date, end_date]
            ).aggregate(total_sales=Coalesce(Sum('value'), Value(Decimal('0'))))['total_sales']

            salad_costs = DailyEntry.objects.filter(
                entry_type='MEATBALL_SALAD',
                date__range=[start_date, end_date]
            ).aggregate(total_cost=Coalesce(Sum('value'), Value(Decimal('0'))))['total_cost']

            # Prepare report items
            items_report = []

            # Get all inventory items
            for item in InventoryItem.objects.all():
                # Find the END inventory for the week
                end_inv = WeeklyInventory.objects.filter(
                    item=item,
                    inventory_type='END',
                    year=year,
                    week_number=end_week
                ).first()

                # Find the START inventory from the previous week
                previous_week = end_week - 1 if end_week > 1 else 52
                previous_year = year if end_week > 1 else year - 1

                start_inv = WeeklyInventory.objects.filter(
                    item=item,
                    inventory_type='START',
                    year=previous_year,
                    week_number=previous_week
                ).first()

                # Calculate units used
                if start_inv and end_inv:
                    units_used = start_inv.quantity - end_inv.quantity
                    cost_of_used = Decimal(units_used) * item.cost
                else:
                    # If no previous START inventory, assume all current inventory was used
                    units_used = end_inv.quantity if end_inv else Decimal('0')
                    cost_of_used = units_used * item.cost

                # Profit calculation
                item_profit = meatball_sales - (cost_of_used + salad_costs)

                items_report.append({
                    'name': item.name,
                    'price': item.cost,
                    'units_used': units_used,
                    'cost_of_used': cost_of_used,
                    'salad_cost': salad_costs,
                    'revenue': meatball_sales,
                    'profit': item_profit
                })

            # Calculate totals
            report_data = {
                'items': items_report,
                'totals': {
                    'total_cost': sum(item['cost_of_used'] for item in items_report),
                    'total_salad': salad_costs,
                    'total_revenue': meatball_sales,
                    'total_profit': meatball_sales - sum(item['cost_of_used'] for item in items_report) - salad_costs
                }
            }

        except Exception as e:
            report_error = f"Error generating report: {str(e)}"

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'report_data': report_data,
        'report_error': report_error
    }

    return render(request, 'core/inventory_report_ajax.html', context)
def move_forward(request):
    if request.method == 'POST':
        if 'add_task' in request.POST:
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                task_form.save()
                messages.success(request, _('Task added successfully!'))
                return redirect('move_forward')
        elif 'add_account' in request.POST:
            account_form = AccountForm(request.POST)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, _('Account added successfully!'))
                return redirect('move_forward')
    else:
        task_form = TaskForm()
        account_form = AccountForm()

    tasks = Task.objects.filter(parent_task=None)
    accounts = Account.objects.all()

    # Calculate the remaining amount for each account
    for account in accounts:
        account.remaining = account.goal - account.balance if account.goal else 0

    context = {
        'task_form': task_form,
        'account_form': account_form,
        'tasks': tasks,
        'accounts': accounts,
    }
    return render(request, 'core/move_forward.html', context)

def reports(request):
    form = DateRangeForm(request.GET or None)
    report_data = None

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        report_data = generate_report(start_date, end_date)

    context = {
        'form': form,
        'report_data': report_data,
    }
    return render(request, 'core/reports.html', context)


# Helper function for generating reports
def generate_report(start_date, end_date):
    report = {
        'shoe_shop': {},
        'barber_shop': {},
        'meatball_stand': {},
    }

    # Shoe Shop Data
    shoe_data = DailyEntry.objects.filter(
        entry_type='SHOE_REVENUE',
        date__range=[start_date, end_date]
    )
    report['shoe_shop'] = {
        'total': shoe_data.aggregate(Sum('value'))['value__sum'] or 0,
        'average': shoe_data.aggregate(Avg('value'))['value__avg'] or 0,
    }

    # Barber Shop Data
    barber_data = DailyEntry.objects.filter(
        entry_type__startswith='BARBER_',
        date__range=[start_date, end_date]
    )
    report['barber_shop'] = {
        'total_haircuts': barber_data.exclude(
            entry_type='BARBER_FREE'
        ).aggregate(Sum('value'))['value__sum'] or 0,
        'free_haircuts': barber_data.filter(
            entry_type='BARBER_FREE'
        ).aggregate(Sum('value'))['value__sum'] or 0,
    }

    # Meatball Stand Data
    meatball_data = DailyEntry.objects.filter(
        entry_type__startswith='MEATBALL_',
        date__range=[start_date, end_date]
    )
    sales = meatball_data.filter(entry_type='MEATBALL_SALES').aggregate(Sum('value'))['value__sum'] or 0
    costs = meatball_data.filter(entry_type='MEATBALL_SALAD').aggregate(Sum('value'))['value__sum'] or 0

    report['meatball_stand'] = {
        'total_sales': sales,
        'total_costs': costs,
        'net_profit': sales - costs,
    }

    # Calculate overall totals
    report['total_revenue'] = (
            report['shoe_shop']['total'] +
            report['barber_shop']['total_haircuts'] +
            report['meatball_stand']['total_sales']
    )

    return report

@require_http_methods(["POST"])
def add_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        try:
            task = form.save()
            return JsonResponse({
                'status': 'success',
                'task_id': task.id,
                'name': task.name,
                'description': task.description,
                'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    else:
        # Return form errors
        errors = {field: errors[0] for field, errors in form.errors.items()}
        return JsonResponse({
            'status': 'error',
            'errors': errors
        }, status=400)


@require_http_methods(["POST"])
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    form = TaskForm(request.POST, instance=task)

    if form.is_valid():
        try:
            task = form.save()
            return JsonResponse({
                'status': 'success',
                'name': task.name,
                'description': task.description,
                'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    else:
        # Return form errors
        errors = {field: errors[0] for field, errors in form.errors.items()}
        return JsonResponse({
            'status': 'error',
            'errors': errors
        }, status=400)

@require_http_methods(["POST"])
def delete_task(request, task_id):
   task = get_object_or_404(Task, id=task_id)
   task.delete()
   return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def complete_task(request, task_id):
   task = get_object_or_404(Task, id=task_id)
   task.completed = True
   task.save()
   return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def add_subtask(request, task_id):
   parent_task = get_object_or_404(Task, id=task_id)
   form = TaskForm(request.POST)
   if form.is_valid():
       subtask = form.save(commit=False)
       subtask.parent_task = parent_task
       subtask.save()
       return JsonResponse({'status': 'success'})
   return JsonResponse({'status': 'error'}, status=400)


def task_diagram(request):
    tasks = Task.objects.all()
    mermaid_code = generate_task_diagram(tasks)  # We'll create this function
    return render(request, 'core/task_diagram.html', {'mermaid_code': mermaid_code})


def generate_task_diagram(tasks):
    diagram = ["graph TD"]

    # Debug logging
    print("Tasks in diagram generation:",
          [(t.id, t.name, t.parent_task_id if t.parent_task else 'None') for t in tasks])

    # Add nodes and relationships
    processed_nodes = set()
    relationships = set()

    for task in tasks:
        task_id = f"task{task.id}"
        # Clean task name and escape quotes
        task_name = task.name.strip().replace('"', '\\"')

        if task_id not in processed_nodes:
            diagram.append(f'    {task_id}["{task_name}"]')
            processed_nodes.add(task_id)

            # If task is completed, style it green, otherwise pink
            if task.completed:
                diagram.append(f'    style {task_id} fill:#90EE90,stroke:#333')
            else:
                diagram.append(f'    style {task_id} fill:#FFB6C1,stroke:#333')

        # Add relationship if task has a parent
        if task.parent_task:
            parent_id = f"task{task.parent_task.id}"
            relationship = f"    {parent_id} --> {task_id}"
            if relationship not in relationships:
                relationships.add(relationship)
                diagram.append(relationship)

    result = "\n".join(diagram)
    print("Generated Mermaid Diagram:")
    print(result)
    return result


def task_diagram(request):
    # Get only active (non-completed) tasks with their relationships
    tasks = Task.objects.select_related('parent_task').all()
    mermaid_code = generate_task_diagram(tasks)
    return render(request, 'core/task_diagram.html', {
        'mermaid_code': mermaid_code,
        'tasks': tasks  # Pass tasks to template for debugging
    })

@require_http_methods(["POST"])
def add_account(request):
   form = AccountForm(request.POST)
   if form.is_valid():
       try:
           account = form.save()
           messages.success(request, _('Account added successfully!'))
           return JsonResponse({'status': 'success', 'account_id': account.id})
       except Exception as e:
           messages.error(request, str(e))
           return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
   return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@require_http_methods(["POST"])
def edit_account(request, account_id):
   account = get_object_or_404(Account, id=account_id)
   form = AccountForm(request.POST, instance=account)
   if form.is_valid():
       form.save()
       return JsonResponse({'status': 'success'})
   return JsonResponse({'status': 'error'}, status=400)

@require_http_methods(["POST"])
def delete_account(request, account_id):
   account = get_object_or_404(Account, id=account_id)
   account.delete()
   return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def update_account_balance(request, account_id):
   account = get_object_or_404(Account, id=account_id)
   try:
       new_balance = Decimal(request.POST.get('balance', 0))
       account.balance = new_balance
       account.save()
       return JsonResponse({'status': 'success'})
   except Exception as e:
       return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

import logging
logger = logging.getLogger('core')


