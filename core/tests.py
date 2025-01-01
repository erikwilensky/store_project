from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from .models import DailyEntry, Task, Account, InventoryItem, WeeklyInventory
from .forms import ShoeShopForm, BarberShopForm, MeatballStandForm

class DailyEntryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

    def test_shoe_shop_entry(self):
        data = {
            'date': self.today,
            'revenue': '1500.50'
        }
        response = self.client.post(reverse('save_shoe_entry'), data)
        self.assertEqual(response.status_code, 200)
        entry = DailyEntry.objects.get(date=self.today, entry_type='SHOE_REVENUE')
        self.assertEqual(entry.value, Decimal('1500.50'))

    def test_barber_shop_entry(self):
        data = {
            'date': self.today,
            'adult_haircuts': '5',
            'child_haircuts': '3',
            'free_haircuts': '1'
        }
        response = self.client.post(reverse('save_barber_entry'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            DailyEntry.objects.get(date=self.today, entry_type='BARBER_ADULT').value,
            Decimal('5')
        )

class TaskTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            name="Test Task",
            description="Test Description",
            deadline=timezone.now().date()
        )

    def test_task_creation(self):
        self.assertEqual(self.task.name, "Test Task")
        self.assertFalse(self.task.completed)

    def test_subtask_creation(self):
        subtask = Task.objects.create(
            name="Subtask",
            parent_task=self.task
        )
        self.assertEqual(subtask.parent_task, self.task)

class AccountTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            name="Test Account",
            balance=Decimal('1000.00'),
            goal=Decimal('2000.00')
        )

    def test_progress_calculation(self):
        self.assertEqual(self.account.progress_percentage(), 50)

    def test_remaining_amount(self):
        self.assertEqual(self.account.remaining_amount(), Decimal('1000.00'))

class InventoryTests(TestCase):
    def setUp(self):
        self.item = InventoryItem.objects.create(
            name="Test Item",
            cost=Decimal('10.00')
        )
        self.today = timezone.now().date()

    def test_weekly_inventory(self):
        WeeklyInventory.objects.create(
            item=self.item,
            week_number=1,
            year=2024,
            inventory_type='START',
            quantity=100
        )
        self.assertTrue(
            WeeklyInventory.objects.filter(item=self.item, inventory_type='START').exists()
        )

class FormTests(TestCase):
    def test_shoe_shop_form(self):
        form_data = {
            'date': timezone.now().date(),
            'revenue': '1500.50'
        }
        form = ShoeShopForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_shoe_shop_form(self):
        form_data = {
            'date': timezone.now().date(),
            'revenue': '-100'  # Negative revenue should be invalid
        }
        form = ShoeShopForm(data=form_data)
        self.assertFalse(form.is_valid())

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_reports_view(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/reports.html')