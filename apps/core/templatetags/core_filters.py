from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Split a string by a delimiter and return a list
    Usage: {{ "apple,orange,banana"|split:"," }}
    """
    if not value:
        return []
    return value.split(delimiter)

@register.filter
def strip(value):
    """
    Strip whitespace from a string
    Usage: {{ " hello world "|strip }}
    """
    if not value:
        return ""
    return str(value).strip()