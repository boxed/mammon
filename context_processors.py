def general(request):
    from django.conf import settings
    if 'HTTP_USER_AGENT' in request.META:
        agent = request.META['HTTP_USER_AGENT'].lower()
    else:
        agent = 'unknown'
    from mammon.money.models import *
    accounts = Account.objects.filter(user=request.user) if request.user.is_authenticated() else []
    return {
        'base':'base.html', 
        'community':'Mammon', 
        'user_agent': agent,
        'settings': settings,
        'accounts': accounts,
        }