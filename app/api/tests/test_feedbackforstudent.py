"""
Test Suite for Objective 1: Student Cognitive Assessment and Feedback System
"""

import json
from unittest.mock import patch, Mock, MagicMock, ANY
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta

from ..models import (
    EduquestUser,
    Course,
    CourseGroup,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserAnswerAttempt,
    StudentCognitiveProfile,
    StudentFeedback,
    AcademicYear,
    Term
)
from ..tasks import generate_personalised_feedback, update_cognitive_profile
from ..tests.factory import (
    EduquestUserFactory,
    CourseFactory,
    CourseGroupFactory,
    QuestFactory,
    QuestionFactory,
    AnswerFactory,
    UserQuestAttemptFactory,
    UserAnswerAttemptFactory,
    TermFactory
)


class BaseTestCase(TestCase):
    """Base test case that creates Private Course Group before any tests"""
    
    def setUp(self):
        """Create Private Course Group if it doesn't exist"""
        super().setUp()
        self._ensure_private_course_group()
    
    def _ensure_private_course_group(self):
        """Create the Private Course Group required by EduquestUser.save()"""
        if not CourseGroup.objects.filter(name="Private Course Group").exists():
            academic_year, _ = AcademicYear.objects.get_or_create(
                start_year=2024,
                end_year=2025
            )
            term = TermFactory(academic_year=academic_year)
            course = CourseFactory(term=term)
            CourseGroupFactory(
                course=course,
                name="Private Course Group"
            )


class StudentCognitiveProfileModelTest(BaseTestCase):
    """Test the StudentCognitiveProfile model"""

    def setUp(self):
        """Set up test user"""
        super().setUp()
        self.user = EduquestUserFactory()

    def test_cognitive_profile_creation(self):
        """Test creating a cognitive profile"""
        profile = StudentCognitiveProfile.objects.create(
            student=self.user,
            remember_accuracy=85.5,
            understand_accuracy=75.0,
            apply_accuracy=60.0,
            analyse_accuracy=55.0,
            evaluate_accuracy=70.0,
            create_accuracy=50.0,
            weak_topics={'Python': 45.0, 'Algorithms': 50.0},
            competency_level='Intermediate',
            recommend_difficulty=5.0
        )

        self.assertEqual(profile.student, self.user)
        self.assertEqual(profile.remember_accuracy, 85.5)
        self.assertEqual(profile.competency_level, 'Intermediate')
        self.assertIn('Python', profile.weak_topics)
        self.assertEqual(profile.weak_topics['Python'], 45.0)

    def test_cognitive_profile_one_to_one_relationship(self):
        """Test that each user can only have one cognitive profile"""
        StudentCognitiveProfile.objects.create(student=self.user)

        with self.assertRaises(Exception):
            StudentCognitiveProfile.objects.create(student=self.user)

    def test_cognitive_profile_str_method(self):
        """Test string representation"""
        profile = StudentCognitiveProfile.objects.create(student=self.user)
        expected = f"Cognitive Profile of {self.user.username}"
        self.assertEqual(str(profile), expected)

    def test_cognitive_profile_defaults(self):
        """Test default values"""
        profile = StudentCognitiveProfile.objects.create(student=self.user)

        self.assertEqual(profile.remember_accuracy, 0.0)
        self.assertEqual(profile.understand_accuracy, 0.0)
        self.assertEqual(profile.competency_level, 'Beginner')
        self.assertEqual(profile.recommend_difficulty, 5.0)
        self.assertEqual(profile.weak_topics, {})


