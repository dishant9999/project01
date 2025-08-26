from django.core.management.base import BaseCommand
from timetable_app.models import Professor, Subject, Stream, Location, TimeSlot
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Validates data to ensure timetable generation is possible.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data validation...'))
        
        errors = []

        # Check 1: All academic subjects must have a professor and lectures
        for subject in Subject.objects.filter(is_non_academic=False):
            if not subject.professors.exists():
                errors.append(f"Academic Subject '{subject.name}' has no professor assigned.")
            if subject.lectures_per_week <= 0:
                errors.append(f"Academic Subject '{subject.name}' has 0 or fewer lectures per week.")

        # Check 2: All streams must have subjects
        for stream in Stream.objects.all():
            if not stream.subjects.exists():
                errors.append(f"Stream '{stream.name}' has no subjects assigned.")

        # Check 3: Professor workload is manageable
        professors = Professor.objects.all()
        for professor in professors:
            assigned_subjects = Subject.objects.filter(professors=professor)
            total_lectures_needed = sum(s.lectures_per_week for s in assigned_subjects)
            if total_lectures_needed > professor.total_weekly_lectures:
                errors.append(f"Professor '{professor.name}' has more lectures assigned ({total_lectures_needed}) than their weekly limit ({professor.total_weekly_lectures}).")
            
            # Check 4: Professor working hours
            if professor.working_hours_start >= professor.working_hours_end:
                errors.append(f"Professor '{professor.name}' has invalid working hours.")

        # Check 5: Enough locations
        if not Location.objects.exists():
            errors.append("No locations have been added to the database.")
            
        # Check 6: Enough time slots
        if not TimeSlot.objects.exists():
            errors.append("No time slots have been added to the database.")

        if errors:
            self.stdout.write(self.style.ERROR('Validation Failed! Please fix the following issues:'))
            for error in errors:
                self.stdout.write(self.style.WARNING(f'- {error}'))
            return False
        else:
            self.stdout.write(self.style.SUCCESS('Data is valid. Timetable generation can proceed.'))
            return True