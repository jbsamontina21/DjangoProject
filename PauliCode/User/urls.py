from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path('userlist/', views.userlist, name='userlist'),
    path('user/edit/<str:school_id>/', views.user_edit, name="user_edit"),
    path('user/delete/<str:school_id>/', views.user_delete, name="user_delete"),
]