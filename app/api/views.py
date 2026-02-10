import uuid
from collections import defaultdict
import os
import requests
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from datetime import timedelta
from django.db.models import Count, Q, Max, Avg, Prefetch
from .excel import Excel
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from django.conf import settings
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    CourseGroup,
    UserCourseGroupEnrollment,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserAnswerAttempt,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
    Document,
    StudentFeedback
)
from .serializers import (
    EduquestUserSerializer,
    ImageSerializer,
    AcademicYearSerializer,
    TermSerializer,
    CourseSerializer,
    CourseGroupSerializer,
    UserCourseGroupEnrollmentSerializer,
    QuestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    UserQuestAttemptSerializer,
    UserAnswerAttemptSerializer,
    BadgeSerializer,
    UserQuestBadgeSerializer,
    UserCourseBadgeSerializer,
    DocumentSerializer,
    StudentFeedbackSerializer
)
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# Test view to check the request method and data

@api_view(['GET', 'POST'])
@csrf_exempt
def test_view(request):
    return Response({
        'method': request.method,
        'data': request.data,
    })


@api_view(['GET'])
def status_view(request):
    return Response({
        'status': 'OK'
    })


class EduquestUserViewSet(viewsets.ModelViewSet):
    queryset = EduquestUser.objects.all().order_by('-id')
    serializer_class = EduquestUserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_email(self, request):
        email = request.query_params.get('email')
        queryset = EduquestUser.objects.get(email=email)
        serializer = EduquestUserSerializer(queryset)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_admin(self, request):
        queryset = EduquestUser.objects.filter(is_staff=True).order_by('-id')
        serializer = EduquestUserSerializer(queryset, many=True)
        return Response(serializer.data)


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all().order_by('-id')
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = AcademicYear.objects.exclude(start_year=0).order_by('-id')
        serializer = AcademicYearSerializer(queryset, many=True)
        return Response(serializer.data)


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all().order_by('-id')
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Term.objects.exclude(name='Private Term').order_by('-id')
        serializer = TermSerializer(queryset, many=True)
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-id')
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Course.objects.exclude(type='Private').order_by('-id')
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_enrolled_user(self, request):
        user_id = request.query_params.get('user_id')
        # Get the course group enrollments for the given user
        course_group_enrollments = UserCourseGroupEnrollment.objects.filter(student_id=user_id)
        # Extract the course IDs from the related course groups
        course_ids = CourseGroup.objects.filter(
            id__in=course_group_enrollments.values_list('course_group', flat=True)
        ).values_list('course_id', flat=True)
        # Query the courses excluding Private courses
        queryset = Course.objects.exclude(type='Private').filter(id__in=course_ids).order_by('-id')

        # Serialize the results
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CourseGroupViewSet(viewsets.ModelViewSet):
    queryset = CourseGroup.objects.all().order_by('-id')
    serializer_class = CourseGroupSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_course(self, request):
        course_id = request.query_params.get('course_id')
        queryset = CourseGroup.objects.filter(course=course_id).order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_private_course(self, request):
        queryset = CourseGroup.objects.filter(course__type='Private').order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = CourseGroup.objects.exclude(course__type='Private').order_by('-id')
        serializer = CourseGroupSerializer(queryset, many=True)
        return Response(serializer.data)


class UserCourseGroupEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = UserCourseGroupEnrollment.objects.all().order_by('-id')
    serializer_class = UserCourseGroupEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_course_group_and_user(self, request):
        course_group_id = request.query_params.get('course_group_id')
        user_id = request.query_params.get('user_id')
        queryset = UserCourseGroupEnrollment.objects.filter(course_group=course_group_id, student=user_id).order_by(
            '-id')
        serializer = UserCourseGroupEnrollmentSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_course_and_user(self, request):
        course_id = request.query_params.get('course_id')
        user_id = request.query_params.get('user_id')
        queryset = UserCourseGroupEnrollment.objects.filter(course_group__course=course_id, student=user_id).order_by(
            '-id')
        serializer = UserCourseGroupEnrollmentSerializer(queryset, many=True)
        return Response(serializer.data)


