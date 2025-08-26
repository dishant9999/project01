from django.db import models
from django.contrib.auth.models import AbstractUser

# We will create a custom user model to handle different user roles (Admin, Student, Teacher).
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

# Model for university departments.
class Department(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

# Model for university locations (classrooms, labs, etc.).
class Location(models.Model):
    LOCATION_CHOICES = (
        ('classroom', 'Classroom'),
        ('lab', 'Lab'),
        ('auditorium', 'Auditorium'),
        ('hall', 'Hall'),
    )
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_CHOICES)
    floor = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.location_type})"

# Model for professors.
class Professor(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    working_hours_start = models.TimeField()
    working_hours_end = models.TimeField()
    total_weekly_lectures = models.IntegerField()
    departments = models.ManyToManyField(Department)

    def __str__(self):
        return self.name

# Model for academic subjects.
class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    lectures_per_week = models.IntegerField()
    lecture_duration_minutes = models.IntegerField()
    is_non_academic = models.BooleanField(default=False) # New field
    professors = models.ManyToManyField(Professor, blank=True) # Blank is True for non-academic subjects

    def __str__(self):
        return f"{self.name} ({self.code})"

# Model for streams and semesters.
class Stream(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    division = models.CharField(max_length=50, null=True, blank=True)
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=10)
    number_of_days = models.IntegerField(default=5) # New field
    non_academic_lectures_per_week = models.IntegerField(default=0) # New field
    coordinator = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, related_name='coordinated_streams')
    subjects = models.ManyToManyField(Subject)

    def __str__(self):
        return f"{self.name} - {self.division} - Sem {self.semester} ({self.academic_year})"

# New model for defining a time slot
class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

# Model for a single entry in the timetable.
class TimetableEntry(models.Model):
    DAY_CHOICES = (
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
    )
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Timetable Entries"
        ordering = ['day_of_week', 'timeslot__start_time']

    def __str__(self):
        return f"{self.stream} | {self.subject} | {self.day_of_week} ({self.timeslot})"