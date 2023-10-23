from django.contrib import admin
from gazebo.models import Course, Student, SystemState 

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

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'major', 'graduation_year']
    search_fields = ['user__username', 'major']

# Need configuration for other models
@admin.register(SystemState)
class SystemStateAdmin(admin.ModelAdmin):
    list_display = ['semester', 'state']
    search_fields = ['semester']