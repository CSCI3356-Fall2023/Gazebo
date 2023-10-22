from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/student/', views.student_register, name='student_register'),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('courses/', views.list_courses, name='list_courses'),
    path('', views.landing, name='landing'),
    path('status/', views.status_change, name='status_change'),
    path('login/', views.login_view, name='login')
]
