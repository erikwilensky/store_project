from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import DailyEntry, Task, Account, InventoryItem, WeeklyInventory

# core/forms.py
class BaseEntryForm(forms.Form):
    date = forms.DateField(
        initial=timezone.now,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().strftime('%Y-%m-%d')
            }
        )
    )

class DateInput(forms.DateInput):
    input_type = 'date'


class DailyEntryForm(forms.ModelForm):
    class Meta:
        model = DailyEntry
        fields = ['date', 'entry_type', 'value']
        widgets = {
            'date': DateInput(attrs={'class': 'form-control'}),
            'entry_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ShoeShopForm(forms.Form):
    date = forms.DateField(
        label=_('Date'),
        initial=timezone.now,
        widget=DateInput(attrs={'class': 'form-control'})
    )
    revenue = forms.DecimalField(
        label=_('Revenue (฿)'),
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'})
    )


class BarberShopForm(forms.Form):
    date = forms.DateField(
        label=_('Date'),
        initial=timezone.now,
        widget=DateInput(attrs={'class': 'form-control'})
    )
    adult_haircuts = forms.IntegerField(
        label=_('Adult Haircuts'),
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )
    child_haircuts = forms.IntegerField(
        label=_('Child Haircuts'),
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )
    free_haircuts = forms.IntegerField(
        label=_('Free Haircuts'),
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )


class MeatballStandForm(forms.Form):
    date = forms.DateField(
        label=_('Date'),
        initial=timezone.now,
        widget=DateInput(attrs={'class': 'form-control'})
    )
    sales = forms.DecimalField(
        label=_('Sales (฿)'),
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'})
    )
    salad_cost = forms.DecimalField(
        label=_('Salad Cost (฿)'),
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'})
    )


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'deadline', 'parent_task']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deadline': DateInput(attrs={'class': 'form-control'}),
            'parent_task': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError(_('Deadline cannot be in the past'))
        return deadline


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'goal']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'goal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_goal(self):
        goal = self.cleaned_data.get('goal')
        if goal and goal <= 0:
            raise forms.ValidationError(_('Goal must be greater than zero'))
        return goal


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0'
            })
        }


class WeeklyInventoryForm(forms.ModelForm):
    class Meta:
        model = WeeklyInventory
        fields = ['item', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1'
            })
        }


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        label=_('Start Date'),
        widget=DateInput(attrs={'class': 'form-control'})
    )
    end_date = forms.DateField(
        label=_('End Date'),
        widget=DateInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(_('End date must be after start date'))

        return cleaned_data