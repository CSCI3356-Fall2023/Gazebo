from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext as _
import gazebo.settings

class Course(models.Model):
    COURSE_TYPES = [
        ('lecture', 'Lecture'),
        ('lab', 'Lab'),
        ('discussion', 'Discussion'),
    ]
    
    number = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES)
    description = models.TextField()
    section = models.CharField(max_length=10)
    instructor = models.CharField(max_length=255)
    # look into making days field a list
    days = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    capacity = models.IntegerField(default=0)
    current_enrollment = models.IntegerField(default=0)
    num_watches = models.IntegerField(default=0)
    is_open = models.BooleanField()
    
class Student(models.Model):
    user = models.OneToOneField(gazebo.settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    major = models.CharField(max_length=255)
    minor = models.CharField(max_length=255, blank=True, null=True)
    eagle_id = models.CharField(max_length=10)
    graduation_year = models.CharField(max_length=10)


class Watch(models.Model):
    student_id = models.CharField(max_length=10)
    course_id = models.CharField(max_length=10)
    num_students = models.IntegerField(default=0)

class Log(models.Model):
    student_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField()
    action = models.CharField(max_length=10)

class SystemState(models.Model):
    state = models.CharField(max_length=10)
    semester = models.CharField(max_length=15)

class CustomUser(AbstractUser):
    eagle_id = models.CharField(max_length=20)
    email = models.EmailField()
    major = models.CharField(max_length=100, blank=True, null=True)
    minor = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    
    

