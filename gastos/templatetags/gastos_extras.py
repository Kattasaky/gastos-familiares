from django import template

register = template.Library()


@register.filter(name='abs_value')
def abs_value(value):
    """
    Filtro de valor absoluto.
    Uso: {{ -5|abs_value }} → 5
    """
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter(name='mul')
def mul(value, arg):
    """Multiplicar: {{ 5|mul:3 }} → 15"""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter(name='div')
def div(value, arg):
    """Dividir: {{ 10|div:2 }} → 5"""
    try:
        return float(value) / float(arg)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
