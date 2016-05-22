from collections import defaultdict
from datetime import timedelta, datetime
from time import strptime
from mammon.middleware import get_current_request


def first_of_next_month(reference_date):
    if reference_date.month == 12:
        return datetime(reference_date.year + 1, 1, 1)
    else:
        return datetime(reference_date.year, reference_date.month + 1, 1)


def first_of_previous_month(reference_date):
    if reference_date.month == 1:
        return datetime(reference_date.year - 1, 12, 1)
    else:
        return datetime(reference_date.year, reference_date.month - 1, 1)


def get_start_of_period(reference, user):
    start_time = first_of_previous_month(reference)
    days_offset = int(get_period_setting(user).value)
    start_time += timedelta(days=days_offset - 1)
    return start_time


def get_end_of_period(reference, user):
    end_time = first_of_next_month(reference)
    days_offset = int(get_period_setting(user).value)
    end_time += timedelta(days=days_offset)
    return end_time


def get_period_setting(user):
    from mammon.authentication.models import Detail
    request = get_current_request()
    if not hasattr(request, 'period_setting'):
        request.period_setting = Detail.objects.get_or_create(owner_user=user, owner_group__isnull=True, name='mammon_period_days', defaults={'value': '25'})[0]
    return request.period_setting


def get_history_months_setting(user):
    from mammon.authentication.models import Detail
    return Detail.objects.get_or_create(owner_user=user, owner_group__isnull=True, name='mammon_history_months', defaults={'value': '12'})[0]


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
    return 'd' in classification and '1' in classification


def expand_format(fmt):
    m = {
        't': 'description',
        'd': 'date',
        '_': 'empty',
        '1': 'number',
    }
    return ', '.join([m[x] for x in fmt])


def datetime_from_string(string):
    try:
        string = string.strip()
        string, dot, microseconds = string.partition('.')
        microseconds = int(microseconds.rstrip("Z") or '0')
        return datetime(*strptime(string, '%Y-%m-%d %H:%M:%S')[:6]) + timedelta(microseconds=microseconds)
    except ValueError:
        pass
    try:
        return datetime(*strptime(string, '%Y-%m-%d %H:%M')[:6])
    except ValueError:
        try:
            return datetime(*strptime(string, '%Y-%m-%d')[:3])
        except ValueError:
            return datetime(*strptime(string, '%y-%m-%d')[:3])


def standardize_number(s):
    s = s.strip()
    if s == '':
        return 0.0
    if s.endswith('kr'):
        s = s[:-2].replace(',', '.')
    if len(s) > 3 and s[-3] == ',':
        s = s.replace('.', '').replace(',', '.').replace(' ', '')
    else:
        s = s.replace(',', '').replace(' ', '')
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
        return '1'
    return 't'


def classify_row(row):
    classification = ''
    for item in row:
        classification += classify(item)
    return classification, row


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
        if a + b == result or a - b == result:
            return index2
        if b + a == result or b - a == result:
            return index1
    return -1


def original_line_hash(amount, a_datetime, description, user):
    assert isinstance(amount, float)
    assert isinstance(a_datetime, datetime)
    assert isinstance(description, unicode)
    import hashlib
    original = (u'%s\t%s\t%s\t%s' % (user.id, amount, a_datetime.strftime('%Y-%m-%d'), description)).encode('ascii', 'xmlcharrefreplace')
    original_md5 = hashlib.md5(original).hexdigest()
    return original_md5


def nest_dict(list_of_dicts, keys, unroll_last_list=True):
    if not keys:
        if unroll_last_list and type(list_of_dicts) in (tuple, list) and len(list_of_dicts) == 1:
            return list_of_dicts[0]
        return list_of_dicts
    first_key = keys[0]
    rest_keys = keys[1:]
    result = defaultdict(list)
    for r in list_of_dicts:
        result[r[first_key]] += [{k: v for k, v in r.items() if k != first_key}]
    return {k: nest_dict(v, rest_keys) for k, v in result.items()}
