from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone
import datetime


class DailyEntry(models.Model):
    ENTRY_TYPES = [
        ('SHOE_REVENUE', _('Shoe Shop Revenue')),
        ('BARBER_ADULT', _('Barber Adult Haircut')),
        ('BARBER_CHILD', _('Barber Child Haircut')),
        ('BARBER_FREE', _('Barber Free Haircut')),
        ('MEATBALL_SALES', _('Meatball Sales')),
        ('MEATBALL_SALAD', _('Meatball Salad Cost')),
    ]

    date = models.DateField(_('Date'))
    entry_type = models.CharField(_('Entry Type'), max_length=20, choices=ENTRY_TYPES)
    value = models.DecimalField(
        _('Value'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        unique_together = ['date', 'entry_type']
        indexes = [
            models.Index(fields=['date', 'entry_type']),
        ]
        ordering = ['-date', 'entry_type']
        verbose_name = _('Daily Entry')
        verbose_name_plural = _('Daily Entries')

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.date} - ฿{self.value}"


class Task(models.Model):
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    deadline = models.DateField(_('Deadline'), null=True, blank=True)
    completed = models.BooleanField(_('Completed'), default=False)
    parent_task = models.ForeignKey(
        'self',
        verbose_name=_('Parent Task'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        ordering = ['deadline', '-created_at']
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return self.name

    def get_all_subtasks(self):
        return self.subtasks.all()

    def is_overdue(self):
        if self.deadline and not self.completed:
            return self.deadline < timezone.now().date()
        return False


class Account(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    balance = models.DecimalField(
        _('Balance'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    goal = models.DecimalField(
        _('Goal'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')

    def __str__(self):
        return self.name

    def progress_percentage(self):
        if self.goal <= 0:
            return 100
        progress = (self.balance / self.goal) * 100
        return min(progress, 100)

    def remaining_amount(self):
        return max(self.goal - self.balance, Decimal('0.00'))


class InventoryItem(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    cost = models.DecimalField(
        _('Cost'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Inventory Item')
        verbose_name_plural = _('Inventory Items')

    def __str__(self):
        return f"{self.name} - ฿{self.cost}"


class WeeklyInventory(models.Model):
    INVENTORY_TYPES = [
        ('START', _('Start of Week')),
        ('END', _('End of Week')),
    ]

    item = models.ForeignKey(
        InventoryItem,
        verbose_name=_('Item'),
        on_delete=models.CASCADE,
        related_name='weekly_counts'
    )
    week_number = models.IntegerField(_('Week Number'))
    year = models.IntegerField(_('Year'))
    inventory_type = models.CharField(_('Type'), max_length=5, choices=INVENTORY_TYPES)
    quantity = models.IntegerField(_('Quantity'), validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        unique_together = ['item', 'week_number', 'year', 'inventory_type']
        indexes = [
            models.Index(fields=['week_number', 'year']),
        ]
        ordering = ['-year', '-week_number', 'item']
        verbose_name = _('Weekly Inventory')
        verbose_name_plural = _('Weekly Inventories')

    def __str__(self):
        return f"{self.item.name} - Week {self.week_number}/{self.year} - {self.get_inventory_type_display()}"

    @staticmethod
    def get_completed_weeks():
        """Returns weeks that have both start and end counts for all items"""
        weeks = WeeklyInventory.objects.values('week_number', 'year').distinct()
        completed_weeks = []
        for week in weeks:
            items_count = InventoryItem.objects.count()
            week_counts = WeeklyInventory.objects.filter(
                week_number=week['week_number'],
                year=week['year']
            ).count()
            if week_counts == items_count * 2:  # Both START and END for all items
                completed_weeks.append({
                    'week_number': week['week_number'],
                    'year': week['year'],
                    'is_complete': True
                })
        return completed_weeks

    @classmethod
    def generate_report(cls, year, week):
        """Generates usage report for a specific week"""
        inventories = cls.objects.filter(year=year, week_number=week)
        report = {}

        for item in InventoryItem.objects.all():
            start = inventories.filter(item=item, inventory_type='START').first()
            end = inventories.filter(item=item, inventory_type='END').first()

            if start and end:
                used = start.quantity - end.quantity
                cost = used * item.cost
                report[item.name] = {
                    'start': start.quantity,
                    'end': end.quantity,
                    'used': used,
                    'cost': cost
                }

        return report


# core/models.py
def check_database():
    try:
        with get_connection() as conn:
            # Check tables exist
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN 
                ('daily_entries', 'inventory_items', 'weekly_inventory')
            """).fetchall()

            # Check sample data
            sample = conn.execute("""
                SELECT * FROM daily_entries LIMIT 1
            """).fetchall()

            return bool(tables and sample)
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False