class StudentFeedbackModelTest(BaseTestCase):
    """Test the StudentFeedback model"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.academic_year = AcademicYear.objects.create(
            start_year=2024,
            end_year=2025
        )
        self.term = TermFactory(academic_year=self.academic_year)
        self.course = CourseFactory(term=self.term)
        
        self.user = EduquestUserFactory()
        self.course_group = CourseGroupFactory(course=self.course)
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.user)
        self.attempt = UserQuestAttemptFactory(quest=self.quest, student=self.user)

    def test_student_feedback_creation(self):
        """Test creating student feedback"""
        feedback = StudentFeedback.objects.create(
            user_quest_attempt=self.attempt,
            quest_summary={
                'overall_bloom_rating': 3,
                'overall_bloom_level': 'Apply',
                'summary': 'Shows solid understanding with room to improve on application.'
            },
            subtopic_feedback=[
                {
                    'subtopic': 'Algorithms',
                    'bloom_rating': 2,
                    'bloom_level': 'Understand',
                    'evidence': 'Missed key distinctions in runtime analysis.',
                    'improvement_focus': 'Practice comparing algorithm complexity.'
                }
            ],
            study_tips=['Review algorithm complexity basics.']
        )

        self.assertEqual(feedback.user_quest_attempt, self.attempt)
        self.assertIn('overall_bloom_rating', feedback.quest_summary)
        self.assertEqual(len(feedback.subtopic_feedback), 1)
        self.assertEqual(len(feedback.study_tips), 1)

    def test_student_feedback_one_to_one_relationship(self):
        """Test that each attempt can only have one feedback"""
        StudentFeedback.objects.create(user_quest_attempt=self.attempt)

        with self.assertRaises(Exception):
            StudentFeedback.objects.create(user_quest_attempt=self.attempt)

    def test_student_feedback_str_method(self):
        """Test string representation"""
        feedback = StudentFeedback.objects.create(user_quest_attempt=self.attempt)
        expected = f"Feedback for {self.attempt.student.username} on Quest {self.attempt.quest.name}"
        self.assertEqual(str(feedback), expected)

    def test_student_feedback_json_fields(self):
        """Test JSON field handling"""
        feedback = StudentFeedback.objects.create(
            user_quest_attempt=self.attempt,
            quest_summary={'overall_bloom_rating': 1, 'overall_bloom_level': 'Remember', 'summary': 'Test'},
            subtopic_feedback=[{'subtopic': 'Test', 'bloom_rating': 1, 'bloom_level': 'Remember'}],
            study_tips=['Tip 1']
        )

        feedback_from_db = StudentFeedback.objects.get(id=feedback.id)

        self.assertIsInstance(feedback_from_db.quest_summary, dict)
        self.assertIsInstance(feedback_from_db.subtopic_feedback, list)
        self.assertIsInstance(feedback_from_db.study_tips, list)


class QuestionCognitiveFieldsTest(BaseTestCase):
    """Test the new cognitive fields added to Question model"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.academic_year = AcademicYear.objects.create(
            start_year=2024,
            end_year=2025
        )
        self.term = TermFactory(academic_year=self.academic_year)
        self.course = CourseFactory(term=self.term)
        
        self.user = EduquestUserFactory()
        self.course_group = CourseGroupFactory(course=self.course)
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.user)

    def test_question_with_cognitive_fields(self):
        """Test creating questions with cognitive metadata"""
        question = Question.objects.create(
            quest=self.quest,
            text='What is a hash table?',
            number=1,
            max_score=10.0,
            cognitive_level='Remember',
            topic='Data Structures',
            difficulty_score=3.5,
            explanation='A hash table is a data structure...'
        )

        self.assertEqual(question.cognitive_level, 'Remember')
        self.assertEqual(question.topic, 'Data Structures')
        self.assertEqual(question.difficulty_score, 3.5)
        self.assertIsNotNone(question.explanation)

    def test_question_cognitive_fields_optional(self):
        """Test that cognitive fields are optional"""
        question = Question.objects.create(
            quest=self.quest,
            text='Basic question',
            number=1,
            max_score=5.0
        )

        self.assertIsNone(question.cognitive_level)
        self.assertIsNone(question.topic)
        self.assertIsNone(question.difficulty_score)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UpdateCognitiveProfileTaskTest(BaseTestCase):
    """Test the update_cognitive_profile Celery task"""

    def setUp(self):
        """Set up test data with multiple quest attempts"""
        super().setUp()
        
        self.academic_year = AcademicYear.objects.create(
            start_year=2025,
            end_year=2026
        )
        self.term = TermFactory(academic_year=self.academic_year)
        self.course = CourseFactory(term=self.term)
        
        self.user = EduquestUserFactory()
        self.course_group = CourseGroupFactory(course=self.course)
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.user)

        self.questions = []
        cognitive_levels = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
        topics = ['Data Structures', 'Algorithms', 'Python', 'Complexity']

        for i, level in enumerate(cognitive_levels):
            question = Question.objects.create(
                quest=self.quest,
                text=f'Question about {level}',
                number=i + 1,
                max_score=10.0,
                cognitive_level=level,
                topic=topics[i % len(topics)],
                difficulty_score=5.0
            )
            self.questions.append(question)

            Answer.objects.create(
                question=question,
                text='Correct answer',
                is_correct=True,
                reason='This is correct'
            )
            Answer.objects.create(
                question=question,
                text='Wrong answer',
                is_correct=False,
                reason='This is wrong'
            )

    def test_update_cognitive_profile_creates_profile(self):
        """Test that task creates a cognitive profile if it doesn't exist"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        # Create answer attempts - correctness is in the Answer, not UserAnswerAttempt
        for i, question in enumerate(self.questions[:3]):
            correct_answer = question.answers.filter(is_correct=True).first()
            UserAnswerAttempt.objects.create(
                user_quest_attempt=attempt,
                question=question,
                answer=correct_answer,
                is_correct=True  # ✅ ADDED
            )

        update_cognitive_profile(self.user.id)

        self.assertTrue(
            StudentCognitiveProfile.objects.filter(student=self.user).exists()
        )

    def test_update_cognitive_profile_calculates_accuracy(self):
        """Test accuracy calculation for each cognitive level"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        # Answer Remember question correctly
        remember_q = [q for q in self.questions if q.cognitive_level == 'Remember'][0]
        correct_ans = remember_q.answers.filter(is_correct=True).first()
        UserAnswerAttempt.objects.create(
            user_quest_attempt=attempt,
            question=remember_q,
            answer=correct_ans,
            is_correct=True  # ✅ ADDED
        )

        # Answer Apply question incorrectly
        apply_q = [q for q in self.questions if q.cognitive_level == 'Apply'][0]
        wrong_ans = apply_q.answers.filter(is_correct=False).first()
        UserAnswerAttempt.objects.create(
            user_quest_attempt=attempt,
            question=apply_q,
            answer=wrong_ans,
            is_correct=False  # ✅ ADDED
        )

        update_cognitive_profile(self.user.id)

        profile = StudentCognitiveProfile.objects.get(student=self.user)
        self.assertEqual(profile.remember_accuracy, 100.0)
        self.assertEqual(profile.apply_accuracy, 0.0)

    def test_update_cognitive_profile_identifies_weak_topics(self):
        """Test identification of weak topics (< 60% accuracy)"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        # Create 5 Python questions, answer 2 correctly and 3 incorrectly
        for i in range(5):
            question = Question.objects.create(
                quest=self.quest,
                text=f'Python question {i}',
                number=len(self.questions) + i + 1,
                max_score=10.0,
                cognitive_level='Apply',
                topic='Python'
            )

            correct_ans = Answer.objects.create(
                question=question,
                text='Correct',
                is_correct=True,
                reason='Correct'
            )
            wrong_ans = Answer.objects.create(
                question=question,
                text='Wrong',
                is_correct=False,
                reason='Wrong'
            )

            # Answer first 2 correctly, rest incorrectly
            if i < 2:
                UserAnswerAttempt.objects.create(
                    user_quest_attempt=attempt,
                    question=question,
                    answer=correct_ans,
                    is_correct=True  # ✅ ADDED
                )
            else:
                UserAnswerAttempt.objects.create(
                    user_quest_attempt=attempt,
                    question=question,
                    answer=wrong_ans,
                    is_correct=False  # ✅ ADDED
                )

        update_cognitive_profile(self.user.id)

        profile = StudentCognitiveProfile.objects.get(student=self.user)
        self.assertIn('Python', profile.weak_topics)
        self.assertLess(profile.weak_topics['Python'], 60.0)

    def test_update_cognitive_profile_determines_competency_level(self):
        """Test competency level determination based on average accuracy"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        # Answer all questions correctly
        for question in self.questions:
            correct_ans = question.answers.filter(is_correct=True).first()
            UserAnswerAttempt.objects.create(
                user_quest_attempt=attempt,
                question=question,
                answer=correct_ans,
                is_correct=True  # ✅ ADDED
            )

        update_cognitive_profile(self.user.id)

        profile = StudentCognitiveProfile.objects.get(student=self.user)
        self.assertEqual(profile.competency_level, 'Advanced')
        self.assertEqual(profile.recommend_difficulty, 8.0)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class GeneratePersonalisedFeedbackTaskTest(BaseTestCase):
    """Test the generate_personalised_feedback Celery task"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.academic_year = AcademicYear.objects.create(
            start_year=2025,
            end_year=2026
        )
        self.term = TermFactory(academic_year=self.academic_year)
        self.course = CourseFactory(term=self.term)
        
        self.user = EduquestUserFactory()
        self.course_group = CourseGroupFactory(course=self.course)
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.user)

        self.question1 = Question.objects.create(
            quest=self.quest,
            text='What is a hash table?',
            number=1,
            max_score=10.0,
            cognitive_level='Remember',
            topic='Data Structures'
        )

        self.correct_answer1 = Answer.objects.create(
            question=self.question1,
            text='A data structure that maps keys to values',
            is_correct=True,
            reason='Correct definition'
        )

        self.wrong_answer1 = Answer.objects.create(
            question=self.question1,
            text='A type of array',
            is_correct=False,
            reason='Incorrect'
        )

        self.attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        self.answer_attempt = UserAnswerAttempt.objects.create(
            user_quest_attempt=self.attempt,
            question=self.question1,
            answer=self.correct_answer1,
            is_correct=True  # ✅ ADDED
        )

    @patch('api.tasks.requests.post')
    def test_generate_feedback_calls_flask_api(self, mock_post):
        """Test that the task calls Flask microservice"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'quest_summary': {
                'overall_bloom_rating': 2,
                'overall_bloom_level': 'Understand',
                'summary': 'Basic understanding with gaps.'
            },
            'subtopic_feedback': [],
            'study_tips': []
        }
        mock_post.return_value = mock_response

        generate_personalised_feedback(self.attempt.id)

        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args

        self.assertIn('/generate_feedback', call_args[0][0])

        request_data = call_args[1]['json']
        self.assertEqual(request_data['student_id'], self.user.id)
        self.assertEqual(request_data['quest_id'], self.quest.id)
        self.assertIn('answers', request_data)
        self.assertEqual(len(request_data['answers']), 1)

    @patch('api.tasks.requests.post')
    def test_generate_feedback_saves_to_database(self, mock_post):
        """Test that feedback is saved to database"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'quest_summary': {
                'overall_bloom_rating': 4,
                'overall_bloom_level': 'Analyze',
                'summary': 'Shows strong analytical skill with minor gaps.'
            },
            'subtopic_feedback': [
                {
                    'subtopic': 'Data Structures',
                    'bloom_rating': 3,
                    'bloom_level': 'Apply',
                    'evidence': 'Applied definitions correctly.',
                    'improvement_focus': 'Practice more real-world examples.'
                }
            ],
            'study_tips': ['Practice more real-world examples.']
        }
        mock_post.return_value = mock_response

        generate_personalised_feedback(self.attempt.id)

        self.assertTrue(
            StudentFeedback.objects.filter(user_quest_attempt=self.attempt).exists()
        )

        feedback = StudentFeedback.objects.get(user_quest_attempt=self.attempt)
        self.assertIn('overall_bloom_rating', feedback.quest_summary)
        self.assertEqual(len(feedback.subtopic_feedback), 1)
        self.assertEqual(len(feedback.study_tips), 1)

    @patch('api.tasks.requests.post')
    def test_generate_feedback_handles_api_error(self, mock_post):
        """Test handling of Flask API errors"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        try:
            generate_personalised_feedback(self.attempt.id)
        except Exception as e:
            self.fail(f"Task raised exception: {e}")

        self.assertFalse(
            StudentFeedback.objects.filter(user_quest_attempt=self.attempt).exists()
        )

    @patch('api.tasks.requests.post')
    def test_generate_feedback_with_multiple_questions(self, mock_post):
        """Test feedback generation with multiple questions and cognitive levels"""
        question2 = Question.objects.create(
            quest=self.quest,
            text='Implement a hash table',
            number=2,
            max_score=15.0,
            cognitive_level='Create',
            topic='Data Structures'
        )

        correct_ans2 = Answer.objects.create(
            question=question2,
            text='Implementation code',
            is_correct=True,
            reason='Correct'
        )

        wrong_ans2 = Answer.objects.create(
            question=question2,
            text='Wrong implementation',
            is_correct=False,
            reason='Wrong'
        )

        UserAnswerAttempt.objects.create(
            user_quest_attempt=self.attempt,
            question=question2,
            answer=wrong_ans2,
            is_correct=False  # ✅ ADDED
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'quest_summary': {
                'overall_bloom_rating': 2,
                'overall_bloom_level': 'Understand',
                'summary': 'Needs more practice on implementation.'
            },
            'subtopic_feedback': [],
            'study_tips': ['Practice coding.']
        }
        mock_post.return_value = mock_response

        generate_personalised_feedback(self.attempt.id)

        request_data = mock_post.call_args[1]['json']
        self.assertEqual(len(request_data['answers']), 2)

        cognitive_levels = [ans['cognitive_level'] for ans in request_data['answers']]
        self.assertIn('Remember', cognitive_levels)
        self.assertIn('Create', cognitive_levels)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UserQuestAttemptIntegrationTest(BaseTestCase):
    """Test the integration between UserQuestAttempt.save() and tasks"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.academic_year = AcademicYear.objects.create(
            start_year=2025,
            end_year=2026
        )
        self.term = TermFactory(academic_year=self.academic_year)
        self.course = CourseFactory(term=self.term)
        
        self.user = EduquestUserFactory()
        self.course_group = CourseGroupFactory(course=self.course)
        self.quest = QuestFactory(course_group=self.course_group, organiser=self.user)

    @patch('api.tasks.generate_personalised_feedback.delay')
    @patch('api.tasks.update_cognitive_profile.delay')
    def test_save_triggers_tasks_on_submission(self, mock_update_profile, mock_generate_feedback):
        """Test that saving a submitted attempt triggers both tasks"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=False
        )

        attempt.submitted = True
        attempt.save()

        mock_generate_feedback.assert_called_once()
        mock_update_profile.assert_called_once()

    @patch('api.tasks.generate_personalised_feedback.delay')
    @patch('api.tasks.update_cognitive_profile.delay')
    def test_save_does_not_trigger_tasks_on_create(self, mock_update_profile, mock_generate_feedback):
        """Test that creating a new attempt doesn't trigger tasks"""
        UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        mock_generate_feedback.assert_not_called()
        mock_update_profile.assert_not_called()

    @patch('api.tasks.generate_personalised_feedback.delay')
    @patch('api.tasks.update_cognitive_profile.delay')
    def test_save_does_not_trigger_tasks_when_already_submitted(self, mock_update_profile, mock_generate_feedback):
        """Test that re-saving a submitted attempt doesn't trigger tasks again"""
        attempt = UserQuestAttempt.objects.create(
            quest=self.quest,
            student=self.user,
            submitted=True
        )

        attempt.submitted = True
        attempt.save()

        mock_generate_feedback.assert_not_called()
        mock_update_profile.assert_not_called()
