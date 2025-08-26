from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import CustomUserCreationForm, TaskForm, ProfessorForm, StreamForm, LocationForm, SubjectForm, DepartmentForm, TimeSlotForm
from .models import TimetableEntry, Stream, CustomUser, Task, Location, Professor, Subject, Department, TimeSlot
from django.db.models import Sum
import csv
from django.http import HttpResponse
from datetime import timedelta
from timetable_app.timetable_generator import generate_timetable
from timetable_app.management.commands.validate_data import Command as ValidateCommand
from io import StringIO
from django.db.models import F

# Home page view
def home(request):
    return render(request, 'timetable_app/home.html')

# User Registration View
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'timetable_app/register.html', {'form': form})

# User Login View
class CustomLoginView(LoginView):
    template_name = 'timetable_app/login.html'

user_login = CustomLoginView.as_view()

# Unified Dashboard for all users
@login_required
def dashboard(request):
    # Fetch all streams for the filter dropdown
    streams = Stream.objects.all()
    selected_stream_id = request.GET.get('stream_id')
    
    # Get all locations and types for the location sheet filter
    locations = Location.objects.all()
    location_types = [choice[0] for choice in Location.LOCATION_CHOICES]
    selected_location_type = request.GET.get('location_type')
    selected_location_floor = request.GET.get('floor')
    
    # Data for all users
    all_users = CustomUser.objects.all()
    
    # Get user-specific data for task scheduler
    form = TaskForm()
    scheduled_tasks = []
    pending_tasks = []
    
    # Filter the timetable based on user role and selected stream
    if request.user.is_superuser or request.user.role == 'admin':
        if selected_stream_id:
            timetable_entries = TimetableEntry.objects.filter(stream__id=selected_stream_id).order_by('day_of_week', 'timeslot__start_time')
        else:
            timetable_entries = TimetableEntry.objects.all().order_by('day_of_week', 'timeslot__start_time')
    else:
        first_stream = Stream.objects.first()
        timetable_entries = TimetableEntry.objects.filter(stream=first_stream).order_by('day_of_week', 'timeslot__start_time')
        
        if request.method == 'POST' and 'add_task' in request.POST:
            form = TaskForm(request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.user = request.user
                task.save()
                return redirect('dashboard')
        
        scheduled_tasks = Task.objects.filter(user=request.user, is_scheduled=True, is_completed=False).order_by('priority')
        pending_tasks = Task.objects.filter(user=request.user, is_scheduled=False, is_completed=False).order_by('priority')
    
    if selected_location_type:
        locations = locations.filter(location_type=selected_location_type)
    if selected_location_floor:
        locations = locations.filter(floor=selected_location_floor)

    context = {
        'streams': streams,
        'selected_stream_id': selected_stream_id,
        'timetable_entries': timetable_entries,
        'locations': locations,
        'location_types': location_types,
        'selected_location_type': selected_location_type,
        'selected_location_floor': selected_location_floor,
        'form': form,
        'scheduled_tasks': scheduled_tasks,
        'pending_tasks': pending_tasks,
        'all_users': all_users,
        'role_choices': CustomUser.ROLE_CHOICES,
    }
    
    return render(request, 'timetable_app/dashboard.html', context)

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = True
    task.save()
    return redirect('dashboard')

@login_required
def reschedule_tasks(request):
    if request.method == 'POST':
        free_time_str = request.POST.get('free_time')
        try:
            minutes = int(free_time_str)
            available_time = timedelta(minutes=minutes)
        except (ValueError, TypeError):
            return redirect('dashboard')
        
        Task.objects.filter(user=request.user, is_scheduled=True, is_completed=False).update(is_scheduled=False)
        
        pending_tasks = Task.objects.filter(user=request.user, is_scheduled=False, is_completed=False).order_by('priority')
        
        for pending_task in pending_tasks:
            if pending_task.estimated_time <= available_time:
                pending_task.is_scheduled = True
                pending_task.save()
                available_time -= pending_task.estimated_time
            else:
                break
    return redirect('dashboard')

@login_required
def update_user_role(request, user_id):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to perform this action.")
    
    if request.method == 'POST':
        user_to_update = get_object_or_404(CustomUser, id=user_id)
        new_role = request.POST.get('role')
        if new_role in [choice[0] for choice in CustomUser.ROLE_CHOICES]:
            user_to_update.role = new_role
            user_to_update.save()
    
    return redirect('dashboard')

@login_required
def run_generator_view(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to perform this action.")
    
    validator = ValidateCommand()
    is_valid = validator.handle()

    if is_valid:
        generate_timetable()
        return redirect('dashboard')
    else:
        # The validator will print errors to the console, but we can't capture them here.
        # This is a simplified approach to avoid the bug.
        return render(request, 'timetable_app/validation_error.html', {'errors': ["Validation failed. Please check the terminal for details."]})
        
@login_required
def download_timetable(request):
    selected_stream_id = request.GET.get('stream_id')
    if selected_stream_id:
        timetable_entries = TimetableEntry.objects.filter(stream__id=selected_stream_id).order_by('day_of_week', 'timeslot__start_time')
    else:
        timetable_entries = TimetableEntry.objects.all().order_by('day_of_week', 'timeslot__start_time')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="timetable.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Stream', 'Day', 'Time', 'Subject', 'Professor', 'Location'])
    
    for entry in timetable_entries:
        writer.writerow([
            entry.stream,
            entry.get_day_of_week_display(),
            entry.timeslot,
            entry.subject.name,
            entry.professor.name,
            entry.location.name
        ])
    return response

@login_required
def download_location_sheet(request):
    locations = Location.objects.all()
    
    filter_type = request.GET.get('location_type')
    filter_floor = request.GET.get('floor')
    
    if filter_type:
        locations = locations.filter(location_type=filter_type)
    if filter_floor:
        locations = locations.filter(floor=filter_floor)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="locations.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Type', 'Floor'])
    
    for location in locations:
        writer.writerow([location.name, location.get_location_type_display(), location.floor])

    return response

# New data management views

@login_required
def manage_data(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to view this page.")
    
    professors = Professor.objects.all()
    streams = Stream.objects.all()
    locations = Location.objects.all()
    subjects = Subject.objects.all()
    time_slots = TimeSlot.objects.all()
    departments = Department.objects.all()
    
    context = {
        'professors': professors,
        'streams': streams,
        'locations': locations,
        'subjects': subjects,
        'time_slots': time_slots,
        'departments': departments,
    }
    
    return render(request, 'timetable_app/manage_data.html', context)

@login_required
def add_data(request, model_name):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to add data.")
    
    model_map = {
        'professor': (ProfessorForm, Professor, 'Professor'),
        'stream': (StreamForm, Stream, 'Stream'),
        'location': (LocationForm, Location, 'Location'),
        'subject': (SubjectForm, Subject, 'Subject'),
        'department': (DepartmentForm, Department, 'Department'),
        'timeslot': (TimeSlotForm, TimeSlot, 'Time Slot'),
    }
    
    FormClass, ModelClass, title = model_map.get(model_name, (None, None, ''))
    if not FormClass:
        return HttpResponse("Invalid model name.")

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_data')
    else:
        form = FormClass()
        
    context = {'form': form, 'title': f'Add {title}'}
    return render(request, 'timetable_app/add_data.html', context)

@login_required
def edit_data(request, model_name, pk):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to edit data.")
    
    model_map = {
        'professor': (ProfessorForm, Professor, 'Professor'),
        'stream': (StreamForm, Stream, 'Stream'),
        'location': (LocationForm, Location, 'Location'),
        'subject': (SubjectForm, Subject, 'Subject'),
        'department': (DepartmentForm, Department, 'Department'),
        'timeslot': (TimeSlotForm, TimeSlot, 'Time Slot'),
    }

    FormClass, ModelClass, title = model_map.get(model_name, (None, None, ''))
    if not FormClass:
        return HttpResponse("Invalid model name.")

    instance = get_object_or_404(ModelClass, pk=pk)
    
    if request.method == 'POST':
        form = FormClass(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('manage_data')
    else:
        form = FormClass(instance=instance)
        
    context = {'form': form, 'title': f'Edit {title}'}
    return render(request, 'timetable_app/add_data.html', context)

@login_required
def delete_data(request, model_name, pk):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to delete data.")

    model_map = {
        'professor': Professor,
        'stream': Stream,
        'location': Location,
        'subject': Subject,
        'department': Department,
        'timeslot': TimeSlot,
    }

    ModelClass = model_map.get(model_name)
    if not ModelClass:
        return HttpResponse("Invalid model name.")

    instance = get_object_or_404(ModelClass, pk=pk)
    instance.delete()
    
    return redirect('manage_data')