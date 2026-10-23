// One function per backend endpoint (backend/app/api/v1/endpoints/*).
import { api, apiWithMessage } from "./api-client";
import type {
  Category,
  Chapter,
  CompleteLessonResult,
  Course,
  CourseDetail,
  CourseProgress,
  CourseStatus,
  Enrollment,
  Lesson,
  LessonProgressState,
  LessonType,
  MyCourse,
  Paginated,
  Question,
  QuestionInput,
  Quiz,
  QuizAttempt,
  QuizAttemptWithStudent,
  QuizDetail,
  QuizInput,
  QuizResult,
  QuizStart,
  QuizStudent,
  Role,
  StudentProgress,
  UploadedFile,
  User,
  UserBrief,
} from "./types";

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (body: { email: string; password: string }) =>
    api<{ access_token: string; user: UserBrief }>({ method: "POST", url: "/auth/login", data: body }),
  register: (body: { email: string; password: string; full_name: string }) =>
    api<UserBrief>({ method: "POST", url: "/auth/register", data: body }),
  logout: () => api<null>({ method: "POST", url: "/auth/logout" }),
  me: () => api<User>({ url: "/auth/me" }),
  updateProfile: (body: { full_name?: string; avatar_url?: string }) =>
    apiWithMessage<User>({ method: "PUT", url: "/auth/profile", data: body }),
  changePassword: (body: { current_password: string; new_password: string }) =>
    apiWithMessage<null>({ method: "POST", url: "/auth/change-password", data: body }),
};

