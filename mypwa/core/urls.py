# core/urls.py
from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # --- Authentication URLs ---
    # Root URL: Redirect to login if not authenticated
    path('', RedirectView.as_view(pattern_name='login'), name='index_redirect'),
    
    # Custom Auth URLs
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),

    # --- Email Verification & Custom Password Reset URLs ---
    path('verify_email/', views.verify_email, name='verify_email'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/', views.reset_password, name='reset_password'),
    # --- Confirm Email Change URL ---
    path('confirm-email-change/', views.confirm_email_change, name='confirm_email_change'),

    # --- Built-in Password Change URLs (Using Django's secure views) ---
    # These are simpler and use Django's built-in security for password changes.
    # They automatically require the user to be logged in.
    # The templates need to be created at registration/password_change_form.html
    # and registration/password_change_done.html
    path('password/change/', auth_views.PasswordChangeView.as_view(
        # template_name='registration/change_password.html', # Optional: if you want a custom template name
        success_url='/dashboard/' # Redirect to dashboard on successful password change
        # The default template names are registration/password_change_form.html
        # and registration/password_change_done.html, which is standard.
    ), name='password_change'), # Standard Django name
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        # template_name='registration/change_password_done.html' # Optional: if you want a custom template name
    ), name='password_change_done'), # Standard Django name

    # --- Main Application URLs ---
    path('dashboard/', views.home, name='dashboard'),

    # Properties URLs
    path('properties/', views.properties, name='properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/<int:property_id>/', views.property_detail, name='property_detail'),
    path('properties/<int:property_id>/edit/', views.edit_property, name='edit_property'),

    # Tenant URLs
    # Note: Based on your models.py suggestion, tenant_id should be a UUID.
    # Ensure your views and templates handle UUIDs correctly.
    # If tenant_id is still an IntegerField in your model, change <uuid:tenant_id> back to <int:tenant_id>
    path('properties/<int:property_id>/add_tenant/', views.add_tenant, name='add_tenant'),
    path('tenants/<uuid:tenant_id>/edit/', views.edit_tenant, name='edit_tenant'),
    path('tenants/<uuid:tenant_id>/delete/', views.delete_tenant, name='delete_tenant'),

    # Transactions URLs
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/bulk/', views.add_bulk_transaction, name='add_bulk_transaction'),
    path('transactions/log/', views.transaction_log, name='transaction_log'),
    path('transactions/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),

    # Tools URLs
    path('tools/', views.tools_home, name='tools_home'),
    path('tools/value-calculator/', views.property_value_calculator, name='value_calculator'),
    path('tools/trend-tracking/', views.trend_tracking, name='trend_tracking'),
    path('tax-summary/', views.tax_summary, name='tax_summary'),

    # Scenario URLs
    path('tools/scenarios/', views.scenario_list, name='scenario_list'),
    path('tools/scenarios/add/', views.add_scenario, name='add_scenario'),
    path('tools/scenarios/delete/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
    path('tools/scenarios/compare/', views.scenario_comparison, name='scenario_comparison'),

    # --- User Settings URLs ---
    path('settings/', views.user_settings, name='user_settings'),

    # --- Delete Account URL ---
    path('settings/delete-account/', views.delete_account, name='delete_account'),

    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/delete/<int:alert_id>/', views.alert_delete, name='alert_delete'),
]