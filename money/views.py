# coding=utf-8
from __future__ import unicode_literals
from collections import Counter
from copy import copy
from decimal import Decimal
from math import sqrt
from dateutil.relativedelta import relativedelta
from django.utils.translation import ugettext_lazy
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import login_required
from django.template.context import RequestContext
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator, EmptyPage
from django.db.models.aggregates import Sum
from django.forms import ModelForm
from django import forms
from mammon.money import *
from mammon.money.models import *


def std_deviation(l):
    sum1 = 0.0
    sum2 = 0.0
    n = 0.0
    for x in l:
        sum1 += x
        sum2 += x * x
        n += 1.0
        sum1, sum2, n = sum1, sum2, n
    return sqrt(sum2 / n - sum1 * sum1 / n / n)


class AccessDeniedException(Exception):
    pass


def get_page_size(request):
    if 'page_size' in request.REQUEST:
        return int(request.REQUEST['page_size'])
    return 20


def transaction_filter(request, transactions):
    # limit the transactions for display
    transactions = transactions.filter(user=request.user)
    if 'start_time' in request.REQUEST and 'end_time' in request.REQUEST and request.REQUEST['start_time'] and \
            request.REQUEST['end_time']:
        transactions = transactions.filter(time__gt=datetime_from_string(request.GET['start_time']),
                                           time__lt=datetime_from_string(request.REQUEST['end_time']))
    if 'q' in request.REQUEST and request.REQUEST['q']:
        transactions = transactions.filter(description__icontains=request.REQUEST['q'])
    if 'category' in request.REQUEST and request.REQUEST['category']:
        transactions = transactions.filter(category__pk=request.REQUEST['category'])
    if 'account' in request.REQUEST and request.REQUEST['account']:
        transactions = transactions.filter(account__pk=request.REQUEST['account'])
    if 'greater_than' in request.REQUEST and request.REQUEST['greater_than']:
        transactions = transactions.filter(amount__gt=request.REQUEST['greater_than'])
    if 'less_than' in request.REQUEST and request.REQUEST['less_than']:
        transactions = transactions.filter(amount__lt=request.REQUEST['less_than'])
    return transactions.order_by('-time')


@login_required
def index(request):
    try:
        last_transaction = Transaction.objects.filter(user=request.user).order_by('-time')[0]
    except (Transaction.DoesNotExist, IndexError):
        last_transaction = None
    return render_to_response('money/index.html',
                              RequestContext(request, {
                                  'matched_count': Transaction.objects.filter(user=request.user,
                                                                              category__isnull=False).count(),
                                  'unmatched_count': Transaction.objects.filter(user=request.user,
                                                                                category__isnull=True).count(),
                                  'transactions': transaction_filter(request,
                                                                     Transaction.objects.filter(user=request.user,
                                                                                                category__isnull=True)),
                                  'last_transaction': last_transaction,
                                  'categories': Category.objects.filter(user=request.user),
                              }))


@login_required
def view_categories(request):
    return render_to_response('money/view_categories.html',
                              RequestContext(request, {'categories': Category.objects.filter(user=request.user)}))


@login_required
def view_accounts(request):
    return render_to_response('money/view_accounts.html',
                              RequestContext(request, {'accounts': Account.objects.filter(user=request.user)}))


@login_required
def delete_account(request, account_id):
    account = get_object_or_404(Account, pk=account_id)
    if account.user != request.user:
        raise AccessDeniedException('cannot delete others categories')
    Category.objects.filter(account=account).update(account=None)
    Transaction.objects.filter(account=account).update(account=None)
    account.delete()
    return HttpResponseRedirect('/settings/')


@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if category.user != request.user:
        raise AccessDeniedException('cannot delete others categories')
    Transaction.objects.filter(category=category).update(category=None)
    category.delete()
    return HttpResponseRedirect('/')


