from curia.authentication.models import Detail
from datetime import timedelta
from curia import *

def get_start_of_period(reference, user):
    start_time = first_of_previous_month(reference)
    days_offset = int(get_period_setting(user).value)
    start_time += timedelta(days=days_offset-1)
    return start_time

def get_end_of_period(reference, user):
    end_time = first_of_next_month(reference)
    days_offset = int(get_period_setting(user).value)
    end_time += timedelta(days=days_offset)
    return end_time

def get_bank_setting(user):
    return Detail.objects.get_or_create(owner_user=user, owner_group__isnull=True, name='mammon_bank', defaults={'value':'Nordea'})[0]

def get_period_setting(user):
    return Detail.objects.get_or_create(owner_user=user, owner_group__isnull=True, name='mammon_period_days', defaults={'value':'25'})[0]

def get_history_months_setting(user):
    return Detail.objects.get_or_create(owner_user=user, owner_group__isnull=True, name='mammon_history_months', defaults={'value':'12'})[0]
 
def update_matches_for_user(user, reset=False):
    from mammon.money.models import *
    categories = list(Category.objects.filter(user=user))
    if reset:
        transactions = Transaction.objects.filter(user=user)
    else:
        transactions = Transaction.objects.filter(user=user, category__isnull=True)

    for transaction in transactions:
        for category in categories:
            if category.matches(transaction):
                transaction.category = category
                transaction.save()
                continue

