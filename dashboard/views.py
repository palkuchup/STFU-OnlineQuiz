from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg
from accounts.models import CustomUser, RegistrationRequest, StudentProfile, TeacherProfile
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


def register_view(request):
    """Web-based student registration — creates a RegistrationRequest pending admin approval."""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    GRADE_CHOICES = [(7, 'Grade 7'), (8, 'Grade 8'), (9, 'Grade 9'), (10, 'Grade 10')]

    if request.method == 'POST':
        school_id   = request.POST.get('school_id', '').strip()
        password    = request.POST.get('password', '')
        confirm     = request.POST.get('confirm_password', '')

        errors = []
        if not all([school_id, password]):
            errors.append('All required fields must be filled in.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
            
        user = CustomUser.objects.filter(school_id=school_id).first()
        if not user:
            errors.append(f'School ID "{school_id}" is not recognized. Please contact your administrator.')
        elif user.has_usable_password():
            errors.append(f'An account with School ID "{school_id}" is already fully registered.')
            
        existing_request = RegistrationRequest.objects.filter(school_id=school_id).first()
        if existing_request:
            if existing_request.status == RegistrationRequest.STATUS_PENDING:
                errors.append(f'A pending registration request for School ID "{school_id}" already exists.')
            elif existing_request.status == RegistrationRequest.STATUS_APPROVED:
                errors.append(f'A registration request for School ID "{school_id}" has already been approved.')
            elif existing_request.status == RegistrationRequest.STATUS_REJECTED:
                # Delete the rejected request to allow re-registration
                existing_request.delete()

        if not request.FILES.get('id_photo_front') or not request.FILES.get('id_photo_back') or not request.FILES.get('selfie_photo'):
            errors.append('All verification photos (Front ID, Back ID, and Selfie) are required.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'dashboard/login.html', {'active_tab': 'register'})
        else:
            # Get grade level and section from pre-registered user if available
            grade_level = None
            section = ''
            if hasattr(user, 'student_profile'):
                grade_level = user.student_profile.grade_level
                section = user.student_profile.section
            
            reg = RegistrationRequest(
                school_id=school_id,
                temp_password=password,
                grade_level=grade_level,
                section=section
            )
            # Optional photo uploads
            if request.FILES.get('id_photo_front'):
                reg.id_photo_front = request.FILES['id_photo_front']
            if request.FILES.get('id_photo_back'):
                reg.id_photo_back = request.FILES['id_photo_back']
            if request.FILES.get('selfie_photo'):
                reg.selfie_photo = request.FILES['selfie_photo']
            reg.save()

            messages.success(
                request,
                'Registration submitted! An administrator will review your request. '
                'You will receive your login credentials once approved.'
            )
            return redirect('login')

    return render(request, 'dashboard/login.html')


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

    if request.method == 'POST':
        school_id = request.POST.get('school_id', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role')
        grade_level = request.POST.get('grade_level')
        subject_specialization = request.POST.get('subject_specialization')

        if CustomUser.objects.filter(school_id=school_id).exists():
            messages.error(request, f'School ID {school_id} already exists.')
        else:
            try:
                user = CustomUser(
                    school_id=school_id,
                    username=school_id,
                    first_name=first_name,
                    last_name=last_name,
                    role=int(role),
                    is_active=True
                )
                user.set_unusable_password()
                user.save()

                if user.role == CustomUser.ROLE_STUDENT:
                    StudentProfile.objects.create(
                        user=user,
                        grade_level=int(grade_level) if grade_level else None,
                        is_self_registered=False
                    )
                elif user.role == CustomUser.ROLE_TEACHER:
                    subject_code = 'english' # default
                    subject_ids = request.POST.getlist('subject_specialization')
                    if subject_ids:
                        vacant_subjects = Subject.objects.filter(subject_id__in=subject_ids)
                        if vacant_subjects.exists():
                            subject_code = vacant_subjects.first().subject_code
                            vacant_subjects.update(teacher=user)
                    
                    TeacherProfile.objects.create(
                        user=user,
                        employee_id=school_id,  # Fallback employee_id
                        subject_specialization=subject_code
                    )

                messages.success(request, f'User {first_name} {last_name} ({school_id}) added successfully.')
            except Exception as e:
                messages.error(request, f'Error adding user: {str(e)}')
        return redirect('admin-users')

    role_filter = request.GET.get('role')
    users = CustomUser.objects.all().order_by('-created_at')
    if role_filter is not None:
        users = users.filter(role=role_filter)
        
    vacant_subjects = Subject.objects.filter(teacher__isnull=True).order_by('grade_level', 'subject_code')

    context = {
        'users': users,
        'role_filter': role_filter,
        'vacant_subjects': vacant_subjects,
    }
    return render(request, 'dashboard/admin/users.html', context)


@login_required
def admin_edit_user(request, user_id):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')
        
    user = get_object_or_404(CustomUser, user_id=user_id)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role')
        
        user.first_name = first_name
        user.last_name = last_name
        
        try:
            new_role = int(role)
            # If role changed, handle profiles
            if user.role != new_role:
                # delete old profile if it existed
                if user.role == CustomUser.ROLE_STUDENT and hasattr(user, 'student_profile'):
                    user.student_profile.delete()
                elif user.role == CustomUser.ROLE_TEACHER and hasattr(user, 'teacher_profile'):
                    user.teacher_profile.delete()
                    
                user.role = new_role
                user.save()
                
                # create new profile
                if new_role == CustomUser.ROLE_STUDENT:
                    StudentProfile.objects.create(
                        user=user, 
                        grade_level=request.POST.get('grade_level') or None,
                        is_self_registered=False
                    )
                elif new_role == CustomUser.ROLE_TEACHER:
                    subject_code = 'english'
                    subject_ids = request.POST.getlist('subject_specialization')
                    if subject_ids:
                        selected_subjects = Subject.objects.filter(subject_id__in=subject_ids)
                        if selected_subjects.exists():
                            subject_code = selected_subjects.first().subject_code
                            selected_subjects.update(teacher=user)
                            
                    TeacherProfile.objects.create(
                        user=user, 
                        employee_id=user.school_id,
                        subject_specialization=subject_code
                    )
            else:
                user.save()
                # Update existing profile
                if new_role == CustomUser.ROLE_STUDENT and hasattr(user, 'student_profile'):
                    profile = user.student_profile
                    profile.grade_level = request.POST.get('grade_level') or None
                    profile.save()
                elif new_role == CustomUser.ROLE_TEACHER and hasattr(user, 'teacher_profile'):
                    profile = user.teacher_profile
                    subject_ids = request.POST.getlist('subject_specialization')
                    
                    # Clear old subjects
                    Subject.objects.filter(teacher=user).update(teacher=None)
                    
                    if subject_ids:
                        selected_subjects = Subject.objects.filter(subject_id__in=subject_ids)
                        if selected_subjects.exists():
                            profile.subject_specialization = selected_subjects.first().subject_code
                            selected_subjects.update(teacher=user)
                            
                    profile.save()
            messages.success(request, f'User {user.school_id} updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            
    return redirect('admin-users')


@login_required
def admin_delete_user(request, user_id):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')
        
    user = get_object_or_404(CustomUser, user_id=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
        else:
            try:
                user.delete()
                messages.success(request, f'User {user.school_id} deleted successfully.')
            except Exception as e:
                messages.error(request, f'Error deleting user: {str(e)}')
                
    return redirect('admin-users')



@login_required
def admin_registration_requests(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    status_filter = request.GET.get('status', 'pending')
    requests_qs = RegistrationRequest.objects.all().order_by('-submitted_at')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    # Attach pre-registered user details to each request
    enriched_requests = []
    for req in requests_qs:
        user = CustomUser.objects.filter(school_id=req.school_id).first()
        req.user_info = user
        enriched_requests.append(req)

    context = {
        'requests': enriched_requests,
        'status_filter': status_filter,
        'pending_count': RegistrationRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'dashboard/admin/registration_requests.html', context)


@login_required
def admin_review_request(request, request_id):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    reg = get_object_or_404(RegistrationRequest, request_id=request_id)
    user = CustomUser.objects.filter(school_id=reg.school_id).first()
    reg.user_info = user

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            if not user:
                messages.error(request, f"School ID {reg.school_id} not found in pre-registered list.")
            elif user.has_usable_password():
                messages.error(request, f"School ID {reg.school_id} is already fully registered.")
            else:
                user.set_password(reg.temp_password)
                user.is_active = True
                user.save()

                if user.role == CustomUser.ROLE_STUDENT:
                    # Check if student profile already exists
                    if hasattr(user, 'student_profile'):
                        profile = user.student_profile
                        # Update profile with registration request data
                        if reg.grade_level:
                            profile.grade_level = reg.grade_level
                        if reg.section:
                            profile.section = reg.section
                        if reg.id_photo_front:
                            profile.id_photo_front = reg.id_photo_front
                        if reg.id_photo_back:
                            profile.id_photo_back = reg.id_photo_back
                        if reg.selfie_photo:
                            profile.selfie_photo = reg.selfie_photo
                        profile.is_self_registered = True
                        profile.save()
                    else:
                        # Get grade level from pre-registered user's profile if available, or use default
                        grade_level = reg.grade_level
                        if not grade_level and hasattr(user, 'student_profile'):
                            grade_level = user.student_profile.grade_level
                        elif not grade_level:
                            grade_level = 7  # Default grade if not provided
                        
                        StudentProfile.objects.create(
                            user=user,
                            grade_level=grade_level,
                            id_photo_front=reg.id_photo_front,
                            id_photo_back=reg.id_photo_back,
                            selfie_photo=reg.selfie_photo,
                            section=reg.section if reg.section else '',
                            is_self_registered=True,
                        )
                    # Enroll student in subjects
                    grade_to_use = reg.grade_level
                    if not grade_to_use and hasattr(user, 'student_profile'):
                        grade_to_use = user.student_profile.grade_level
                    if grade_to_use:
                        subjects = Subject.objects.filter(grade_level=grade_to_use)
                        for subject in subjects:
                            Enrollment.objects.get_or_create(student=user, subject=subject)

                reg.status = RegistrationRequest.STATUS_APPROVED
                reg.reviewed_at = timezone.now()
                reg.reviewed_by = request.user
                reg.save()
                messages.success(request, f"Request for {reg.school_id} approved successfully.")
                return redirect('admin-reg-requests')
                
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            additional_message = request.POST.get('additional_message', '')
            
            full_reason = rejection_reason
            if additional_message:
                full_reason += f" - {additional_message}"
                
            reg.status = RegistrationRequest.STATUS_REJECTED
            reg.rejection_reason = full_reason
            reg.reviewed_at = timezone.now()
            reg.reviewed_by = request.user
            reg.save()
            messages.success(request, f"Request for {reg.school_id} rejected.")
            return redirect('admin-reg-requests')

    context = {
        'req': reg,
        'pending_count': RegistrationRequest.objects.filter(status='pending').count(),
    }
    return render(request, 'dashboard/admin/review_request.html', context)


@login_required
def admin_subjects(request):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    subjects = Subject.objects.select_related('teacher').order_by('grade_level', 'subject_code')
    context = {
        'subjects': subjects,
        'grade_list': [7, 8, 9, 10],
    }
    return render(request, 'dashboard/admin/subjects.html', context)


@login_required
def admin_subject_detail(request, subject_id):
    if not (request.user.role == CustomUser.ROLE_ADMIN or request.user.is_superuser):
        return redirect('login')

    subject = get_object_or_404(Subject, subject_id=subject_id)
    enrollments = Enrollment.objects.filter(subject=subject).select_related('student')
    quizzes = Quiz.objects.filter(subject=subject).order_by('-created_at')

    context = {
        'subject': subject,
        'enrollments': enrollments,
        'quizzes': quizzes,
    }
    return render(request, 'dashboard/admin/subject_detail.html', context)


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

    my_subjects = Subject.objects.filter(teacher=request.user).order_by('grade_level', 'subject_code')

    context = {
        'subject_data': my_subjects,
        'my_subjects': my_subjects,
    }
    return render(request, 'dashboard/teacher/quizzes.html', context)


@login_required
def teacher_subject_quizzes(request, subject_id):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    subject = get_object_or_404(Subject, pk=subject_id, teacher=request.user)
    quizzes = Quiz.objects.filter(subject=subject, created_by=request.user).select_related('subject').order_by('-created_at')

    context = {
        'subject': subject,
        'quizzes': quizzes,
    }
    return render(request, 'dashboard/teacher/subject_quizzes.html', context)


@login_required
def teacher_quiz_results(request, quiz_id):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    quiz = Quiz.objects.get(quiz_id=quiz_id, created_by=request.user)
    
    # Get all students enrolled in this subject
    enrollments = Enrollment.objects.filter(
        subject=quiz.subject,
        is_active=True
    ).select_related('student')
    
    # Get all attempts for this quiz
    attempts = QuizAttempt.objects.filter(
        quiz=quiz, is_completed=True
    ).select_related('student')
    
    # Create a map of student_id -> attempt
    attempt_map = {attempt.student_id: attempt for attempt in attempts}
    
    # Prepare student list
    student_data = []
    for enrollment in enrollments:
        student = enrollment.student
        attempt = attempt_map.get(student.user_id)
        student_info = {
            'student': student,
            'attempt': attempt,
            'is_completed': attempt is not None
        }
        student_data.append(student_info)

    context = {
        'quiz': quiz,
        'student_data': student_data,
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

    # Automatically calculate final grade based on quiz attempts ONLY if a Final Exam has been completed
    for enrollment in enrollments:
        attempts = QuizAttempt.objects.filter(
            student=enrollment.student,
            quiz__subject=enrollment.subject,
            is_completed=True
        )
        
        # Check if they have completed a final exam
        has_final_exam = attempts.filter(quiz__quiz_type='final_exam').exists()
        
        if has_final_exam:
            avg_score = attempts.aggregate(avg=Avg('percentage'))['avg']
            enrollment.final_grade = avg_score
            enrollment.is_promoted = (avg_score >= enrollment.subject.passing_score)
            enrollment.save(update_fields=['final_grade', 'is_promoted'])
        else:
            # If no final exam, clear it (in case it was set previously by the old logic)
            if enrollment.final_grade is not None:
                enrollment.final_grade = None
                enrollment.is_promoted = False
                enrollment.save(update_fields=['final_grade', 'is_promoted'])

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
    ).exclude(
        attempts__student=student,
        attempts__is_completed=True
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

    enrolled_subjects = Subject.objects.filter(
        enrollments__student=request.user,
        enrollments__is_active=True
    ).order_by('grade_level', 'subject_code').distinct()

    context = {'subject_data': enrolled_subjects}
    return render(request, 'dashboard/student/quizzes.html', context)


@login_required
def student_subject_quizzes(request, subject_id):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    subject = get_object_or_404(Subject, pk=subject_id)
    # Check if student is enrolled
    if not Enrollment.objects.filter(student=request.user, subject=subject).exists():
        messages.error(request, 'You are not enrolled in this subject.')
        return redirect('student-quizzes')

    quizzes = Quiz.objects.filter(subject=subject, is_active=True).select_related('subject', 'created_by').order_by('-created_at')
    completed_attempts = QuizAttempt.objects.filter(
        student=request.user,
        quiz__in=quizzes,
        is_completed=True
    ).select_related('quiz')
    # Create map of quiz id to attempt
    attempt_map = {attempt.quiz_id: attempt for attempt in completed_attempts}

    # Prepare quiz data
    quiz_data = []
    for quiz in quizzes:
        quiz_info = {
            'quiz': quiz,
            'is_completed': quiz.quiz_id in attempt_map,
            'attempt': attempt_map.get(quiz.quiz_id)
        }
        quiz_data.append(quiz_info)

    context = {
        'subject': subject,
        'quiz_data': quiz_data
    }
    return render(request, 'dashboard/student/subject_quizzes.html', context)


@login_required
def student_history(request):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    attempts = QuizAttempt.objects.filter(
        student=request.user, is_completed=True
    ).select_related('quiz__subject').order_by('-completed_at')

    context = {'attempts': attempts}
    return render(request, 'dashboard/student/history.html', context)


# ── Teacher: Create Quiz ──────────────────────────────────────────────────────

@login_required
def teacher_create_quiz(request):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    my_subjects = Subject.objects.filter(teacher=request.user).order_by('grade_level', 'subject_code')

    if request.method == 'POST':
        from quizzes.models import Question, Choice
        import json

        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        subject_id   = request.POST.get('subject')
        quiz_type    = request.POST.get('quiz_type', 'regular')
        time_limit   = int(request.POST.get('time_limit', 0) or 0)
        is_active    = request.POST.get('is_active') == 'on'
        allow_multi  = request.POST.get('allow_multiple_attempts') == 'on'
        show_answers = request.POST.get('show_answers_after_submit') == 'on'

        if not title or not subject_id:
            messages.error(request, 'Title and Subject are required.')
        else:
            try:
                subject = Subject.objects.get(pk=subject_id, teacher=request.user)
                quiz = Quiz.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    created_by=request.user,
                    quiz_type=quiz_type,
                    time_limit=time_limit,
                    is_active=is_active,
                    allow_multiple_attempts=allow_multi,
                    show_answers_after_submit=show_answers,
                )

                # Parse question data sent as indexed POST fields
                q_idx = 0
                while True:
                    q_text = request.POST.get(f'questions[{q_idx}][text]', '').strip()
                    if not q_text:
                        break
                    question = Question.objects.create(
                        quiz=quiz,
                        text=q_text,
                        order=q_idx + 1,
                    )
                    correct_choice = request.POST.get(f'questions[{q_idx}][correct]', '0')
                    for c_idx in range(4):
                        c_text = request.POST.get(f'questions[{q_idx}][choices][{c_idx}]', '').strip()
                        if c_text:
                            Choice.objects.create(
                                question=question,
                                text=c_text,
                                is_correct=(str(c_idx) == correct_choice),
                                order=c_idx + 1,
                            )
                    q_idx += 1

                messages.success(request, f'Quiz "{quiz.title}" created with {q_idx} questions!')
                return redirect('teacher-quizzes')
            except Subject.DoesNotExist:
                messages.error(request, 'Invalid subject selected.')

    context = {'my_subjects': my_subjects}
    return render(request, 'dashboard/teacher/create_quiz.html', context)


@login_required
def teacher_edit_quiz(request, quiz_id):
    if request.user.role != CustomUser.ROLE_TEACHER:
        return redirect('login')

    from quizzes.models import Question, Choice
    quiz = get_object_or_404(Quiz, quiz_id=quiz_id, created_by=request.user)
    my_subjects = Subject.objects.filter(teacher=request.user).order_by('grade_level', 'subject_code')

    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        subject_id   = request.POST.get('subject')
        quiz_type    = request.POST.get('quiz_type', 'regular')
        time_limit   = int(request.POST.get('time_limit', 0) or 0)
        is_active    = request.POST.get('is_active') == 'on'
        allow_multi  = request.POST.get('allow_multiple_attempts') == 'on'
        show_answers = request.POST.get('show_answers_after_submit') == 'on'

        if not title or not subject_id:
            messages.error(request, 'Title and Subject are required.')
        else:
            try:
                subject = Subject.objects.get(pk=subject_id, teacher=request.user)
                # Update quiz fields
                quiz.title = title
                quiz.description = description
                quiz.subject = subject
                quiz.quiz_type = quiz_type
                quiz.time_limit = time_limit
                quiz.is_active = is_active
                quiz.allow_multiple_attempts = allow_multi
                quiz.show_answers_after_submit = show_answers
                quiz.save()

                # Delete existing questions/choices
                quiz.questions.all().delete()

                # Parse new question data
                q_idx = 0
                while True:
                    q_text = request.POST.get(f'questions[{q_idx}][text]', '').strip()
                    if not q_text:
                        break
                    question = Question.objects.create(
                        quiz=quiz,
                        text=q_text,
                        order=q_idx + 1,
                    )
                    correct_choice = request.POST.get(f'questions[{q_idx}][correct]', '0')
                    for c_idx in range(4):
                        c_text = request.POST.get(f'questions[{q_idx}][choices][{c_idx}]', '').strip()
                        if c_text:
                            Choice.objects.create(
                                question=question,
                                text=c_text,
                                is_correct=(str(c_idx) == correct_choice),
                                order=c_idx + 1,
                            )
                    q_idx += 1

                messages.success(request, f'Quiz "{quiz.title}" updated successfully!')
                return redirect('teacher-quizzes')
            except Subject.DoesNotExist:
                messages.error(request, 'Invalid subject selected.')

    # Pass existing questions to template
    questions = quiz.questions.prefetch_related('choices').all()
    context = {
        'my_subjects': my_subjects,
        'quiz': quiz,
        'questions': questions,
        'is_edit': True
    }
    return render(request, 'dashboard/teacher/create_quiz.html', context)


# ── Student: Take Quiz ────────────────────────────────────────────────────────

@login_required
def student_take_quiz(request, quiz_id):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    from quizzes.models import Question, Choice

    quiz = Quiz.objects.prefetch_related(
        'questions__choices'
    ).get(quiz_id=quiz_id, is_active=True)

    # Check the student is enrolled in this subject
    if not Enrollment.objects.filter(student=request.user, subject=quiz.subject).exists():
        messages.error(request, 'You are not enrolled in this subject.')
        return redirect('student-quizzes')

    # Prevent re-attempting regular quizzes unless multiple attempts allowed
    if not quiz.allow_multiple_attempts:
        existing = QuizAttempt.objects.filter(
            student=request.user, quiz=quiz, is_completed=True
        ).first()
        if existing:
            messages.info(request, 'You have already completed this quiz.')
            return redirect('student-quiz-result', attempt_id=existing.attempt_id)

    context = {
        'quiz': quiz,
        'questions': quiz.questions.prefetch_related('choices').all(),
    }
    return render(request, 'dashboard/student/take_quiz.html', context)


@login_required
def student_submit_quiz(request, quiz_id):
    """POST only — receive answers, score, save, redirect to result."""
    if request.user.role != CustomUser.ROLE_STUDENT or request.method != 'POST':
        return redirect('student-quizzes')

    from quizzes.models import Question, Choice
    from django.utils import timezone

    quiz = Quiz.objects.get(quiz_id=quiz_id, is_active=True)

    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
    )

    for question in quiz.questions.all():
        choice_id = request.POST.get(f'q_{question.question_id}')
        selected = None
        if choice_id:
            try:
                selected = Choice.objects.get(choice_id=choice_id, question=question)
            except Choice.DoesNotExist:
                pass
        from results.models import StudentAnswer
        StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_choice=selected,
        )

    attempt.compute_score()
    attempt.is_completed = True
    attempt.completed_at = timezone.now()
    attempt.save()

    return redirect('student-quiz-result', attempt_id=attempt.attempt_id)


@login_required
def student_quiz_result(request, attempt_id):
    if request.user.role != CustomUser.ROLE_STUDENT:
        return redirect('login')

    attempt = QuizAttempt.objects.prefetch_related(
        'answers__question__choices',
        'answers__selected_choice',
    ).get(attempt_id=attempt_id, student=request.user)

    context = {'attempt': attempt}
    return render(request, 'dashboard/student/quiz_result.html', context)

