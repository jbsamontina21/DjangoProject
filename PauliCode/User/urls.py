from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # shows the login page
    path('login/', views.login_view, name='login'),  # handles login form submission
    path('logout/', views.logout_view, name='logout'),  # handles logout
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
]
