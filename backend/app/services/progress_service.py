"""Service – Enrollment & Progress business logic (SDD §4.3)."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.utils import utc_now
from app.models.models import Enrollment, Lesson, QuizAttempt, User
from app.repositories.course_repository import CourseRepository, LessonRepository
from app.repositories.progress_repository import EnrollmentRepository, LessonProgressRepository
from app.repositories.quiz_repository import QuizAttemptRepository, QuizRepository
from app.schemas.course import CourseResponse
from app.schemas.progress import (
    CompleteLessonRequest,
    CompleteLessonResponse,
    CourseProgressResponse,
    EnrollmentResponse,
    LessonProgressState,
    MyCourseResponse,
    QuizProgressState,
    SaveLessonPositionRequest,
)
from app.services.permissions import bad_request, forbidden, get_course_or_404, not_found


def summarize_attempts(attempts: list[QuizAttempt]) -> dict:
    """Attempts used, best score and pass state of one learner on one quiz."""
    scores = [a.score for a in attempts if a.score is not None]
    return {
        "attempts_used": len(attempts),
        "best_score": max(scores) if scores else None,
        "is_passed": any(a.is_passed for a in attempts),
    }


class ProgressCalculator:
    """Recomputes `enrollments.progress_percentage`.

    Progress = (completed lessons + passed quizzes) / (total lessons + total quizzes) * 100.
    Once a course is COMPLETED it stays completed, even if the instructor adds content later.
    """

    def __init__(self, db: Session):
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.progress_repo = LessonProgressRepository(db)
        self.quiz_repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)

    def recalculate(self, enrollment: Enrollment) -> Enrollment:
        total_lessons = self.course_repo.count_lessons(enrollment.course_id)
        quiz_ids = [q.id for q in self.quiz_repo.get_by_course(enrollment.course_id)]
        completed_lessons = self.progress_repo.count_completed(enrollment.id)
        passed_quizzes = self.attempt_repo.count_passed_quizzes(enrollment.user_id, quiz_ids)

        total = total_lessons + len(quiz_ids)
        done = completed_lessons + passed_quizzes
        pct = round(min(done / total * 100, 100.0), 2) if total > 0 else 0.0

        update: dict = {"progress_percentage": pct}
        if pct >= 100.0 and enrollment.status != "COMPLETED":
            update["status"] = "COMPLETED"
            update["completed_at"] = utc_now()
        return self.enrollment_repo.update(enrollment, **update)

    def recalculate_course(self, course_id: int) -> None:
        """Refresh every enrollment of a course after its structure changed."""
        for enrollment in self.enrollment_repo.get_by_course(course_id):
            self.recalculate(enrollment)


class EnrollmentService:
    def __init__(self, db: Session):
        self.db = db
        self.enrollment_repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.progress_repo = LessonProgressRepository(db)
        self.quiz_repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.calculator = ProgressCalculator(db)

    # ── Enrollment ────────────────────────────────────────────────────────────
    def enroll(self, user: User, course_id: int) -> Enrollment:
        course = get_course_or_404(self.db, course_id)
        if course.status != "PUBLISHED":
            raise bad_request("Chỉ có thể đăng ký các khóa học đã xuất bản.")
        if course.instructor_id == user.id:
            raise bad_request("Bạn không thể đăng ký khóa học do chính mình giảng dạy.")
        if self.enrollment_repo.get_by_user_and_course(user.id, course_id):
            raise bad_request("Bạn đã đăng ký khóa học này rồi.")
        return self.enrollment_repo.create(user_id=user.id, course_id=course_id)

    def get_my_courses(self, user_id: int, status_filter: str | None = None) -> list[MyCourseResponse]:
        return [
            MyCourseResponse(
                enrollment=EnrollmentResponse.model_validate(e),
                course=CourseResponse.model_validate(e.course),
            )
            for e in self.enrollment_repo.get_by_user(user_id, status_filter)
        ]

    # ── Progress ──────────────────────────────────────────────────────────────
    def get_course_progress(self, user_id: int, course_id: int) -> CourseProgressResponse:
        enrollment = self.enrollment_repo.get_by_user_and_course(user_id, course_id)
        if not enrollment:
            raise forbidden("Bạn chưa đăng ký khóa học này.")
        enrollment = self.calculator.recalculate(enrollment)

        records = {p.lesson_id: p for p in self.progress_repo.get_all_for_enrollment(enrollment.id)}
        lessons = [
            LessonProgressState.model_validate(records[lid]) if lid in records else LessonProgressState(lesson_id=lid)
            for lid in self.course_repo.get_lesson_ids(course_id)
        ]

        quizzes = self.quiz_repo.get_by_course(course_id)
        attempts = self.attempt_repo.get_by_user_and_quizzes(user_id, [q.id for q in quizzes])
        quiz_states = [
            QuizProgressState(
                quiz_id=q.id,
                title=q.title,
                chapter_id=q.chapter_id,
                max_attempts=q.max_attempts,
                **summarize_attempts([a for a in attempts if a.quiz_id == q.id]),
            )
            for q in quizzes
        ]

        completed_lessons = sum(1 for lp in lessons if lp.is_completed)
        passed_quizzes = sum(1 for qs in quiz_states if qs.is_passed)
        return CourseProgressResponse(
            enrollment=EnrollmentResponse.model_validate(enrollment),
            total_items=len(lessons) + len(quiz_states),
            completed_items=completed_lessons + passed_quizzes,
            total_lessons=len(lessons),
            completed_lessons=completed_lessons,
            lessons=lessons,
            quizzes=quiz_states,
        )

    def _get_lesson_and_enrollment(self, user_id: int, lesson_id: int) -> tuple[Lesson, Enrollment]:
        lesson = self.lesson_repo.get_with_course(lesson_id)
        if not lesson:
            raise not_found("Bài học không tồn tại.")
        enrollment = self.enrollment_repo.get_by_user_and_course(user_id, lesson.chapter.course_id)
        if not enrollment:
            raise forbidden("Bạn chưa đăng ký khóa học chứa bài học này.")
        return lesson, enrollment

    def get_lesson_progress(self, user_id: int, lesson_id: int) -> LessonProgressState:
        """Used by the player to restore the last watched position."""
        _, enrollment = self._get_lesson_and_enrollment(user_id, lesson_id)
        record = self.progress_repo.get_by_enrollment_and_lesson(enrollment.id, lesson_id)
        if record is None:
            return LessonProgressState(lesson_id=lesson_id)
        return LessonProgressState.model_validate(record)

    @staticmethod
    def _clamp_position(lesson: Lesson, second: int) -> int:
        if lesson.duration_seconds > 0:
            return min(second, lesson.duration_seconds)
        return second

    def save_position(self, user_id: int, lesson_id: int, data: SaveLessonPositionRequest) -> LessonProgressState:
        """Periodically called by the player to remember the watch position (no completion)."""
        lesson, enrollment = self._get_lesson_and_enrollment(user_id, lesson_id)
        record = self.progress_repo.upsert(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            last_watched_second=self._clamp_position(lesson, data.last_watched_second),
            is_completed=False,
        )
        return LessonProgressState.model_validate(record)

    def complete_lesson(self, user_id: int, lesson_id: int, data: CompleteLessonRequest) -> CompleteLessonResponse:
        lesson, enrollment = self._get_lesson_and_enrollment(user_id, lesson_id)

        # Server-side guard of the ">= 80% watched" rule for videos with a known duration
        if lesson.lesson_type == "VIDEO" and lesson.duration_seconds > 0:
            required = lesson.duration_seconds * settings.VIDEO_COMPLETION_THRESHOLD
            if data.last_watched_second < required:
                raise bad_request(
                    f"Cần xem tối thiểu {int(settings.VIDEO_COMPLETION_THRESHOLD * 100)}% thời lượng video để hoàn thành bài học."
                )

        self.progress_repo.upsert(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            last_watched_second=self._clamp_position(lesson, data.last_watched_second),
            is_completed=True,
        )
        enrollment = self.calculator.recalculate(enrollment)

        return CompleteLessonResponse(
            lesson_id=lesson_id,
            is_completed=True,
            course_progress_percentage=enrollment.progress_percentage,
            is_course_completed=enrollment.status == "COMPLETED",
        )
