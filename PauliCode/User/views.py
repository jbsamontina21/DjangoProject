from django.shortcuts import render, redirect, get_object_or_404
from .models import User
from django.contrib import messages


def index(request):
    return render(request, 'User/index.html')

def dashboard(request):
    return render(request, 'User/dashboard.html', {
        'currentpage': 'dashboard'
    })


def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        school_id = request.POST.get('school_id', '').strip()
        user_type = request.POST.get('user_type', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        context = {
            'first_name': first_name,
            'last_name': last_name,
            'school_id': school_id,
            'user_type': user_type,
        }

        if not all([first_name, last_name, school_id, user_type, password, confirm_password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'User/sign-up.html', context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'User/sign-up.html', context)

        if User.objects.filter(school_id=school_id).exists():
            messages.error(request, "School ID already exists.")
            return render(request, 'User/sign-up.html', context)

        User.objects.create(
            school_id=school_id,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type=user_type.capitalize()
        )
        messages.success(request, "Account created successfully!")
        return render(request, 'User/sign-up.html', {'redirect': True})

    return render(request, 'User/sign-up.html')


   

def userlist(request):
    users = User.objects.all()

    # Handle Add User (POST from modal)
    if request.method == "POST" and "add_user" in request.POST:
        school_id = request.POST.get("school_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        user_type = request.POST.get("user_type")
        user_image = request.FILES.get("user_image")

        User.objects.create(
            school_id=school_id,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            user_image=user_image
        )
        return redirect("userlist")

    return render(request, 'User/userlist.html', {
        'users': users,
        'currentpage': 'userlist'
    })


# ✅ FIXED: use school_id, not user_id
def user_edit(request, school_id):
    user = get_object_or_404(User, school_id=school_id)

    if request.method == "POST":
        user.school_id = request.POST.get("school_id")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.user_type = request.POST.get("user_type")
        if request.FILES.get("user_image"):
            user.user_image = request.FILES.get("user_image")
        user.save()
        return redirect("userlist")

    return redirect("userlist")


# ✅ FIXED: use school_id, not user_id
def user_delete(request, school_id):
    user = get_object_or_404(User, school_id=school_id)
    if request.method == "POST":
        user.delete()
    return redirect("userlist")
