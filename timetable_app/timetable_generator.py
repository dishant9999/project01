from django.db import transaction
from .models import Professor, Location, Subject, Stream, TimetableEntry, TimeSlot
import random

def generate_timetable():
    print("Starting timetable generation...")
    
    with transaction.atomic():
        TimetableEntry.objects.all().delete()
        
        all_time_slots = list(TimeSlot.objects.all())
        all_locations = list(Location.objects.all())
        all_professors = list(Professor.objects.all())
        all_streams = list(Stream.objects.all())
        all_days = ['mon', 'tue', 'wed', 'thu', 'fri']

        if not all_time_slots or not all_locations or not all_professors or not all_streams:
            print("Error: Incomplete data. Please add professors, locations, time slots, and streams.")
            return

        for stream in all_streams:
            subjects_to_schedule = list(stream.subjects.all())
            
            # Simple list to keep track of assignments to avoid conflicts
            assigned_slots = []
            
            # First, schedule all academic subjects
            academic_subjects = [s for s in subjects_to_schedule if not s.is_non_academic]
            for subject in academic_subjects:
                for _ in range(subject.lectures_per_week):
                    slot_found = False
                    for day_index in range(stream.number_of_days):
                        day = all_days[day_index]
                        for timeslot in all_time_slots:
                            
                            is_lunch_break = timeslot.start_time.hour == 12 and timeslot.start_time.minute == 15
                            if is_lunch_break:
                                continue
                            
                            # Find professor
                            for professor in subject.professors.all():
                                # Check for professor's weekly lecture limit
                                professor_lectures_count = len([s for s in assigned_slots if s[2] == professor])
                                if professor_lectures_count >= professor.total_weekly_lectures:
                                    continue
                                    
                                professor_conflict = any(s[2] == professor for s in assigned_slots if s[0] == day and s[1] == timeslot)
                                if professor_conflict:
                                    continue
                                
                                # Find location
                                location = None
                                location_conflict = any(s[3] == location for s in assigned_slots if s[0] == day and s[1] == timeslot)
                                
                                if 'lab' in subject.name.lower():
                                    available_locations = [loc for loc in all_locations if loc.location_type == 'lab' and not any(s[3] == loc for s in assigned_slots if s[0] == day and s[1] == timeslot)]
                                    if available_locations:
                                        location = available_locations[0]
                                else:
                                    available_classrooms = [loc for loc in all_locations if loc.location_type == 'classroom' and not any(s[3] == loc for s in assigned_slots if s[0] == day and s[1] == timeslot)]
                                    if available_classrooms:
                                        location = available_classrooms[0]
                                
                                if location:
                                    TimetableEntry.objects.create(
                                        stream=stream,
                                        subject=subject,
                                        professor=professor,
                                        location=location,
                                        day_of_week=day,
                                        timeslot=timeslot
                                    )
                                    assigned_slots.append((day, timeslot, professor, location))
                                    slot_found = True
                                    break
                                
                            if slot_found:
                                break
                        if slot_found:
                            break
                    if not slot_found:
                        print(f"Could not find a valid slot for {subject.name} in {stream.name}. Timetable incomplete.")
                        return
                        
            # Now, fill the remaining slots with non-academic subjects
            non_academic_subjects = [s for s in subjects_to_schedule if s.is_non_academic]
            for subject in non_academic_subjects:
                for _ in range(stream.non_academic_lectures_per_week):
                    slot_found = False
                    for day_index in range(stream.number_of_days):
                        day = all_days[day_index]
                        for timeslot in all_time_slots:
                            
                            is_lunch_break = timeslot.start_time.hour == 12 and timeslot.start_time.minute == 15
                            if is_lunch_break:
                                continue
                            
                            # Check if the slot is empty
                            is_slot_empty = not any(s for s in assigned_slots if s[0] == day and s[1] == timeslot)
                            if is_slot_empty:
                                TimetableEntry.objects.create(
                                    stream=stream,
                                    subject=subject,
                                    professor=None, # No professor for non-academic
                                    location=None, # No location for non-academic
                                    day_of_week=day,
                                    timeslot=timeslot
                                )
                                assigned_slots.append((day, timeslot, None, None))
                                slot_found = True
                                break
                        if slot_found:
                            break
                    if not slot_found:
                        print(f"Could not find a valid slot for {subject.name} in {stream.name}. Timetable incomplete.")
                        return
                        

    print("Timetable generated and saved successfully!")