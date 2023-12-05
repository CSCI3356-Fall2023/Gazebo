from django.contrib import admin
from gazebo.models import Course, SystemState, CustomUser, History

@admin.register(Course)
# need to be able to filter by period of day (morning, afternoon, evening),
# day of the week, professor, course level
class CourseAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'instructor', 
                    'current_enrollment', 'capacity', 
                    'description', 'section', 'days', 
                    'start_time', 'end_time', 'location',
                    'num_watches', 'is_open', 'course_type']
    search_fields = ['name', 'instructor', 'number', 
                     'is_open', 'days', 'start_time', 
                     'end_time', 'num_watches', 'location', 
                     'course_type']


# Need configuration for other models
@admin.register(SystemState)
class SystemStateAdmin(admin.ModelAdmin):
    list_display = ['semester', 'state']
    search_fields = ['semester']

@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['semester', 'first_name', 'last_name', 'course_name', 'instructor', 'number']
    search_fields = ['semester', 'first_name', 'last_name', 'course_name', 'instructor', 'number']

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['eagle_id', 'email', 'major', 'minor', 'department']
    search_fields = ['eagle_id']