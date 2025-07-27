# core/urls.py
from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root URL: Redirect to login if not authenticated
    path('', RedirectView.as_view(pattern_name='login'), name='index_redirect'),
    
    # Your actual home view (protected)
    path('dashboard/', views.home, name='dashboard'),
    
    # Auth URLs with enhanced security
    path('login/', views.login_view, name='login'),
    
     path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('register/', views.register, name='register'),

    # Properties URLs
    path('properties/', views.properties, name='properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/edit/', views.edit_property, name='edit_property'),

    # Transactions URLs
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/bulk/', views.add_bulk_transaction, name='add_bulk_transaction'),
    path('transactions/log/', views.transaction_log, name='transaction_log'),
    path('transactions/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),

    # Tools URLs
    path('tools/', views.tools_home, name='tools_home'),
    path('tools/value-calculator/', views.property_value_calculator, name='value_calculator'),
    path('tools/trend-tracking/', views.trend_tracking, name='trend_tracking'),

    # Scenario URLs
    path('tools/scenarios/', views.scenario_list, name='scenario_list'),
    path('tools/scenarios/add/', views.add_scenario, name='add_scenario'),
    path('tools/scenarios/delete/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
    path('tools/scenarios/compare/', views.scenario_comparison, name='scenario_comparison'),
    
    #Tenant URLs
    path('properties/<int:property_id>/add_tenant/', views.add_tenant, name='add_tenant'),
    path('tenants/<int:tenant_id>/edit/', views.edit_tenant, name='edit_tenant'),
    path('tenants/<int:tenant_id>/delete/', views.delete_tenant, name='delete_tenant'),
] 