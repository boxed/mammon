from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('add/', views.add_transactions),
    path('update_matching/', views.update_matching),
    path('getting_started/', views.getting_started),
    path('find_outliers/', views.find_outliers),

    path('transactions/edit/', views.edit_transactions),
    path('transactions/', views.view_transactions),
    path('transactions/export/', views.export_transactions),
    path('transactions/import/', views.import_transactions),
    path('transactions/<int:transaction_id>/split/', views.split_transaction),
    path('transactions/<int:transaction_id>/unsplit/', views.unsplit_transaction),
    path('transactions/<int:transaction_id>/all_like_this/', views.all_like_this),
    path('transactions/<int:transaction_id>/edit/date/', views.edit_transaction_date),
    path('transactions/<int:transaction_id>/edit/description/', views.edit_transaction_description),
    path('transactions/<int:transaction_id>/edit/category/', views.edit_transaction_category),
    path('transactions/<int:transaction_id>/edit/account/', views.edit_transaction_account),
    path('transactions/<int:transaction_id>/edit/month/', views.edit_transaction_month),
    path('transactions/<int:transaction_id>/edit/properties/', views.edit_transaction_properties),
    path('transactions/<int:transaction_id>/delete/', views.delete_transaction),
    path('transactions/delete_zeroes/', views.delete_empty_transactions),

    path('categories/', views.view_categories),
    path('categories/<int:category_id>/', views.view_category),
    path('categories/<int:category_id>/page/<int:page>/', views.view_category),
    path('categories/<int:category_id>/delete/', views.delete_category),
    path('categories/add/', views.add_category),
    path('categories/new/', views.new_category),

    path('accounts/', views.view_accounts),
    path('accounts/<int:account_id>/', views.view_account),
    path('accounts/<int:account_id>/page/<int:page>/', views.view_account),
    path('accounts/add/', views.add_account),
    path('accounts/<int:account_id>/edit/name/', views.edit_account_name),
    path('accounts/<int:account_id>/delete/', views.delete_account),

    path('summary/', views.view_summary),
    path('summary/<str:period>/', views.view_summary),
    path('summary/<str:period>/<int:year>/', views.view_summary),
    path('summary/<str:period>/<int:year>/<int:month>/', views.view_summary),
    path('history/', views.view_history),

    path('settings/', views.settings),

    path('iphone-mammon.css', views.stylesheet, {'template': 'iphone-mammon.css'}),
    path('mammon.css', views.stylesheet, {'template': 'mammon.css'}),
    path('inline_edit.js', views.stylesheet, {'template': 'inline_edit.js', 'mimetype': 'text/javascript'}),
    path('input_overlay.js', views.stylesheet, {'template': 'input_overlay.js', 'mimetype': 'text/javascript'}),
    path('dialogs.js', views.stylesheet, {'template': 'dialogs.js', 'mimetype': 'text/javascript'}),
    path('input_overlay.css', views.stylesheet, {'template': 'input_overlay.css'}),
]