@login_required
def view_category(request, category_id, page='1'):
    class EditForm(ModelForm):
        update_existing_transactions = forms.BooleanField(label=ugettext_lazy('Update existing transactions'), required=False)

        class Meta:
            model = Category
            fields = ('name', 'matching_rules', 'period', 'account')

    EditForm.base_fields['account'].queryset = request.user.account_set.all()

    return view_grouping(request, Category, category_id, EditForm, 'category', '/categories', page)


@login_required
def view_account(request, account_id, page='1'):
    class EditForm(ModelForm):
        class Meta:
            model = Account
            fields = ('name',)

    return view_grouping(request, Account, account_id, EditForm, 'account', '/accounts', page)


@login_required
def view_grouping(request, group_class, group_id, form_class, group_name, url_base, page):
    group = get_object_or_404(group_class, pk=group_id)
    if group.user != request.user:
        raise AccessDeniedException('cannot edit others categories')

    transactions = transaction_filter(request, Transaction.objects.filter(**{group_name: group}))

    if request.POST:
        post = copy(request.POST)
        for key, value in post.items():
            if value == 'None':
                post[key] = None
        form = form_class(post, instance=group)
        if form.is_valid():
            group = form.save()
            update_matches_for_user(request.user)
            if 'update_existing_transactions' in form.cleaned_data:
                transactions.update(account=group.account)
    else:
        form = form_class(initial={}, instance=group)

    paginator = Paginator(transactions, get_page_size(request))
    return render_to_response('money/view_category.html', RequestContext(request, {
        'paginator': paginator,
        'page': page,
        'base_url': '%s/%d/' % (url_base, group.id),
        'form': form,
        'transactions': paginator.page(page).object_list,
        'unmatched_transactions': Transaction.objects.filter(user=request.user, category__isnull=True),
        'categories': Category.objects.filter(user=request.user),
        'group': group,
        'group_name': group_name,
        'sum': transactions.aggregate(Sum('amount'))['amount__sum'],
        'delete_message': ugettext_lazy('Delete this %s' % group_name),
        'confirm_delete_message': ugettext_lazy('Are you sure you want to delete this %s?' % group_name),
    }))


@login_required
def view_transactions(request, page='1'):
    transactions = transaction_filter(request, Transaction.objects.filter(user=request.user))
    paginator = Paginator(transactions, get_page_size(request))
    categories = Category.objects.filter(user=request.user)
    accounts = Account.objects.filter(user=request.user)

    data = dict([(key, value) for key, value in request.REQUEST.items() if value])

    class FilterForm(forms.Form):
        q = forms.CharField(label=ugettext_lazy('Description'), required=False)
        start_time = forms.DateTimeField(required=False, label=ugettext_lazy('Start time'))
        end_time = forms.DateTimeField(required=False, label=ugettext_lazy('End time'))
        greater_than = forms.FloatField(required=False, label=ugettext_lazy('Greater than'))
        less_than = forms.FloatField(required=False, label=ugettext_lazy('Less than'))
        category = forms.ChoiceField(choices=[('', '')] + [(category.pk, category.name) for category in categories], required=False, label=ugettext_lazy('Category'))
        account = forms.ChoiceField(choices=[('', '')] + [(account.pk, account.name) for account in accounts], required=False, label=ugettext_lazy('Account'))

    class BulkEditForm(forms.Form):
        bulk_description = forms.CharField(label=ugettext_lazy('Append description'), required=False)
        bulk_category = forms.ChoiceField(choices=[('', '')] + [(category.pk, category.name) for category in categories], required=False, label=ugettext_lazy('Category'))
        bulk_account = forms.ChoiceField(choices=[('', '')] + [(account.pk, account.name) for account in accounts], required=False, label=ugettext_lazy('Account'))

    for name, field in FilterForm.base_fields.items():
        BulkEditForm.base_fields[name] = forms.CharField(required=False, widget=forms.HiddenInput)

    filter_form = FilterForm(data)
    bulk_edit_form = BulkEditForm(data)

    if request.POST:
        update = {}
        if bulk_edit_form.is_valid():
            if bulk_edit_form.cleaned_data['bulk_description']:
                for transaction in transactions:
                    transaction.description += ' ' + bulk_edit_form.cleaned_data['bulk_description']
                    transaction.save()
            if bulk_edit_form.cleaned_data['bulk_category']:
                update['category'] = Category.objects.get(user=request.user,
                                                          pk=bulk_edit_form.cleaned_data['bulk_category'])
            if bulk_edit_form.cleaned_data['bulk_account']:
                update['account'] = Account.objects.get(user=request.user,
                                                        pk=bulk_edit_form.cleaned_data['bulk_account'])
            transactions.update(**update)
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        transactions = paginator.page(page).object_list
    except EmptyPage:
        page = 1
        transactions = paginator.page(page).object_list

    return render_to_response('money/view_transaction_list.html', RequestContext(request, {
        'filter_form': filter_form,
        'bulk_edit_form': bulk_edit_form,
        'paginator': paginator,
        'page': page,
        'base_url': '/transactions/',
        'transactions': transactions,
        'categories': categories,
        'sum': transactions.aggregate(Sum('amount'))['amount__sum'] if transactions else 0,
    }))


