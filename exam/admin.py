from django.contrib import admin
from .models import PracticeTest, Passage, Question, TestAttempt, QuestionAnswer, UserProfile

@admin.register(PracticeTest)
class PracticeTestAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'difficulty_label', 'get_question_count', 'is_active']
    list_filter = ['difficulty_label', 'is_active']

@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ['title', 'passage_type', 'author']
    list_filter = ['passage_type']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'question_number', 'skill_category', 'question_type', 'correct_answer']
    list_filter = ['test', 'skill_category', 'question_type']
    search_fields = ['question_text']

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'status', 'estimated_ged_score', 'percentage_score', 'started_at']
    list_filter = ['status', 'test']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_score', 'baseline_score', 'study_streak_days']
