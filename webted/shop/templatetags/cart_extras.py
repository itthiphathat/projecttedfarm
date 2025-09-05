from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """ คูณค่า value กับ arg """
    return value * arg

@register.filter
def to_int(value):
    """ แปลงค่าเป็น int """
    return int(value)
