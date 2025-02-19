from django import template

register = template.Library()

@register.filter(name='sub')
def sub(value, arg):
    #减法过滤器
    return int(value) - int(arg)
