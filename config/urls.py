from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from dashboard import views as views_dashboard
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views_dashboard.landing, name='landing'),
    path('dashboard/', include('dashboard.urls')),
    path('exam/', include('exam.urls')),
    path('auth/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('auth/register/', include('dashboard.urls_auth')),
]
