from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _

class Course(models.Model):
    number = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    course_level = models.CharField(max_length=10, default = '')
    description = models.TextField()
    num_watches = models.IntegerField(default=0)

class Section(models.Model):
    COURSE_TYPES = [
        ('lecture', 'Lecture'),
        ('lab', 'Lab'),
        ('discussion', 'Discussion'),
    ]

    course_number = models.CharField(max_length=10, default = '')
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES)
    section_number = models.CharField(max_length=10)
    section_id = models.CharField(max_length=255, default ='', blank=True, null=True)
    instructor = models.CharField(max_length=255)
    days = models.CharField(max_length=255)
    start_time = models.CharField(max_length=255, blank=True, null=True)
    end_time = models.CharField(max_length=255, blank=True, null=True)
    period_of_day = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255)
    capacity = models.IntegerField(default=0)
    current_enrollment = models.IntegerField(default=0)
    num_watches = models.IntegerField(default=0)
    is_open = models.BooleanField(default=True)
    if current_enrollment == capacity:
        is_open = False

    @property
    def seats_available(self):
        if self.capacity - self.current_enrollment < 0:
            return 0
        
        return self.capacity - self.current_enrollment

class Log(models.Model):
    student_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    action = models.CharField(max_length=10)

class SystemState(models.Model):
    state = models.CharField(max_length=10)
    semester = models.CharField(max_length=15)

class CustomUser(AbstractUser):
    eagle_id = models.CharField(max_length=20)
    school = models.CharField(max_length=100, blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)
    minor = models.CharField(max_length=100, blank=True, null=True)
    is_administrator = models.BooleanField(default=False)
    department = models.CharField(max_length=100, blank=True, null=True)

class Watch(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, default=None)
    num_students = models.IntegerField(default=0)

class History(models.Model):
    semester = models.CharField(max_length=15)
    first_name = models.CharField(max_length=15)
    last_name = models.CharField(max_length=20)
    course_name = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    number = models.CharField(max_length=10) 
    
class Meta:
    unique_together = ('student', 'course')
    
    

