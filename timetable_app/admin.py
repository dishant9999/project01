from django.contrib import admin
from .models import CustomUser, Department, Location, Professor, Subject, Stream, TimetableEntry

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Department)
admin.site.register(Location)
admin.site.register(Professor)
admin.site.register(Subject)
admin.site.register(Stream)
admin.site.register(TimetableEntry)