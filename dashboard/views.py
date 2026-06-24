from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from accounts.models import CustomUser, RegistrationRequest
from subjects.models import Subject, Enrollment
from quizzes.models import Quiz
from results.models import QuizAttempt


# ── Authentication ────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        school_id = request.POST.get('school_id', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, school_id=school_id, password=password)
        if user:
            login(request, user)
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid School ID or password.')

    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def redirect_by_role(user):
    if user.role == CustomUser.ROLE_ADMIN or user.is_superuser:
        return redirect('admin-dashboard')
    elif user.role == CustomUser.ROLE_TEACHER:
        return redirect('teacher-dashboard')
    else:
        return redirect('student-dashboard')


# ── Admin Dashboard ───────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    total_students = CustomUser.objects.filter(role=CustomUser.ROLE_STUDENT).count()
    students_by_grade = []
    for g in [7, 8, 9, 10]:
        count = CustomUser.objects.filter(role=CustomUser.ROLE_STUDENT, student_profile__grade_level=g).count()
        percentage = (count / total_students * 100) if total_students > 0 else 0
        students_by_grade.append({'grade': g, 'count': count, 'percentage': percentage})

    context = {
        'total_teachers': CustomUser.objects.filter(role=CustomUser.ROLE_TEACHER).count(),
        'total_students': total_students,
        'total_subjects': Subject.objects.count(),
        'total_quizzes': Quiz.objects.count(),
        'pending_requests': RegistrationRequest.objects.filter(status='pending').count(),
        'recent_requests': RegistrationRequest.objects.filter(status='pending').order_by('-submitted_at')[:5],
        'recent_attempts': QuizAttempt.objects.filter(is_completed=True).order_by('-completed_at')[:10],
        'teachers': CustomUser.objects.filter(role=CustomUser.ROLE_TEACHER).select_related('teacher_profile'),
        'students_by_grade': students_by_grade,
    }
    return render(request, 'dashboard/admin/dashboard.html', context)


@login_required
def admin_users(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    role_filter = request.GET.get('role')
    users = CustomUser.objects.all().order_by('-created_at')
    if role_filter is not None:
        users = users.filter(role=role_filter)

    context = {
        'users': users,
        'role_filter': role_filter,
    }
    return render(request, 'dashboard/admin/users.html', context)


@login_required
def admin_registration_requests(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    status_filter = request.GET.get('status', 'pending')
    requests_qs = RegistrationRequest.objects.all()
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    context = {
        'requests': requests_qs.order_by('-submitted_at'),
        'status_filter': status_filter,
        'pending_count': RegistrationRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'dashboard/admin/registration_requests.html', context)


@login_required
def admin_subjects(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    subjects = Subject.objects.select_related('teacher').order_by('grade_level', 'subject_code')
    context = {'subjects': subjects}
    return render(request, 'dashboard/admin/subjects.html', context)


# ── Teacher Dashboard ─────────────────────────────────────────────────────────

@login_required
def teacher_dashboard(request):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    teacher = request.user
    my_subjects = Subject.objects.filter(teacher=teacher)
    my_quizzes = Quiz.objects.filter(created_by=teacher).select_related('subject')
    recent_results = QuizAttempt.objects.filter(
        quiz__created_by=teacher,
        is_completed=True
    ).select_related('student', 'quiz').order_by('-completed_at')[:10]

    context = {
        'teacher': teacher,
        'my_subjects': my_subjects,
        'total_quizzes': my_quizzes.count(),
        'active_quizzes': my_quizzes.filter(is_active=True).count(),
        'recent_quizzes': my_quizzes[:5],
        'recent_results': recent_results,
        'total_students': Enrollment.objects.filter(
            subject__teacher=teacher
        ).values('student').distinct().count(),
    }
    return render(request, 'dashboard/teacher/dashboard.html', context)


@login_required
def teacher_quizzes(request):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    quizzes = Quiz.objects.filter(created_by=request.user).select_related('subject').order_by('-created_at')
    context = {'quizzes': quizzes}
    return render(request, 'dashboard/teacher/quizzes.html', context)


@login_required
def teacher_quiz_results(request, quiz_id):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    quiz = Quiz.objects.get(quiz_id=quiz_id, created_by=request.user)
    attempts = QuizAttempt.objects.filter(
        quiz=quiz, is_completed=True
    ).select_related('student').order_by('-completed_at')

    context = {
        'quiz': quiz,
        'attempts': attempts,
        'avg_score': attempts.aggregate(avg=Avg('percentage'))['avg'] or 0,
        'total_attempts': attempts.count(),
    }
    return render(request, 'dashboard/teacher/quiz_results.html', context)


@login_required
def teacher_students(request):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    enrollments = Enrollment.objects.filter(
        subject__teacher=request.user
    ).select_related('student', 'subject').order_by('subject__grade_level', 'student__last_name')

    context = {'enrollments': enrollments}
    return render(request, 'dashboard/teacher/students.html', context)


# ── Student Dashboard ─────────────────────────────────────────────────────────

@login_required
def student_dashboard(request):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    student = request.user
    profile = getattr(student, 'student_profile', None)
    enrollments = Enrollment.objects.filter(
        student=student, is_active=True
    ).select_related('subject__teacher')

    available_quizzes = Quiz.objects.filter(
        subject__enrollments__student=student,
        is_active=True
    ).select_related('subject').distinct()

    completed_attempts = QuizAttempt.objects.filter(
        student=student, is_completed=True
    ).select_related('quiz__subject').order_by('-completed_at')

    context = {
        'student': student,
        'profile': profile,
        'enrollments': enrollments,
        'available_quizzes': available_quizzes[:6],
        'recent_attempts': completed_attempts[:5],
        'total_quizzes_taken': completed_attempts.count(),
        'avg_score': completed_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0,
    }
    return render(request, 'dashboard/student/dashboard.html', context)


@login_required
def student_quizzes(request):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    enrolled_subject_ids = Enrollment.objects.filter(
        student=request.user, is_active=True
    ).values_list('subject_id', flat=True)

    quizzes = Quiz.objects.filter(
        subject_id__in=enrolled_subject_ids, is_active=True
    ).select_related('subject').order_by('subject__grade_level', 'subject__subject_code')

    context = {'quizzes': quizzes}
    return render(request, 'dashboard/student/quizzes.html', context)


@login_required
def student_history(request):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    attempts = QuizAttempt.objects.filter(
        student=request.user, is_completed=True
    ).select_related('quiz__subject').order_by('-completed_at')

    context = {'attempts': attempts}
    return render(request, 'dashboard/student/history.html', context)
