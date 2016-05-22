from django.template import Library


register = Library()


@register.filter
def relative_date(value):
    from curia import relative_date_formatting
    return relative_date_formatting(value)


@register.filter
def javascript_string_escape(value):
    return value.replace('\r', '\n').replace('\\', '\\\\').replace('\n', '\\\n').replace('\"', '\\"')
