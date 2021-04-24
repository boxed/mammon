# coding=utf-8
from django.utils.safestring import mark_safe


def general(request):
    from django.conf import settings
    if 'HTTP_USER_AGENT' in request.META:
        agent = request.META['HTTP_USER_AGENT'].lower()
    else:
        agent = 'unknown'
    from mammon.money.models import Account
    accounts = Account.objects.filter(user=request.user) if request.user.is_authenticated else []
    is_mac = 'Mac' in request.META.get('HTTP_USER_AGENT', '')
    return {
        'base': 'base.html',
        'community': 'Mammon',
        'user_agent': agent,
        'settings': settings,
        'accounts': accounts,
        'command_button': '⌘' if is_mac else 'Ctrl',
        'ctrl_label': mark_safe('&#x2303;') if is_mac else 'Ctrl+',
        'enter_label': mark_safe('&#x21A9;') if is_mac else 'Enter',
    }
