from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .forms import CustomUserCreationForm, TaskForm, ProfessorForm, StreamForm, LocationForm, SubjectForm, DepartmentForm, TimeSlotForm, TimetableEntryForm
from .models import TimetableEntry, Stream, CustomUser, Task, Location, Professor, Subject, Department, TimeSlot
import csv
from django.db.models import F
import random
from datetime import timedelta
from django.db import transaction
from itertools import product

def home(request):
    return render(request, 'timetable_app/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'timetable_app/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'timetable_app/login.html'

user_login = CustomLoginView.as_view()

@login_required
def dashboard(request):
    streams = Stream.objects.all()
    selected_stream_id = request.GET.get('stream_id')
    
    locations = Location.objects.all()
    location_types = [choice[0] for choice in Location.LOCATION_CHOICES]
    selected_location_type = request.GET.get('location_type')
    selected_location_floor = request.GET.get('floor')
    
    all_users = CustomUser.objects.all()
    
    form = TaskForm()
    scheduled_tasks = []
    pending_tasks = []
    all_time_slots = TimeSlot.objects.all().order_by('start_time')
    all_days = ['mon', 'tue', 'wed', 'thu', 'fri']
    
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
        'all_time_slots': all_time_slots,
        'all_days': all_days,
    }
    
    return render(request, 'timetable_app/dashboard.html', context)

@login_required
def manage_timetable(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return HttpResponse("You are not authorized to view this page.")

    streams = Stream.objects.all()
    departments = Department.objects.all()
    selected_stream_id = request.GET.get('stream_id')
    
    all_days = ['mon', 'tue', 'wed', 'thu', 'fri']
    all_time_slots = TimeSlot.objects.all().order_by('start_time')

    timetable_data = {}
    location_timetable_data = {}
    
    if selected_stream_id:
        stream = get_object_or_404(Stream, id=selected_stream_id)
        entries = TimetableEntry.objects.filter(stream=stream).order_by('day_of_week', 'timeslot__start_time')
        
        for day in all_days:
            timetable_data[day] = {}
            for timeslot in all_time_slots:
                slot_entries = entries.filter(day_of_week=day, timeslot=timeslot)
                timetable_data[day][timeslot.id] = slot_entries
    
    all_locations = Location.objects.all()
    
    for day in all_days:
        location_timetable_data[day] = {}
        for timeslot in all_time_slots:
            entries = TimetableEntry.objects.filter(day_of_week=day, timeslot=timeslot)
            for location in all_locations:
                location_entries = entries.filter(location=location)
                if location_entries:
                    location_timetable_data[day][timeslot.id] = location_timetable_data[day].get(timeslot.id, {})
                    location_timetable_data[day][timeslot.id][location.id] = location_entries
    
    context = {
        'departments': departments,
        'streams': streams,
        'selected_stream_id': selected_stream_id,
        'timetable_data': timetable_data,
        'all_days': all_days,
        'all_time_slots': all_time_slots,
        'all_locations': all_locations,
        'location_timetable_data': location_timetable_data,
    }

    return render(request, 'timetable_app/manage_timetable.html', context)

@login_required
def get_slot_options(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    day = request.GET.get('day')
    timeslot_id = request.GET.get('timeslot_id')
    stream_id = request.GET.get('stream_id')
    
    if not all([day, timeslot_id, stream_id]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    stream = get_object_or_404(Stream, id=stream_id)

    occupied_professors = TimetableEntry.objects.filter(day_of_week=day, timeslot=timeslot).exclude(professor=None).values_list('professor_id', flat=True)
    occupied_locations = TimetableEntry.objects.filter(day_of_week=day, timeslot=timeslot).exclude(location=None).values_list('location_id', flat=True)
    
    available_professors = Professor.objects.exclude(id__in=occupied_professors).filter(departments=stream.department).distinct()
    available_locations = Location.objects.exclude(id__in=occupied_locations)

    subjects = Subject.objects.filter(professors__in=available_professors).distinct()

    subject_options = [{'id': s.id, 'name': s.name} for s in subjects]
    professor_options = [{'id': p.id, 'name': p.name} for p in available_professors]
    location_options = [{'id': l.id, 'name': f"{l.name} ({l.location_type})"} for l in available_locations]

    return JsonResponse({
        'subjects': subject_options,
        'professors': professor_options,
        'locations': location_options
    })

@login_required
def add_timetable_entry(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        stream_id = request.POST.get('stream_id')
        day = request.POST.get('day')
        timeslot_id = request.POST.get('timeslot_id')
        subject_id = request.POST.get('subject_id')
        professor_id = request.POST.get('professor_id')
        location_id = request.POST.get('location_id')
        
        try:
            with transaction.atomic():
                stream = get_object_or_404(Stream, id=stream_id)
                timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
                subject = get_object_or_404(Subject, id=subject_id)
                professor = get_object_or_404(Professor, id=professor_id)
                location = get_object_or_404(Location, id=location_id)

                TimetableEntry.objects.create(
                    stream=stream,
                    day_of_week=day,
                    timeslot=timeslot,
                    subject=subject,
                    professor=professor,
                    location=location
                )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'created'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_timetable_entry(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        if not entry_id:
            return JsonResponse({'error': 'Entry ID not provided.'}, status=400)
        
        entry = get_object_or_404(TimetableEntry, id=entry_id)
        entry.delete()
        
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

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
        locations = locations.filter(floor=selected_location_floor)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="locations.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Type', 'Floor'])
    
    for location in locations:
        writer.writerow([location.name, location.get_location_type_display(), location.floor])

    return response

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