from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

# a little hack to get curias change password page to redirect to the root
from mammon.money import standardize_number, datetime_from_string


# noinspection PyUnusedLocal
def user_get_absolute_url(self):
    return '/'


User.get_absolute_url = user_get_absolute_url


class Account(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    name = models.CharField(blank=False, max_length=100, verbose_name=_('Name'))
    hide = models.BooleanField(default=False, verbose_name=_('Hide'))

    def __unicode__(self):
        return self.name

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class Format(models.Model):
    user = models.ForeignKey(User)
    raw_format = models.CharField(blank=False, max_length=100, db_index=True)
    parse_format = models.CharField(blank=False, max_length=100)

    def __unicode__(self):
        return u'%s: %s, %s' % (self.user, self.raw_format, self.parse_format)

    def parse_row(self, row):
        descriptions = []
        amount = None
        date = None
        for index, value in enumerate(self.parse_format):
            if value == '1':
                new_amount = standardize_number(row[index])
                assert not amount or not new_amount
                if new_amount:
                    amount = new_amount
            elif value == 'd':
                date = datetime_from_string(row[index])
            elif value == 't':
                descriptions.append(row[index])
        assert amount is not None
        assert date is not None
        assert len(descriptions) > 0
        return amount, date, u' '.join(descriptions)

    def compatible_with(self, classification):
        if classification == self.raw_format:
            return True
        for c, f in zip(classification, self.parse_format):
            if f == 'd' and c != f:
                return False
            if f == '1' and c != f:
                return False
        return True


class Category(models.Model):
    PERIODS = (
        (None, 'unknown'),
        (1, 'monthly'),
        (2, 'bi-monthly'),
        (3, 'quarterly'),
        (6, 'half-yearly'),
        (12, 'yearly'),
    )

    user = models.ForeignKey(User, verbose_name=_('User'))
    account = models.ForeignKey(Account, null=True, blank=True, default=None, verbose_name=_('Account'))
    name = models.CharField(max_length=100, verbose_name=_('Name'), blank=False)
    matching_rules = models.TextField(blank=True, verbose_name=_('Matching rules'))
    period = models.IntegerField(default=None, null=True, blank=True, choices=PERIODS, verbose_name=_('Period'))

    def add_rule(self, rule):
        self.matching_rules = '\n'.join([x for x in self.matching_rules.split('\n') if x] + [rule])

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def matches(self, transaction):
        for rule in self.matching_rules.splitlines():
            if rule.strip() != '':
                if rule.strip().lower() in transaction.description.lower():
                    return True
        return False

    def __unicode__(self):
        if self.name.strip() != '':
            return self.name
        else:
            return '<no name>'

    class Meta:
        ordering = ('name',)


class Transaction(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    account = models.ForeignKey(Account, null=True, blank=True, default=None)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    time = models.DateTimeField()
    description = models.TextField()
    category = models.ForeignKey(Category, blank=True, null=True)
    virtual = models.BooleanField(default=False)  # means that this isn't the original transaction, but a part of a split transaction
    original_md5 = models.CharField(max_length=32, db_index=True)

    def __unicode__(self):
        from time import strftime

        return '%s %s %s %s' % (self.user, strftime('%Y-%m-%d', self.time.timetuple()), self.description, self.amount)

    class Meta:
        ordering = ('time', 'description')