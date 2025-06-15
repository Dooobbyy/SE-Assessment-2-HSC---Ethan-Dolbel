from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ajax/month-summary/', views.get_monthly_summary_ajax, name='ajax_month_summary'),
    path('ajax/chart-data/', views.get_chart_data, name='ajax_chart_data'),
    path('ajax/pie-chart-data/', views.get_pie_chart_data, name='ajax_pie_chart_data'),
    path('properties/', views.properties_view, name='properties'),
]