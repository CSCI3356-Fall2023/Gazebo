from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    # path('register/student/', views.student_register, name='student_register'),
    path("login", views.login, name="login"),
    path("callback", views.callback, name="callback"),
    path("logout/", views.logout, name="logout"),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('additional_info/', views.additional_info, name='additional_info'),
    path('courses/', views.list_courses, name='list_courses'),
    path('', views.landing, name='landing'),
    # path("", views.index, name="index"),
    path('status/', views.status_change, name='status_change'),
    # path('login/', views.login_view, name='login')
    path('course_offering_api/', views.course_offering_api, name='course_offering_api'),
    path('waitlist_activity_api/', views.waitlist_activity_api, name='waitlist_activity_api'),
    path('toggle_watchlist/<int:course_id>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watchlist/', views.watchlist_view, name='watchlist_view'),
    path('error/', views.temp_view, name = 'temp_view'),
]
