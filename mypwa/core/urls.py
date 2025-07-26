# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),
    path('properties/', views.properties, name='properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/edit/', views.edit_property, name='edit_property'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/bulk/', views.add_bulk_transaction, name='add_bulk_transaction'),
    path('transactions/log/', views.transaction_log, name='transaction_log'),
    path('transactions/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),
    
    # Tools URLs
    path('tools/', views.tools_home, name='tools_home'),
    path('tools/value-calculator/', views.property_value_calculator, name='value_calculator'),
    path('tools/scenarios/add/', views.add_scenario, name='add_scenario'),
    path('tools/trend-tracking/', views.trend_tracking, name='trend_tracking'),
        #Scenario URLs
        path('tools/scenarios/', views.scenario_list, name='scenario_list'),
        path('tools/scenarios/delete/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
        path('tools/scenarios/compare/', views.scenario_comparison, name='scenario_comparison'),
]