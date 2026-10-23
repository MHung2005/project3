// Types mirror backend/app/schemas/*. Datetimes are naive UTC strings – parse with `parseDate`.

export type Role = "STUDENT" | "INSTRUCTOR" | "ADMIN";
export type CourseStatus = "DRAFT" | "PENDING" | "PUBLISHED" | "REJECTED";
export type LessonType = "VIDEO" | "DOCUMENT";
export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE";

export interface Envelope<T> {
  success: boolean;
  message: string;
  data: T;
  error: unknown;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface UserBrief {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  avatar_url: string | null;
}

export interface User extends UserBrief {
  is_active: boolean;
  created_at: string;
}

export interface InstructorBrief {
  id: number;
  full_name: string;
  avatar_url: string | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
}

export interface Course {
  id: number;
  instructor_id: number;
  category_id: number;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  status: CourseStatus;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
  instructor: InstructorBrief | null;
  category: Pick<Category, "id" | "name" | "slug"> | null;
}

export interface Lesson {
  id: number;
  chapter_id: number;
  title: string;
  lesson_type: LessonType;
  video_url: string | null;
  document_url: string | null;
  duration_seconds: number;
  order_index: number;
  is_free_preview: boolean;
  created_at: string;
  is_locked: boolean;
  youtube_video_id: string | null;
}

export interface Chapter {
  id: number;
  course_id: number;
  title: string;
  order_index: number;
  created_at: string;
  lessons: Lesson[];
}

export interface QuizBrief {
  id: number;
  chapter_id: number | null;
  title: string;
  duration_minutes: number;
  max_attempts: number;
  passing_score: number;
}

export interface CourseDetail extends Course {
  chapters: Chapter[];
  quizzes: QuizBrief[];
  total_lessons: number;
  total_duration_seconds: number;
  enrollment_count: number;
  is_enrolled: boolean;
}

export interface Enrollment {
  id: number;
  user_id: number;
  course_id: number;
  enrolled_at: string;
  status: "IN_PROGRESS" | "COMPLETED";
  progress_percentage: number;
  completed_at: string | null;
}

export interface MyCourse {
  enrollment: Enrollment;
  course: Course;
}

export interface LessonProgressState {
  lesson_id: number;
  is_completed: boolean;
  last_watched_second: number;
  completed_at: string | null;
}

export interface QuizProgressState {
  quiz_id: number;
  title: string;
  chapter_id: number | null;
  attempts_used: number;
  max_attempts: number;
  best_score: number | null;
  is_passed: boolean;
}

export interface CourseProgress {
  enrollment: Enrollment;
  total_items: number;
  completed_items: number;
  total_lessons: number;
  completed_lessons: number;
  lessons: LessonProgressState[];
  quizzes: QuizProgressState[];
}

export interface CompleteLessonResult {
  lesson_id: number;
  is_completed: boolean;
  course_progress_percentage: number;
  is_course_completed: boolean;
}

export interface StudentProgress {
  user_id: number;
  email: string;
  full_name: string;
  avatar_url: string | null;
  enrolled_at: string;
  progress_percentage: number;
  completed_lessons: number;
  total_lessons: number;
  status: "IN_PROGRESS" | "COMPLETED";
  completed_at: string | null;
}

export interface QuestionOption {
  id: number;
  question_id: number;
  content: string;
  is_correct: boolean;
  order_index: number;
}

export interface Question {
  id: number;
  instructor_id: number;
  content: string;
  question_type: QuestionType;
  explanation: string | null;
  created_at: string;
  options: QuestionOption[];
}

export interface QuestionOptionInput {
  content: string;
  is_correct: boolean;
  order_index: number;
}

export interface QuestionInput {
  content: string;
  question_type: QuestionType;
  explanation: string | null;
  options: QuestionOptionInput[];
}

export interface Quiz {
  id: number;
  course_id: number;
  chapter_id: number | null;
  title: string;
  description: string | null;
  duration_minutes: number;
  max_attempts: number;
  passing_score: number;
  created_at: string;
}

export interface QuizDetail extends Quiz {
  questions: { order_index: number; point: number; question: Question }[];
}

export interface QuizStudent extends Quiz {
  question_count: number;
  attempts_used: number;
  best_score: number | null;
  is_passed: boolean;
}

export interface QuizInput {
  course_id: number;
  chapter_id: number | null;
  title: string;
  description: string | null;
  duration_minutes: number;
  max_attempts: number;
  passing_score: number;
  question_ids: number[];
}

export interface SafeQuestion {
  id: number;
  content: string;
  question_type: QuestionType;
  options: { id: number; content: string; order_index: number }[];
}

export interface QuizStart {
  attempt_id: number;
  attempt_number: number;
  duration_minutes: number;
  started_at: string;
  expires_at: string;
  questions: SafeQuestion[];
}

export interface QuestionReview {
  question_id: number;
  content: string;
  point: number;
  options: QuestionOption[];
  user_selected: number[];
  correct_options: number[];
  is_correct: boolean;
  explanation: string | null;
}

export interface QuizResult {
  attempt_id: number;
  status: "SUBMITTED" | "TIMEOUT" | "IN_PROGRESS";
  score: number;
  is_passed: boolean;
  passing_score: number;
  submitted_at: string;
  review: QuestionReview[];
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  user_id: number;
  attempt_number: number;
  started_at: string;
  submitted_at: string | null;
  score: number | null;
  is_passed: boolean;
  status: "SUBMITTED" | "TIMEOUT" | "IN_PROGRESS";
}

export interface QuizAttemptWithStudent extends QuizAttempt {
  full_name: string;
  email: string;
}

export interface UploadedFile {
  file_url: string;
  filename: string;
  file_size: number;
  bucket: string;
  object_name: string;
}