@login_required
def export_transactions(request):
    transactions = transaction_filter(request, Transaction.objects.filter(user=request.user)).order_by('time')

    def export():
        for transaction in transactions:
            yield '%s\t%s\t%s\t%s\t%s\n' % (
                transaction.time.date().isoformat(), transaction.description, transaction.amount,
                transaction.category or '', transaction.account or '')

    return HttpResponse(export(), content_type='text/csv; charset="utf8')


@login_required
def import_transactions(request):
    if not request.POST:
        return render_to_response('money/import.html', RequestContext(request, {}))
    else:
        data = force_unicode(request.POST['data'])
        rows = [row for row in data.replace('\r\n', '\n').split('\n') if row]
        for row in rows:
            date, description, amount, category, account = row.split('\t')
            category = Category.objects.get_or_create(user=request.user, name=category)[0] if category.strip() else None
            account = Account.objects.get_or_create(user=request.user, name=account)[0] if account.strip() else None
            Transaction.objects.create(user=request.user, time=datetime.strptime(date, '%Y-%m-%d'),
                                       description=description, amount=amount, category=category, account=account)
        return HttpResponse('Imported %s transactions' % len(rows))


def transactions_for_period(request, start_time, end_time, user):
    return list(transaction_filter(request, Transaction.objects.filter(user=user, time__gt=start_time, time__lt=end_time)).select_related('account', 'category'))


def create_summary(request, start_time, end_time, user):
    transactions = transactions_for_period(request, start_time, end_time, user)
    accounts = {}
    default_account = Account(name=' default', pk=0)
    default_category = Category(name=' other', pk=0)

    sum_per_account_per_category_per_month = {}

    period_setting = get_period_setting(request.user)

    def month_from_transaction(t):
        if t.time.day > period_setting:
            return t.time.month
        else:
            return t.time.month - 1

    number_of_months = (end_time.year - start_time.year) * 12 + end_time.month - start_time.month - 1

    for transaction in transactions:
        categories = accounts.setdefault(transaction.account or default_account, {})
        if transaction.account is None or not transaction.account.hide:
            category = categories.setdefault(transaction.category or default_category, {})
            category['sum'] = category.get('sum', 0) + transaction.amount
            sum_of_month = sum_per_account_per_category_per_month.setdefault(transaction.account or default_account, {}).setdefault(transaction.category or default_category, dict([(i, {'sum': 0}) for i in range(1, number_of_months)])).setdefault(month_from_transaction(transaction), {})
            sum_of_month['sum'] = sum_of_month.get('sum', 0) + transaction.amount

    for account, categories in accounts.items():
        if not len(categories.items()):
            del accounts[account]

    max_value = None
    for account, categories in accounts.items():
        s = max([abs(x[1]['sum']) for x in categories.items()])
        max_value = max(max_value, s)

    for account, categories in accounts.items():
        for category, values in categories.items():
            values['severity'] = 0
            if max_value:
                values['severity'] = abs(values['sum']) / max_value
            values['std_deviation'] = std_deviation(
                [float(month['sum']) for month in sum_per_account_per_category_per_month[account][category].values()])

    for account, categories in accounts.items():
        account.total = sum([x[1]['sum'] for x in categories.items()])
        if account.total < 0:
            account.lossgain = 'loss'
        else:
            account.lossgain = 'gain'
        accounts[account] = sorted(categories.items())

    return accounts, transactions


