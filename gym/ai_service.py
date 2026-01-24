"""
AI Service
Handles AI-powered features using Google Gemini
"""
import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
import json


class GeminiAIService:
    """Google Gemini AI integration for workout and diet plans"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_workout_plan(self, member_profile, goals, duration_weeks=4, days_per_week=3):
        """
        Generate personalized workout plan
        
        Args:
            member_profile: MemberProfile object
            goals: str - fitness goals (e.g., "weight loss", "muscle gain", "endurance")
            duration_weeks: int - plan duration in weeks
            days_per_week: int - workout days per week
        
        Returns:
            dict with workout plan
        """
        prompt = f"""
        Create a detailed {duration_weeks}-week workout plan for a gym member with the following profile:
        
        Age: {member_profile.age}
        Membership Type: {member_profile.get_membership_type_display()}
        Goals: {goals}
        Workout Days per Week: {days_per_week}
        
        Please provide a structured workout plan in JSON format with the following structure:
        {{
            "plan_name": "Personalized Workout Plan",
            "duration_weeks": {duration_weeks},
            "goals": "{goals}",
            "weeks": [
                {{
                    "week_number": 1,
                    "focus": "Foundation Building",
                    "workouts": [
                        {{
                            "day": "Monday",
                            "workout_name": "Upper Body Strength",
                            "exercises": [
                                {{
                                    "name": "Bench Press",
                                    "sets": 3,
                                    "reps": "10-12",
                                    "rest_seconds": 90,
                                    "notes": "Focus on form"
                                }}
                            ]
                        }}
                    ]
                }}
            ],
            "nutrition_tips": ["Tip 1", "Tip 2"],
            "recovery_tips": ["Tip 1", "Tip 2"]
        }}
        
        Make it specific, progressive, and suitable for their age and goals.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            text = response.text
            
            # Try to parse JSON from response
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            else:
                json_str = text.strip()
            
            workout_plan = json.loads(json_str)
            return {
                'success': True,
                'plan': workout_plan,
                'generated_at': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback_plan': self._get_fallback_workout_plan(goals, duration_weeks, days_per_week)
            }
    
    def generate_diet_plan(self, member_profile, goals, dietary_restrictions=None):
        """
        Generate personalized diet plan
        
        Args:
            member_profile: MemberProfile object
            goals: str - fitness goals
            dietary_restrictions: list - dietary restrictions (e.g., ["vegetarian", "gluten-free"])
        
        Returns:
            dict with diet plan
        """
        restrictions = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
        
        prompt = f"""
        Create a detailed weekly diet plan for a gym member with the following profile:
        
        Age: {member_profile.age}
        Goals: {goals}
        Dietary Restrictions: {restrictions}
        
        Please provide a structured diet plan in JSON format with the following structure:
        {{
            "plan_name": "Personalized Diet Plan",
            "goals": "{goals}",
            "daily_calories": 2000,
            "macros": {{
                "protein_grams": 150,
                "carbs_grams": 200,
                "fats_grams": 60
            }},
            "meals": [
                {{
                    "day": "Monday",
                    "breakfast": {{
                        "name": "Protein Oatmeal",
                        "ingredients": ["Oats", "Protein powder", "Banana"],
                        "calories": 400,
                        "protein": 30,
                        "carbs": 50,
                        "fats": 10
                    }},
                    "lunch": {{}},
                    "dinner": {{}},
                    "snacks": []
                }}
            ],
            "hydration_tips": ["Drink 3L water daily"],
            "supplement_recommendations": ["Whey protein", "Multivitamin"]
        }}
        
        Make it practical, balanced, and aligned with their goals.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Extract JSON
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            else:
                json_str = text.strip()
            
            diet_plan = json.loads(json_str)
            return {
                'success': True,
                'plan': diet_plan,
                'generated_at': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback_plan': self._get_fallback_diet_plan(goals)
            }
    
    def analyze_workout_progress(self, workout_logs):
        """
        Analyze workout progress and provide insights
        
        Args:
            workout_logs: QuerySet of WorkoutLog objects
        
        Returns:
            dict with analysis and recommendations
        """
        # Prepare workout data
        workout_data = []
        for log in workout_logs[:30]:  # Last 30 workouts
            workout_data.append({
                'exercise': log.exercise.name,
                'value': float(log.value),
                'sets': log.sets,
                'reps': log.reps,
                'date': log.logged_at.strftime('%Y-%m-%d')
            })
        
        prompt = f"""
        Analyze the following workout data and provide insights:
        
        {json.dumps(workout_data, indent=2)}
        
        Please provide analysis in JSON format:
        {{
            "overall_progress": "Excellent/Good/Needs Improvement",
            "strengths": ["Strength 1", "Strength 2"],
            "areas_to_improve": ["Area 1", "Area 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "predicted_goals": {{
                "next_month": "Prediction for next month",
                "three_months": "Prediction for 3 months"
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            else:
                json_str = text.strip()
            
            analysis = json.loads(json_str)
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_fallback_workout_plan(self, goals, duration_weeks, days_per_week):
        """Fallback workout plan if AI fails"""
        return {
            "plan_name": "Basic Workout Plan",
            "duration_weeks": duration_weeks,
            "goals": goals,
            "weeks": [
                {
                    "week_number": 1,
                    "focus": "Foundation",
                    "workouts": [
                        {
                            "day": "Monday",
                            "workout_name": "Full Body",
                            "exercises": [
                                {"name": "Squats", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                                {"name": "Bench Press", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                                {"name": "Rows", "sets": 3, "reps": "10-12", "rest_seconds": 90}
                            ]
                        }
                    ]
                }
            ],
            "nutrition_tips": ["Eat protein-rich foods", "Stay hydrated"],
            "recovery_tips": ["Get 7-8 hours sleep", "Stretch after workouts"]
        }
    
    def _get_fallback_diet_plan(self, goals):
        """Fallback diet plan if AI fails"""
        return {
            "plan_name": "Basic Diet Plan",
            "goals": goals,
            "daily_calories": 2000,
            "macros": {"protein_grams": 150, "carbs_grams": 200, "fats_grams": 60},
            "meals": [
                {
                    "day": "Monday",
                    "breakfast": {
                        "name": "Oatmeal with Protein",
                        "calories": 400,
                        "protein": 30,
                        "carbs": 50,
                        "fats": 10
                    }
                }
            ],
            "hydration_tips": ["Drink 3L water daily"],
            "supplement_recommendations": ["Whey protein"]
        }


# Convenience functions
def generate_ai_workout_plan(member, goals, duration_weeks=4, days_per_week=3):
    """Quick function to generate workout plan"""
    service = GeminiAIService()
    return service.generate_workout_plan(member, goals, duration_weeks, days_per_week)


def generate_ai_diet_plan(member, goals, dietary_restrictions=None):
    """Quick function to generate diet plan"""
    service = GeminiAIService()
    return service.generate_diet_plan(member, goals, dietary_restrictions)


def analyze_member_progress(workout_logs):
    """Quick function to analyze progress"""
    service = GeminiAIService()
    return service.analyze_workout_progress(workout_logs)
