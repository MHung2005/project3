"""Enrollment, progress tracking and quiz tests (SDD §4.3, §4.4, §8.1-2)."""
from datetime import timedelta

from app.models.models import QuizAttempt
from tests.conftest import auth_header, make_instructor, make_student, published_course

QUESTION = {
    "content": "Giao thức nào được sử dụng để truyền tải web an toàn?",
    "question_type": "SINGLE_CHOICE",
    "explanation": "HTTPS mã hóa lưu lượng bằng TLS/SSL.",
    "options": [
        {"content": "HTTP", "is_correct": False, "order_index": 1},
        {"content": "HTTPS", "is_correct": True, "order_index": 2},
        {"content": "FTP", "is_correct": False, "order_index": 3},
    ],
}
MULTI = {
    "content": "Những framework nào dùng cho Backend Python?",
    "question_type": "MULTIPLE_CHOICE",
    "options": [
        {"content": "FastAPI", "is_correct": True, "order_index": 1},
        {"content": "Django", "is_correct": True, "order_index": 2},
        {"content": "React", "is_correct": False, "order_index": 3},
    ],
}


def _setup(client, max_attempts=3, passing_score=8.0):
    teacher = make_instructor(client)
    th = auth_header(teacher)
    data = published_course(client, teacher)
    q1 = client.post("/api/v1/instructor/questions", json=QUESTION, headers=th).json()["data"]
    q2 = client.post("/api/v1/instructor/questions", json=MULTI, headers=th).json()["data"]
    quiz = client.post(
        "/api/v1/instructor/quizzes",
        json={
            "course_id": data["course"]["id"],
            "chapter_id": data["chapter"]["id"],
            "title": "Kiểm tra Chương 1",
            "duration_minutes": 15,
            "max_attempts": max_attempts,
            "passing_score": passing_score,
            "question_ids": [q1["id"], q2["id"]],
        },
        headers=th,
    )
    assert quiz.status_code == 201, quiz.text
    student = make_student(client)
    sh = auth_header(student)
    assert client.post(f"/api/v1/courses/{data['course']['id']}/enroll", headers=sh).status_code == 201
    return {**data, "th": th, "sh": sh, "q1": q1, "q2": q2, "quiz": quiz.json()["data"]}


def _correct_answers(ctx):
    q1_correct = [o["id"] for o in ctx["q1"]["options"] if o["is_correct"]]
    q2_correct = [o["id"] for o in ctx["q2"]["options"] if o["is_correct"]]
    return [
        {"question_id": ctx["q1"]["id"], "selected_option_ids": q1_correct},
        {"question_id": ctx["q2"]["id"], "selected_option_ids": q2_correct},
    ]


def test_question_validation(client):
    th = auth_header(make_instructor(client))
    bad = {**QUESTION, "options": [{"content": "A", "is_correct": True}, {"content": "B", "is_correct": True}]}
    assert client.post("/api/v1/instructor/questions", json=bad, headers=th).status_code == 400
    none = {**QUESTION, "options": [{"content": "A"}, {"content": "B"}]}
    assert client.post("/api/v1/instructor/questions", json=none, headers=th).status_code == 400


def test_enroll_rules(client):
    ctx = _setup(client)
    course_id = ctx["course"]["id"]
    assert client.post(f"/api/v1/courses/{course_id}/enroll", headers=ctx["sh"]).status_code == 400  # twice
    assert client.post(f"/api/v1/courses/{course_id}/enroll", headers=ctx["th"]).status_code == 400  # own course

    my = client.get("/api/v1/me/courses", headers=ctx["sh"]).json()["data"]
    assert len(my) == 1 and my[0]["course"]["id"] == course_id


def test_lesson_progress_flow(client):
    ctx = _setup(client)
    sh, video, doc = ctx["sh"], ctx["video"], ctx["doc"]
    course_id = ctx["course"]["id"]

    assert client.get(f"/api/v1/lessons/{video['id']}/progress", headers=sh).json()["data"]["last_watched_second"] == 0
    client.put(f"/api/v1/lessons/{video['id']}/progress", json={"last_watched_second": 120}, headers=sh)
    state = client.get(f"/api/v1/lessons/{video['id']}/progress", headers=sh).json()["data"]
    assert state == {**state, "last_watched_second": 120, "is_completed": False}

    # < 80% of 600s is rejected
    r = client.post(f"/api/v1/lessons/{video['id']}/complete", json={"last_watched_second": 300}, headers=sh)
    assert r.status_code == 400

    r = client.post(f"/api/v1/lessons/{video['id']}/complete", json={"last_watched_second": 520}, headers=sh)
    assert r.status_code == 200
    # 3 items: 2 lessons + 1 quiz
    assert r.json()["data"] == {
        "lesson_id": video["id"], "is_completed": True, "course_progress_percentage": 33.33, "is_course_completed": False,
    }

    r = client.post(f"/api/v1/lessons/{doc['id']}/complete", json={}, headers=sh)
    assert r.json()["data"]["course_progress_percentage"] == 66.67

    # Completion is sticky – saving an earlier position does not undo it
    client.put(f"/api/v1/lessons/{video['id']}/progress", json={"last_watched_second": 10}, headers=sh)
    progress = client.get(f"/api/v1/courses/{course_id}/progress", headers=sh).json()["data"]
    assert progress["completed_lessons"] == 2 and progress["total_items"] == 3
    assert progress["enrollment"]["status"] == "IN_PROGRESS"

    # Not enrolled → forbidden
    other = auth_header(make_student(client, "other@example.com"))
    assert client.post(f"/api/v1/lessons/{doc['id']}/complete", json={}, headers=other).status_code == 403


