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


@register.filter
def duration(td):
    total_seconds = int(td.total_seconds())

    days = total_seconds // 86400
    remaining_hours = total_seconds % 86400
    remaining_minutes = remaining_hours % 3600
    hours = remaining_hours // 3600
    minutes = remaining_minutes // 60
    seconds = remaining_minutes % 60

    days_str = f'{days}дн ' if days else ''
    hours_str = f'{hours}'.rjust(2, '0')
    minutes_str = f'{minutes}'.rjust(2, '0')
    seconds_str = f'{seconds}'.rjust(2, '0')

    return f'{days_str}{hours_str}:{minutes_str}:{seconds_str}'

@register.filter
def get_item(dictionary, key):
    """В словаре с несколькими вложенностями поиск по названию ключей
    {{общий словарь|get_item:ключ первого уровня|get_item:ключ следующего уровня}}"""
    return dictionary.get(key)

@register.filter
def batch(iterable, n):
    """
    Разбивает итерируемый объект на подсписки длиной n.
    Пример: [1, 2, 3, 4, 5] | batch:2 -> [[1, 2], [3, 4], [5]]
    """
    length = len(iterable)
    for i in range(0, length, n):
        yield iterable[i:i + n]

