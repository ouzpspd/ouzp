from django import template
import urllib.parse


register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Данный метод добавляет в url строку дополнительные параметры. Используется для добавления номера страницы
    в поисковый запрос когда количество результатов больше 50"""
    query = context['request'].GET.copy()
    query.update(kwargs)
    return urllib.parse.urlencode(query)


@register.filter
def multiply(value, arg):
    """Данный метод добавляет пользовательский фильтр в шаблонах с возможностью умножения"""
    return value * arg


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

