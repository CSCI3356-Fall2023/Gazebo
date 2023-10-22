from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext as _



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
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    capacity = models.IntegerField()
    current_enrollment = models.IntegerField(default=0)
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    major = models.CharField(max_length=255)
    minor = models.CharField(max_length=255, blank=True, null=True)
    eagle_id = models.CharField(max_length=10)
    graduation_year = models.CharField(max_length=10)


class SystemState(models.Model):
    state = models.CharField(max_length=10)
    semester = models.CharField(max_length=15)

class CustomUser(AbstractUser):
    eagle_id = models.CharField(max_length=20)
    major = models.CharField(max_length=100, blank=True, null=True)
    minor = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='customuser_set', 
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='customuser_set',  
    )

