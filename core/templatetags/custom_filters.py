from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide_by(value, arg):
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply_by(value, arg):
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError):
        return 0