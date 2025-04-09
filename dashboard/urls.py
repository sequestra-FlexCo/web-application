from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sessions/', views.session_list, name='session_list'),
    path('session_detail/<int:session_id>/activate/', views.activate_session, name='activate_session'),
    path('session_detail/<int:session_id>/end/', views.end_session, name='end_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/download/', views.download_session_csv, name='download_session_csv'),
    path('session/<int:session_id>/chart/', views.session_chart_view, name='session_chart'),
    path('session/<int:session_id>/chart-data/', views.session_chart_data, name='session_chart_data'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/set-rpm/', views.set_rpm, name='set_rpm'),
    # Stirrer Logs
    path('session/<int:session_id>/stirrer-chart/', views.stirrer_chart_view, name='stirrer_chart'),
    path('session/<int:session_id>/stirrer-chart-data/', views.stirrer_chart_data, name='stirrer_chart_data'),
    path('session/<int:session_id>/stirrer-download/', views.download_stirrer_csv, name='download_stirrer_csv'),
]   

