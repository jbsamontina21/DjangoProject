from django.shortcuts import render, redirect, get_object_or_404
from .models import User
from django.contrib import messages

# ---------------- LOGIN & DASHBOARD ---------------- #

def index(request):
    # If already logged in, redirect to dashboard
    if request.session.get('school_id'):
        return redirect('dashboard')
    return render(request, 'User/index.html')


def login_view(request):
    if request.method == 'POST':
        school_id = request.POST.get('school_id', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(school_id=school_id, password=password)
            
            # store user data in session
            request.session['school_id'] = user.school_id
            request.session['first_name'] = user.first_name
            request.session['last_name'] = user.last_name
            request.session['user_image'] = user.user_image.url
            request.session['user_type'] = user.user_type

            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        except User.DoesNotExist:
            messages.error(request, "Invalid School ID or Password.")
            return redirect('index')

    return render(request, 'User/index.html')


def dashboard(request):
    school_id = request.session.get('school_id')

    if not school_id:
        # redirect to login if not logged in
        messages.warning(request, "Please log in first.")
        return redirect('index')

    user = User.objects.filter(school_id=school_id).first()

    return render(request, 'User/dashboard.html', {
        'currentpage': 'dashboard',
        'user': user,
    })


def logout_view(request):
    request.session.flush()  # clears all session data
    messages.success(request, "You have been logged out successfully.")
    return redirect('index')

# ---------------- SIGNUP ---------------- #

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

# ---------------- USER MANAGEMENT ---------------- #


