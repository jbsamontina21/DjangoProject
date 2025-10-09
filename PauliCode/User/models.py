from django.db import models
from datetime import datetime
from django.utils import timezone
import os, random
from django.utils.html import mark_safe

now = timezone.now()

def image_path(instance, filename):
    basefilename, file_extension = os.path.splitext(filename)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    randomstr = ''.join((random.choice(chars)) for x in range(10))
    _now = datetime.now()

    return 'profile_pic/{basename}_{randomstring}{ext}'.format(basename=basefilename, randomstring=randomstr, ext=file_extension)

class User(models.Model):
    school_id = models.CharField(max_length=20, primary_key=True, verbose_name="School ID")
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    password = models.CharField(max_length=255, verbose_name="Password")
    user_image = models.ImageField(upload_to=image_path, default = 'profile_pic/image.png')
    STUDENT = 'Student'
    TEACHER = 'Teacher'
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, verbose_name="User Type")

    def image_tag(self):
        return mark_safe(f'<img src="{self.user_image.url}" width="50" height="50" />')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_type})"
