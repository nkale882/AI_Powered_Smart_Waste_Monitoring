from django.db import models

# Create your models here.
from django.db import models

class Position(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'position'

# 🧹 Cleaning Crew Model
class CleaningCrew(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    address = models.TextField()
    verified = models.BooleanField(default=False)
    hire_date = models.DateField(auto_now_add=True)
    availability_status = models.BooleanField(default=True)
    experience_years = models.IntegerField(default=0)
    annual_salary = models.IntegerField( null=True, blank=True)
    assigned_area = models.CharField(max_length=100, null=True, blank=True)

    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'crew_user'

# 🧠 Admin Model 
class Admin(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=50, default="admin")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'admin'

# 📍 Task Model
class CleaningTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ]
    TASK_TYPE_CHOICES = [
        ('garbage', 'Garbage'),
        ('spill', 'Spill'),
        ('both', 'Garbage & Spill'),
    ]

    location = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    snapshot = models.ImageField(upload_to='detections/')
    description = models.TextField(default="Detected via CCTV")
    assigned_to = models.ForeignKey(CleaningCrew, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, null=True, blank=True)  # 👈 Added this line
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task at {self.location} - {self.status}"
    
    class Meta:
        db_table = 'Task Management'
