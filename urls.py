from django.conf.urls.defaults import *
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'mammon.money.views.index'),
    (r'^add/$', 'mammon.money.views.add_transactions'),
    (r'^update_matching/$', 'mammon.money.views.update_matching'),
    
    (r'^transactions/edit/$', 'mammon.money.views.edit_transactions'),
    (r'^transactions/$', 'mammon.money.views.view_transactions'),
    (r'^transactions/export/$', 'mammon.money.views.export_transactions'),
    (r'^transactions/import/$', 'mammon.money.views.import_transactions'),
    (r'^transactions/page/(?P<page>\d+)/$', 'mammon.money.views.view_transactions'),
    (r'^transactions/(?P<transaction_id>\d+)/split/$', 'mammon.money.views.split_transaction'),
    (r'^transactions/(?P<transaction_id>\d+)/all_like_this/$', 'mammon.money.views.all_like_this'),
    (r'^transactions/(?P<transaction_id>\d+)/edit/date/$', 'mammon.money.views.edit_transaction_date'),
    (r'^transactions/(?P<transaction_id>\d+)/edit/description/$', 'mammon.money.views.edit_transaction_description'),
    (r'^transactions/(?P<transaction_id>\d+)/edit/category/$', 'mammon.money.views.edit_transaction_category'),
    (r'^transactions/(?P<transaction_id>\d+)/edit/account/$', 'mammon.money.views.edit_transaction_account'),
    (r'^transactions/(?P<transaction_id>\d+)/edit/properties/$', 'mammon.money.views.edit_transaction_properties'),
    (r'^transactions/(?P<transaction_id>\d+)/delete/$', 'mammon.money.views.delete_transaction'),
    (r'^transactions/delete_zeroes/$', 'mammon.money.views.delete_empty_transactions'),
    (r'^transactions/delete_range/$', 'mammon.money.views.delete_range'),
    
    (r'^categories/$', 'mammon.money.views.view_categories'),
    (r'^categories/(?P<category_id>\d+)/$', 'mammon.money.views.view_category'),
    (r'^categories/(?P<category_id>\d+)/page/(?P<page>\d+)/$', 'mammon.money.views.view_category'),
    (r'^categories/(?P<category_id>\d+)/delete/$', 'mammon.money.views.delete_category'),
    (r'^categories/add/$', 'mammon.money.views.add_category'),

    (r'^accounts/$', 'mammon.money.views.view_accounts'),
    (r'^accounts/(?P<account_id>\d+)/$', 'mammon.money.views.view_account'),
    (r'^accounts/(?P<account_id>\d+)/page/(?P<page>\d+)/$', 'mammon.money.views.view_account'),
    (r'^accounts/add/$', 'mammon.money.views.add_account'),
    (r'^accounts/(?P<account_id>\d+)/edit/name/$', 'mammon.money.views.edit_account_name'),
    (r'^accounts/(?P<account_id>\d+)/delete/$', 'mammon.money.views.delete_account'),
    
    (r'^summary/$', 'mammon.money.views.view_summary'),
    (r'^summary/(?P<period>\w+)/$', 'mammon.money.views.view_summary'),
    (r'^summary/(?P<period>\w+)/(?P<year>\d+)/$', 'mammon.money.views.view_summary'),
    (r'^summary/(?P<period>\w+)/(?P<year>\d+)/(?P<month>\d+)/$', 'mammon.money.views.view_summary'),
    (r'^history/$', 'mammon.money.views.view_history'),

    (r'^settings/$', 'mammon.money.views.settings'),
    (r'^settings/password/$', 'curia.authentication.views.edit_user_password'),

    (r'^registration/user_agreement/$', 'django.views.generic.simple.direct_to_template', {'template': 'user_agreement.html'}),

    (r'^login/', 'mammon.views.login' ),
    (r'^logout/', 'curia.authentication.views.logout' ),
    (r'^registration/', include('curia.registration.urls')),

    (r'^iphone-mammon.css$', 'curia.base.views.stylesheet', {'template':'iphone-mammon.css'}),
    (r'^mammon.css$', 'curia.base.views.stylesheet', {'template':'mammon.css'}),
    (r'^inline_edit.js$', 'curia.base.views.stylesheet', {'template':'inline_edit.js', 'mimetype':'text/javascript'}),
    (r'^input_overlay.js$', 'curia.base.views.stylesheet', {'template':'input_overlay.js', 'mimetype':'text/javascript'}),
    (r'^dialogs.js$', 'curia.base.views.stylesheet', {'template':'dialogs.js', 'mimetype':'text/javascript'}),
    (r'^input_overlay.css$', 'curia.base.views.stylesheet', {'template':'input_overlay.css'}),
    
    (r'^echo_headers/', 'mammon.views.echo_headers' ),
    (r'^bin2/gfskod', 'mammon.views.echo_headers' ),

    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': 'django.conf'}),

#    (r'^test/', 'mammon.money.views.test'),

    # Uncomment this for admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/var/www-python/kodare/django/contrib/admin/media'}),
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.DOCUMENT_ROOT+'curia/site-media'}),
    (r'^site-media2/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.DOCUMENT_ROOT+'mammon/site-media'}),
)
