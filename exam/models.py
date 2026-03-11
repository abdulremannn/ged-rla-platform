from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Passage(models.Model):
    PASSAGE_TYPES = [
        ('informational', 'Informational Text'),
        ('argumentative', 'Argumentative Essay'),
        ('historical', 'Historical Document'),
        ('science', 'Science Article'),
        ('editorial', 'Editorial'),
        ('literary', 'Literary Nonfiction'),
    ]
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200, blank=True)
    passage_type = models.CharField(max_length=30, choices=PASSAGE_TYPES)
    content = models.TextField()
    source = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PracticeTest(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    difficulty_label = models.CharField(max_length=50)
    time_limit_minutes = models.IntegerField(default=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Practice Test {self.number}: {self.title}"

    def get_question_count(self):
        return self.questions.count()


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('drag_drop', 'Drag and Drop / Ordering'),
        ('text_analysis', 'Text Analysis'),
        ('editing', 'Editing and Revision'),
        ('extended_response', 'Extended Response'),
    ]
    SKILL_CATEGORIES = [
        ('reading_comprehension', 'Reading Comprehension'),
        ('argument_analysis', 'Argument Analysis'),
        ('grammar_editing', 'Grammar & Editing'),
        ('evidence_based', 'Evidence-Based Reasoning'),
        ('logical_reasoning', 'Logical Reasoning'),
        ('text_improvement', 'Text Improvement'),
        ('vocabulary', 'Vocabulary in Context'),
        ('structure_function', 'Structure & Function'),
    ]

    test = models.ForeignKey(PracticeTest, on_delete=models.CASCADE, related_name='questions')
    passage = models.ForeignKey(Passage, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_number = models.IntegerField()
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPES, default='multiple_choice')
    skill_category = models.CharField(max_length=40, choices=SKILL_CATEGORIES)
    question_text = models.TextField()
    option_a = models.TextField(blank=True)
    option_b = models.TextField(blank=True)
    option_c = models.TextField(blank=True)
    option_d = models.TextField(blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    explanation_correct = models.TextField()
    explanation_a = models.TextField(blank=True)
    explanation_b = models.TextField(blank=True)
    explanation_c = models.TextField(blank=True)
    explanation_d = models.TextField(blank=True)
    difficulty_points = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']

    def __str__(self):
        return f"Test {self.test.number} Q{self.question_number}"

    def get_option(self, letter):
        return getattr(self, f'option_{letter.lower()}', '')

    def get_explanation(self, letter):
        return getattr(self, f'explanation_{letter.lower()}', '')


class TestAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('timed_out', 'Timed Out'),
        ('abandoned', 'Abandoned'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(PracticeTest, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    raw_score = models.IntegerField(null=True, blank=True)
    percentage_score = models.FloatField(null=True, blank=True)
    estimated_ged_score = models.IntegerField(null=True, blank=True)
    reading_comprehension_score = models.FloatField(null=True, blank=True)
    argument_analysis_score = models.FloatField(null=True, blank=True)
    grammar_editing_score = models.FloatField(null=True, blank=True)
    evidence_based_score = models.FloatField(null=True, blank=True)
    logical_reasoning_score = models.FloatField(null=True, blank=True)
    text_improvement_score = models.FloatField(null=True, blank=True)
    current_question = models.IntegerField(default=1)
    flagged_questions = models.TextField(default='[]')
    time_remaining_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - Test {self.test.number} - {self.status}"

    def calculate_scores(self):
        answers = self.answers.all()
        total = answers.count()
        if total == 0:
            return
        correct = answers.filter(is_correct=True).count()
        self.raw_score = correct
        self.percentage_score = round((correct / total) * 100, 1)
        self.estimated_ged_score = self._calculate_ged_score(self.percentage_score)
        for category in ['reading_comprehension', 'argument_analysis', 'grammar_editing',
                         'evidence_based', 'logical_reasoning', 'text_improvement']:
            cat_answers = answers.filter(question__skill_category=category)
            if cat_answers.exists():
                cat_correct = cat_answers.filter(is_correct=True).count()
                score = round((cat_correct / cat_answers.count()) * 100, 1)
                setattr(self, f'{category}_score', score)
        self.save()

    def _calculate_ged_score(self, percentage):
        if percentage < 30:
            return 100 + int(percentage * 1.0)
        elif percentage < 50:
            return 130 + int((percentage - 30) * 0.75)
        elif percentage < 65:
            return 145 + int((percentage - 50) * 0.8)
        elif percentage < 75:
            return 157 + int((percentage - 65) * 0.8)
        elif percentage < 85:
            return 165 + int((percentage - 75) * 1.0)
        elif percentage < 92:
            return 175 + int((percentage - 85) * 0.86)
        else:
            return min(200, 181 + int((percentage - 92) * 2.4))


class QuestionAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Q{self.question.question_number}: {self.selected_answer}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    target_score = models.IntegerField(default=190)
    baseline_score = models.IntegerField(default=155)
    study_streak_days = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    total_study_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_best_score(self):
        attempts = self.user.test_attempts.filter(status='completed')
        if attempts.exists():
            return attempts.order_by('-estimated_ged_score').first().estimated_ged_score
        return None

    def get_average_score(self):
        attempts = self.user.test_attempts.filter(status='completed', estimated_ged_score__isnull=False)
        if attempts.exists():
            scores = [a.estimated_ged_score for a in attempts]
            return round(sum(scores) / len(scores))
        return None
