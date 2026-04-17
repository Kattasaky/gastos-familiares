from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """
    Filtro personalizado para valor absoluto.
    Uso en template: {{ numero|abs_value }}
    """
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value