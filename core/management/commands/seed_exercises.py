from django.core.management.base import BaseCommand
from core.gamification_models import Exercise

class Command(BaseCommand):
    help = 'Seeds initial database of exercises'

    def handle(self, *args, **kwargs):
        exercises = [
            # Strength - Chest
            {'name': 'Bench Press', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['chest', 'triceps', 'shoulders']},
            {'name': 'Push Ups', 'category': 'strength', 'measurement_type': 'reps', 'muscle_groups': ['chest', 'triceps']},
            {'name': 'Incline Bench Press', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['chest', 'shoulders']},
            
            # Strength - Back
            {'name': 'Deadlift', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['back', 'legs', 'core']},
            {'name': 'Pull Ups', 'category': 'strength', 'measurement_type': 'reps', 'muscle_groups': ['back', 'biceps']},
            {'name': 'Barbell Row', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['back', 'biceps']},
            
            # Strength - Legs
            {'name': 'Squat', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['quads', 'glutes', 'hamstrings']},
            {'name': 'Lunges', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['legs', 'glutes']},
            {'name': 'Leg Press', 'category': 'strength', 'measurement_type': 'weight', 'muscle_groups': ['legs']},
            
            # Cardio
            {'name': 'Treadmill Run', 'category': 'cardio', 'measurement_type': 'distance', 'muscle_groups': ['legs', 'cardio']},
            {'name': 'Cycling', 'category': 'cardio', 'measurement_type': 'distance', 'muscle_groups': ['legs', 'cardio']},
            {'name': 'Rowing Machine', 'category': 'cardio', 'measurement_type': 'distance', 'muscle_groups': ['full_body', 'cardio']},
            
            # Flexibility
            {'name': 'Yoga Session', 'category': 'flexibility', 'measurement_type': 'time', 'muscle_groups': ['full_body']},
            {'name': 'Stretching', 'category': 'flexibility', 'measurement_type': 'time', 'muscle_groups': ['full_body']},
        ]
        
        created_count = 0
        for ex in exercises:
            _, created = Exercise.objects.get_or_create(
                name=ex['name'],
                defaults={
                    'category': ex['category'],
                    'measurement_type': ex['measurement_type'],
                    'muscle_groups': ex['muscle_groups']
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} new exercises'))
