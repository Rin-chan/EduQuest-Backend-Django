# This file contains the template to create the objects in the database.
import datetime
from django.utils import timezone
import pytz


image_list = [
    {"name": "Cloud Computing", "filename": "cloud_computing.svg"},
    {"name": "Introduction to Data Science & Artificial Intelligence", "filename": "intro_to_data_science_and_ai.svg"},
    {"name": "Artificial Intelligence", "filename": "artificial_intelligence.svg"},
    {"name": "Computer Organisation & Architecture", "filename": "computer_organisation_and_architecture.svg"},
    {"name": "Computer Security", "filename": "computer_security.svg"},
    {"name": "Data Structures & Algorithms", "filename": "data_structures_and_algorithms.svg"},
    {"name": "Introduction to Databases", "filename": "intro_to_databases.svg"},
    {"name": "Introduction to Computational Thinking and Programming", "filename": "intro_to_computational_thinking_and_programming.svg"},
    {"name": "Probability & Statistics for Computing", "filename": "probability_and_statistics_for_computing.svg"},
    {"name": "First Attempt Badge", "filename": "first_attempt_badge.svg"},
    {"name": "Completionist Badge", "filename": "completionist_badge.svg"},
    {"name": "Expert Badge", "filename": "expert_badge.svg"},
    {"name": "Speedster Badge", "filename": "speedster_badge.svg"},
    {"name": "Perfectionist Badge", "filename": "perfectionist_badge.svg"},
    {"name": "Full Attendance Badge", "filename": "full_attendance_badge.svg"},
    {"name": "Half Attendance Badge", "filename": "half_attendance_badge.svg"},
    {"name": "Private Course", "filename": "private_course.svg"},
    {"name": "Private Quest", "filename": "private_quest.svg"},
    {"name": "Kahoot Quest", "filename": "kahoot.svg"},
    {"name": "Eduquest MCQ Quest", "filename": "multiple_choice.svg"},
    {"name": "Wooclap Quest", "filename": "wooclap.svg"},
]

badge_list = [
    {
        "name": "First Attempt",
        "description": "Awarded upon completing any quest for the first time.",
        "type": "Quest",
        "image": "first_attempt_badge.svg",
        "condition": "Non-private quest, Did not attempt any quest before"
    },
    {
        "name": "Completionist",
        "description": "Awarded upon completing all quests within a course after the course has ended.",
        "type": "Course",
        "image": "completionist_badge.svg",
        "condition":  "Non-private quest, Completed all quests within a course, Course has ended and set to Expired by the instructor"
    },
    {
        "name": "Expert",
        "description": "Awarded for achieving the highest score on a quest among all users.",
        "type": "Quest",
        "image": "expert_badge.svg",
        "condition": "Non-private quest, Achieved the highest score among all users, Score > 0, Quest has "
                     "ended and expired"
    },
    {
        "name": "Speedster",
        "description": "Awarded for achieving shortest overall time.",
        "type": "Quest",
        "image": "speedster_badge.svg",
        "condition": "Non-private quest, Has the shortest overall time, Be one of the top three scores, "
                     "Score > 0, Quest has ended and expired"
    },
    {
        "name": "Perfectionist",
        "description": "Awarded for achieving a perfect score on a quiz.",
        "type": "Quest",
        "image": "perfectionist_badge.svg",
        "condition": "Non-private Quest, Achieved a perfect score"
    },
    {
        "name": "Full Attendance",
        "description": "Awarded for completing over 70% of tutorial quests in a course group.",
        "type": "Course",
        "image": "full_attendance_badge.svg",
        "condition": "Non-private tutorial quest, Submitted attempts for over 70% of tutorials"
    },
    {
        "name": "Half Attendance",
        "description": "Awarded for completing over 50% of tutorial quests in a course group.",
        "type": "Course",
        "image": "half_attendance_badge.svg",
        "condition": "Non-private tutorial quest, Submitted attempts for over 50% of tutorials"
    }
]

year_list = [
    {
        "start_year": 2024,
        "end_year": 2025
    }
]


sg_timezone = pytz.timezone('Asia/Singapore')

term_list = [
    {
        "name": "Semester 1",
        "start_date": timezone.make_aware(datetime.datetime(2024, 8, 12, 0, 0, 0), sg_timezone),
        "end_date": timezone.make_aware(datetime.datetime(2024, 12, 6, 23, 59, 59), sg_timezone)
    },
    {
        "name": "Semester 2",
        "start_date": timezone.make_aware(datetime.datetime(2025, 1, 13, 0, 0, 0), sg_timezone),
        "end_date": timezone.make_aware(datetime.datetime(2025, 5, 9, 23, 59, 59), sg_timezone)
    }
]

course_list = [
    {"name": "Probability & Statistics for Computing", "code": "SC2000", "description": "This course provides the basic mathematical foundations for probability and statistics which are necessary for anyone pursuing a computing degree course. The course covers the basic concepts of probability and statistics, and their applications in computing."},
    {"name": "Introduction to Computational Thinking and Programming", "code": "SC1003", "description": "The aim of this course is hence to take students with no prior experience of thinking in a computational manner to a point where you can derive simple algorithms and code the programs to solve some basic problems in your domain of studies. Student will also learn about basic program construct and simple data structures."},
    {"name": "Introduction to Databases", "code": "SC2207", "description": "Learn about database design, management, and SQL. Understand relational databases, normalization, indexing, and transactions, and gain practical experience with database management systems."}
]

course_group_list = [
    {"course_code": "SC2000", "name": "SCED", "session_day": "Monday", "session_time": "2:30 PM - 3:30 PM"},
    {"course_code": "SC2000", "name": "SCS3", "session_day": "Tuesday", "session_time": "5:30 PM - 6:30 PM"},
    {"course_code": "SC2000", "name": "SCSH", "session_day": "Tuesday", "session_time": "10:30 AM - 11:30 AM"},
    {"course_code": "SC2000", "name": "SCSI", "session_day": "Thursday", "session_time": "2:30 PM - 3:30 PM"},
    {"course_code": "SC2000", "name": "SCSJ", "session_day": "Thursday", "session_time": "9:30 AM - 10:30 AM"},
    {"course_code": "SC1003", "name": "SWLA", "session_day": "Friday", "session_time": "10:30 AM - 11:30 AM"},
    {"course_code": "SC2207", "name": "TEL1", "session_day": "Wednesday", "session_time": "12:30 PM - 1:30 PM"},
]