// ── Categories ────────────────────────────────────────────────────────────────
export const categoryApi = {
  list: () => api<Category[]>({ url: "/categories" }),
  create: (body: { name: string; slug: string; description?: string | null }) =>
    apiWithMessage<Category>({ method: "POST", url: "/admin/categories", data: body }),
  update: (id: number, body: { name?: string; slug?: string; description?: string | null }) =>
    apiWithMessage<Category>({ method: "PUT", url: `/admin/categories/${id}`, data: body }),
  remove: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/admin/categories/${id}` }),
};

// ── Public courses ────────────────────────────────────────────────────────────
export interface CourseQuery {
  page?: number;
  limit?: number;
  category_id?: number;
  search?: string;
}

export const courseApi = {
  list: (params: CourseQuery) => api<Paginated<Course>>({ url: "/courses", params }),
  detail: (id: number) => api<CourseDetail>({ url: `/courses/${id}` }),
  enroll: (id: number) => apiWithMessage<Enrollment>({ method: "POST", url: `/courses/${id}/enroll` }),
};

// ── Learning & progress ───────────────────────────────────────────────────────
export const learnApi = {
  myCourses: (status?: "IN_PROGRESS" | "COMPLETED") => api<MyCourse[]>({ url: "/me/courses", params: { status } }),
  courseProgress: (courseId: number) => api<CourseProgress>({ url: `/courses/${courseId}/progress` }),
  lesson: (lessonId: number) => api<Lesson>({ url: `/lessons/${lessonId}` }),
  lessonProgress: (lessonId: number) => api<LessonProgressState>({ url: `/lessons/${lessonId}/progress` }),
  savePosition: (lessonId: number, last_watched_second: number) =>
    api<LessonProgressState>({ method: "PUT", url: `/lessons/${lessonId}/progress`, data: { last_watched_second } }),
  complete: (lessonId: number, last_watched_second: number) =>
    apiWithMessage<CompleteLessonResult>({
      method: "POST",
      url: `/lessons/${lessonId}/complete`,
      data: { last_watched_second },
    }),
};

// ── Quizzes (learner) ─────────────────────────────────────────────────────────
export const quizApi = {
  forCourse: (courseId: number) => api<QuizStudent[]>({ url: `/courses/${courseId}/quizzes` }),
  start: (quizId: number) => api<QuizStart>({ method: "POST", url: `/quizzes/${quizId}/start` }),
  submit: (attemptId: number, answers: { question_id: number; selected_option_ids: number[] }[]) =>
    apiWithMessage<QuizResult>({ method: "POST", url: `/quizzes/attempts/${attemptId}/submit`, data: { answers } }),
  attempt: (attemptId: number) => api<QuizResult>({ url: `/quizzes/attempts/${attemptId}` }),
  myAttempts: (quizId: number) => api<QuizAttempt[]>({ url: `/quizzes/${quizId}/attempts` }),
};

// ── Instructor ────────────────────────────────────────────────────────────────
export interface CourseInput {
  title: string;
  category_id: number;
  description?: string | null;
  thumbnail_url?: string | null;
}

export interface LessonInput {
  title: string;
  lesson_type: LessonType;
  video_url?: string | null;
  document_url?: string | null;
  duration_seconds: number;
  is_free_preview: boolean;
  order_index?: number;
}

export const instructorApi = {
  courses: (params: { page?: number; limit?: number; status?: CourseStatus }) =>
    api<Paginated<Course>>({ url: "/instructor/courses", params }),
  course: (id: number) => api<CourseDetail>({ url: `/instructor/courses/${id}` }),
  createCourse: (body: CourseInput) => apiWithMessage<Course>({ method: "POST", url: "/instructor/courses", data: body }),
  updateCourse: (id: number, body: Partial<CourseInput>) =>
    apiWithMessage<Course>({ method: "PUT", url: `/instructor/courses/${id}`, data: body }),
  deleteCourse: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/instructor/courses/${id}` }),
  submitReview: (id: number) => apiWithMessage<Course>({ method: "POST", url: `/instructor/courses/${id}/submit-review` }),

  createChapter: (courseId: number, body: { title: string }) =>
    apiWithMessage<Chapter>({ method: "POST", url: `/instructor/courses/${courseId}/chapters`, data: body }),
  updateChapter: (id: number, body: { title?: string; order_index?: number }) =>
    apiWithMessage<Chapter>({ method: "PUT", url: `/instructor/chapters/${id}`, data: body }),
  deleteChapter: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/instructor/chapters/${id}` }),

  createLesson: (chapterId: number, body: LessonInput) =>
    apiWithMessage<Lesson>({ method: "POST", url: `/instructor/chapters/${chapterId}/lessons`, data: body }),
  updateLesson: (id: number, body: Partial<LessonInput>) =>
    apiWithMessage<Lesson>({ method: "PUT", url: `/instructor/lessons/${id}`, data: body }),
  deleteLesson: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/instructor/lessons/${id}` }),

  students: (courseId: number) => api<StudentProgress[]>({ url: `/instructor/courses/${courseId}/students` }),
  enrollStudent: (courseId: number, student_email: string) =>
    apiWithMessage<Enrollment>({
      method: "POST",
      url: `/instructor/courses/${courseId}/enroll-student`,
      data: { student_email },
    }),

  questions: (params: { page?: number; limit?: number; search?: string }) =>
    api<Paginated<Question>>({ url: "/instructor/questions", params }),
  createQuestion: (body: QuestionInput) =>
    apiWithMessage<Question>({ method: "POST", url: "/instructor/questions", data: body }),
  updateQuestion: (id: number, body: QuestionInput) =>
    apiWithMessage<Question>({ method: "PUT", url: `/instructor/questions/${id}`, data: body }),
  deleteQuestion: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/instructor/questions/${id}` }),

  quizzes: (courseId: number) => api<Quiz[]>({ url: `/instructor/courses/${courseId}/quizzes` }),
  quiz: (id: number) => api<QuizDetail>({ url: `/instructor/quizzes/${id}` }),
  createQuiz: (body: QuizInput) => apiWithMessage<Quiz>({ method: "POST", url: "/instructor/quizzes", data: body }),
  updateQuiz: (id: number, body: Partial<QuizInput>) =>
    apiWithMessage<Quiz>({ method: "PUT", url: `/instructor/quizzes/${id}`, data: body }),
  deleteQuiz: (id: number) => apiWithMessage<null>({ method: "DELETE", url: `/instructor/quizzes/${id}` }),
  quizAttempts: (id: number) => api<QuizAttemptWithStudent[]>({ url: `/instructor/quizzes/${id}/attempts` }),
};

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminApi = {
  users: (params: { page?: number; limit?: number; role?: Role; search?: string; is_active?: boolean }) =>
    api<Paginated<User>>({ url: "/admin/users", params }),
  setStatus: (id: number, is_active: boolean) =>
    apiWithMessage<User>({ method: "PATCH", url: `/admin/users/${id}/status`, data: { is_active } }),
  setRole: (id: number, role: Role) =>
    apiWithMessage<User>({ method: "PATCH", url: `/admin/users/${id}/role`, data: { role } }),

  courses: (params: { page?: number; limit?: number; status?: CourseStatus; search?: string; category_id?: number }) =>
    api<Paginated<Course>>({ url: "/admin/courses", params }),
  course: (id: number) => api<CourseDetail>({ url: `/admin/courses/${id}` }),
  approve: (id: number) => apiWithMessage<Course>({ method: "POST", url: `/admin/courses/${id}/approve` }),
  reject: (id: number, reason: string) =>
    apiWithMessage<Course>({ method: "POST", url: `/admin/courses/${id}/reject`, data: { reason } }),
};

// ── Storage ───────────────────────────────────────────────────────────────────
export const storageApi = {
  upload: (file: File, bucket: "materials" | "thumbnails") => {
    const form = new FormData();
    form.append("file", file);
    form.append("bucket", bucket);
    return api<UploadedFile>({ method: "POST", url: "/storage/upload", data: form });
  },
  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiWithMessage<{ file: UploadedFile; user: User }>({
      method: "POST",
      url: "/storage/upload-avatar",
      data: form,
    });
  },
};
