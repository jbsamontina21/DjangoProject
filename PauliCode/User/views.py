from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Class, Problem, Enrollment, ProblemTestCase, Submission
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse 
import json, requests   
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# ---------------- LOGIN & DASHBOARD ---------------- #

def index(request):
    school_id = request.session.get('school_id')
    if school_id:
        user_type = request.session.get('user_type')
        if user_type == 'Teacher':
            return redirect('dashboard')
        else:
            return redirect('StudentDashboard')
    return render(request, 'User/index.html')



def login_view(request):
    if request.method == 'POST':
        school_id = request.POST.get('school_id', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(school_id=school_id, password=password)
            
            # Store user data in session
            request.session['school_id'] = user.school_id
            request.session['first_name'] = user.first_name
            request.session['last_name'] = user.last_name
            request.session['user_image'] = user.user_image.url if user.user_image else None
            request.session['user_type'] = user.user_type

            messages.success(request, f"Welcome back, {user.first_name}!")

            # Redirect based on user type
            if user.user_type == 'Teacher':
                return redirect('dashboard')  # make sure 'dashboard' exists in urls.py
            else:
                return redirect('StudentDashboard')  

        except User.DoesNotExist:
            messages.error(request, "Invalid School ID or Password.")
            return redirect('index')

    # Render login page
    return render(request, 'User/index.html')


#-------------TEACHER DASHBOARD----------------------#
def dashboard(request):
    school_id = request.session.get('school_id')

    if not school_id:
        # Redirect to login if not logged in
        messages.warning(request, "Please log in first.")
        return redirect('index')

    user = User.objects.filter(school_id=school_id).first()

    # Get classes created by the teacher
    classes = Class.objects.filter(teacher=user).order_by('-class_id')

    return render(request, 'User/dashboard.html', {
        'currentpage': 'dashboard',
        'user': user,
        'classes': classes,  # Pass class list to template
    })

    

def logout_view(request):
    request.session.flush()  # Clears all session data
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


# ---------------- CLASS MANAGEMENT ---------------- #

def create_class(request):
    if request.method == "POST":
        class_code = request.POST.get("class_code")
        title = request.POST.get("title")
        description = request.POST.get("description")
        upload_icon = request.FILES.get("upload_icon")

        teacher = User.objects.get(school_id=request.session.get("school_id"))

        # Prevent duplicate class codes
        if Class.objects.filter(class_code=class_code).exists():
            messages.error(request, "Class code already exists.")
            # Redirect back to the same page (MyClasses or dashboard)
            previous_page = request.META.get('HTTP_REFERER', '')
            if 'MyClasses' in previous_page:
                return redirect('MyClasses')
            return redirect('dashboard')

        # Create the class
        Class.objects.create(
            class_code=class_code,
            title=title,
            description=description,
            upload_icon=upload_icon,
            teacher=teacher
        )
        messages.success(request, "Class created successfully!")

        # Redirect to the same page where the request came from
        previous_page = request.META.get('HTTP_REFERER', '')
        if 'MyClasses' in previous_page:
            return redirect('MyClasses')
        return redirect('dashboard')

    return redirect('dashboard')

def MyClasses(request):
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    teacher = User.objects.filter(school_id=school_id).first()
    classes = Class.objects.filter(teacher=teacher).order_by('-class_id')  # use class_id

    return render(request, 'User/MyClasses.html', {
        'currentpage': 'MyClasses',
        'user': teacher,
        'classes': classes,
    })



def delete_class(request, class_id):
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    class_obj = get_object_or_404(Class, class_id=class_id, teacher__school_id=school_id)
    class_obj.delete()
    messages.success(request, "Class deleted successfully!")
    return redirect('MyClasses')

# ---------------- CLASS DETAILS PAGE ---------------- #

def classDetails(request, class_id):
    # Check if user is logged in
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    # Get teacher info
    teacher = get_object_or_404(User, school_id=school_id)

    # Get the class object
    class_obj = get_object_or_404(Class, class_id=class_id, teacher=teacher)

    # Base query
    problems = Problem.objects.filter(class_id=class_obj).order_by('-problem_id')

    # Get students enrolled
    students = (
        Enrollment.objects.filter(class_id=class_obj)
        .select_related('student_id')
        .order_by('student_id__first_name')
    )

    # ---- SEARCH AND FILTER ----
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', '').strip()

    # If the filter button is clicked again (same filter), reset it
    last_filter = request.session.get('last_filter', '')

    if filter_type == last_filter:
        # Clicking the same filter twice removes it
        filter_type = ''
        request.session['last_filter'] = ''
    else:
        # Otherwise, remember the current filter
        request.session['last_filter'] = filter_type

    # Apply search and filter logic
    if query:
        problems = problems.filter(problem_title__icontains=query)
    if filter_type == 'Assignment':
        problems = problems.filter(problem_type='Assignment')
    elif filter_type == 'Quiz':
        problems = problems.filter(problem_type='Quiz')

    # If search bar is empty and submitted, refresh (no filter)
    if not query and not filter_type:
        problems = Problem.objects.filter(class_id=class_obj).order_by('-problem_id')

    return render(request, 'User/classDetails.html', {
        'currentpage': 'MyClasses',
        'user': teacher,
        'class': class_obj,
        'problems': problems,
        'students': students,
        'query': query,
        'filter_type': filter_type,
    })



    # ---- ADD PROBLEM------------

def add_problem(request, class_id):
    # Ensure user is logged in
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    teacher = get_object_or_404(User, school_id=school_id)
    class_obj = get_object_or_404(Class, class_id=class_id, teacher=teacher)

    if request.method == "POST":
        title = request.POST.get("problem_title", "").strip()
        description = request.POST.get("problem_description", "").strip()
        problem_type = request.POST.get("problem_type", "").strip()
        total_score = request.POST.get("total_score", "").strip()
        time_limit = request.POST.get("time_limit", "").strip()
        due_date = request.POST.get("due_date", "").strip()

        # Test cases
        inputs = [
            request.POST.get(f"input{i}", "").strip() for i in range(1, 4)
        ]
        outputs = [
            request.POST.get(f"output{i}", "").strip() for i in range(1, 4)
        ]

        # Validation
        if not all([title, description, problem_type, total_score, time_limit, due_date]):
            messages.error(request, "Please fill in all fields.")
            return redirect('classDetails', class_id=class_id)

        try:
            total_score = int(total_score)
            time_limit = int(time_limit)
            due_date = datetime.fromisoformat(due_date)
        except ValueError:
            messages.error(request, "Invalid input values.")
            return redirect('classDetails', class_id=class_id)

        # Create Problem
        problem = Problem.objects.create(
            class_id=class_obj,
            teacher_id=teacher,
            problem_title=title,
            problem_description=description,
            problem_type=problem_type,
            total_score=total_score,
            time_limit=time_limit,
            due_date=due_date,
        )

        # Add test cases
        for i in range(3):
            if inputs[i] or outputs[i]:
                ProblemTestCase.objects.create(
                    problem_id=problem,
                    input_data=inputs[i],
                    expected_output=outputs[i]
                )

        messages.success(request, f"Problem '{title}' created successfully!")
        return redirect('classDetails', class_id=class_id)

    return redirect('classDetails', class_id=class_id)

#--------------------------Problem Details---------------------------------#

def get_problem_details(request, problem_id):
    """Return JSON data for a specific problem (used in modal)."""
    problem = get_object_or_404(Problem, pk=problem_id)
    test_cases = ProblemTestCase.objects.filter(problem_id=problem)

    data = {
        "problem_id": problem.problem_id,
        "title": problem.problem_title,
        "description": problem.problem_description,
        "type": problem.problem_type,
        "score": problem.total_score,
        "time_limit": problem.time_limit,
        "due_date": problem.due_date.strftime("%Y-%m-%dT%H:%M"),
        "test_cases": [
            {"input": t.input_data, "output": t.expected_output} for t in test_cases
        ]
    }
    return JsonResponse(data)


#----------------------Problem Deletion------------------------------------#

def delete_problem(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    class_id = problem.class_id.class_id
    problem.delete()
    messages.success(request, "Problem deleted successfully.")
    return redirect('classDetails', class_id=class_id)

#----------------------Edit Problem-----------------------------------------#
def edit_problem(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    class_id = problem.class_id.class_id

    if request.method == "POST":
        title = request.POST.get("problem_title", "").strip()
        description = request.POST.get("problem_description", "").strip()
        problem_type = request.POST.get("problem_type", "").strip()
        total_score = request.POST.get("total_score", "").strip()
        time_limit = request.POST.get("time_limit", "").strip()
        due_date = request.POST.get("due_date", "").strip()

        try:
            problem.problem_title = title
            problem.problem_description = description
            problem.problem_type = problem_type
            problem.total_score = int(total_score)
            problem.time_limit = int(time_limit)
            problem.due_date = datetime.fromisoformat(due_date)
            problem.save()

            # Update only this problem's test cases
            ProblemTestCase.objects.filter(problem_id=problem.problem_id).delete()
            for i in range(3):
                input_data = request.POST.get(f"input{i+1}", "").strip()
                output_data = request.POST.get(f"output{i+1}", "").strip()
                if input_data or output_data:
                    ProblemTestCase.objects.create(
                        problem_id=problem,
                        input_data=input_data,
                        expected_output=output_data
                    )

            messages.success(request, f"Problem '{problem.problem_title}' updated successfully!")
        except Exception as e:
            messages.error(request, f"Update failed: {e}")

    return redirect('classDetails', class_id=class_id)


#---------------Student Part-------------------------#

#---------------Student Dashboard--------------------#
def StudentDashboard(request):  # for student
    school_id = request.session.get('school_id')

    if not school_id:
        # Redirect to login if not logged in
        messages.warning(request, "Please log in first.")
        return redirect('index')

    student = User.objects.filter(school_id=school_id).first()

    # Get all classes the student is enrolled in
    enrolled_classes = Class.objects.filter(
        enrollment__student_id=student
    ).order_by('-class_id').distinct()

    return render(request, 'Students/StudentDashboard.html', {
        'currentpage': 'StudentDashboard',
        'user': student,
        'classes': enrolled_classes,
    })


#---------------Student Enrolled Classes----------------#
def StudentClass(request):
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    student = User.objects.filter(school_id=school_id).first()

    # Get classes the student is enrolled in
    enrolled_classes = Class.objects.filter(
        enrollment__student_id=student
    ).order_by('-class_id').distinct()

    return render(request, 'Students/StudentClass.html', {
        'currentpage': 'StudentClass',
        'user': student,
        'classes': enrolled_classes,
    })

# ---------------- JOIN CLASS (STUDENT) ---------------- #
def join_class(request):
    if request.method == "POST":
        school_id = request.session.get('school_id')
        if not school_id:
            messages.warning(request, "Please log in first.")
            return redirect('index')

        student = User.objects.get(school_id=school_id)
        class_code = request.POST.get('class_code', '').strip()

        if not class_code:
            messages.error(request, "Please enter a class code.")
            return redirect('StudentClass')

        try:
            class_obj = Class.objects.get(class_code=class_code)
        except Class.DoesNotExist:
            messages.error(request, "Class not found. Please check the code.")
            return redirect('StudentClass')

        # Check if already enrolled
        if Enrollment.objects.filter(class_id=class_obj, student_id=student).exists():
            messages.warning(request, f"You are already enrolled in '{class_obj.title}'.")
            return redirect('StudentClass')

        # Create enrollment
        Enrollment.objects.create(class_id=class_obj, student_id=student)
        messages.success(request, f"Successfully joined '{class_obj.title}'!")
        return redirect('StudentClass')

    # If GET request, just redirect
    return redirect('StudentClass')

#---------------STUDENT CLASS DETAILS PAGE---------------------#

def student_class_details(request, class_id):
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    student = get_object_or_404(User, school_id=school_id)

    # Ensure the student is enrolled in this class
    class_obj = get_object_or_404(Class, class_id=class_id, enrollment__student_id=student)

    # Get problems for this class
    problems = Problem.objects.filter(class_id=class_obj).order_by('-problem_id')

    # Optional: Apply search/filter if needed
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', '').strip()
    if query:
        problems = problems.filter(problem_title__icontains=query)
    if filter_type == 'Assignment':
        problems = problems.filter(problem_type='Assignment')
    elif filter_type == 'Quiz':
        problems = problems.filter(problem_type='Quiz')

    return render(request, 'Students/student_class_details.html', {
        'user': student,
        'class': class_obj,
        'problems': problems,
        'query': query,
        'filter_type': filter_type,
        'currentpage': 'StudentClass',
    })

#------------------Unenroll Function--------------------#
def unenroll_class(request, class_id):
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    student = get_object_or_404(User, school_id=school_id)
    enrollment = Enrollment.objects.filter(class_id=class_id, student_id=student).first()
    if enrollment:
        enrollment.delete()
        messages.success(request, "You have unenrolled from the class.")
    else:
        messages.error(request, "You are not enrolled in this class.")

    return redirect('StudentClass')

# External code runner API
PISTON_URL = "https://emkc.org/api/v2/piston/execute"

# ---------------- PLAYGROUND PAGE ---------------- #
def playground(request, problem_id):
    """Renders the coding playground for a student"""
    school_id = request.session.get('school_id')
    if not school_id:
        messages.warning(request, "Please log in first.")
        return redirect('index')

    student = get_object_or_404(User, school_id=school_id)
    problem = get_object_or_404(Problem, pk=problem_id)

    return render(request, 'Students/StudentPlayGround.html', {
        'user': student,
        'problem': problem
    })


# ---------------- RUN & CHECK CODE ---------------- #
@csrf_exempt
def run_playground_code(request):
    """
    Handles Run Code and Check Code actions:
    - Run Code: executes student's code and returns output
    - Check Code: runs all test cases, computes score, and saves Submission
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    data = json.loads(request.body)
    code = data.get("code", "")
    language = data.get("language", "python")
    check_mode = data.get("check_mode", False)
    problem_id = data.get("problem_id")
    student_id = request.session.get("school_id")

    if not student_id:
        return JsonResponse({"error": "You must be logged in."}, status=403)

    student = get_object_or_404(User, school_id=student_id)

    # ---------- RUN CODE ONLY ----------
    if not check_mode:
        try:
            response = requests.post(PISTON_URL, json={
                "language": language,
                "version": "*",
                "files": [{"content": code}]
            })
            result = response.json()
            output = result.get("run", {}).get("output", "No output.")
            return JsonResponse({"output": output})
        except Exception as e:
            return JsonResponse({"error": f"Execution error: {e}"}, status=500)

    # ---------- CHECK CODE (with test cases) ----------
    problem = get_object_or_404(Problem, pk=problem_id)
    test_cases = ProblemTestCase.objects.filter(problem_id=problem)

    if not test_cases.exists():
        return JsonResponse({"error": "No test cases found."}, status=404)

    passed = 0
    total = test_cases.count()
    results = []

    for idx, tc in enumerate(test_cases, start=1):
        try:
            response = requests.post(PISTON_URL, json={
                "language": language,
                "version": "*",
                "files": [{"content": code}],
                "stdin": tc.input_data
            })
            result = response.json()
            output = result.get("run", {}).get("output", "").strip()
        except Exception as e:
            output = f"Error: {e}"

        expected = tc.expected_output.strip()

        if output == expected:
            passed += 1
            results.append(f"✅ Test {idx}: Passed")
        else:
            results.append(
                f"❌ Test {idx}: Failed\nExpected: {expected}\nGot: {output}"
            )

    # ---------- Compute & Save Score ----------
    total_score = problem.total_score
    score_per_case = total_score / total if total > 0 else 0
    final_score = int(round(passed * score_per_case))

    # Update or Create submission
    Submission.objects.update_or_create(
        problem_id=problem,
        student_id=student,
        defaults={
            "code": code,
            "score": final_score,
            "submitted_at": timezone.now()
        }
    )

    summary = f"{passed}/{total} test cases passed.\nScore: {final_score}/{total_score}"
    return JsonResponse({
        "result_summary": "\n".join(results) + "\n\n" + summary,
        "score": final_score,
        "passed": passed,
        "total": total
    })

@csrf_exempt
def submit_problem(request):
    """
    Handles problem submission by student.
    Checks test cases, calculates score, and saves Submission.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    data = json.loads(request.body)
    code = data.get("code", "")
    language = data.get("language", "python")
    problem_id = data.get("problem_id")
    student_id = request.session.get("school_id")

    if not student_id:
        return JsonResponse({"error": "You must be logged in."}, status=403)

    student = get_object_or_404(User, school_id=student_id)
    problem = get_object_or_404(Problem, pk=problem_id)
    test_cases = ProblemTestCase.objects.filter(problem_id=problem)

    if not test_cases.exists():
        return JsonResponse({"error": "No test cases found."}, status=404)

    passed = 0
    total = test_cases.count()
    results = []

    for idx, tc in enumerate(test_cases, start=1):
        try:
            response = requests.post(PISTON_URL, json={
                "language": language,
                "version": "*",
                "files": [{"content": code}],
                "stdin": tc.input_data
            })
            result = response.json()
            output = result.get("run", {}).get("output", "").strip()
        except Exception as e:
            output = f"Error: {e}"

        expected = tc.expected_output.strip()

        if output == expected:
            passed += 1
            results.append(f"✅ Test {idx}: Passed")
        else:
            results.append(
                f"❌ Test {idx}: Failed\nExpected: {expected}\nGot: {output}"
            )

    # Compute final score
    total_score = problem.total_score
    score_per_case = total_score / total if total > 0 else 0
    final_score = int(round(passed * score_per_case))

    # Save submission
    Submission.objects.update_or_create(
        problem_id=problem,
        student_id=student,
        defaults={
            "code": code,
            "score": final_score,
            "submitted_at": timezone.now()
        }
    )

    summary = f"{passed}/{total} test cases passed.\nScore: {final_score}/{total_score}"
    return JsonResponse({
        "result_summary": "\n".join(results) + "\n\n" + summary,
        "score": final_score,
        "passed": passed,
        "total": total
    })
