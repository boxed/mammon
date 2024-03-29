# coding=utf-8


import html.parser
from collections import Counter
from copy import copy
from datetime import date
from decimal import Decimal
from math import sqrt
from time import strftime

from dateutil.relativedelta import relativedelta
from django.utils.html import format_html
from django.utils.http import http_date
from django.utils.translation import (
    gettext,
    ugettext_lazy,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import login_required
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from django.db.models.aggregates import Sum, Count
from django.forms import ModelForm
from django import forms
from iommi.form import (
    date_parse,
    Form,
)

from mammon.authentication.models import MetaUser
from mammon.money import *
from mammon.money.models import *
from tri_declarative import (
    class_shortcut,
    evaluate,
)
from iommi import (
    Action,
    Column as ColumnBase,
    Table as TableBase,
    Page,
)


def inline_edit_select_cell_format(table, column, row, value, **_):
    options = '<option value=""></option>' + '\n'.join(['<option value="%s"%s>%s</option>' % (choice.pk, ' selected="selected"' if choice == value else '', choice) for choice in column.choices])

    return mark_safe('<select class="inline_editable_select" edit_url="%sedit/%s/" id="%s">%s</select>' % (row.get_absolute_url(), column.iommi_name(), row.pk, options))


class Column(ColumnBase):

    @classmethod
    @class_shortcut(
        call_target__attribute='text',
        cell__format=lambda table, column, row, value, **_: mark_safe('<span class="inline_editable" edit_url="%sedit/%s/" id="%s">%s</span>' % (row.get_absolute_url(), column.iommi_name(), row.pk, value)),
        cell__attrs__class__foo=True,
    )
    def inline_edit(cls, call_target=None, **kwargs):
        return call_target(**kwargs)

    @classmethod
    @class_shortcut(
        call_target__attribute='choice_queryset',
        cell__format=inline_edit_select_cell_format,
        filter__include=True,
    )
    def inline_edit_select(cls, call_target=None, **kwargs):
        return call_target(**kwargs)


class Table(TableBase):
    class Meta:
        member_class = Column


# TODO: i18n
class TransactionTable(Table):
    class Meta:
        auto__model = Transaction
        rows = lambda request, **_: Transaction.objects.filter(user=request.user)
        attrs__id = 'transaction_list'
        columns = dict(
            select__include=True,
            user__include=False,
            original_md5__include=False,
            date__filter=dict(
                parse=date_parse,
                include=True,
                field__include=False,
            ),
            month__cell=dict(
                format=lambda value, row, **_: format_html('<div class="inline_editable" edit_url="{}edit/month/">{}</div>', row.get_absolute_url(), value),
            ),
            month__filter=dict(include=True, field__include=False),
            description=Column.inline_edit(
                cell__attrs__class__description=True,
                filter__freetext__include=True,
                filter__include=True,
            ),
            amount=dict(
                cell__attrs__class={'numeric': True},
                header__attrs__class={'numeric': True},
                filter=dict(include=True, field__include=False),
            ),
            category=Column.inline_edit_select(
                model=Category,
                choices=lambda request, **_: Category.objects.filter(user=request.user),
                bulk__include=True,
                cell__attrs__class__category=True,
            ),
            account=Column.inline_edit_select(
                model=Account,
                choices=lambda request, **_: Account.objects.filter(user=request.user),
                include=lambda request, **_: Account.objects.filter(user=request.user).exists(),
                bulk__include=True,
                cell__attrs__class__account=True,
            ),

            split=Column.icon(
                'share-alt',
                cell__attrs={
                    'onclick': lambda row, **_: 'split_transaction(%s)' % row.pk,
                    'title': ugettext_lazy('Split'),
                },
            ),
            unsplit=Column.icon(
                'share-alt',
                cell__value=lambda row, **_: row.virtual,
                cell__attrs={
                    'onclick': lambda row, **_: 'unsplit_transaction(%s)' % row.pk,
                    'class': {'unsplit': True},
                    'title': ugettext_lazy('From a split transaction. Click to unsplit.')
                },
            ),
            delete=Column.icon(
                'trash',
                cell__attrs={
                    'onclick': lambda row, **_: 'delete_transaction(%s, true)' % row.pk,
                    'title': ugettext_lazy('Delete'),
                },
            ),
        )


def next_month(d):
    if d.month == 12:
        return datetime(d.year + 1, 1, d.day)
    else:
        return datetime(d.year, d.month + 1, d.day)


def std_deviation(values):
    sum1 = Decimal(0.0)
    sum2 = Decimal(0.0)
    n = Decimal(0.0)
    for x in values:
        sum1 += x
        sum2 += x * x
        n += Decimal(1.0)
        sum1, sum2, n = sum1, sum2, n
    return sqrt(sum2 / n - sum1 * sum1 / n / n)


class AccessDeniedException(Exception):
    pass


def get_page_size(request):
    if 'page_size' in request.GET:
        return int(request.GET['page_size'])
    return 20


class DataPoint:
    def __init__(self, date, amount):
        self.date, self.amount = datetime_from_string(date) if type(date) in (str, str) else date, amount

    def __repr__(self):
        return '(%s, %s)' % (self.date, self.amount)


def transaction_filter(request):
    return Transaction.objects.filter(user=request.user).order_by('-date')


@login_required
def index(request):
    if not Category.objects.filter(user=request.user).exists():
        return Page(template='money/index_no_categories.html')

    transactions = Transaction.objects.filter(user=request.user)

    if not transactions.exists():
        return Page(template='money/index_welcome.html')

    unclassified = transactions.filter(category=None)

    if not unclassified.exists():
        return Page(parts__text=gettext('All transactions have been classified'))
        # <p ></p>
        #             <div style="font-size: 80%; padding-top: 20px">
        #                 {% trans "Latest transaction" %}: {{ last_transaction.date|relative_date }}
        #             </div>

    try:
        last_transaction = Transaction.objects.filter(user=request.user, virtual=False).order_by('-date')[0]
    except (Transaction.DoesNotExist, IndexError):
        last_transaction = None
    return Page(
        parts__table=TransactionTable(
            rows=unclassified,
        ),
        context={
            'matched_count': Transaction.objects.filter(user=request.user, category__isnull=False).count(),
            'unmatched_count': Transaction.objects.filter(user=request.user, category__isnull=True).count(),
            'last_transaction': last_transaction,
            'categories': Category.objects.filter(user=request.user),
        }
    )


@login_required
def view_categories(request):
    return Table(
        auto__rows=Category.objects.filter(user=request.user),
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
        columns__user__include=False,
        columns__matching_rules__cell__attrs__class__pre=True,
        actions__new_category=Action(attrs__href='new/'),
    )


@login_required
def view_accounts(request):
    return render(request, 'money/view_accounts.html', {'accounts': Account.objects.filter(user=request.user)})


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
            fields = ('name', 'hide')

    return view_grouping(request, Account, account_id, EditForm, 'account', '/accounts', page)


@login_required
def view_grouping(request, group_class, group_id, form_class, group_name, url_base, page):
    group = get_object_or_404(group_class, pk=group_id)
    if group.user != request.user:
        raise AccessDeniedException('cannot edit others categories')

    transactions = Transaction.objects.filter(user=request.user, **{group_name: group})

    if request.POST:
        post = copy(request.POST)
        for key, value in list(post.items()):
            if value == 'None':
                post[key] = None
        form = form_class(post, instance=group)
        if form.is_valid():
            group = form.save()
            update_matches_for_user(request.user)
            if 'update_existing_transactions' in form.cleaned_data and form.cleaned_data['update_existing_transactions']:
                transactions.update(account=group.account)
    else:
        form = form_class(initial={}, instance=group)

    paginator = Paginator(transactions, get_page_size(request))
    return render(request, 'money/view_category.html', {
        'paginator': paginator,
        'page': page,
        'base_url': '%s/%d/' % (url_base, group.id),
        'form': form,
        'categories': Category.objects.filter(user=request.user),
        'group': group,
        'group_name': group_name,
        'sum': transactions.aggregate(Sum('amount'))['amount__sum'],
        'delete_message': ugettext_lazy('Delete this %s' % group_name),
        'confirm_delete_message': ugettext_lazy('Are you sure you want to delete this %s?' % group_name),
    })


@login_required
def view_transactions(request):
    # TODO: bulk edit on description field should be append, not set
    return TransactionTable()


@login_required
def export_transactions(request):
    transactions = transaction_filter(request)

    def export():
        for transaction in transactions:
            yield ('%s\t%s\t%s\t%s\t%s\t%s\n' % (
                transaction.date.date().isoformat(),
                transaction.month.date().isoformat(),
                transaction.description.replace('\t', '    '),
                transaction.amount,
                transaction.category or '', transaction.account or '')
           ).encode('utf8')

    return HttpResponse(export(), content_type='text/csv; charset=utf-8')


@login_required
def import_transactions(request):
    if not request.POST:
        return render(request, 'money/import.html', {})
    else:
        data = request.POST['data']
        rows = [row for row in data.replace('\r\n', '\n').split('\n') if row]
        for row in rows:
            date, month, description, amount, category, account = row.split('\t')
            category = Category.objects.get_or_create(user=request.user, name=category)[0] if category.strip() else None
            account = Account.objects.get_or_create(user=request.user, name=account)[0] if account.strip() else None
            time = datetime.strptime(date, '%Y-%m-%d')
            month = datetime.strptime(month, '%Y-%m-%d')

            Transaction.objects.create(
                user=request.user,
                time=time,
                month=month,
                description=description,
                amount=amount,
                category=category,
                account=account,
            )
        return HttpResponse('Imported %s transactions' % len(rows))


def transactions_for_user(user):
    return Transaction.objects.filter(user=user).select_related('account', 'category')


def transactions_for_period(request, start_time, end_time):
    return transaction_filter(request).filter(month__gte=start_time, month__lt=end_time).select_related('account', 'category')


def create_summary(request, start_time, end_time, user):
    transactions = transactions_for_period(request, start_time, end_time)

    number_of_months = (end_time.year - start_time.year) * 12 + end_time.month - start_time.month

    new_way = transactions.values('account_id', 'category_id', 'month').annotate(Sum('amount')).order_by()
    account_by_pk = {x.pk: x for x in Account.objects.filter(user=user)}
    account_by_pk[None] = Account(name=' default', pk=0)
    category_by_pk = {x.pk: x for x in Category.objects.filter(user=user)}
    category_by_pk[None] = Category(name=' other', pk=0)

    new_way = list(new_way)
    for r in new_way:
        r['account'] = account_by_pk[r['account_id']]
        r['category'] = category_by_pk[r['category_id']]
        r['sum'] = r['amount__sum']
        del r['account_id']
        del r['category_id']
        del r['amount__sum']
    accounts = nest_dict(new_way, ['account', 'category', 'month'])

    # Set the sum of months key
    for account, categories in list(accounts.items()):
        for category, months in list(categories.items()):
            months['sum'] = sum([x['sum'] for x in list(months.values())])

    max_value = None
    for account, categories in list(accounts.items()):
        s = max([abs(months['sum']) for _, months in list(categories.items())])
        if max_value is None:
            max_value = s
        else:
            max_value = max(max_value, s)

    for account, categories in list(accounts.items()):
        for category, months in list(categories.items()):
            months['severity'] = 0
            if max_value:
                months['severity'] = abs(months['sum']) / max_value
            sums = [v['sum'] for k, v in list(months.items()) if type(k) != str]
            sums += [Decimal(0.0)] * (number_of_months - len(sums))
            months['std_deviation'] = std_deviation(sums)

    total = Decimal(0)
    for account, categories in list(accounts.items()):
        account.total = sum([x['sum'] for x in list(categories.values())])
        total += account.total
        if account.total < 0:
            account.lossgain = 'loss'
        else:
            account.lossgain = 'gain'
        accounts[account] = sorted(categories.items())

    accounts = dict(sorted(accounts.items()))

    return accounts, transactions, total


def adjust_start_end_times(request, start_time, end_time):
    try:
        first_time = transactions_for_user(request.user).exclude(virtual=True).order_by('date')[0].date
        last_time = transactions_for_user(request.user).exclude(virtual=True).order_by('-date')[0].date

        # Adjust so that start_time starts on a month we have complete data for
        if first_time > start_time:
            start_time = get_start_of_period(first_time, request.user)
        while first_time > start_time:
            start_time = next_month(start_time)

        # Adjust so that end_time ends on a month we have complete data for
        if end_time > last_time:
            end_time = get_end_of_period(last_time - timedelta(days=62), request.user)
    except IndexError:
        pass
    return start_time, end_time


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
        if 'start_time' in request.GET and 'end_time' in request.GET:  # allow start/end time to be overwritten by URL
            start_time = datetime_from_string(request.GET['start_time'])
            end_time = datetime_from_string(request.GET['end_time'])
        else:
            start_time = get_start_of_period(datetime(int(year), 1, 1), request.user)
            end_time = datetime(start_time.year + 1, start_time.month, start_time.day)

            start_time, end_time = adjust_start_end_times(request, start_time, end_time)
    else:
        raise Exception('Invalid period')

    last_period_start_time = get_start_of_period(reference - timedelta(days=15), request.user)
    last_period_end_time = get_end_of_period(last_period_start_time, request.user)

    summary, transactions, total = create_summary(request, start_time, end_time, request.user)

    projected_transactions = []
    last_month = False
    # calculate projections for the current unfinished month only
    if period == 'month' and year == datetime.now().year and month == datetime.now().month:
        last_month = True
        last_period_transactions = transactions_for_period(request, last_period_start_time, last_period_end_time)
        transaction_descriptions = set([x.description for x in transactions])
        for last_period_transaction in last_period_transactions:
            if last_period_transaction.category and last_period_transaction.category.period == 1 and last_period_transaction.description not in transaction_descriptions:
                projected_transactions.append(last_period_transaction)

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

    resp = render(request, 'money/view_period.html', {
                                  'lossgain': 'loss' if total < 0 else 'gain',
                                  'summary': summary,
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
                              })
    import time
    resp['Expires'] = http_date(time.time() + 1000)
    return resp


@login_required
def view_history(request):
    from django.db import connection
    from datetime import datetime

    cursor = connection.cursor()
    reference = datetime.now()
    months = get_history_months_setting(request.user)
    if 'months' in request.GET:
        months.value = request.GET['months']
        months.save()

    when_statements = ''
    year = reference.year
    month = reference.month

    start_period = get_start_of_period(reference, request.user)
    end_period = get_end_of_period(reference, request.user)

    start_period, end_period = adjust_start_end_times(request, start_period, end_period)

    end_period = "'%(year)d-%(month)d-%(day)d'" % {'year': end_period.year if end_period.month != 1 else end_period.year - 1, 'month': end_period.month - 1, 'day': end_period.day}

    # TODO: change this to use the month column instead of this complicated logic
    for i in range(int(months.value) + 1):
        period = get_start_of_period(datetime(year, month, 1), request.user)
        when_statements += " when date > '%(year)d-%(month)d-%(day)d' then '%(year)d-%(month)d-%(day)d' \n" % {
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
              and date < %s
        group by account_id, bracket""" % (when_statements, request.user.id, end_period)
    cursor.execute(statement)

    result = defaultdict(list)
    no_account = Account(name='', pk=0)
    for row in cursor.fetchall():
        try:
            account = Account.objects.get(pk=row[0])
        except Account.DoesNotExist:
            account = no_account
        if account.hide:
            continue

        if row[1]:
            result[account].append(DataPoint(row[1], row[2]))

    sums = {}
    for key in result:
        sums[key] = sum([x.amount for x in result[key]])

    def gini(list_of_values):
        sorted_list = sorted(list_of_values)
        height, area = 0, 0
        for value in sorted_list:
            height += value
            area += height - value / 2.
        fair_area = height * len(list_of_values) / 2
        return (fair_area - area) / fair_area

    c = {'result': sorted(result.items()),
         'statement': statement,
         'months': months.value,
         'sums': sums,
         'gini': gini([float(x.amount) for x in result[no_account]][:-1]) if result else 0,
         'total_sum': sum(sums.values())}

    return render(request, 'money/history.html', c)


@login_required
def delete_transaction(request, transaction_id):
    Transaction.objects.get(pk=transaction_id, user=request.user).delete()
    return HttpResponseRedirect(request.GET['next'] if 'next' in request.GET else '/')


@login_required
def delete_empty_transactions(request):
    Transaction.objects.filter(user=request.user, amount=0).delete()
    return HttpResponseRedirect('/')


@login_required
def edit_transaction_description(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    transaction.description = request.POST['new_content']
    transaction.save()
    return HttpResponse(transaction.description)


@login_required
def edit_transaction_month(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    transaction.month = request.POST['new_content']
    transaction.save()
    return HttpResponse(request.POST['new_content'])


@login_required
def edit_transaction_properties(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    if 'category' in request.POST and request.POST['category']:
        category = Category.objects.get_or_create(user=request.user, name=request.POST['category'], defaults={})[0]
        transaction.category = category
    if 'description' in request.POST and request.POST['description']:
        transaction.description = request.POST['description']
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
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    transaction.date = datetime_from_string(request.POST['new_content'])
    transaction.save()
    return HttpResponse(transaction.date.strftime('%Y-%m-%d'))


@login_required
def edit_account_name(request, account_id):
    account = Account.objects.get(pk=account_id, user=request.user)
    account.name = request.POST['new_content']
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
def new_category(request):
    def pre_save(instance, request, **_):
        instance.user = request.user

    return Form.create(
        auto__model=Category,
        auto__exclude=['user'],
        extra__pre_save_all_but_related_fields=pre_save,
    )


@login_required
def update_matching(request):
    reset = 'reset' in request.GET
    update_matches_for_user(request.user, reset)
    return HttpResponseRedirect('/')


@login_required
def split_transaction(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)

    if request.POST:
        total_sum_before = transactions_for_user(request.user).aggregate(Sum('amount'))['amount__sum']

        num_parts = int(request.POST['parts'])
        if 'equal_parts' in request.POST:
            parts = [transaction.amount / Decimal(num_parts) for _ in range(num_parts - 1)]
        else:
            parts = [Decimal(request.POST['part_%s' % part_id]) for part_id in range(num_parts - 1)]

        distribute = 'distribute' in request.POST

        date = transaction.date
        for number, part in enumerate(parts):
            if distribute:
                date += relativedelta(months=1)
            Transaction.objects.create(user=request.user,
                                       description=transaction.description,
                                       date=date,
                                       month=transaction.month,
                                       category=transaction.category,
                                       virtual=True,
                                       amount=part,
                                       original_md5=transaction.original_md5)

        # Final part
        transaction.amount -= sum(parts)
        transaction.save()

        total_sum_after = transactions_for_user(request.user).aggregate(Sum('amount'))['amount__sum']

        assert total_sum_after == total_sum_before

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'money/split_transaction.html', {'transaction': transaction})


@login_required
def unsplit_transaction(request, transaction_id):
    assert request.method == 'POST'

    total_sum_before = transactions_for_user(request.user).aggregate(Sum('amount'))['amount__sum']

    transaction = transactions_for_user(request.user).get(pk=transaction_id)
    transactions = transactions_for_user(request.user).filter(original_md5=transaction.original_md5)
    original_transaction = transactions.get(virtual=False)
    original_transaction.amount = sum([x.amount for x in transactions])
    transactions.filter(virtual=True).delete()  # delete all but the original
    original_transaction.save()

    total_sum_after = transactions_for_user(request.user).aggregate(Sum('amount'))['amount__sum']

    assert total_sum_after == total_sum_before

    return HttpResponse('OK')


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
            meta = MetaUser.objects.get_or_create(user=request.user)[0]
            meta.language = form.cleaned_data['language']
            meta.save()
            period_setting.value = form.cleaned_data['period']
            period_setting.save()
            request.session['django_language'] = meta.language
            return HttpResponseRedirect('/')
    else:
        form = SettingsForm(initial={'language': request.session['django_language'], 'period': period_setting.value})

    return render(request, 'money/settings.html', {'form': form,
                                                                              'accounts': Account.objects.filter(
                                                                                  user=request.user)})


@login_required
def add_transactions(request):
    if not request.POST:
        return render(request, 'money/add.html', {})
    else:
        data = request.POST['data']

        # TODO: don't do this in prod
        if '\t' not in data:
            data = data.replace(';', '\t')

        table_raw = [list(classify_row(x.split('\t'))) for x in data.split('\n')]
        table = [(classification, r) for classification, r in table_raw if has_requisite_data(classification)]

        counter = Counter([classification for classification, r in table])
        if not list(counter.items()):
            return HttpResponse(str(ugettext_lazy("Sorry, I couldn't figure out the format of that input")))
        most_significant_format = max([(x, y) for y, x in list(counter.items())])[1]

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
                    amount, date_, description = fmt.parse_row(row)
                    original_md5 = original_line_hash(amount, date_, description, request.user)
                    if Transaction.objects.filter(user=request.user, original_md5=original_md5).exists():
                        # duplicate line, ignore it
                        # print 'ignored duplicate line'
                        pass
                    else:
                        year = date_.year
                        month = date_.month
                        day = date_.day
                        if day > 25:
                            month += 1
                            if month == 13:
                                month = 1
                                year += 1

                        to_add.append(
                            Transaction(
                                user=request.user,
                                amount=str(amount),
                                date=date_,
                                month=date(year, month, 1),
                                description=description,
                                original_md5=original_md5,
                            )
                        )
            Transaction.objects.bulk_create(to_add)
            update_matches_for_user(request.user)
            return HttpResponse('redirect_home')
        except Format.DoesNotExist:
            number_default = find_default_number(table, most_significant_format)

            return render(request, 'money/ask_for_format.html', {
                'format': most_significant_format,
                'table': table,
                'number_default': number_default,
                'date_default': most_significant_format.find('d'),
                'text_default': most_significant_format.find('t'),
                'data': data,
            })


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
        c = {
            'transaction': transaction,
            'description_spans': mark_safe(result),
            'category': request.GET['category'],
            'account': request.GET.get('account')
        }
        return render(request, 'money/all_like_this.html', c)
    elif request.method == 'POST':
        start_index = int(request.POST['start_index'])
        end_index = int(request.POST['end_index'])
        assert start_index < end_index
        category = Category.objects.get_or_create(user=request.user, name=request.POST['category'])[0]
        category.add_rule(transaction.description[int(start_index):int(end_index) + 1])
        category.save()
        if request.POST.get('account'):
            transaction.account = Account.objects.get_or_create(user=request.user, name=request.POST['account'])[0]
        update_matches_for_user_and_category(request.user, category)
        return HttpResponse('OK')


@login_required
def getting_started(request):
    if request.method == 'POST':
        data = request.POST.copy()
        del data['csrfmiddlewaretoken']
        for description, category_name in data.items():
            if not category_name:
                continue
            category = Category.objects.get_or_create(user=request.user, name=category_name)[0]
            category.add_rule(description)
            transactions_for_user(request.user).filter(description=description).update(category=category)
            category.save()
        return HttpResponseRedirect('.')

    transactions = transactions_for_user(request.user).filter(category__isnull=True)
    foo = [
        (x['description'], x['description__count'])
        for x in transactions.values('description').annotate(Count('description')).order_by('-description__count')
        if x['description__count'] > 1
    ]

    count = transactions_for_user(request.user).count()
    if count:
        percent_done = (transactions_for_user(request.user).filter(category__isnull=False).count() / count * 100.0)
    else:
        percent_done = 0
    c = {
        'foo': foo,
        'categories': Category.objects.filter(user=request.user),
        'percent_done': '%.1f' % percent_done
    }

    return render(request, 'money/getting_started.html', c)


@login_required
def find_outliers(request):
    skip_count = int(request.GET.get('skip', 0))

    # 1. Grab the summary view of the entire period of the user
    transactions = transactions_for_user(request.user)
    start_time = transactions.order_by('date')[0].date
    end_time = transactions.order_by('-date')[0].date
    if end_time > datetime.now():
        end_time = datetime.now()
    start_time, end_time = adjust_start_end_times(request, start_time, end_time)
    accounts, _, _ = create_summary(request, start_time, end_time, request.user)

    # 2. From that, get the category with the highest stddev
    categories = dict(accounts[Account(name=' default', pk=0)])
    highest_deviation_category, highest_deviation_data = sorted(list(categories.items()), key=lambda x: x[1]['std_deviation'], reverse=True)[skip_count]

    # 3. Graph the size of the months for that category. At this point outliers should stand out visually.
    sum_by_month = {k: v['sum'] for k, v in list(highest_deviation_data.items()) if type(k) is not str}

    # 4. Allow to expand the month group and act on the transactions.
    filter_category = highest_deviation_category if highest_deviation_category.pk else None

    c = {
        'category': highest_deviation_category,
        'categories': Category.objects.filter(user=request.user),
        'transactions_by_month': sorted([
            (month, sorted(transactions_for_user(request.user).filter(account=None, category=filter_category, time__gt=get_start_of_period(month, request.user), time__lte=get_start_of_period(month + timedelta(days=31), request.user)), reverse=True, key=lambda x: abs(x.amount)))
            for month in list(highest_deviation_data.keys()) if type(month) == datetime
        ]),
        'graph': [DataPoint(k, v) for k, v in list(sum_by_month.items())],
        'skip_count': skip_count + 1,
    }

    return render(request, 'money/find_outliers.html', c)


def stylesheet(request, template, mimetype='text/css'):
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    if 'ie' in user_agent:
        browser = 'ie'
    elif 'webkit' in user_agent:
        browser = 'webkit'
    elif 'mozilla' in user_agent:
        browser = 'mozilla'
    elif 'opera' in user_agent:
        browser = 'opera'
    else:
        browser = 'unknown'

    from django.template import loader
    from django.http import HttpResponse

    return HttpResponse(loader.render_to_string(template, request=request, context={'browser': browser, 'user_agent': user_agent}),
                        content_type=mimetype)
