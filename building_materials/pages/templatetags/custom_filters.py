from django import template

register = template.Library()


@register.filter
def replace_space(value):
    """Заменяет пробелы на подчеркивания для безопасных id"""
    return value.replace(" ", "_")
