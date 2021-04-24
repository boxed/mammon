from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.index),
    re_path(r'^add/$', views.add_transactions),
    re_path(r'^update_matching/$', views.update_matching),

    re_path(r'^getting_started/$', views.getting_started),
    re_path(r'^find_outliers/$', views.find_outliers),

    re_path(r'^transactions/edit/$', views.edit_transactions),
    re_path(r'^transactions/$', views.view_transactions),
    re_path(r'^transactions/export/$', views.export_transactions),
    re_path(r'^transactions/import/$', views.import_transactions),
    re_path(r'^transactions/(?P<transaction_id>\d+)/split/$', views.split_transaction),
    re_path(r'^transactions/(?P<transaction_id>\d+)/unsplit/$', views.unsplit_transaction),
    re_path(r'^transactions/(?P<transaction_id>\d+)/all_like_this/$', views.all_like_this),
    re_path(r'^transactions/(?P<transaction_id>\d+)/edit/date/$', views.edit_transaction_date),
    re_path(r'^transactions/(?P<transaction_id>\d+)/edit/description/$', views.edit_transaction_description),
    re_path(r'^transactions/(?P<transaction_id>\d+)/edit/category/$', views.edit_transaction_category),
    re_path(r'^transactions/(?P<transaction_id>\d+)/edit/account/$', views.edit_transaction_account),
    re_path(r'^transactions/(?P<transaction_id>\d+)/edit/properties/$', views.edit_transaction_properties),
    re_path(r'^transactions/(?P<transaction_id>\d+)/delete/$', views.delete_transaction),
    re_path(r'^transactions/delete_zeroes/$', views.delete_empty_transactions),

    re_path(r'^categories/$', views.view_categories),
    re_path(r'^categories/(?P<category_id>\d+)/$', views.view_category),
    re_path(r'^categories/(?P<category_id>\d+)/page/(?P<page>\d+)/$', views.view_category),
    re_path(r'^categories/(?P<category_id>\d+)/delete/$', views.delete_category),
    re_path(r'^categories/add/$', views.add_category),

    re_path(r'^accounts/$', views.view_accounts),
    re_path(r'^accounts/(?P<account_id>\d+)/$', views.view_account),
    re_path(r'^accounts/(?P<account_id>\d+)/page/(?P<page>\d+)/$', views.view_account),
    re_path(r'^accounts/add/$', views.add_account),
    re_path(r'^accounts/(?P<account_id>\d+)/edit/name/$', views.edit_account_name),
    re_path(r'^accounts/(?P<account_id>\d+)/delete/$', views.delete_account),

    re_path(r'^summary/$', views.view_summary),
    re_path(r'^summary/(?P<period>\w+)/$', views.view_summary),
    re_path(r'^summary/(?P<period>\w+)/(?P<year>\d+)/$', views.view_summary),
    re_path(r'^summary/(?P<period>\w+)/(?P<year>\d+)/(?P<month>\d+)/$', views.view_summary),
    re_path(r'^history/$', views.view_history),

    re_path(r'^settings/$', views.settings),

    re_path(r'^iphone-mammon.css$', views.stylesheet, {'template': 'iphone-mammon.css'}),
    re_path(r'^mammon.css$', views.stylesheet, {'template': 'mammon.css'}),
    re_path(r'^inline_edit.js$', views.stylesheet, {'template': 'inline_edit.js', 'mimetype': 'text/javascript'}),
    re_path(r'^input_overlay.js$', views.stylesheet, {'template': 'input_overlay.js', 'mimetype': 'text/javascript'}),
    re_path(r'^dialogs.js$', views.stylesheet, {'template': 'dialogs.js', 'mimetype': 'text/javascript'}),
    re_path(r'^input_overlay.css$', views.stylesheet, {'template': 'input_overlay.css'}),
]
