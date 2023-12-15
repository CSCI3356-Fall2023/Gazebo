from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('admin/', include('gazebo.admin_urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path("login", views.login, name="login"),
    path("callback", views.callback, name="callback"),
    path("logout/", views.logout, name="logout"),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('additional_info/', views.additional_info, name='additional_info'),
    path('courses/', views.list_courses, name='list_courses'),
    path('course_offering_api/', views.course_offering_api, name='course_offering_api'),
    path('waitlist_activity_api/', views.waitlist_activity_api, name='waitlist_activity_api'),
    path('toggle_watchlist/<slug:section_number>/<slug:course_number>', views.toggle_watchlist, name='toggle_watchlist'),
    path('watchlist/', views.watchlist_view, name='watchlist_view'),
    path('error/', views.temp_view, name = 'temp_view'),
]
