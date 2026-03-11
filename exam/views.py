import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import PracticeTest, Question, TestAttempt, QuestionAnswer, UserProfile


@login_required
def start_exam(request, test_number):
    test = get_object_or_404(PracticeTest, number=test_number)
    
    # Check for in-progress attempt
    existing = TestAttempt.objects.filter(
        user=request.user, test=test, status='in_progress'
    ).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'resume' and existing:
            return redirect('exam:take_exam', attempt_id=existing.id)
        elif action == 'new':
            if existing:
                existing.status = 'abandoned'
                existing.save()
            attempt = TestAttempt.objects.create(
                user=request.user,
                test=test,
                time_remaining_seconds=test.time_limit_minutes * 60
            )
            # Pre-create answer slots
            for question in test.questions.all():
                QuestionAnswer.objects.create(attempt=attempt, question=question)
            return redirect('exam:take_exam', attempt_id=attempt.id)
    
    return render(request, 'exam/start.html', {
        'test': test,
        'existing_attempt': existing,
        'question_count': test.get_question_count(),
    })


@login_required
def take_exam(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status == 'completed':
        return redirect('exam:results', attempt_id=attempt.id)
    
    questions = attempt.test.questions.prefetch_related('passage').all()
    answers = {a.question_id: a for a in attempt.answers.all()}
    
    # Build questions data for template
    questions_data = []
    for q in questions:
        ans = answers.get(q.id)
        questions_data.append({
            'id': q.id,
            'number': q.question_number,
            'type': q.question_type,
            'skill': q.get_skill_category_display(),
            'text': q.question_text,
            'passage': {
                'title': q.passage.title,
                'author': q.passage.author,
                'passage_type': q.passage.passage_type,
                'content': q.passage.content,
            } if q.passage else None,
            'options': [
                {'letter': 'A', 'text': q.option_a},
                {'letter': 'B', 'text': q.option_b},
                {'letter': 'C', 'text': q.option_c},
                {'letter': 'D', 'text': q.option_d},
            ],
            'selected': ans.selected_answer if ans else '',
            'flagged': ans.is_flagged if ans else False,
        })
    
    flagged = json.loads(attempt.flagged_questions) if attempt.flagged_questions else []
    
    return render(request, 'exam/exam.html', {
        'attempt': attempt,
        'test': attempt.test,
        'questions_data': json.dumps(questions_data),
        'questions_list': questions_data,
        'time_remaining': attempt.time_remaining_seconds or attempt.test.time_limit_minutes * 60,
        'flagged_questions': flagged,
        'total_questions': len(questions_data),
    })


@login_required
@require_POST
def save_answer(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    if attempt.status != 'in_progress':
        return JsonResponse({'status': 'error', 'message': 'Attempt not in progress'})
    
    data = json.loads(request.body)
    question_id = data.get('question_id')
    selected = data.get('selected_answer', '')
    is_flagged = data.get('is_flagged', False)
    time_remaining = data.get('time_remaining', 0)
    
    question = get_object_or_404(Question, id=question_id, test=attempt.test)
    
    answer, _ = QuestionAnswer.objects.get_or_create(attempt=attempt, question=question)
    answer.selected_answer = selected
    answer.is_correct = (selected == question.correct_answer) if selected else False
    answer.is_flagged = is_flagged
    answer.save()
    
    # Update attempt
    attempt.current_question = data.get('current_question', attempt.current_question)
    attempt.time_remaining_seconds = time_remaining
    
    # Update flagged list
    flagged = json.loads(attempt.flagged_questions) if attempt.flagged_questions else []
    q_num = question.question_number
    if is_flagged and q_num not in flagged:
        flagged.append(q_num)
    elif not is_flagged and q_num in flagged:
        flagged.remove(q_num)
    attempt.flagged_questions = json.dumps(flagged)
    attempt.save()
    
    answered_count = attempt.answers.exclude(selected_answer='').count()
    return JsonResponse({
        'status': 'ok',
        'answered_count': answered_count,
        'total': attempt.test.get_question_count()
    })


@login_required
@require_POST
def submit_exam(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    if attempt.status != 'in_progress':
        return JsonResponse({'status': 'error'})
    
    data = json.loads(request.body)
    time_remaining = data.get('time_remaining', 0)
    
    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    time_total = attempt.test.time_limit_minutes * 60
    attempt.time_taken_seconds = time_total - time_remaining
    attempt.save()
    attempt.calculate_scores()
    
    # Update user profile study minutes
    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.total_study_minutes += (attempt.time_taken_seconds or 0) // 60
        from datetime import date
        today = date.today()
        if profile.last_study_date == today:
            pass
        elif profile.last_study_date and (today - profile.last_study_date).days == 1:
            profile.study_streak_days += 1
        else:
            profile.study_streak_days = 1
        profile.last_study_date = today
        profile.save()
    except Exception:
        pass
    
    return JsonResponse({'status': 'ok', 'redirect': f'/exam/results/{attempt.id}/'})


@login_required
def exam_results(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.select_related('question', 'question__passage').order_by('question__question_number')
    
    # Build detailed results
    results = []
    for ans in answers:
        q = ans.question
        results.append({
            'number': q.question_number,
            'text': q.question_text,
            'passage': q.passage,
            'your_answer': ans.selected_answer,
            'correct_answer': q.correct_answer,
            'is_correct': ans.is_correct,
            'options': {
                'A': q.option_a, 'B': q.option_b,
                'C': q.option_c, 'D': q.option_d
            },
            'explanation': q.explanation_correct,
            'explanation_chosen': q.get_explanation(ans.selected_answer) if ans.selected_answer else '',
            'skill': q.get_skill_category_display(),
            'type': q.get_question_type_display(),
        })
    
    # Skill breakdown
    skill_scores = {}
    for cat_field, cat_label in [
        ('reading_comprehension_score', 'Reading Comprehension'),
        ('argument_analysis_score', 'Argument Analysis'),
        ('grammar_editing_score', 'Grammar & Editing'),
        ('evidence_based_score', 'Evidence-Based Reasoning'),
        ('logical_reasoning_score', 'Logical Reasoning'),
        ('text_improvement_score', 'Text Improvement'),
    ]:
        score = getattr(attempt, cat_field)
        if score is not None:
            skill_scores[cat_label] = score
    
    # Weak areas
    weak_areas = [(label, score) for label, score in skill_scores.items() if score < 70]
    weak_areas.sort(key=lambda x: x[1])
    
    # GED score band
    ged = attempt.estimated_ged_score or 0
    if ged >= 175:
        score_band = "College Ready / Mastery"
        score_color = "#34c759"
    elif ged >= 165:
        score_band = "College Ready"
        score_color = "#30d158"
    elif ged >= 145:
        score_band = "Passing Score"
        score_color = "#ff9f0a"
    else:
        score_band = "Below Passing"
        score_color = "#ff453a"
    
    return render(request, 'exam/results.html', {
        'attempt': attempt,
        'results': results,
        'skill_scores': skill_scores,
        'weak_areas': weak_areas,
        'score_band': score_band,
        'score_color': score_color,
        'total': len(results),
        'correct': sum(1 for r in results if r['is_correct']),
        'incorrect': sum(1 for r in results if not r['is_correct']),
    })
