from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dict by key - used in results template"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def minutes_display(seconds):
    if not seconds:
        return '0'
    return str(seconds // 60)
