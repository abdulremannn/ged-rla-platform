from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Avg, Count
from exam.models import PracticeTest, TestAttempt, UserProfile


@login_required
def home(request):
    tests = PracticeTest.objects.all()
    attempts = TestAttempt.objects.filter(user=request.user).select_related('test')
    
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    completed = attempts.filter(status='completed')
    in_progress = attempts.filter(status='in_progress')
    
    # Test status map
    completed_map = {a.test.number: a for a in completed.order_by('-completed_at')}
    in_progress_map = {a.test.number: a for a in in_progress.order_by('-started_at')}
    
    test_data = []
    for test in tests:
        status = 'not_started'
        score = None
        attempt = None
        if test.number in completed_map:
            status = 'completed'
            attempt = completed_map[test.number]
            score = attempt.estimated_ged_score
        elif test.number in in_progress_map:
            status = 'in_progress'
            attempt = in_progress_map[test.number]
        
        test_data.append({
            'test': test,
            'status': status,
            'score': score,
            'attempt': attempt,
        })
    
    # Analytics
    scores = [a.estimated_ged_score for a in completed if a.estimated_ged_score]
    avg_score = round(sum(scores) / len(scores)) if scores else None
    best_score = max(scores) if scores else None
    
    # Category averages
    category_scores = {}
    if completed.exists():
        for cat, label in [
            ('reading_comprehension_score', 'Reading Comprehension'),
            ('argument_analysis_score', 'Argument Analysis'),
            ('grammar_editing_score', 'Grammar & Editing'),
            ('evidence_based_score', 'Evidence-Based Reasoning'),
            ('logical_reasoning_score', 'Logical Reasoning'),
            ('text_improvement_score', 'Text Improvement'),
        ]:
            vals = [getattr(a, cat) for a in completed if getattr(a, cat) is not None]
            if vals:
                category_scores[label] = round(sum(vals) / len(vals), 1)
    
    # Score trend (last 5 completed tests)
    trend = list(completed.order_by('completed_at')[:10].values_list('estimated_ged_score', flat=True))
    
    # Recommendations
    recommendations = []
    if category_scores:
        weak = [(label, score) for label, score in category_scores.items() if score < 70]
        weak.sort(key=lambda x: x[1])
        for label, score in weak[:3]:
            rec_map = {
                'Reading Comprehension': 'Practice identifying main ideas and supporting details. Re-read passages actively.',
                'Argument Analysis': 'Focus on identifying claims, evidence, and logical structure in editorial texts.',
                'Grammar & Editing': 'Review comma rules, subject-verb agreement, and pronoun-antecedent agreement.',
                'Evidence-Based Reasoning': 'Practice selecting the most relevant textual evidence to support claims.',
                'Logical Reasoning': 'Study common logical fallacies: post hoc, false dichotomy, hasty generalization.',
                'Text Improvement': 'Practice identifying sentences that disrupt paragraph flow and coherence.',
            }
            recommendations.append({'area': label, 'score': score, 'tip': rec_map.get(label, 'Review this skill area.')})
    
    return render(request, 'dashboard/home.html', {
        'test_data': test_data,
        'profile': profile,
        'completed_count': completed.count(),
        'avg_score': avg_score,
        'best_score': best_score,
        'score_trend': trend,
        'category_scores': category_scores,
        'recommendations': recommendations,
    })


@login_required
def analytics(request):
    attempts = TestAttempt.objects.filter(user=request.user, status='completed').order_by('completed_at')
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    chart_data = []
    for a in attempts:
        chart_data.append({
            'test': f'Test {a.test.number}',
            'ged_score': a.estimated_ged_score,
            'percentage': a.percentage_score,
            'date': a.completed_at.strftime('%b %d') if a.completed_at else '',
        })
    
    skill_history = {}
    for a in attempts:
        for cat, label in [
            ('reading_comprehension_score', 'Reading Comprehension'),
            ('argument_analysis_score', 'Argument Analysis'),
            ('grammar_editing_score', 'Grammar & Editing'),
            ('evidence_based_score', 'Evidence'),
            ('logical_reasoning_score', 'Logical Reasoning'),
            ('text_improvement_score', 'Text Improvement'),
        ]:
            val = getattr(a, cat)
            if val is not None:
                if label not in skill_history:
                    skill_history[label] = []
                skill_history[label].append(val)
    
    return render(request, 'dashboard/analytics.html', {
        'attempts': attempts,
        'chart_data': chart_data,
        'skill_history': skill_history,
        'profile': profile,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard:home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})