def test_quiz_start_does_not_leak_answers(client):
    ctx = _setup(client)
    r = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=ctx["sh"])
    assert r.status_code == 200
    raw = r.text
    assert "is_correct" not in raw and "explanation" not in raw
    data = r.json()["data"]
    assert data["attempt_number"] == 1 and len(data["questions"]) == 2

    # Re-starting resumes the same attempt instead of consuming a new one
    again = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=ctx["sh"]).json()["data"]
    assert again["attempt_id"] == data["attempt_id"]


def test_quiz_submit_grading_and_course_completion(client):
    ctx = _setup(client)
    sh = ctx["sh"]
    client.post(f"/api/v1/lessons/{ctx['video']['id']}/complete", json={"last_watched_second": 600}, headers=sh)
    client.post(f"/api/v1/lessons/{ctx['doc']['id']}/complete", json={}, headers=sh)

    # Attempt 1: only half right → 5.0, fail
    attempt = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=sh).json()["data"]
    answers = _correct_answers(ctx)
    answers[1]["selected_option_ids"] = answers[1]["selected_option_ids"][:1]  # partial multi-choice = wrong
    r = client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": answers}, headers=sh)
    result = r.json()["data"]
    assert result["score"] == 5.0 and result["is_passed"] is False and result["status"] == "SUBMITTED"
    assert result["review"][0]["explanation"] == QUESTION["explanation"]

    # Cannot submit twice
    r = client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": answers}, headers=sh)
    assert r.status_code == 400

    # Attempt 2: all correct → 10.0, pass → course complete
    attempt = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=sh).json()["data"]
    assert attempt["attempt_number"] == 2
    r = client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": _correct_answers(ctx)}, headers=sh)
    assert r.json()["data"]["score"] == 10.0 and r.json()["data"]["is_passed"] is True

    progress = client.get(f"/api/v1/courses/{ctx['course']['id']}/progress", headers=sh).json()["data"]
    assert progress["enrollment"]["progress_percentage"] == 100.0
    assert progress["enrollment"]["status"] == "COMPLETED"
    assert progress["quizzes"][0]["best_score"] == 10.0

    # Review can be re-opened later
    review = client.get(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}", headers=sh).json()["data"]
    assert review["score"] == 10.0 and all(item["is_correct"] for item in review["review"])

    # Instructor sees results; quiz with attempts cannot be deleted
    results = client.get(f"/api/v1/instructor/quizzes/{ctx['quiz']['id']}/attempts", headers=ctx["th"]).json()["data"]
    assert len(results) == 2
    assert client.delete(f"/api/v1/instructor/quizzes/{ctx['quiz']['id']}", headers=ctx["th"]).status_code == 400
    # Question used in a quiz cannot be deleted
    assert client.delete(f"/api/v1/instructor/questions/{ctx['q1']['id']}", headers=ctx["th"]).status_code == 400


def test_quiz_max_attempts(client):
    ctx = _setup(client, max_attempts=1)
    sh = ctx["sh"]
    attempt = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=sh).json()["data"]
    client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": []}, headers=sh)
    r = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=sh)
    assert r.status_code == 403 and "hết số lượt" in r.json()["message"]


def test_quiz_submit_after_time_limit(client, db):
    ctx = _setup(client)
    sh = ctx["sh"]
    attempt = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=sh).json()["data"]

    row = db.get(QuizAttempt, attempt["attempt_id"])
    row.started_at = row.started_at - timedelta(minutes=30)
    db.commit()

    r = client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": _correct_answers(ctx)}, headers=sh)
    data = r.json()["data"]
    assert data["status"] == "TIMEOUT" and data["score"] == 0.0 and data["is_passed"] is False


def test_quiz_requires_enrollment_and_ownership(client):
    ctx = _setup(client)
    outsider = auth_header(make_student(client, "outsider@example.com"))
    assert client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=outsider).status_code == 403

    attempt = client.post(f"/api/v1/quizzes/{ctx['quiz']['id']}/start", headers=ctx["sh"]).json()["data"]
    r = client.post(f"/api/v1/quizzes/attempts/{attempt['attempt_id']}/submit", json={"answers": []}, headers=outsider)
    assert r.status_code == 403

    # Another instructor cannot put foreign questions into their quiz
    other_teacher = auth_header(make_instructor(client, "t2@example.com"))
    r = client.post(
        "/api/v1/instructor/quizzes",
        json={"course_id": ctx["course"]["id"], "title": "Hack", "question_ids": [ctx["q1"]["id"]]},
        headers=other_teacher,
    )
    assert r.status_code == 403


def test_learner_quiz_list(client):
    ctx = _setup(client)
    quizzes = client.get(f"/api/v1/courses/{ctx['course']['id']}/quizzes", headers=ctx["sh"]).json()["data"]
    assert quizzes[0]["question_count"] == 2 and quizzes[0]["attempts_used"] == 0
