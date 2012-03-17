# coding=UTF8
from curia.shortcuts import *
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.views import login_required
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, InvalidPage
from django.db.models.aggregates import Sum
from curia import *
from mammon.money.models import *
from mammon.money import *
from mammon import *
import sys
from datetime import datetime, timedelta

SUPPORTED_BANKS = [
    ('Nordea', 'Nordea'), 
    ('SEB', 'SEB'),
    ('Swedbank', 'Swedbank'),
    ('Handelsbanken', 'Handelsbanken'),
]

@login_required
def index(request):
    try:
        last_transaction = Transaction.objects.filter(user=request.user).order_by('-time')[0]
    except:
        last_transaction = None
    return render_to_response(request, 'money/index.html', 
        {
            'matched_count': Transaction.objects.filter(user=request.user, category__isnull=False).count(),
            'unmatched_count':Transaction.objects.filter(user=request.user, category__isnull=True).count(),
            'transactions':Transaction.objects.filter(user=request.user, category__isnull=True),
            'last_transaction':last_transaction,
            'categories': Category.objects.filter(user=request.user),
        })

@login_required
def view_categories(request):
    return render_to_response(request, 'money/view_categories.html', {'categories': Category.objects.filter(user=request.user)})

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
    category = get_object_or_404(Category, pk=category_id)
    if category.user != request.user:
        raise AccessDeniedException('cannot edit others categories')
        
    from django.forms import ModelForm
    from django import forms
    class EditForm(ModelForm):
        update_existing_transactions = forms.BooleanField(label=_('Update existing transactions'), required=False)
        class Meta:
            model = Category
            fields = ('name', 'matching_rules', 'period', 'account')

    transactions = Transaction.objects.filter(category=category).order_by('-time')

    if request.POST:
        from copy import copy
        post = copy(request.POST)
        if post['period'] == 'None':
            post['period'] = None
        form = EditForm(post, instance=category)
        if form.is_valid():
            form.save()
            update_matches_for_user(request.user)
            if 'update_existing_transactions' in request.REQUEST:
                for transaction in transactions:
                    transaction.account = category.account
    else:
        form = EditForm(initial={}, instance=category)
    
    # limit the transactions for display
    if 'start_time' in request.GET and 'end_time' in request.GET:
        transactions = transactions.filter(time__gt=datetime_from_string(request.GET['start_time']), time__lt=datetime_from_string(request.GET['end_time']))

    page_size = 20
    paginator = Paginator(transactions, page_size)
    return render_to_response(request, 'money/view_category.html', {
        'paginator': paginator,
        'page': page,
        'base_url': '/categories/%d/' % category.id,
        'form': form, 
        'transactions': paginator.page(page).object_list,
        'unmatched_transactions':Transaction.objects.filter(user=request.user, category__isnull=True),
        'categories': Category.objects.filter(user=request.user),
        'category': category,
        'sum': transactions.aggregate(Sum('amount'))['amount__sum'],
        })
        
@login_required
def view_transaction_list(request, page='1'):
    page_size = 20
    paginator = Paginator(Transaction.objects.filter(user=request.user).order_by('-time'), page_size)
    return render_to_response(request, 'money/view_transaction_list.html', {
        'paginator': paginator,
        'page': page,
        'base_url': '/transactions/',
        'transactions': paginator.page(page).object_list,
        'categories': Category.objects.filter(user=request.user),
        'base_url': '/transactions/',
        })
        
def transactions_for_period(start_time, end_time, user):
    return list(Transaction.objects.filter(user=user, time__gt=start_time, time__lt=end_time))
        
