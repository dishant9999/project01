from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Professor, Stream, Location, Subject, Department, TimeSlot

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email',)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user

class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ['name', 'email', 'working_hours_start', 'working_hours_end', 'total_weekly_lectures', 'departments']
        widgets = {
            'departments': forms.CheckboxSelectMultiple(),
        }

class StreamForm(forms.ModelForm):
    class Meta:
        model = Stream
        fields = ['name', 'department', 'division', 'semester', 'academic_year', 'number_of_days', 'non_academic_lectures_per_week', 'coordinator', 'subjects']
        widgets = {
            'subjects': forms.CheckboxSelectMultiple(),
        }

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'location_type', 'floor']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'lectures_per_week', 'lecture_duration_minutes', 'is_non_academic', 'professors']
        widgets = {
            'professors': forms.CheckboxSelectMultiple(),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

# New form for TimeSlot
class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time']