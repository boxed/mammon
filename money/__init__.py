from datetime import timedelta, datetime
from time import strptime
from curia import *
from curia.authentication.models import Detail

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
    from mammon.money.models import Category, Transaction
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

def update_matches_for_user_and_category(user, category):
    from mammon.money.models import Transaction
    transactions = Transaction.objects.filter(user=user, category__isnull=True)

    for transaction in transactions:
        if category.matches(transaction):
            transaction.category = category
            transaction.save()
            continue

def has_requisite_data(classification):
    return 't' in classification and 'd' in classification and '1' in classification

def expand_format(format):
    m = {
        't': 'description',
        'd': 'date',
        '_': 'empty',
        '1': 'number',
    }
    return ', '.join([m[x] for x in format])

def datetime_from_string(string):
    try:
        string = string.strip()
        string, dot, microseconds = string.partition('.')
        microseconds = int(microseconds.rstrip("Z") or '0')
        return datetime(*strptime(string, '%Y-%m-%d %H:%M:%S')[:6])+timedelta(microseconds=microseconds)
    except ValueError:
        pass
    try:
        return datetime(*strptime(string, '%Y-%m-%d %H:%M')[:6])
    except ValueError:
        return datetime(*strptime(string, '%Y-%m-%d')[:3])

def standardize_number(s):
    if len(s) > 3 and s[-3] == ',':
        s = s.replace('.', '').replace(',', '.').replace(' ', '')
    else:
        s = s.replace(',', '').replace(' ', '')
    if s == '':
        raise ValueError()
    else:
        return float(s)

def classify(item):
    item = item.strip()
    try:
        datetime_from_string(item)
        return 'd'
    except ValueError:
        pass
    try:
        standardize_number(item)
        return '1'
    except ValueError:
        pass
    if item == '':
        return '_'
    return 't'

def classify_row(row):
    classification = ''
    for item in row:
        classification += classify(item)
    return classification, row

def has_requisite_data(classification):
    return 't' in classification and 'd' in classification and '1' in classification

def find_default_number(table, most_significant_format):
    from itertools import permutations
    number_rows = {}
    for index, column in enumerate(most_significant_format):
        if column == '1':
            number_rows[index] = [standardize_number(x[1][index]) for x in table if x[0] == most_significant_format]
    for index1, index2 in permutations(number_rows.keys(), 2):
        a = number_rows[index1][0]
        b = number_rows[index2][0]
        result = number_rows[index2][1]
        if a+b == result or a-b == result:
            return index2
        if b+a == result or b-a == result:
            return index1
    return -1
