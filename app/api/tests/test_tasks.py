from django.test import TestCase
from django.utils import timezone

from api.models import UserCourseBadge
from api.tasks import award_tutorial_attendance_badges_for_course
from api.tests.factory import (
    BadgeFactory,
    CourseFactory,
    CourseGroupFactory,
    ImageFactory,
    QuestFactory,
    UserCourseGroupEnrollmentFactory,
    UserQuestAttemptFactory,
)


class TutorialAttendanceBadgesTaskTest(TestCase):
    def test_awards_full_and_half_attendance_badges(self):
        course = CourseFactory()
        course_group = CourseGroupFactory(course=course)

        full_badge_image = ImageFactory(name="Full Attendance Badge", filename="full_attendance_badge.svg")
        half_badge_image = ImageFactory(name="Half Attendance Badge", filename="half_attendance_badge.svg")
        BadgeFactory(
            name="Full Attendance",
            description="Full attendance",
            type="Course",
            condition="Submitted attempts for over 70% of tutorials",
            image=full_badge_image,
        )
        BadgeFactory(
            name="Half Attendance",
            description="Half attendance",
            type="Course",
            condition="Submitted attempts for over 50% of tutorials",
            image=half_badge_image,
        )

        student_full = UserCourseGroupEnrollmentFactory(course_group=course_group).student
        student_half = UserCourseGroupEnrollmentFactory(course_group=course_group).student

        tutorial_quests = [
            QuestFactory(course_group=course_group, type="Kahoot!", tutorial_date=timezone.now()),
            QuestFactory(course_group=course_group, type="Kahoot!", tutorial_date=timezone.now()),
            QuestFactory(course_group=course_group, type="Kahoot!", tutorial_date=timezone.now()),
        ]

        for quest in tutorial_quests:
            UserQuestAttemptFactory(student=student_full, quest=quest, submitted=True)

        for quest in tutorial_quests[:2]:
            UserQuestAttemptFactory(student=student_half, quest=quest, submitted=True)

        award_tutorial_attendance_badges_for_course(course.id)

        full_badge_awarded = UserCourseBadge.objects.filter(
            user_course_group_enrollment__student=student_full,
            badge__name="Full Attendance",
        ).exists()
        half_badge_awarded = UserCourseBadge.objects.filter(
            user_course_group_enrollment__student=student_half,
            badge__name="Half Attendance",
        ).exists()

        self.assertTrue(full_badge_awarded)
        self.assertTrue(half_badge_awarded)
