from django import template

register = template.Library()


@register.filter
def get_field(form, field_name):
    return form[field_name]



@register.filter
def attr(obj, name):
    return obj.get(name)

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)