@login_required
def view_summary(request, period='month', year=None, month=None):
    reference = datetime.now()
    year = reference.year if year is None else int(year)
    month = reference.month if month is None else int(month)
    reference = datetime(int(year), int(month), 1)

    if period == 'month':
        start_time = get_start_of_period(reference, request.user)
        end_time = get_end_of_period(start_time, request.user)
    elif period == 'year':
        if 'start_time' in request.REQUEST and 'end_time' in request.REQUEST:  # allow start/end time to be overwritten by URL
            from mammon.money import datetime_from_string

            start_time = datetime_from_string(request.REQUEST['start_time'])
            end_time = datetime_from_string(request.REQUEST['end_time'])
        else:
            start_time = get_start_of_period(datetime(int(year), 1, 1), request.user)
            end_time = get_end_of_period(datetime(int(year) + 1, 1, 1) - timedelta(days=31), request.user)

            if end_time > datetime.now():
                end_time = get_end_of_period(datetime.now() - timedelta(days=62), request.user)
    else:
        raise Exception('Invalid period')

    last_period_start_time = get_start_of_period(reference - timedelta(days=15), request.user)
    last_period_end_time = get_end_of_period(last_period_start_time, request.user)

    accounts, transactions = create_summary(request, start_time, end_time, request.user)

    projected_transactions = []
    last_month = False
    # calculate projections for the current unfinished month only
    if period == 'month' and year == datetime.now().year and month == datetime.now().month:
        last_month = True
        last_period_transactions = transactions_for_period(request, last_period_start_time, last_period_end_time,
                                                           request.user)
        transaction_descriptions = set([x.description for x in transactions])
        for last_period_transaction in last_period_transactions:
            if last_period_transaction.category and last_period_transaction.category.period == 1 and last_period_transaction.description not in transaction_descriptions:
                projected_transactions.append(last_period_transaction)

    total = sum([x.total for x in accounts])

    if period == 'month':
        prev = first_of_previous_month(end_time)
        previous_year, previous_month = prev.year, prev.month
        next_url = first_of_next_month(end_time)
        next_year, next_month = next_url.year, first_of_next_month(end_time).month if not last_month else None,
        next_period = next_month
    elif period == 'year':
        previous_year, previous_month = year - 1, None
        next_year, next_month = year + 1, None
        next_period = year < datetime.now().year
    else:
        assert False

    return render_to_response('money/view_period.html',
                              RequestContext(request, {
                                  'lossgain': 'loss' if total < 0 else 'gain',
                                  'account_summaries': sorted(accounts.items()),
                                  'total': total,
                                  'year': year,
                                  'month': month,
                                  'period': period,
                                  'monthly_average_divisor': (end_time - start_time).days / 30,

                                  'projected_transactions': projected_transactions,
                                  'projected_sum': sum([x.amount for x in projected_transactions]),

                                  'previous_year': previous_year,
                                  'previous_month': previous_month,

                                  'next_year': next_year,
                                  'next_month': next_month,

                                  'start_time': start_time,
                                  'end_time': end_time,

                                  'next_period': next_period,

                                  'transactions': transactions,
                                  'categories': Category.objects.filter(user=request.user),
                              }))


