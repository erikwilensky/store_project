from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return 0
    try:
        return dictionary.get(key, 0)
    except (AttributeError, TypeError):
        return 0