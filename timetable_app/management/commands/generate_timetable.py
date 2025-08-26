from django.core.management.base import BaseCommand
from timetable_app.timetable_generator import generate_timetable

class Command(BaseCommand):
    help = 'Generates the university timetable automatically.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting timetable generation...'))
        try:
            generate_timetable()
            self.stdout.write(self.style.SUCCESS('Timetable generation finished successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))