import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser, TeacherProfile, StudentProfile
from subjects.models import Subject, Enrollment
from quizzes.models import Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Seeds the database with teachers, subjects, students, and sample quizzes.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Admin
        if not CustomUser.objects.filter(school_id='ADMIN').exists():
            admin = CustomUser.objects.create_superuser(
                school_id='ADMIN',
                username='ADMIN',
                password='adminpassword',
                first_name='System',
                last_name='Admin',
                role=CustomUser.ROLE_ADMIN
            )
            self.stdout.write(self.style.SUCCESS('Created Admin: ADMIN / adminpassword'))

        # 2. Create Teachers
        teachers_data = [
            {'id': 'ENG001', 'first': 'Maria', 'last': 'Santos', 'subject': TeacherProfile.SUBJECT_ENGLISH},
            {'id': 'MTH001', 'first': 'Juan', 'last': 'Reyes', 'subject': TeacherProfile.SUBJECT_MATH},
            {'id': 'SCI001', 'first': 'Ana', 'last': 'Cruz', 'subject': TeacherProfile.SUBJECT_SCIENCE},
            {'id': 'FIL001', 'first': 'Jose', 'last': 'Bautista', 'subject': TeacherProfile.SUBJECT_FILIPINO},
        ]

        teachers = {}
        for t in teachers_data:
            user, created = CustomUser.objects.get_or_create(
                school_id=t['id'],
                defaults={
                    'username': t['id'],
                    'first_name': t['first'],
                    'last_name': t['last'],
                    'role': CustomUser.ROLE_TEACHER,
                }
            )
            if created:
                user.set_password('teacher123')
                user.save()
                TeacherProfile.objects.create(
                    user=user,
                    employee_id=t['id'],
                    subject_specialization=t['subject']
                )
            teachers[t['subject']] = user
        self.stdout.write(self.style.SUCCESS('Created 4 Teachers'))

        # 3. Create Subjects (4 subjects x 4 grades = 16)
        subject_descriptions = {
            'english': {
                7: ('English - Grade 7', 'Philippine Literature and National Identity — Foundational multiliteracies; exploring Philippine prose, poetry, and informational texts; creating content that reflects local/national identity.'),
                8: ('English - Grade 8', 'Afro-Asian Literature and Cultural Diversity — Global perspective building; analyzing Afro-Asian literature; information processing, source citation, and recognizing biases.'),
                9: ('English - Grade 9', 'Anglo-American Literature and Social Issues — Critical literacy; examining Anglo-American literature to critique societal values; argumentation, logic, and reasoning with complex social topics.'),
                10: ('English - Grade 10', 'World Literature and Global Citizenship — Advanced functional literacy; evaluating world literary masterpieces; research, civic expression, academic writing, and persuasive essays.'),
            },
            'math': {
                7: ('Math - Grade 7', 'Numbers and Algebra Foundations — Integers, fractions, rational numbers, algebraic expressions, linear equations, and proportional reasoning using the MATATAG curriculum.'),
                8: ('Math - Grade 8', 'Geometry and Measurement — Triangle congruence, similarity, surface area and volume, the Pythagorean theorem, and coordinate geometry.'),
                9: ('Math - Grade 9', 'Patterns, Functions, and Relations — Quadratic functions and equations, variations, radical expressions, and applying algebra to real-world contexts.'),
                10: ('Math - Grade 10', 'Advanced Algebra and Probability — Polynomial functions, circles, combinatorics, probability, and statistics as tools for evidence-based decision-making.'),
            },
            'science': {
                7: ('Science - Grade 7', 'Matter and Living Systems — Properties and classification of matter, the cell as the basic unit of life, ecosystems, and biodiversity within the Philippine context.'),
                8: ('Science - Grade 8', 'Force, Motion, and Energy — Newton\'s laws of motion, waves, sound, light, electricity, and basic chemical reactions with emphasis on real-world application.'),
                9: ('Science - Grade 9', 'Earth and Space Sciences — Plate tectonics, volcanic and earthquake activity, weather and climate patterns, solar system exploration, and environmental stewardship.'),
                10: ('Science - Grade 10', 'Chemistry and Biology Integration — Organic chemistry fundamentals, genetics and heredity, evolution, and the interconnectedness of biological and chemical systems.'),
            },
            'filipino': {
                7: ('Filipino - Grade 7', 'Wika at Kulturang Pilipino — Pag-unawa sa mga tekstong naratibo at deskriptibo, gramatika, at paglinang ng kasanayang pangwika sa konteksto ng kulturang Pilipino.'),
                8: ('Filipino - Grade 8', 'Panitikang Asyano — Pagsusuri ng mga akdang Asyano, pagkilala sa pagkakaiba ng kultura, at pag-unlad ng kritikal na pag-iisip sa pamamagitan ng panitikan.'),
                9: ('Filipino - Grade 9', 'Panitikang Pandaigdig — Pag-aaral ng mga akdang pampanitikang pandaigdig, argumentasyon, persuasyon, at pagpapahayag ng sariling pananaw.'),
                10: ('Filipino - Grade 10', 'Filipino para sa Akademikong Layunin — Pagsulat ng akademikong papel, pagbuo ng talumpati, malalim na pagsusuri ng mga teksto, at paghahanda para sa mas mataas na antas ng pag-aaral.'),
            }
        }

        created_subjects = []
        for code, grades in subject_descriptions.items():
            for level, (name, desc) in grades.items():
                subject, _ = Subject.objects.get_or_create(
                    subject_code=code,
                    grade_level=level,
                    defaults={
                        'name': name,
                        'description': desc,
                        'teacher': teachers[code]
                    }
                )
                created_subjects.append(subject)
        self.stdout.write(self.style.SUCCESS('Created 16 Subjects'))

        # 4. Create Students (5 per grade level)
        student_id_counter = 1
        for grade in [7, 8, 9, 10]:
            for i in range(5):
                school_id = f'2024-{str(student_id_counter).zfill(4)}'
                user, created = CustomUser.objects.get_or_create(
                    school_id=school_id,
                    defaults={
                        'username': school_id,
                        'first_name': f'Student{student_id_counter}',
                        'last_name': f'Grade{grade}',
                        'role': CustomUser.ROLE_STUDENT,
                    }
                )
                if created:
                    user.set_password('student123')
                    user.save()
                    StudentProfile.objects.create(
                        user=user,
                        grade_level=grade,
                        section=f'{grade}-A'
                    )
                    # Auto enroll
                    grade_subjects = [s for s in created_subjects if s.grade_level == grade]
                    for sub in grade_subjects:
                        Enrollment.objects.get_or_create(student=user, subject=sub)
                
                student_id_counter += 1
        self.stdout.write(self.style.SUCCESS('Created 20 Students and Enrolled them'))

        # 5. Create a sample Quiz for English Grade 7
        english_7 = Subject.objects.get(subject_code='english', grade_level=7)
        if not Quiz.objects.filter(title='Philippine Literature Basics').exists():
            quiz = Quiz.objects.create(
                title='Philippine Literature Basics',
                description='A short assessment on the foundations of Philippine Literature.',
                subject=english_7,
                created_by=teachers['english'],
                quiz_type=Quiz.QUIZ_TYPE_REGULAR,
                time_limit=15,
                is_active=True
            )
            
            # Q1
            q1 = Question.objects.create(quiz=quiz, text='What is the first book printed in the Philippines?', order=1)
            Choice.objects.create(question=q1, text='Doctrina Christiana', is_correct=True, order=1)
            Choice.objects.create(question=q1, text='Noli Me Tangere', is_correct=False, order=2)
            Choice.objects.create(question=q1, text='Florante at Laura', is_correct=False, order=3)
            Choice.objects.create(question=q1, text='Urbana at Felisa', is_correct=False, order=4)
            
            # Q2
            q2 = Question.objects.create(quiz=quiz, text='Who is considered the national hero of the Philippines who wrote Noli Me Tangere?', order=2)
            Choice.objects.create(question=q2, text='Andres Bonifacio', is_correct=False, order=1)
            Choice.objects.create(question=q2, text='Apolinario Mabini', is_correct=False, order=2)
            Choice.objects.create(question=q2, text='Jose Rizal', is_correct=True, order=3)
            Choice.objects.create(question=q2, text='Emilio Aguinaldo', is_correct=False, order=4)

        self.stdout.write(self.style.SUCCESS('Created sample Quiz for English Grade 7'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
