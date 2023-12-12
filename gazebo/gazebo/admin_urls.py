from django.urls import path
from . import views

urlpatterns = [
    # path('', views.status_change, name='status_change'),
    path('dashboard/', views.status_change, name='status_change'),
    path('login/', views.admin_login, name='admin_login'),
    path('course_list/', views.admin_course_list, name='admin_course_list'),
    path('admin_report/', views.admin_report, name='admin_report_default'),
    path('admin_report/<str:semester>/', views.admin_report, name='admin_report'),
    path('download_report/', views.download_report, name='download_report'),
]