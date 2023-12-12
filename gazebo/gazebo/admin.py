from django.contrib import admin
from gazebo.models import Course, SystemState, Section, Watch, CustomUser, History

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'course_level', 'description']
    search_fields = ['number', 'name', 'course_level', 'description']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'current_enrollment', 'capacity', 
                    'section_number', 'days', 'start_time', 
                    'end_time', 'location', 'num_watches', 
                    'is_open', 'course_type', 'period_of_day']
    search_fields = ['instructor', 'is_open', 'days', 
                     'start_time', 'end_time', 'num_watches', 
                     'location', 'course_type', 'period_of_day']

@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    list_display = ['student', 'section', 'num_students']
    search_fields = ['student', 'section', 'num_students']


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