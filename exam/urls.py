from django.urls import path
from . import views

app_name = 'exam'

urlpatterns = [
    path('start/<int:test_number>/', views.start_exam, name='start_exam'),
    path('take/<int:attempt_id>/', views.take_exam, name='take_exam'),
    path('save/<int:attempt_id>/', views.save_answer, name='save_answer'),
    path('submit/<int:attempt_id>/', views.submit_exam, name='submit_exam'),
    path('results/<int:attempt_id>/', views.exam_results, name='results'),
]
