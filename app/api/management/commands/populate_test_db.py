import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import (
    EduquestUser,
    Course,
    CourseGroup,
    Image,
    AcademicYear,
    Term,
    Badge,
    Document,
    Quest,
    UserCourseGroupEnrollment,
    Question,
    Answer,
    UserQuestAttempt,
    UserAnswerAttempt,
)
from .template import *
from faker import Faker
import random

User = get_user_model()
fake = Faker()
load_dotenv()


class Command(BaseCommand):
    help = 'Populate the test database for unit testing'
    instructor = None
    admin = None
    student = None

    def handle(self, *args, **kwargs):
        self.clear_db()
        self.admin = self.get_admin()
        self.create_images()
        self.create_badges()
        self.create_academic_years_terms()
        self.create_courses()
        self.create_private_course_group()
        self.student = self.create_student()
        self.instructor = self.create_staff()
        self.create_course_groups()
        self.create_fake_data()

    def clear_db(self):
        eduquest_users = EduquestUser.objects.exclude(is_superuser=True)
        eduquest_users.delete()
        Image.objects.all().delete()
        AcademicYear.objects.all().delete()
        Badge.objects.all().delete()

        confirm = input("Do you want to delete all the uploaded documents in Azure Storage? (y/n): ")
        if confirm.lower() == 'y':
            self.delete_all_documents()
            # Document.objects.all().delete()
            print("Deleted all Document objects")
        else:
            print("Skipped deleting Document objects")

        print("Cleared all tables")

    def create_staff(self):
        try:
            instructor, created = EduquestUser.objects.get_or_create(
                email='CHINANN.ONG@STAFF.MAIN.NTU.EDU.SG',
                defaults={
                    'email': 'CHINANN.ONG@STAFF.MAIN.NTU.EDU.SG',
                    'username': 'Ong Chin Ann',
                    'nickname': 'Ong Chin Ann',
                    'first_name': 'Chin Ann',
                    'last_name': 'Ong',
                    'is_staff': True,
                }
            )
            return instructor
        except Exception as e:
            print(f"Failed to create staff: {str(e)}")

    def create_student(self):
        try:
            student, created = EduquestUser.objects.get_or_create(
                email='C210101@E.NTU.EDU.SG',
                defaults={
                    'email': 'C210101@E.NTU.EDU.SG',
                    'username': '#TEOH XI SHENG#',
                    'nickname': 'TEOH XI SHENG',
                    'first_name': 'XI SHENG',
                    'last_name': 'TEOH',
                    'is_staff': True,
                }
            )
            return student
        except Exception as e:
            print(f"Failed to create student: {str(e)}")

    def get_admin(self):
        try:
            admin = EduquestUser.objects.get(username='admin')
            return admin
        except Exception as e:
            print(f"Failed to get admin: {str(e)}")

    def delete_all_documents(self):
        # Delete all Document objects
        Document.objects.all().delete()

        # Initialize the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(
            os.environ.get('AZURE_STORAGE_ACCOUNT_CONNECTION_STRING'))
        container_name = os.environ.get('AZURE_CONTAINER')

        # List all blobs in the container
        container_client = blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs()

        # Delete each blob
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob)
            blob_client.delete_blob()
            print(f"Deleted blob: {blob.name}")

    def create_images(self):
        for image_item in image_list:
            Image.objects.create(
                name=image_item["name"],
                filename=image_item["filename"]
            )
            print(f"Created image: {image_item['name']}")

    def create_badges(self):
        for badge in badge_list:
            Badge.objects.create(
                name=badge["name"],
                description=badge["description"],
                type=badge["type"],
                condition=badge["condition"],
                image=Image.objects.get(filename=badge["image"])
            )

    def create_academic_years_terms(self):
        # Create a private year and term for the private course
        private_academic_year, _ = AcademicYear.objects.get_or_create(
            start_year=0,
            end_year=0
        )
        Term.objects.get_or_create(
            academic_year=private_academic_year,
            name="Private Term",
            defaults={"start_date": None, "end_date": None}
        )

        # Create normal academic years and their terms
        for year in year_list:
            academic_year = AcademicYear.objects.create(
                start_year=year["start_year"],
                end_year=year["end_year"]
            )
            for term_item in term_list:
                Term.objects.create(
                    academic_year=academic_year,
                    name=term_item["name"],
                    start_date=term_item["start_date"],
                    end_date=term_item["end_date"]
                )
                print(f"Created academic year: {academic_year.start_year}-{academic_year.end_year}")

    def create_courses(self):
        # Get semester 1
        term = Term.objects.get(name="Semester 1")
        for course_item in course_list:
            course = Course.objects.create(
                name=course_item["name"],
                description=course_item["description"],
                code=course_item["code"],
                term=term,
                type='System-enroll',
                status='Active',
                image=Image.objects.get(name=course_item["name"])
            )
            course.coordinators.set([self.admin])
            print(f"Created course: {course.name}")

        # Create a private course
        term = Term.objects.filter(name="Private Term").order_by('id').first()
        course, _ = Course.objects.get_or_create(
            name="Private Course",
            defaults={
                "description": "This is a private course created for all students to generate their own quests and questions.",
                "code": "PRIVATE",
                "term": term,
                "type": "Private",
                "status": "Active",
                "image": Image.objects.get(name="Private Course")
            }
        )
        course.coordinators.set([self.admin])
        print(f"Created a private course: {course.name}")

    def create_private_course_group(self):
        course = Course.objects.filter(name="Private Course").order_by('id').first()
        course_group, _ = CourseGroup.objects.get_or_create(
            name="Private Course Group",
            course=course,
            defaults={
                "session_day": "",
                "session_time": "",
                "instructor": self.admin
            }
        )
        print(f"Created a private course group: {course_group.name}")

    def create_course_groups(self):
        # Get all courses
        course_list = Course.objects.all()
        for course in course_list:
            for course_group_group in course_group_list:
                if course.code == course_group_group["course_code"]:
                    CourseGroup.objects.create(
                        name=course_group_group["name"],
                        session_day=course_group_group["session_day"],
                        session_time=course_group_group["session_time"],
                        instructor=self.instructor,
                        course=course  # Ensure the course is set
                    )
                    print(f"Created course group: {course_group_group['name']}")

    def create_fake_data(self):
        confirm = input("Do you want to use faker to populate the rest of the database with fake data? (y/n): ")
        if confirm.lower() == 'y':
            print("Creating fake data...")
            self.create_fake_students()
            self.create_fake_user_course_group_enrollments()
            self.create_fake_quests()
            self.create_fake_questions()
            self.create_fake_answers()
            self.create_fake_user_quest_attempts()
            self.create_fake_user_answer_attempts()
            print("Finished creating all fake data")

    def create_fake_students(self):
        for _ in range(6):
            name = fake.name().upper()
            user = EduquestUser.objects.create(
                username=f"#{name}#",
                email=f"{fake.user_name().upper()}@e.ntu.edu.sg",
                password='password',
                nickname=name,
                is_active=True,
                is_staff=False
            )
        print(f"Finished creating all fake students")

    def create_fake_user_course_group_enrollments(self):
        # Get all students
        student_list = EduquestUser.objects.filter(is_superuser=False)
        # Get all course groups
        course_group_list = CourseGroup.objects.exclude(name="Private Course Group")
        # Get all courses
        course_list = Course.objects.exclude(name="Private Course")
        for student in student_list:
            for course in course_list:
                # Filter course groups for the current course
                course_groups_for_course = [cg for cg in course_group_list if cg.course == course]
                if course_groups_for_course:
                    # Ensure the student is enrolled in at least one course group for the current course
                    course_group = random.choice(course_groups_for_course)
                    UserCourseGroupEnrollment.objects.create(
                        student=student,
                        course_group=course_group
                    )
        print(f"Finished creating all fake user course group enrollments for student: {student.username}")

    def create_fake_quests(self):
        # Get all course groups
        course_group_list = CourseGroup.objects.exclude(name="Private Course Group")
        image = Image.objects.get(name="Eduquest MCQ Quest")
        for course_group in course_group_list:
            for i in range(random.randint(0, 2)):
                Quest.objects.create(
                    course_group=course_group,
                    name=f"Quest {i + 1}",
                    description=fake.text(),
                    max_attempts=5,
                    type='Eduquest MCQ',
                    status='Active',
                    organiser=self.instructor,
                    image=image,
                )
            print(f"Finished creating all fake quests for course group: {course_group.name}")

    def create_fake_questions(self):
        # Get all quests
        quest_list = Quest.objects.exclude(name="Private Quest")
        for quest in quest_list:
            # Some quest may not have any questions created yet
            for i in range(random.randint(1, 3)):
                Question.objects.create(
                    quest=quest,
                    text=fake.sentence(nb_words=10),
                    number=i + 1,
                    max_score=random.randint(1, 5)
                )
            print(f"Finished creating all fake questions for quest: {quest.name}")

    def create_fake_answers(self):
        # Get all questions
        question_list = Question.objects.all()
        for question in question_list:
            for i in range(random.randint(2, 4)):
                Answer.objects.create(
                    question=question,
                    text=fake.sentence(nb_words=3),
                    is_correct=random.choice([True, False])
                )
            print(f"Finished creating all fake answers for question: {question.text}")

    def create_fake_user_quest_attempts(self):
        # Get all students
        student_list = EduquestUser.objects.filter(is_superuser=False)
        # Get all quests
        quest_list = Quest.objects.all()
        for student in student_list:
            for quest in quest_list:
                UserQuestAttempt.objects.create(
                    student=student,
                    quest=quest,
                    first_attempted_date=timezone.make_aware(
                        fake.date_time_this_month(before_now=True, after_now=False)
                    ),
                )
            print(f"Finished creating all fake user quest attempts for student: {student.username}")

    def create_fake_user_answer_attempts(self):
        # Get all user quest attempts
        user_quest_attempt_list = UserQuestAttempt.objects.all()
        for user_quest_attempt in user_quest_attempt_list:
            user_answer_attempts = []
            # Get all questions for the quest
            question_list = Question.objects.filter(quest=user_quest_attempt.quest)
            for question in question_list:
                # Get all answers for the question
                answer_list = Answer.objects.filter(question=question)
                for answer in answer_list:
                    # Create the UserAnswerAttempt instance for each answer
                    user_answer_attempts.append(UserAnswerAttempt(
                        user_quest_attempt=user_quest_attempt,
                        question=question,
                        answer=answer,
                        is_selected=random.choice([True, False]),
                        # score_achieved can be ignored or set to default
                    ))
            # Bulk create all UserAnswerAttempt instances
            UserAnswerAttempt.objects.bulk_create(user_answer_attempts)

            # Since we're ignoring score calculation, we don't need to update total_score_achieved
            # Optionally, set total_score_achieved to 0 if needed
            user_quest_attempt.total_score_achieved = 0
            user_quest_attempt.save()

            print(f"Finished creating all user answer attempts with is_selected=False "
                  f"for user quest attempt: {user_quest_attempt.id}")
