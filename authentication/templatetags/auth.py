from datetime import datetime, timedelta
from time import strftime

from django.template import Library
from django.utils.translation import ugettext as _


register = Library()


def relative_date_formatting(date, reference_date=None, show_seconds=False, show_time_of_day=False):
    if not show_time_of_day and show_seconds:
        raise Exception('show_seconds can not be True if show_time_of_day is False')
    if reference_date is None:
        reference_date = datetime.now()
    if reference_date == date:
        return _('now')

    diff = date - reference_date

    time_formatting = ''

    if show_seconds:
        time_formatting = '%H:%M:%S'
    elif show_time_of_day or abs(date.toordinal() - reference_date.toordinal()) <= 1:
        time_formatting = '%H:%M'

    if date.toordinal() == reference_date.toordinal():
        s = ''

        if date > reference_date:  # in future
            s = _('in %s') % s

        diff = abs(diff)
        if diff >= timedelta(hours=1):
            hours = diff.seconds / 60 / 60
            s += _('%s h ') % hours
        if diff >= timedelta(minutes=1):
            minutes = diff.seconds / 60 % 60
            s += _('%s min ') % minutes
        if diff < timedelta(minutes=1):
            s += _('%s s ') % diff.seconds

        if date < reference_date:  # in the past
            s = _('%sago') % s

        return s
    if date.toordinal() - reference_date.toordinal() == -1:
        return _('yesterday at %s') % strftime(time_formatting, date.timetuple())
    elif date.toordinal() - reference_date.toordinal() == 1:
        return _('tomorrow at %s') % strftime(time_formatting, date.timetuple())
    elif date.year != reference_date.year:
        return strftime('%d %b %Y ' + time_formatting, date.timetuple())
    else:
        return strftime('%d %b ' + time_formatting, date.timetuple())


@register.filter
def relative_date(value):
    return relative_date_formatting(value)


@register.filter
def multiply(value, arg):
    return float(value) * float(arg)


@register.filter
def divide(value, arg):
    return float(value) / float(arg)


@register.filter
def javascript_string_escape(value):
    return value.replace('\r', '\n').replace('\\', '\\\\').replace('\n', '\\\n').replace('\"', '\\"')