class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all().order_by('-id')
    serializer_class = QuestSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def non_private(self, request):
        queryset = Quest.objects.exclude(type='Private').order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def private_by_user(self, request):
        user = request.user
        queryset = Quest.objects.filter(organiser=user, type='Private').order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_enrolled_user(self, request):
        user_id = request.query_params.get('user_id')
        # Get all course group enrollments for the user
        course_group_enrollments = UserCourseGroupEnrollment.objects.filter(student=user_id)
        # Get all quests for the course groups
        queryset = Quest.objects.filter(
            course_group__in=course_group_enrollments.values('course_group')
        ).exclude(type='Private').order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_course_group(self, request):
        course_group_id = request.query_params.get('course_group_id')
        queryset = Quest.objects.filter(course_group=course_group_id).order_by('-id')
        serializer = QuestSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def import_quest(self, request):
        try:
            excel_file = request.FILES.get('file')
        except Exception as e:
            return Response(
                {"Error processing excel file": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not excel_file:
            return Response(
                {"No file provided, please try again"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            excel = Excel()
            excel.read_excel_sheets(excel_file)
            questions_data = excel.get_questions()
            users_data = excel.get_users()
        except Exception as e:
            return Response(
                {"Error processing excel file": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract other form data
            quest_data = {
                'type': request.data.get('type'),
                'name': request.data.get('name'),
                'description': request.data.get('description'),
                'status': request.data.get('status'),
                'max_attempts': request.data.get('max_attempts'),
                'course_group_id': request.data.get('course_group_id'),
                'tutorial_date': request.data.get('tutorial_date'),
                'image_id': request.data.get('image_id'),
                'organiser_id': request.data.get('organiser_id')
            }
        except Exception as e:
            return Response(
                {"Error extracting form data": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use atomic transaction to ensure data integrity
        with transaction.atomic():
            try:
                try:
                    # Create a Quest object
                    quest_serializer = QuestSerializer(data=quest_data)
                    quest_serializer.is_valid(raise_exception=True)
                    quest = quest_serializer.save()
                    new_quest_id = quest.id
                except Exception as e:
                    raise ValidationError({"Error creating quest": str(e)})

                try:
                    questions_serializer = []
                    # Process each question in the questions_data list
                    for question_data in questions_data:
                        question_data['quest_id'] = new_quest_id
                        question_serializer = QuestionSerializer(data=question_data)
                        question_serializer.is_valid(raise_exception=True)
                        question = question_serializer.save()
                        questions_serializer.append(question_serializer.data)
                except Exception as e:
                    raise ValidationError({"Error creating questions": str(e)})

                # Enroll users and create UserQuestAttempt and UserAnswerAttempt objects
                for user_data in users_data:
                    try:
                        print(f"Processing user: {user_data['email']}")
                        user, created = EduquestUser.objects.get_or_create(
                            email=user_data['email'],
                            defaults={
                                'email': user_data['email'],
                                'username': user_data['username'],
                                'nickname': user_data['username'],
                            }
                        )
                    except Exception as e:
                        raise ValidationError({"Error creating user": str(e)})

                    try:
                        # Enroll the user in the course group
                        enrollment, enrolled = UserCourseGroupEnrollment.objects.get_or_create(
                            student=user,
                            course_group_id=quest_data['course_group_id'],
                        )
                    except Exception as e:
                        raise ValidationError({"Error enrolling new user": str(e)})

                    try:
                        # Create a UserQuestAttempt object
                        user_quest_attempt_data = {
                            'student_id': user.id,
                            'quest_id': new_quest_id
                        }
                        user_quest_attempt_serializer = UserQuestAttemptSerializer(data=user_quest_attempt_data)
                        user_quest_attempt_serializer.is_valid(raise_exception=True)
                        user_quest_attempt = user_quest_attempt_serializer.save()
                        new_user_quest_attempt_id = user_quest_attempt.id

                        # Get the generated empty-prefilled UserAnswerAttempt objects for the UserQuestAttempt
                        user_answer_attempts = UserAnswerAttempt.objects.filter(
                            user_quest_attempt=new_user_quest_attempt_id
                        )
                    except Exception as e:
                        raise ValidationError({"Error creating user quest attempt": str(e)})

                    # Update selected answers based on Excel data
                    try:
                        selected_answers = excel.get_user_answer_attempts(user.email)
                        for user_answer_attempt in user_answer_attempts:
                            for selected_answer in selected_answers:
                                if selected_answer['number'] == user_answer_attempt.question.number:
                                    if user_answer_attempt.answer.text in selected_answer['selected_answers']:
                                        user_answer_attempt.is_selected = True
                                        user_answer_attempt.save()
                    except Exception as e:
                        raise ValidationError({"Error updating selected answers": str(e)})

            except ValidationError as ve:
                return Response(
                    {"Validation Error": ve.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"Error importing quest": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(questions_serializer, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='bonus-game')
    def bonus_game(self, request, pk=None):
        quest = self.get_object()
        if quest.type != 'Private':
            return Response({"error": "Bonus game is only available for private quests."}, status=status.HTTP_400_BAD_REQUEST)

        if not quest.source_document:
            return Response({"error": "No source document found for this quest."}, status=status.HTTP_400_BAD_REQUEST)

        document_name = os.path.basename(quest.source_document.file.name)
        flask_url = getattr(settings, 'FLASK_MICROSERVICE_URL', 'http://localhost:5000')

        logger.info("[Bonus Game] Calling Flask microservice at %s for document=%s", flask_url, document_name)
        response = requests.post(
            f"{flask_url}/generate_bonus_game",
            json={"document_id": document_name},
            timeout=30
        )
        logger.info("[Bonus Game] Flask response status=%s", response.status_code)

        if response.status_code != 200:
            logger.error("[Bonus Game] Flask error status=%s body=%s", response.status_code, response.text[:500])
            return Response({"error": "Failed to generate bonus game."}, status=response.status_code)

        return Response(response.json())


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('-id')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            # Serialize the created data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all().order_by('-id')
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['put'], url_path='bulk-update')
    def bulk_update(self, request):
        # Ensure the request data is a list
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of items."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the serializer with 'many=True'
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Extract the validated data
        validated_data = serializer.validated_data

        # Collect the IDs of the answers to update
        answer_ids = [item['id'] for item in validated_data]

        # Retrieve the existing answers from the database
        answers = Answer.objects.filter(id__in=answer_ids)

        # Map existing answers by ID for easy lookup
        answer_dict = {answer.id: answer for answer in answers}

        updated_answers = []
        for item in validated_data:
            answer_id = item.get('id')
            if answer_id in answer_dict:
                answer_instance = answer_dict[answer_id]
                # Update the fields
                for attr, value in item.items():
                    setattr(answer_instance, attr, value)
                answer_instance.save()
                updated_answers.append(answer_instance)
            else:
                return Response({"error": f"Answer with id {answer_id} does not exist."},
                                status=status.HTTP_404_NOT_FOUND)

        # Serialize the updated answers to return in the response
        output_serializer = self.get_serializer(updated_answers, many=True)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class UserQuestAttemptViewSet(viewsets.ModelViewSet):
    queryset = UserQuestAttempt.objects.all().order_by('-id')
    serializer_class = UserQuestAttemptSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        user_id = request.query_params.get('user_id')
        queryset = UserQuestAttempt.objects.filter(student=user_id, quest=quest_id).order_by('-id')
        serializer = UserQuestAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserQuestAttempt.objects.filter(quest=quest_id).order_by('-id')
        serializer = UserQuestAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_all_attempts_submitted_by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserQuestAttempt.objects.filter(quest=quest_id)
        for instance in queryset:
            instance.submitted = True
            instance.save()
        return Response({"message": f"All attempts for quest {quest_id} have been marked as submitted."})

    @action(detail=True, methods=['post'], url_path='bonus')
    def award_bonus(self, request, pk=None):
        attempt = self.get_object()
        user = request.user

        if attempt.student_id != user.id:
            return Response({"error": "You can only claim bonus for your own attempts."}, status=status.HTTP_403_FORBIDDEN)

        if attempt.quest.type != 'Private':
            return Response({"error": "Bonus is only available for private quests."}, status=status.HTTP_400_BAD_REQUEST)

        if attempt.bonus_awarded:
            return Response({
                "bonus_awarded": True,
                "bonus_points": attempt.bonus_points
            })

        bonus_points = 5
        attempt.bonus_points = bonus_points
        attempt.bonus_awarded = True
        attempt.save(update_fields=['bonus_points', 'bonus_awarded'])

        user.total_points += bonus_points
        user.save(update_fields=['total_points'])

        return Response({
            "bonus_awarded": True,
            "bonus_points": bonus_points
        })

    # @action(detail=False, methods=['patch'], url_path='bulk-update')
    # def bulk_update(self, request, *args, **kwargs):
    #     """
    #     Bulk update UserQuestAttempt
    #     """
    #     if isinstance(request.data, list):
    #         updated_attempts = []
    #         for attempt_data in request.data:
    #             attempt_id = attempt_data.get('id')
    #             if not attempt_id:
    #                 return Response({"error": "ID is required for each attempt."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #             try:
    #                 # Retrieve the instance to update
    #                 attempt_instance = UserQuestAttempt.objects.get(id=attempt_id)
    #             except UserQuestAttempt.DoesNotExist:
    #                 return Response({"error": f"UserQuestAttempt with id {attempt_id} not found."},
    #                                 status=status.HTTP_404_NOT_FOUND)
    #
    #             # Use the existing serializer for each update
    #             serializer = self.get_serializer(instance=attempt_instance, data=attempt_data, partial=True)
    #             if serializer.is_valid():
    #                 serializer.save()
    #                 updated_attempts.append(serializer.data)
    #             else:
    #                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #
    #         return Response({"updated_attempts": updated_attempts}, status=status.HTTP_200_OK)
    #
    #     return Response({"error": "Expected a list of data."}, status=status.HTTP_400_BAD_REQUEST)


class StudentFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentFeedback.objects.all().order_by('-datetime_created')
    serializer_class = StudentFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def _restrict_queryset(self, request, queryset):
        if request.user.is_staff or request.user.is_superuser:
            return queryset
        return queryset.filter(user_quest_attempt__student=request.user)

    @action(detail=False, methods=['get'])
    def by_attempt(self, request):
        attempt_id = request.query_params.get('user_quest_attempt_id') or request.query_params.get('attempt_id')
        if not attempt_id:
            return Response({"error": "user_quest_attempt_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = StudentFeedback.objects.filter(user_quest_attempt_id=attempt_id)
        queryset = self._restrict_queryset(request, queryset)
        feedback = queryset.first()
        if not feedback:
            return Response({}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(feedback)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='save')
    def save_feedback(self, request):
        attempt_id = request.data.get('user_quest_attempt_id') or request.data.get('attempt_id')
        if not attempt_id:
            return Response({"error": "user_quest_attempt_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attempt = UserQuestAttempt.objects.get(id=attempt_id)
        except UserQuestAttempt.DoesNotExist:
            return Response({"error": "User quest attempt not found."}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_staff or request.user.is_superuser) and attempt.student != request.user:
            return Response({"error": "Not authorized to save feedback for this attempt."}, status=status.HTTP_403_FORBIDDEN)

        defaults = {
            'quest_summary': request.data.get('quest_summary', {}),
            'subtopic_feedback': request.data.get('subtopic_feedback', []),
            'study_tips': request.data.get('study_tips', []),
            'strengths': request.data.get('strengths', []),
            'weaknesses': request.data.get('weaknesses', []),
            'recommendations': request.data.get('recommendations', ''),
            'question_feedback': request.data.get('question_feedback', {}),
        }

        feedback, _ = StudentFeedback.objects.update_or_create(
            user_quest_attempt=attempt,
            defaults=defaults
        )
        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAnswerAttemptViewSet(viewsets.ModelViewSet):
    queryset = UserAnswerAttempt.objects.all().order_by('-id')
    serializer_class = UserAnswerAttemptSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user_quest_attempt(self, request):
        user_quest_attempt_id = request.query_params.get('user_quest_attempt_id')
        queryset = UserAnswerAttempt.objects.filter(user_quest_attempt=user_quest_attempt_id).order_by('-id')
        serializer = UserAnswerAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_quest(self, request):
        quest_id = request.query_params.get('quest_id')
        queryset = UserAnswerAttempt.objects.filter(user_quest_attempt__quest=quest_id).order_by('-id')
        serializer = UserAnswerAttemptSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request, *args, **kwargs):
        """
        Bulk update UserAnswerAttempt
        """
        if isinstance(request.data, list):
            updated_attempts = []
            for attempt_data in request.data:
                attempt_id = attempt_data.get('id')
                if not attempt_id:
                    return Response({"error": "ID is required for each attempt."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Retrieve the instance to update
                    attempt_instance = UserAnswerAttempt.objects.get(id=attempt_id)
                except UserAnswerAttempt.DoesNotExist:
                    return Response({"error": f"UserAnswerAttempt with id {attempt_id} not found."},
                                    status=status.HTTP_404_NOT_FOUND)

                # Use the existing serializer for each update
                serializer = self.get_serializer(instance=attempt_instance, data=attempt_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_attempts.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"updated_attempts": updated_attempts}, status=status.HTTP_200_OK)

        return Response({"error": "Expected a list of data."}, status=status.HTTP_400_BAD_REQUEST)


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all().order_by('-id')
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Allow all authenticated users to view badges,
        # but only staff/superuser to create/update/delete.
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminUser()]


class UserQuestBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserQuestBadge.objects.all().order_by('-id')
    serializer_class = UserQuestBadgeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = UserQuestBadge.objects.filter(user_quest_attempt__student=user_id).order_by('-id')
        serializer = UserQuestBadgeSerializer(queryset, many=True)
        return Response(serializer.data)


class UserCourseBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserCourseBadge.objects.all().order_by('-id')
    serializer_class = UserCourseBadgeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = UserCourseBadge.objects.filter(user_course_group_enrollment__student=user_id).order_by('-id')
        serializer = UserCourseBadgeSerializer(queryset, many=True)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-id')
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        queryset = Document.objects.filter(uploaded_by=user_id).order_by('-id')
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({"No file provided, please try again"}, status=status.HTTP_400_BAD_REQUEST)
            data = {
                'uploaded_by': request.user.id,
                'file': file,
                'name': request.data.get('name'),
                'size': request.data.get('size'),
            }
            serializer = DocumentSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Error uploading document": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AnalyticsPartOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Current time and time one week ago
        now = timezone.now()
        last_week = now - timedelta(weeks=1)

        # 1. Total number of users excluding admin and new users since last week
        total_users = EduquestUser.objects.exclude(is_staff=True).count()
        new_users_last_week = EduquestUser.objects.exclude(is_staff=True).filter(date_joined__gte=last_week).count()
        new_users_percentage = (new_users_last_week / total_users) * 100 if total_users > 0 else 0

        # 2. Total number of course enrollments and new enrollments since last week
        total_enrollments = UserCourseGroupEnrollment.objects.exclude(course_group__course__type="Private").count()
        new_enrollments_last_week = UserCourseGroupEnrollment.objects.exclude(
            course_group__course__type="Private").filter(
            enrolled_on__gte=last_week).count()
        new_enrollments_percentage = (
                                             new_enrollments_last_week / total_enrollments) * 100 if total_enrollments > 0 else 0

        # 3. Total number of quest attempts and new attempts since last week
        total_quest_attempts = UserQuestAttempt.objects.exclude(quest__type="Private").count()
        new_quest_attempts_last_week = UserQuestAttempt.objects.exclude(quest__type="Private").filter(
            first_attempted_date__gte=last_week).count()
        new_quest_attempts_percentage = (
                                                new_quest_attempts_last_week / total_quest_attempts) * 100 if total_quest_attempts > 0 else 0

        # 4. User with the shortest non-zero time_taken and perfect score
        # Filter UserQuestBadge for users with the "Perfectionist" badge
        perfectionist_badge_attempts = UserQuestBadge.objects.filter(
            badge__name="Perfectionist"
        ).annotate(
            time_taken=ExpressionWrapper(
                F('user_quest_attempt__last_attempted_date') - F('user_quest_attempt__first_attempted_date'),
                output_field=DurationField()
            )
        ).filter(
            time_taken__gt=timedelta(seconds=0)
        ).order_by('time_taken').first()

        if perfectionist_badge_attempts:
            shortest_time_user = {
                'nickname': perfectionist_badge_attempts.user_quest_attempt.student.nickname,
                'time_taken': int(perfectionist_badge_attempts.time_taken.total_seconds() * 1000),
                # Convert to milliseconds and round to whole number
                'quest_id': perfectionist_badge_attempts.user_quest_attempt.quest.id,
                'quest_name': perfectionist_badge_attempts.user_quest_attempt.quest.name,
                'course': f"{perfectionist_badge_attempts.user_quest_attempt.quest.course_group.course.code} {perfectionist_badge_attempts.user_quest_attempt.quest.course_group.course.name}"
            }
        else:
            shortest_time_user = None

        data = {
            'user_stats': {
                'total_users': total_users,
                'new_users_percentage': new_users_percentage,
            },
            'course_enrollment_stats': {
                'total_enrollments': total_enrollments,
                'new_enrollments_percentage': new_enrollments_percentage,
            },
            'quest_attempt_stats': {
                'total_quest_attempts': total_quest_attempts,
                'new_quest_attempts_percentage': new_quest_attempts_percentage,
            },
            'shortest_time_user': shortest_time_user
        }

        return Response(data)


class AnalyticsPartTwoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = self.request.query_params.get('user_id')
        option = self.request.query_params.get('option')  # course_progression, badge_progression, or both

        # Validation
        if not user_id:
            return Response({"error": "user_id is required in the URL parameters."}, status=400)
        if not option:
            return Response({"error": "option is required in the URL parameters."}, status=400)
        if option not in ['course_progression', 'badge_progression', 'both']:
            return Response({"error": "option must be either course_progression, badge_progression, or both."},
                            status=400)

        if option == 'course_progression':
            return self.get_course_progression(user_id)
        if option == 'badge_progression':
            return self.get_badge_progression(user_id)
        if option == 'both':
            return self.get_course_and_badge_progression(user_id)

    def get_course_progression(self, user_id):
        # Fetch enrollments with related course and quests in a single query
        enrollments = UserCourseGroupEnrollment.objects.filter(
            student_id=user_id
        ).exclude(
            course_group__course__name="Private Course"
        ).select_related('course_group__course').prefetch_related('course_group__quests')

        course_quest_completion = []

        for enrollment in enrollments:
            course_group = enrollment.course_group
            course = course_group.course

            quest_attempts = UserQuestAttempt.objects.filter(
                student_id=user_id,
                quest__course_group__course_id=course.id,
                submitted=True
            ).distinct('quest')

            completed_quests = quest_attempts.count()
            total_quests = course_group.quests.count()
            completion_ratio = completed_quests / total_quests if total_quests > 0 else 0

            # Get the highest score for each quest attempted in the course
            quest_scores = []
            for quest in course_group.quests.all():
                # Fetch all attempts for this quest by the user
                attempts = UserQuestAttempt.objects.filter(
                    student_id=user_id,
                    quest=quest
                )
                if attempts.exists():
                    # Aggregate the highest score achieved across all attempts for this quest
                    highest_score = attempts.aggregate(
                        highest_score=Sum('total_score_achieved')
                    )['highest_score'] or 0
                else:
                    highest_score = 0

                quest_scores.append({
                    'quest_id': quest.id,
                    'quest_name': quest.name,
                    'max_score': quest.total_max_score(),
                    'highest_score': highest_score
                })

            course_quest_completion.append({
                'course_id': course.id,
                'course_term': f"AY {course.term.academic_year.start_year} - {course.term.academic_year.end_year} {course.term.name}",
                'course_code': course.code,
                'course_name': course.name,
                'completed_quests': completed_quests,
                'total_quests': total_quests,
                'completion_ratio': round(completion_ratio, 2),  # Rounded to 2 decimal places
                'quest_scores': quest_scores
            })
        # Sort the results by completion ratio in descending order
        course_quest_completion.sort(key=lambda x: x['completion_ratio'], reverse=True)

        return Response({'user_course_progression': course_quest_completion})

    def get_badge_progression(self, user_id):
        all_badges = Badge.objects.all()
        # Fetch all quest badges and course badges earned by the user
        user_quest_badges = UserQuestBadge.objects.filter(
            user_quest_attempt__student_id=user_id
        ).select_related('badge')
        # Fetch all course badges earned by the user
        user_course_badges = UserCourseBadge.objects.filter(
            user_course_group_enrollment__student_id=user_id
        ).select_related('badge')
        # Aggregate the badge data
        badge_aggregation = {
            badge.id: {
                'badge_id': badge.id,
                'badge_name': badge.name,
                'badge_filename': badge.image.filename if badge.image else None,
                'count': 0
            } for badge in all_badges
        }

        # Increment the count for each badge earned by the user
        for badge in user_quest_badges:
            badge_aggregation[badge.badge.id]['count'] += 1

        # Increment the count for each course badge earned by the user
        for badge in user_course_badges:
            badge_aggregation[badge.badge.id]['count'] += 1

        # Filter out badges with zero count and sort by count in descending order
        badge_aggregation = [v for v in badge_aggregation.values() if v['count'] > 0]
        sorted_badge_aggregation = sorted(badge_aggregation, key=lambda x: x['count'], reverse=True)

        return Response({'user_badge_progression': sorted_badge_aggregation})

    def get_course_and_badge_progression(self, user_id):
        course_progression = self.get_course_progression(user_id).data
        badge_progression = self.get_badge_progression(user_id).data
        return Response({**course_progression, **badge_progression})


class AnalyticsPartThreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch top 5 users with the most badges with quest badge and course badge combined
        top_users = EduquestUser.objects.annotate(
            quest_badge_count=Count('attempted_quests__earned_quest_badges', distinct=True),
            course_badge_count=Count('enrolled_course_groups__earned_course_badges', distinct=True),
        ).annotate(
            total_badge_count=F('quest_badge_count') + F('course_badge_count')
        ).order_by('-total_badge_count')[:5]

        # Prefetch related badges to reduce database hits
        quest_badges = UserQuestBadge.objects.select_related('badge', 'user_quest_attempt__student').all()
        course_badges = UserCourseBadge.objects.select_related('badge', 'user_course_group_enrollment__student').all()

        user_badge_details = []
        for user in top_users:
            # Aggregate quest badges
            quest_badges_dict = {}
            for badge in quest_badges:
                if badge.user_quest_attempt.student == user:
                    badge_id = badge.badge.id
                    if badge_id not in quest_badges_dict:
                        quest_badges_dict[badge_id] = {
                            "badge_id": badge_id,
                            "badge_name": badge.badge.name,
                            "badge_filename": badge.badge.image.filename,
                            "count": 1
                        }
                    else:
                        quest_badges_dict[badge_id]["count"] += 1

            # Convert the dictionary to a list
            quest_badges_data = list(quest_badges_dict.values())

            # Aggregate course badges similarly
            course_badges_dict = {}
            for badge in course_badges:
                if badge.user_course_group_enrollment.student == user:
                    badge_id = badge.badge.id
                    if badge_id not in course_badges_dict:
                        course_badges_dict[badge_id] = {
                            "badge_id": badge_id,
                            "badge_name": badge.badge.name,
                            "badge_filename": badge.badge.image.filename,
                            "count": 1
                        }
                    else:
                        course_badges_dict[badge_id]["count"] += 1

            # Convert the dictionary to a list
            course_badges_data = list(course_badges_dict.values())

            # Add the aggregated data to the user_badge_details
            user_badge = {
                "user_id": user.id,
                "nickname": user.nickname,
                "badge_count": user.total_badge_count,  # Use the annotated total_badge_count
                "quest_badges": quest_badges_data,
                "course_badges": course_badges_data
            }
            user_badge_details.append(user_badge)

        # Get top 5 most recent badge awards from both UserQuestBadge and UserCourseBadge
        recent_quest_badges = quest_badges.order_by('-awarded_date')[:5]
        recent_course_badges = course_badges.order_by('-awarded_date')[:5]

        # Combine and sort the badges by the most recent award date
        recent_badges = sorted(
            list(recent_quest_badges) + list(recent_course_badges),
            key=lambda badge: badge.awarded_date,
            reverse=True
        )[:5]

        recent_badges_data = []
        record_id = 0
        for badge in recent_badges:
            badge_name = badge.badge.name
            awarded_date = badge.awarded_date
            quest_id = None
            quest_name = None
            if isinstance(badge, UserCourseBadge):
                user_id = badge.user_course_group_enrollment.student.id
                nickname = badge.user_course_group_enrollment.student.nickname
                course_id = badge.user_course_group_enrollment.course_group.course.id
                course_code = badge.user_course_group_enrollment.course_group.course.code
                course_name = badge.user_course_group_enrollment.course_group.course.name
            else:
                user_id = badge.user_quest_attempt.student.id
                nickname = badge.user_quest_attempt.student.nickname
                quest_id = badge.user_quest_attempt.quest.id
                quest_name = badge.user_quest_attempt.quest.name
                course_id = badge.user_quest_attempt.quest.course_group.course.id
                course_code = badge.user_quest_attempt.quest.course_group.course.code
                course_name = badge.user_quest_attempt.quest.course_group.course.name

            badge_data = {
                'record_id': record_id,
                'user_id': user_id,
                'nickname': nickname,
                'badge_name': badge_name,
                'awarded_date': awarded_date,
                'course_id': course_id,
                'course_code': course_code,
                'course_name': course_name,
                'quest_id': quest_id,
                'quest_name': quest_name,
            }
            record_id += 1
            recent_badges_data.append(badge_data)

        data = {
            'top_users_with_most_badges': user_badge_details,
            'recent_badge_awards': recent_badges_data
        }

        return Response(data)


class AnalyticsPartFourView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves comprehensive statistics and aggregations for all courses (excluding private),
        including course groups, enrollments, quests, quest progression,
        and detailed student progress for each quest.
        """
        # Step 1: Fetch all courses except those with type="private"
        courses = Course.objects.exclude(type="Private").select_related(
            'term__academic_year',  # Fetch related Term and AcademicYear
            'image'  # Fetch related Image
        ).prefetch_related(
            Prefetch(
                'groups',
                queryset=CourseGroup.objects.annotate(
                    enrolled_students_count=Count('enrolled_students')  # Annotate enrolled students count
                ).prefetch_related(
                    Prefetch(
                        'quests',
                        queryset=Quest.objects.annotate(
                            quest_completion=Count(
                                'attempted_by__student',
                                filter=Q(attempted_by__submitted=True),
                                distinct=True
                            )
                        )
                    )
                )
            )
        )

        if not courses.exists():
            return Response(
                {"message": "No courses available."},
                status=200
            )

        # Step 2: Fetch all enrollments for the fetched courses
        enrollments = UserCourseGroupEnrollment.objects.filter(
            course_group__course__in=courses
        ).select_related(
            'student',
            'course_group'
        )

        # Mapping: course_group_id -> set of student IDs
        group_to_students = defaultdict(set)
        student_id_to_username = {}

        for enrollment in enrollments:
            group_id = enrollment.course_group.id
            student = enrollment.student
            group_to_students[group_id].add(student.id)
            student_id_to_username[student.id] = student.username

        # Step 3: Fetch all UserQuestAttempt data for the fetched courses' quests and enrolled students
        user_quest_attempts = UserQuestAttempt.objects.filter(
            quest__course_group__course__in=courses,
            student__in=EduquestUser.objects.filter(
                enrolled_course_groups__course_group__course__in=courses
            ).distinct()
        ).values(
            'quest_id',
            'student_id'
        ).annotate(
            highest_score=Max('total_score_achieved')
        )

        # Build a mapping: (quest_id, student_id) -> highest_score
        quest_student_to_score = {}
        for attempt in user_quest_attempts:
            key = (attempt['quest_id'], attempt['student_id'])
            quest_student_to_score[key] = attempt['highest_score']

        # Step 4: Construct response data for all courses
        all_courses_data = []
        for course in courses:
            course_groups_data = []
            for group in course.groups.all():
                group_id = group.id
                enrolled_students_count = group.enrolled_students_count
                enrolled_student_ids = group_to_students.get(group_id, set())

                # Build a list of enrolled students with their usernames
                enrolled_students = [
                    {'student_id': student_id, 'username': student_id_to_username.get(student_id, 'Unknown')}
                    for student_id in enrolled_student_ids
                ]

                # Build quests data for each course group
                quests_data = []
                for quest in group.quests.all():
                    # For each quest, build a list of student progress
                    student_progress = []
                    for student in enrolled_students:
                        key = (quest.id, student['student_id'])
                        highest_score = quest_student_to_score.get(key, None)  # None if no attempts

                        student_progress.append({
                            'username': student['username'],
                            'highest_score': highest_score
                        })

                    quest_data = {
                        'quest_id': quest.id,
                        'quest_name': quest.name,
                        'quest_completion': quest.quest_completion,
                        'quest_max_score': quest.total_max_score(),
                        'students_progress': student_progress
                    }
                    quests_data.append(quest_data)

                # Assemble group data
                group_data = {
                    'group_id': group.id,
                    'group_name': group.name,
                    'enrolled_students': enrolled_students_count,
                    'quests': quests_data
                }
                course_groups_data.append(group_data)

            # Assemble course data
            course_data = {
                'course_id': course.id,
                'course_code': course.code,
                'course_name': course.name,
                'course_term': f"AY {course.term.academic_year.start_year} - {course.term.academic_year.end_year} {course.term.name}",
                'course_image': course.image.filename if course.image else None,
                'course_groups': course_groups_data
            }
            all_courses_data.append(course_data)

        # Step 5: Return the response data
        return Response(all_courses_data)