@login_required
def view_history(request):
    from django.db import connection
    from datetime import datetime

    cursor = connection.cursor()
    reference = datetime.now()
    months = get_history_months_setting(request.user)
    if 'months' in request.REQUEST:
        months.value = request.REQUEST['months']
        months.save()

    when_statements = ''
    year = reference.year
    month = reference.month

    end_period = get_end_of_period(reference, request.user)
    end_period = "'%(year)d-%(month)d-%(day)d'" % {'year': end_period.year if end_period.month != 1 else end_period.year - 1, 'month': end_period.month - 1, 'day': end_period.day}

    for i in range(int(months.value) + 1):
        period = get_start_of_period(datetime(year, month, 1), request.user)
        when_statements += " when time > '%(year)d-%(month)d-%(day)d' then '%(year)d-%(month)d-%(day)d' \n" % {
            'year': period.year, 'month': period.month, 'day': period.day}
        month -= 1
        if not month:
            month = 12
            year -= 1

    statement = """
        select 
        account_id,
        (
            case 
                %s
            end
        ) as bracket, sum(amount)
        from money_transaction
        where user_id = %s
              and time < %s
        group by account_id, bracket""" % (when_statements, request.user.id, end_period)
    cursor.execute(statement)

    class DataPoint:
        def __init__(self, date, amount):
            self.date, self.amount = datetime_from_string(date), amount

        def __repr__(self):
            return '(%s, %s)' % (self.date, self.amount)

    result = {}
    for row in cursor.fetchall():
        try:
            account = Account.objects.get(pk=row[0])
        except Account.DoesNotExist:
            account = None
        if account not in result:
            result[account] = []
        if row[1]:
            result[account].append(DataPoint(row[1], row[2]))

    sums = {}
    for key in result:
        sums[key] = sum([x.amount for x in result[key]])

    c = {'result': sorted(result.items()),
         'statement': statement,
         'months': months.value,
         'sums': sums,
         'total_sum': sum(sums.values())}

    return render_to_response('money/history.html', RequestContext(request, c))


@login_required
def delete_transaction(request, transaction_id):
    Transaction.objects.get(pk=transaction_id, user=request.user).delete()
    return HttpResponseRedirect(request.REQUEST['next'] if 'next' in request.REQUEST else '/')


@login_required
def delete_empty_transactions(request):
    Transaction.objects.filter(user=request.user, amount=0).delete()
    return HttpResponseRedirect('/')


@login_required
def edit_transaction_description(request, transaction_id):
    from django.utils.encoding import smart_unicode

    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    transaction.description = smart_unicode(request.POST['new_content'])
    transaction.save()
    return HttpResponse(transaction.description)


@login_required
def edit_transaction_properties(request, transaction_id):
    from django.utils.encoding import smart_unicode

    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    if 'category' in request.POST and request.POST['category']:
        category = Category.objects.get_or_create(user=request.user, name=request.POST['category'], defaults={})[0]
        transaction.category = category
    if 'description' in request.POST and request.POST['description']:
        transaction.description = smart_unicode(request.POST['description'])
    if 'account' in request.POST and request.POST['account']:
        transaction.account = Account.objects.get_or_create(user=request.user, name=request.POST['account'])[0]
    transaction.save()
    return HttpResponse('ok')