def create_summary(start_time, end_time, user):
    transactions = transactions_for_period(start_time, end_time, user)
    accounts = {}
    default_account = Account(name=' default')
    default_category = Category(name=' other')
    
    def get_or_insert(dic, key, default={}):
        if key not in dic:
            dic[key] = default
        return dic[key]
    
    for transaction in transactions:
        categories = get_or_insert(accounts, transaction.account or default_account, {})
        if transaction.account == None or not transaction.account.hide:
            category = get_or_insert(categories, transaction.category or default_category, {})
            category['sum'] = category.get('sum', 0)+transaction.amount

    for account, categories in accounts.items():
        if len(categories.items()) == 0:
            del accounts[account]
            
    max_value = None
    for account, categories in accounts.items():
        s = max([abs(x[1]['sum']) for x in categories.items()])
        max_value = max(max_value, s)

    for account, categories in accounts.items():
        for category, values in categories.items():
            values['severity'] = 0
            if max_value != 0:
                values['severity'] = abs(values['sum'])/max_value
    
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
    # from django.db.models import Sum
    reference = datetime.now()
    if year is None:
        year = reference.year
    else:
        year = int(year)
    if month is None:
        month = reference.month 
    else:
        year = int(year)
    reference = datetime(int(year), int(month), 1)

    start_time = get_start_of_period(reference, request.user)
    end_time = get_end_of_period(start_time, request.user)
    if period == 'month':
        pass
    elif period == 'year':
        start_time = start_time - timedelta(days=365)
    else:
        raise Exception('Invalid period')
        
    last_period_start_time = get_start_of_period(reference-timedelta(days=15), request.user)
    last_period_end_time = get_end_of_period(last_period_start_time, request.user)
    
    accounts, transactions = create_summary(start_time, end_time, request.user)

    projected_transactions = []
    last_month = False
    # calculate projections for the current unfinished month only
    if year == datetime.now().year and month == datetime.now().month:
        last_month = True
        last_period_transactions = transactions_for_period(last_period_start_time, last_period_end_time, request.user)
        transaction_descriptions = set([x.description for x in transactions])
        for last_period_transaction in last_period_transactions:
            if last_period_transaction.category and last_period_transaction.category.period == 1 and last_period_transaction.description not in transaction_descriptions:
                projected_transactions.append(last_period_transaction)

    total = sum([x.total for x in accounts])
    if total < 0:
        lossgain = 'loss'
    else:
        lossgain = 'gain'
    
    if period == 'month':
        prev = first_of_previous_month(end_time)
        previous_year, previous_month = prev.year, prev.month
        next = first_of_next_month(end_time)
        next_year, next_month = next.year, first_of_next_month(end_time).month if not last_month else None,
        next_period = next_month
    elif period == 'year':
        previous_year, previous_month = year-1, None
        next_year, next_month = year+1, None
        next_period = year < datetime.now().year
        
    return render_to_response(request, 'money/view_period.html', 
        {
            'lossgain':lossgain,
            'account_summaries': accounts.items(),
            'total': total,
            'year': year,
            'month': month,
            'period': period,
            
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

@login_required
def view_history(request):
    from django.db import connection, transaction
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
    for i in range(int(months.value)+1):
        period = get_start_of_period(datetime(year, month, 1), request.user)
        when_statements += " when time > '%(year)d-%(month)d-%(day)d' then '%(year)d-%(month)d-%(day)d' \n" % {'year': period.year, 'month': period.month, 'day': period.day }
        month -= 1
        if month == 0:
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
        group by account_id, bracket""" % (when_statements, request.user.id)
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
    return render_to_response(request, 'money/history.html', {'result': result, 'statement':statement, 'months':months.value, 'sums':sums, 'total_sum':sum(sums.values())})

@login_required
def delete_transaction(request, transaction_id):
    Transaction.objects.get(pk=transaction_id, user=request.user).delete()
    return HttpResponseRedirect(request.GET['next'])

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
def edit_transaction_category(request, transaction_id):
    from django.utils.encoding import smart_unicode
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    try:
        category = Category.objects.get(pk=int(request.POST['new_content']), user=request.user)
    except:
        category = None
    transaction.category = category
    transaction.save()
    return HttpResponse()

@login_required
def edit_transaction_account(request, transaction_id):
    from django.utils.encoding import smart_unicode
    transaction = Transaction.objects.get(pk=transaction_id, user=request.user)
    try:
        account = Account.objects.get(pk=int(request.POST['new_content']), user=request.user)
    except:
        account = None
    transaction.account = account
    transaction.save()
    return HttpResponse()

# example usage:
# edit_object_foreign_key(request, Transaction, transaction_id, fk_class=Account)
# def edit_object_foreign_key(request, object_class, object_id, fk_class, fk_name=None):
#     if fk_name == None:
#         fk_name = fk_class.__name__.lower()
#     from django.utils.encoding import smart_unicode
#     obj = object_class.objects.get(pk=object_id, user=request.user)
#     fk_obj = None
#     fk_id = int(request.POST['new_content'])
#     if fk_id != 0:
#         fk_obj = fk_class.objects.get(pk=fk_id, user=request.user)
#     setattr(obj, fk_name, fk_obj)
#     obj.save()
#     return HttpResponse()

# edit_object_property(request, Account, account_id, 'name', str)
# edit_object_property(request, Account, account_id, 'time', datetime)
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
        Category.objects.create(user=request.user, name=request.POST['name'], matching_rules=request.POST['match'], period=period)
        update_matching(request)
    return HttpResponseRedirect('/')
    
@login_required
def update_matching(request):
    categories = list(Category.objects.filter(user=request.user))
    reset = 'reset' in request.REQUEST
    update_matches_for_user(request.user, reset)
    return HttpResponseRedirect('/')
    
class InvalidTransactionLogFormat(Exception):
    def __init__(self, description):
        self.description = description
        
    def __repr__(self):
        return 'InvalidTransactionLogFormat: %s' % self.description
    
    def __str__(self):
        return self.__repr__()
    
@login_required    
def add_transactions(request):
    from django import forms
    class AddForm(forms.Form):
        bank = forms.ChoiceField(choices=SUPPORTED_BANKS, help_text=_('To change the default, go to <a href="/settings/">settings</a>'))
        data = forms.CharField(widget=forms.Textarea)
        accept_duplicates = forms.BooleanField(widget=forms.HiddenInput, required=False)
        
    bank = get_bank_setting(request.user).value
    
    def standardize_number(s):
        s = s.strip()
        if len(s) > 3 and s[-3] == ',':
            s = s.replace('.', '').replace(',', '.').replace(' ', '')
        if s == '':
            raise InvalidTransactionLogFormat('empty string as number')
        else:
            return float(s)
        
    invalid_lines = []
    if request.POST:
        form = AddForm(request.POST)
        
        duplicate_lines = []

        if form.is_valid():
            bank = form.cleaned_data['bank']
            for line in form.cleaned_data['data'].splitlines():
                if '\t' not in line: # ignore all non-table lines
                    continue
                    
                s = [x.strip() for x in line.split('\t')]
                if len(s) < 3: # ignore lines that have too few fields to even theoretically have all required data
                    continue

                def assert_empty_entry(index):
                    if s[index] != '': 
                        raise InvalidTransactionLogFormat('Component %s not empty: "%s"' % (index, array[index])) # just for validation
                try:
                    if bank == 'Nordea':
                        if len(s) < 5: raise InvalidTransactionLogFormat('incorrect number of, expected less than 5 got %s' % len(s)) # just for validation
                        assert_empty_entry(0)
                        date = datetime_from_string(s[1])
                        description = s[2]
                        nordea_category = s[3]
                        amount = standardize_number(s[4])
                        if len(s) > 5 and s[5] != '':
                            total = standardize_number(s[5]) # just for validation
                    elif bank == 'Handelsbanken':
                        if len(s) != 7: raise InvalidTransactionLogFormat('incorrect number of entries, expected 7 got %s' % len(s)) # just for validation
                        date = datetime_from_string(s[0])
                        assert_empty_entry(1)
                        description = s[2]
                        assert_empty_entry(3)
                        amount = standardize_number(s[4])
                        assert_empty_entry(5)
                        total = standardize_number(s[6]) # just for validation
                    elif bank == 'SEB':
                        if len(s) != 6: raise InvalidTransactionLogFormat('incorrect number of entries, expected 6 got %s' % len(s)) # just for validation
                        date = datetime_from_string(s[0])
                        date2 = datetime_from_string(s[1]) # just for validation
                        # the transaction ID can also be "SKATT <year>" and "RÄNTA <year>" so let's ignore this check...
                        #transaction_id = int(s[2][:-1]) # just for validation, ignoring last character, because it can be "S"
                        description = s[3]
                        amount = standardize_number(s[4])
                        total = standardize_number(s[5]) # just for validation
                    elif bank == 'Swedbank':
                        if len(s) != 6: raise InvalidTransactionLogFormat('incorrect number of entries, expected 6 got %s' % len(s)) # just for validation
                        date = datetime(*strptime(s[0], '%y-%m-%d')[:3])
                        date2 = datetime(*strptime(s[1], '%y-%m-%d')[:3]) # just for validation
                        description = s[2]
                        assert_empty_entry(3)
                        amount = standardize_number(s[4])
                        total = standardize_number(s[5]) # just for validation
                    else:
                        raise InvalidTransactionLogFormat('unknown format')
                except ValueError,e: # failed to parse number or date
                    invalid_lines.append((line, e))
                    continue
                except InvalidTransactionLogFormat,e:
                    invalid_lines.append((line, e))
                    continue
                amount = str(amount)
                import hashlib
                from django.utils.encoding import smart_unicode
                original = (u'%s\t%s\t%s\t%s' % (request.user.id, amount, date, description)).encode('ascii', 'xmlcharrefreplace')
                original_md5 = hashlib.md5(original).hexdigest()
                if form.cleaned_data['accept_duplicates'] == True:
                    Transaction.objects.create(user=request.user, amount=amount, time=date, description=description, original_md5=original_md5)
                else:
                    if Transaction.objects.filter(user=request.user, original_md5=original_md5).count() != 0:
                        duplicate_lines.append(line)
                    else:
                        Transaction.objects.create(user=request.user, amount=amount, time=date, description=description, original_md5=original_md5)
            
            #if invalid_lines:
            #    mail_simple_error('failed to parse transaction(s)', {'bank':bank, 'lines':invalid_lines})
                
            update_matching(request)
            
            if not duplicate_lines and not invalid_lines:
                return HttpResponseRedirect('/')
            else:
                form = AddForm(initial={'data':'\n'.join(duplicate_lines), 'accept_duplicates':True, 'bank':bank})
                if duplicate_lines:
                    form.errors['data'] = ('these rows appear to be duplicates, to accept them post them again',)
    else:
        form = AddForm(initial={'data':'', 'accept_duplicates':False, 'bank':bank})
        
    return render_to_response(request, 'money/add.html', {'form': form, 'invalid_lines': invalid_lines})
    
@login_required
def split_transaction(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    if transaction.user != request.user:
        raise 'access denied'
        
    if request.POST:
        parts = []
        for part_id in range(int(request.POST['parts'])-1):
            parts.append(float(request.POST['part_%s' % part_id]))
        
        # ensure that the parts are in reasonable range
        if transaction.amount < 0:
            parts = [-abs(part) for part in parts]
        else:
            parts = [abs(part) for part in parts]

        if sum([abs(x) for x in parts]) >= abs(transaction.amount):
            raise Exception('invalid split parameters')
            
        for part in [str(part) for part in parts]: # need to convert to string for the Decimal class
            Transaction.objects.create(user=request.user, description=transaction.description, time=transaction.time, category=transaction.category, virtual=True, amount=part, original_md5=transaction.original_md5)

        transaction.amount = str(float(transaction.amount)-sum(parts))
        transaction.save()
        return HttpResponseRedirect('/')
        
    return render_to_response(request, 'money/split_transaction.html', {'transaction':transaction})

@login_required
def delete_range(request):
    from django import forms
    from curia.widgets import DateWidget

    class RangeForm(forms.Form):
        start_time = forms.DateField(label=_('From date'), widget=DateWidget)
        end_time = forms.DateField(label=_('To date'), widget=DateWidget)
        
    message = None
        
    if request.POST:
        Transaction.objects.filter(user=request.user, time__gt=datetime_from_string(request.POST['start_time']), time__lt=datetime_from_string(request.POST['end_time'])).delete()
        message = _('Transactions deleted!')
    form = RangeForm(initial={})

    return render_to_response(request, 'money/delete_range.html', {'form':form, 'message':message})

@login_required
def settings(request):
    from django import forms
    from django import conf
    
    if 'django_language' not in request.session:
        request.session['django_language'] = 'en'
    
    bank_setting = get_bank_setting(request.user)
    period_setting = get_period_setting(request.user)
    languages = [
        ('sv', 'Svenska'),
        ('en', 'English'),
        ]
    
    class SettingsForm(forms.Form):
        bank = forms.ChoiceField(choices=SUPPORTED_BANKS, label=_('Bank'))
        language = forms.ChoiceField(choices=languages, label=_('Language'))
        period = forms.IntegerField(label=_('Financial months begins on day'))

    if request.POST:
        form = SettingsForm(request.POST)

        duplicate_lines = []
        
        try:
            int(form.data['period'])
        except:
            form.errors['period'] = (_('Period must be a number'),)

        if form.is_valid():
            bank_setting.value = form.cleaned_data['bank']
            bank_setting.save()
            meta = request.user.meta
            meta.language = form.cleaned_data['language']
            meta.save()
            period_setting.value = form.cleaned_data['period']
            period_setting.save()
            request.session['django_language'] = meta.language
            return HttpResponseRedirect('/')
    else:
        form = SettingsForm(initial={'bank':bank_setting.value, 'language':request.session['django_language'], 'period':period_setting.value})

    return render_to_response(request, 'money/settings.html', {'form': form, 'accounts':Account.objects.filter(user=request.user)})