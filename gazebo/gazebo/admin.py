from django.contrib import admin
from gazebo.models import Course, SystemState, CustomUser

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'instructor', 
                    'current_enrollment', 'capacity', 
                    'description', 'section', 'days', 
                    'start_time', 'end_time', 'location',
                    'num_watches', 'is_open']
    search_fields = ['name', 'instructor', 'number', 
                     'is_open', 'days', 'start_time', 
                     'end_time', 'num_watches', 'location']


# Need configuration for other models
@admin.register(SystemState)
class SystemStateAdmin(admin.ModelAdmin):
    list_display = ['semester', 'state']
    search_fields = ['semester']


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['eagle_id', 'email', 'major', 'minor', 'department']
    search_fields = ['eagle_id']