@login_required
def edit_transaction_category(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    category = None
    if request.POST['new_content']:
        try:
            category = Category.objects.get(pk=int(request.POST['new_content']), user=request.user)
        except Category.DoesNotExist:
            pass
    transaction.category = category
    transaction.save()
    return HttpResponse()


@login_required
def edit_transaction_account(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    account = None
    if request.POST['new_content']:
        try:
            account = Account.objects.get(pk=int(request.POST['new_content']), user=request.user)
        except Account.DoesNotExist:
            pass
    transaction.account = account
    transaction.save()
    return HttpResponse()


@login_required
def edit_transaction_date(request, transaction_id):
    from django.utils.encoding import smart_unicode

    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    transaction.time = datetime_from_string(smart_unicode(request.POST['new_content']))
    transaction.save()
    return HttpResponse(transaction.time.strftime('%Y-%m-%d'))


@login_required
def edit_account_name(request, account_id):
    from django.utils.encoding import smart_unicode

    account = Account.objects.get(pk=account_id, user=request.user)
    account.name = smart_unicode(request.POST['new_content'])
    account.save()
    return HttpResponse(account.name)


@login_required
def edit_transactions(request):
    if request.POST:
        for post_item in request.POST:
            if post_item.startswith('transaction_category_'):
                transaction = Transaction.objects.get(pk=post_item[len('transaction_category_'):])
                if transaction.user != request.user:
                    raise AccessDeniedException('cannot edit others transactions')

                if request.POST[post_item] != '':
                    transaction.category = Category.objects.get(pk=request.POST[post_item])
                else:
                    transaction.category = None
                transaction.save()
            if post_item.startswith('transaction_account_'):
                transaction = Transaction.objects.get(pk=post_item[len('transaction_account_'):])
                if transaction.user != request.user:
                    raise AccessDeniedException('cannot edit others transactions')

                if request.POST[post_item] != '':
                    transaction.account = Account.objects.get(pk=request.POST[post_item])
                else:
                    transaction.account = None
                transaction.save()
    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    return HttpResponseRedirect('/')


@login_required
def add_account(request):
    if request.POST:
        Account.objects.create(user=request.user, name=request.POST['name'])
    return HttpResponseRedirect('/settings/')


@login_required
def add_category(request):
    if request.POST:
        period = request.POST['period']
        if period == '-':
            period = None
        else:
            period = int(period)
        Category.objects.create(user=request.user, name=request.POST['name'], matching_rules=request.POST['match'],
                                period=period)
        update_matching(request)
    return HttpResponseRedirect('/')


@login_required
def update_matching(request):
    reset = 'reset' in request.REQUEST
    update_matches_for_user(request.user, reset)
    return HttpResponseRedirect('/')


@login_required
def split_transaction(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)

    if request.POST:
        num_parts = int(request.POST['parts'])
        if 'equal_parts' in request.POST:
            parts = [transaction.amount / Decimal(num_parts) for _ in range(num_parts - 1)]
        else:
            parts = [Decimal(request.POST['part_%s' % part_id]) for part_id in range(num_parts - 1)]

        distribute = 'distribute' in request.POST

        time = transaction.time
        for number, part in enumerate(parts):
            if distribute:
                time += relativedelta(months=1)
            Transaction.objects.create(user=request.user,
                                       description=transaction.description,
                                       time=time,
                                       category=transaction.category,
                                       virtual=True,
                                       amount=part,
                                       original_md5=transaction.original_md5)

        # Final part
        transaction.amount -= sum(parts)
        transaction.save()
        return HttpResponseRedirect('/')

    return render_to_response('money/split_transaction.html', RequestContext(request, {'transaction': transaction}))


@login_required
def delete_range(request):
    from django import forms
    from curia.widgets import DateWidget

    class RangeForm(forms.Form):
        start_time = forms.DateField(label=ugettext_lazy('From date'), widget=DateWidget)
        end_time = forms.DateField(label=ugettext_lazy('To date'), widget=DateWidget)

    message = None

    if request.POST:
        Transaction.objects.filter(user=request.user, time__gt=datetime_from_string(request.POST['start_time']),
                                   time__lt=datetime_from_string(request.POST['end_time'])).delete()
        message = ugettext_lazy('Transactions deleted!')
    form = RangeForm(initial={})

    return render_to_response('money/delete_range.html', RequestContext(request, {'form': form, 'message': message}))


@login_required
def settings(request):
    from django import forms

    if 'django_language' not in request.session:
        request.session['django_language'] = 'en'

    period_setting = get_period_setting(request.user)
    languages = [
        ('sv', 'Svenska'),
        ('en', 'English'),
    ]

    class SettingsForm(forms.Form):
        language = forms.ChoiceField(choices=languages, label=ugettext_lazy('Language'))
        period = forms.IntegerField(label=ugettext_lazy('Financial months begins on day'))

    if request.POST:
        form = SettingsForm(request.POST)

        try:
            int(form.data['period'])
        except ValueError:
            form.errors['period'] = (ugettext_lazy('Period must be a number'),)

        if form.is_valid():
            meta = request.user.meta
            meta.language = form.cleaned_data['language']
            meta.save()
            period_setting.value = form.cleaned_data['period']
            period_setting.save()
            request.session['django_language'] = meta.language
            return HttpResponseRedirect('/')
    else:
        form = SettingsForm(initial={'language': request.session['django_language'], 'period': period_setting.value})

    return render_to_response('money/settings.html', RequestContext(request, {'form': form,
                                                                              'accounts': Account.objects.filter(
                                                                                  user=request.user)}))


@login_required
def add_transactions(request):
    if not request.POST:
        return render_to_response('money/add.html', RequestContext(request, {}))
    else:
        data = request.POST['data']
        table_raw = [list(classify_row(x.split('\t'))) for x in data.split('\n')]
        table = [(classification, r) for classification, r in table_raw if has_requisite_data(classification)]

        counter = Counter([classification for classification, r in table])
        if not counter.items():
            return HttpResponse(unicode(ugettext_lazy("Sorry, I couldn't figure out the format of that input")))
        most_significant_format = max([(x, y) for y, x in counter.items()])[1]

        if 'date_choice' in request.POST:
            text_columns = [int(x) for x in request.POST.getlist('text_choices[]')]
            date_column = int(request.POST['date_choice'])
            number_columns = [int(x) for x in request.POST.getlist('number_choices[]')]
            parse_format = [' ' for _ in range(len(most_significant_format))]
            parse_format[date_column] = 'd'
            for nc in number_columns:
                parse_format[nc] = '1'
            for tc in text_columns:
                parse_format[tc] = 't'
            parse_format = ''.join(parse_format)
            Format.objects.create(user=request.user, raw_format=most_significant_format, parse_format=parse_format)

        try:
            fmt = Format.objects.get(user=request.user, raw_format=most_significant_format)
            to_add = []
            for classification, row in table:
                if fmt.compatible_with(classification):
                    amount, date, description = fmt.parse_row(row)
                    original_md5 = original_line_hash(amount, date, description, request.user)
                    if Transaction.objects.filter(user=request.user, original_md5=original_md5).count():
                        # duplicate line, ignore it
                        # print 'ignored duplicate line'
                        pass
                    else:
                        to_add.append(Transaction(user=request.user, amount=str(amount), time=date, description=description, original_md5=original_md5))
            Transaction.objects.bulk_create(to_add)
            update_matches_for_user(request.user)
            return HttpResponse('redirect_home')
        except Format.DoesNotExist:
            number_default = find_default_number(table, most_significant_format)

            return render_to_response('money/ask_for_format.html', RequestContext(request, {
                'format': most_significant_format,
                'table': table,
                'number_default': number_default,
                'date_default': most_significant_format.find('d'),
                'text_default': most_significant_format.find('t'),
                'data': data,
            }))


@login_required
def all_like_this(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)

    if request.method == 'GET':
        result = ''
        for i, c in enumerate(transaction.description.strip()):
            if i == 0 or c == ' ':
                if i:
                    result += '</span>'
                result += ' <span class="word" index="%s">' % i
            if c != ' ':
                result += '<span class="letter" index="%s">%s</span>' % (i, c)
        result += '</span>'
        c = RequestContext(request, {
            'transaction': transaction,
            'description_spans': mark_safe(result),
            'category': request.REQUEST['category'],
            'account': request.REQUEST.get('account')
        })
        return render_to_response('money/all_like_this.html', c)
    elif request.method == 'POST':
        start_index = request.POST['start_index']
        end_index = request.POST['end_index']
        assert start_index < end_index
        category = Category.objects.get_or_create(user=request.user, name=request.POST['category'])[0]
        category.add_rule(transaction.description[int(start_index):int(end_index) + 1])
        category.save()
        if request.POST.get('account'):
            transaction.account = Account.objects.get_or_create(user=request.user, name=request.POST['account'])[0]
        update_matches_for_user_and_category(request.user, category)
        return HttpResponse('OK')
