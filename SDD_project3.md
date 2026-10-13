# ĐẠI HỌC BÁCH KHOA HÀ NỘI
## TRƯỜNG CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG

# TÀI LIỆU THIẾT KẾ HỆ THỐNG (SYSTEM DESIGN DOCUMENT - SDD)
**Đề tài:** Xây dựng nền tảng học trực tuyến hỗ trợ quản lý khóa học và theo dõi tiến độ học tập

- **Giảng viên hướng dẫn:** PGS. TS. Nguyễn Bình Minh
- **Mã lớp học:** 767773
- **Sinh viên thực hiện:** Lê Mạnh Hùng
- **MSSV:** 20235096
- **Ngành/Lớp:** Khoa học máy tính - K68
- **Hà Nội, năm 2026**

---

## Mục lục
1. [Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
   - 1.1 Mục đích tài liệu
   - 1.2 Phạm vi hệ thống
   - 1.3 Thuật ngữ và quy ước
2. [Kiến trúc hệ thống tổng thể](#2-kiến-trúc-hệ-thống-tổng-thể)
   - 2.1 Mô hình kiến trúc phân tầng (3-Tier Layered Architecture)
   - 2.2 Sơ đồ khối kiến trúc hệ thống
   - 2.3 Lựa chọn công nghệ và vai trò
   - 2.4 Cấu trúc mã nguồn Backend (Clean Architecture / Service-Repository)
3. [Thiết kế Cơ sở dữ liệu (Database Design)](#3-thiết-kế-cơ-sở-dữ-liệu-database-design)
   - 3.1 Sơ đồ thực thể liên kết (Entity Relationship Diagram - ERD)
   - 3.2 Chi tiết các bảng dữ liệu (Data Dictionary)
   - 3.3 Thiết kế chỉ mục (Indexes) và ràng buộc toàn vẹn
4. [Thiết kế Luồng nghiệp vụ và Sơ đồ tuần tự (Sequence Diagrams)](#4-thiết-kế-luồng-nghiệp-vụ-và-sơ-đồ-tuần-tự-sequence-diagrams)
   - 4.1 Quy trình Xác thực & Phân quyền (Authentication & Authorization)
   - 4.2 Quy trình Quản lý, Biên soạn và Phê duyệt Khóa học
   - 4.3 Quy trình Học tập & Ghi nhận tiến độ (>80% thời lượng)
   - 4.4 Quy trình Làm bài kiểm tra và Chấm điểm tự động an toàn
   - 4.5 Quy trình Tải lên và Quản lý tài liệu học tập qua MinIO
5. [Thiết kế Giao diện lập trình ứng dụng (RESTful API Specification)](#5-thiết-kế-giao-diện-lập-trình-ứng-dụng-restful-api-specification)
   - 5.1 Quy chuẩn thiết kế API
   - 5.2 Nhóm API Xác thực & Người dùng (Auth & Users)
   - 5.3 Nhóm API Danh mục (Categories)
   - 5.4 Nhóm API Khóa học & Nội dung (Courses, Chapters, Lessons)
   - 5.5 Nhóm API Học tập & Tiến độ (Enrollment & Progress)
   - 5.6 Nhóm API Ngân hàng câu hỏi & Bài kiểm tra (Questions & Quizzes)
   - 5.7 Nhóm API Lưu trữ tệp (Storage)
6. [Thiết kế Kiến trúc Frontend (Next.js 14 Architecture)](#6-thiết-kế-kiến-trúc-frontend-nextjs-14-architecture)
   - 6.1 Cấu trúc thư mục (Next.js App Router)
   - 6.2 Cơ chế phân quyền và bảo vệ Route (Client Middleware)
   - 6.3 Thiết kế Module Player học tập tích hợp YouTube IFrame API
   - 6.4 Quản lý trạng thái (State Management)
7. [Thiết kế Triển khai và Môi trường (Deployment & DevOps)](#7-thiết-kế-triển-khai-và-môi-trường-deployment--devops)
   - 7.1 Sơ đồ triển khai Docker Compose
   - 7.2 Cấu hình dịch vụ (Services Specification)
   - 7.3 Quản lý cấu hình và bảo mật môi trường
8. [Kế hoạch Kiểm thử & Kết luận](#8-kế-hoạch-kiểm-thử--kết-luận)
   - 8.1 Chiến lược kiểm thử
   - 8.2 Kết luận

---

## 1 Giới thiệu tổng quan

### 1.1 Mục đích tài liệu
Tài liệu Thiết kế Hệ thống (System Design Document - SDD) này nhằm chuyển hóa các yêu cầu chức năng và phi chức năng đã được định nghĩa trong **Tài liệu Đặc tả Yêu cầu Phần mềm (SRS)** và **Đề xuất Đề tài (Proposal)** thành một bản thiết kế kỹ thuật chi tiết, khả thi và có tính chuẩn hóa cao. Tài liệu là căn cứ trực tiếp để đội ngũ phát triển xây dựng mã nguồn Backend, Frontend, Cơ sở dữ liệu và triển khai hệ thống trong khuôn khổ đồ án **Project 3**.

### 1.2 Phạm vi hệ thống
Hệ thống là Nền tảng học trực tuyến (E-learning Platform) phục vụ 3 nhóm tác nhân chính:
1. **Học viên (Student):** Tìm kiếm, đăng ký khóa học, theo dõi bài giảng (video YouTube), đọc tài liệu học tập, làm bài kiểm tra trắc nghiệm (quiz), theo dõi tiến độ học tập theo thời gian thực.
2. **Giảng viên (Instructor):** Quản lý cấu trúc khóa học (Khóa học – Chương – Bài học), upload tài liệu học tập, nhúng video YouTube, thiết lập ngân hàng câu hỏi, tạo bài kiểm tra trắc nghiệm, quản lý học viên và giám sát tiến độ.
3. **Quản trị viên (Admin):** Quản lý người dùng và phân quyền (RBAC), quản lý danh mục khóa học, phê duyệt hoặc từ chối xuất bản khóa học.

### 1.3 Thuật ngữ và quy ước
- **RBAC (Role-Based Access Control):** Cơ chế điều khiển truy cập dựa trên vai trò người dùng (Student, Instructor, Admin).
- **JWT (JSON Web Token):** Phương thức truyền thông an toàn xác thực người dùng giữa Client và Server gồm Access Token và Refresh Token.
- **MinIO:** Nền tảng lưu trữ đối tượng (Object Storage) mã nguồn mở tương thích với Amazon S3 API.
- **Passing Score:** Điểm số tối thiểu để học viên được tính là vượt qua bài kiểm tra.
- **YouTube IFrame API:** Giao diện lập trình của YouTube cho phép nhúng video và bắt sự kiện phát, tạm dừng, thời lượng thực tế của người học.

---

## 2 Kiến trúc hệ thống tổng thể

### 2.1 Mô hình kiến trúc phân tầng (3-Tier Layered Architecture)
Hệ thống được thiết kế theo mô hình kiến trúc 3 tầng chuẩn mực nhằm tách bạch rõ ràng giữa giao diện hiển thị, xử lý logic nghiệp vụ và lưu trữ dữ liệu:

1. **Tầng Giao diện (Presentation Layer - Frontend):**
   - Xây dựng bằng **Next.js 14** kết hợp **TypeScript**, **Tailwind CSS** và bộ component **shadcn/ui**.
   - Tối ưu hóa trải nghiệm người dùng với Server Components cho các trang danh mục/khóa học công khai và Client Components cho trang học tập, làm bài thi, bảng quản trị.
2. **Tầng Ứng dụng & Dịch vụ (Application/API Layer - Backend):**
   - Xây dựng bằng **FastAPI (Python 3.11+)**, vận hành qua Web Server **Uvicorn**.
   - Tiếp nhận các yêu cầu HTTP/HTTPS, kiểm thực định danh (JWT), xác thực dữ liệu đầu vào (Pydantic schemas), thực thi nghiệp vụ (Services) và tương tác CSDL qua ORM (**SQLAlchemy 2.0**).
3. **Tầng Dữ liệu & Lưu trữ (Data & Storage Layer):**
   - **Cơ sở dữ liệu quan hệ:** **Microsoft SQL Server 2022** lưu trữ dữ liệu người dùng, khóa học, chương trình học, tiến độ và bài kiểm tra.
   - **Lưu trữ đối tượng (Object Storage):** **MinIO** lưu trữ các tệp tĩnh như tài liệu bài học (PDF, DOCX) và ảnh đại diện (avatar), ảnh bìa khóa học.
   - **Lưu trữ & Phân phối Video:** Tận dụng hạ tầng **YouTube CDN** thông qua cơ chế nhúng (IFrame Embed) giúp giảm tải băng thông máy chủ và đảm bảo chất lượng phát video.

### 2.2 Sơ đồ khối kiến trúc hệ thống

```mermaid
graph TD
    subgraph ClientLayer["1. Presentation Layer (Client)"]
        Browser["Trình duyệt Web (Desktop / Mobile)"]
        NextJS["Next.js 14 App Router (React + TypeScript)"]
        Browser --> NextJS
    end

    subgraph APILayer["2. Application / API Layer (Backend)"]
        FastAPI["FastAPI Web Framework (Python 3.11+)"]
        AuthMiddleware["JWT Authentication & RBAC Middleware"]
        RouterLayer["API Routers (Auth, Course, Quiz, Progress, User)"]
        ServiceLayer["Business Service Layer"]
        RepoLayer["Data Repository / SQLAlchemy ORM Layer"]

        NextJS -->|"RESTful API Calls (HTTPS / JSON)"| FastAPI
        FastAPI --> AuthMiddleware
        AuthMiddleware --> RouterLayer
        RouterLayer --> ServiceLayer
        ServiceLayer --> RepoLayer
    end

    subgraph DataStorageLayer["3. Data & Storage Layer"]
        SQLServer[("Microsoft SQL Server 2022\n(Relational DB)")]
        MinIO[("MinIO Object Storage\n(PDFs, Docs, Thumbnails)")]
        YouTubeCDN["YouTube CDN\n(Video Streaming via IFrame)"]

        RepoLayer -->|"pyodbc / FreeTDS"| SQLServer
        ServiceLayer -->|"S3 Compatible SDK (boto3 / minio-py)"| MinIO
        Browser -.->|"Phát video & Lắng nghe sự kiện qua IFrame API"| YouTubeCDN
    end
```

### 2.3 Lựa chọn công nghệ và vai trò

| Thành phần | Công nghệ | Phiên bản | Vai trò & Lý do lựa chọn |
|---|---|---|---|
| **Frontend Framework** | Next.js | 14+ | App Router hiện đại, hỗ trợ SSR và Client-side rendering mượt mà, tối ưu SEO cho khóa học. |
| **Ngôn ngữ Frontend** | TypeScript | 5.x | Kiểm soát kiểu tĩnh, giảm thiểu lỗi runtime, tăng khả năng bảo trì mã nguồn. |
| **Giao diện & UI** | Tailwind CSS + shadcn/ui | Latest | Thiết kế UI hiện đại, chuẩn hóa accessible components, dễ tùy biến. |
| **Backend Framework** | FastAPI | 0.110+ | Hiệu năng cao (dựa trên Starlette và Pydantic), xử lý bất đồng bộ (async/await), tự động sinh tài liệu Swagger/OpenAPI. |
| **Ngôn ngữ Backend** | Python | 3.11+ | Cú pháp trong sáng, hệ sinh thái phong phú, thuận tiện mở rộng các tính năng AI/Data trong tương lai (ĐATN). |
| **Thư viện ORM** | SQLAlchemy | 2.0+ | ORM chuẩn mực trong Python, hỗ trợ mapping đối tượng quan hệ mạnh mẽ, an toàn trước SQL Injection. |
| **Cơ sở dữ liệu** | Microsoft SQL Server | 2022 | CSDL quan hệ chuẩn doanh nghiệp, tính toàn vẹn dữ liệu (ACID) cao, xử lý giao dịch tin cậy. |
| **Lưu trữ tệp** | MinIO | Latest | Lưu trữ đối tượng tương thích chuẩn AWS S3, triển khai self-hosted nhẹ nhàng qua Docker, tốc độ cao. |
| **Trình phát video** | YouTube IFrame API | v3 Embed | Giảm gánh nặng lưu trữ và streaming video cục bộ, độ ổn định cao, tương thích tốt mọi thiết bị. |
| **Đóng gói & Chạy** | Docker + Docker Compose | Latest | Tạo môi trường phát triển và kiểm thử đồng nhất, dễ dàng triển khai chỉ với một câu lệnh. |

### 2.4 Cấu trúc mã nguồn Backend (Clean Architecture / Service-Repository)
Backend được tổ chức theo cấu trúc phân tầng rõ ràng:

```text
backend/
├── app/
│   ├── core/               # Cấu hình hệ thống, biến môi trường, bảo mật (JWT, hashing)
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py     # Kết nối SQLAlchemy Engine & Session
│   ├── models/             # SQLAlchemy ORM Models (Định nghĩa bảng CSDL)
│   ├── schemas/            # Pydantic Schemas (Request/Response validation)
│   ├── repositories/       # Tầng truy xuất dữ liệu (Data Access Object - DAO)
│   ├── services/           # Tầng nghiệp vụ xử lý logic (Business Logic Layer)
│   ├── api/                # Tầng điều phối API Routers
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── courses.py
│   │   │   │   ├── lessons.py
│   │   │   │   ├── progress.py
│   │   │   │   ├── quizzes.py
│   │   │   │   └── storage.py
│   │   │   └── api_router.py
│   │   └── deps.py         # Dependencies (Get DB session, Get Current User, Require Role)
│   └── main.py             # Entrypoint khởi tạo FastAPI App
├── Dockerfile
└── requirements.txt
```

---

## 3 Thiết kế Cơ sở dữ liệu (Database Design)

### 3.1 Sơ đồ thực thể liên kết (Entity Relationship Diagram - ERD)

```mermaid
erDiagram
    USERS ||--o{ COURSES : "giảng dạy"
    USERS ||--o{ ENROLLMENTS : "đăng ký"
    USERS ||--o{ QUIZ_ATTEMPTS : "làm bài"
    USERS ||--o{ QUESTIONS : "soạn thảo"
    
    CATEGORIES ||--o{ COURSES : "phân loại"
    
    COURSES ||--o{ CHAPTERS : "bao gồm"
    COURSES ||--o{ ENROLLMENTS : "có học viên"
    
    CHAPTERS ||--o{ LESSONS : "chứa bài học"
    CHAPTERS ||--o{ QUIZZES : "chứa quiz chương"
    
    COURSES ||--o{ QUIZZES : "chứa quiz tổng hợp"
    
    ENROLLMENTS ||--o{ LESSON_PROGRESS : "ghi nhận tiến độ"
    LESSONS ||--o{ LESSON_PROGRESS : "thuộc về"
    
    QUESTIONS ||--o{ QUESTION_OPTIONS : "có các phương án"
    QUIZZES ||--o{ QUIZ_QUESTIONS : "chứa câu hỏi"
    QUESTIONS ||--o{ QUIZ_QUESTIONS : "được dùng trong"
    
    QUIZZES ||--o{ QUIZ_ATTEMPTS : "có lượt làm bài"
    QUIZ_ATTEMPTS ||--o{ QUIZ_ATTEMPT_ANSWERS : "ghi nhận đáp án"
    QUESTIONS ||--o{ QUIZ_ATTEMPT_ANSWERS : "trả lời câu"

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string avatar_url
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    CATEGORIES {
        int id PK
        string name UK
        string slug UK
        string description
        datetime created_at
    }

    COURSES {
        int id PK
        int instructor_id FK
        int category_id FK
        string title
        string description
        string thumbnail_url
        string status
        string rejection_reason
        datetime created_at
        datetime updated_at
    }

    CHAPTERS {
        int id PK
        int course_id FK
        string title
        int order_index
        datetime created_at
    }

    LESSONS {
        int id PK
        int chapter_id FK
        string title
        string lesson_type
        string video_url
        string document_url
        int duration_seconds
        int order_index
        boolean is_free_preview
        datetime created_at
    }

    ENROLLMENTS {
        int id PK
        int user_id FK
        int course_id FK
        datetime enrolled_at
        string status
        float progress_percentage
        datetime completed_at
    }

    LESSON_PROGRESS {
        int id PK
        int enrollment_id FK
        int lesson_id FK
        boolean is_completed
        int last_watched_second
        datetime completed_at
    }

    QUESTIONS {
        int id PK
        int instructor_id FK
        text content
        string question_type
        text explanation
        datetime created_at
    }

    QUESTION_OPTIONS {
        int id PK
        int question_id FK
        text content
        boolean is_correct
        int order_index
    }

    QUIZZES {
        int id PK
        int course_id FK
        int chapter_id FK
        string title
        text description
        int duration_minutes
        int max_attempts
        float passing_score
        datetime created_at
    }

    QUIZ_QUESTIONS {
        int id PK
        int quiz_id FK
        int question_id FK
        int order_index
        float point
    }

    QUIZ_ATTEMPTS {
        int id PK
        int quiz_id FK
        int user_id FK
        int attempt_number
        datetime started_at
        datetime submitted_at
        float score
        boolean is_passed
        string status
    }

    QUIZ_ATTEMPT_ANSWERS {
        int id PK
        int attempt_id FK
        int question_id FK
        string selected_option_ids
    }
```

### 3.2 Chi tiết các bảng dữ liệu (Data Dictionary)

#### Bảng 1: `users` (Thông tin người dùng và phân quyền)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh người dùng |
| `email` | NVARCHAR(255) | NOT NULL, UNIQUE | Địa chỉ email (dùng để đăng nhập) |
| `hashed_password` | NVARCHAR(255) | NOT NULL | Mật khẩu đã băm (Bcrypt) |
| `full_name` | NVARCHAR(150) | NOT NULL | Họ và tên người dùng |
| `avatar_url` | NVARCHAR(500) | NULL | Đường dẫn ảnh đại diện (lưu trên MinIO) |
| `role` | NVARCHAR(20) | NOT NULL, DEFAULT 'STUDENT' | Vai trò: `'STUDENT'`, `'INSTRUCTOR'`, `'ADMIN'` |
| `is_active` | BIT | NOT NULL, DEFAULT 1 | Trạng thái tài khoản (1: Hoạt động, 0: Bị khóa) |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo tài khoản |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm cập nhật |

#### Bảng 2: `categories` (Danh mục khóa học)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh danh mục |
| `name` | NVARCHAR(100) | NOT NULL, UNIQUE | Tên danh mục (ví dụ: Lập trình Web, AI) |
| `slug` | NVARCHAR(120) | NOT NULL, UNIQUE | Đường dẫn thân thiện (ví dụ: lap-trinh-web) |
| `description` | NVARCHAR(500) | NULL | Mô tả tóm tắt danh mục |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo |

#### Bảng 3: `courses` (Thông tin khóa học)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh khóa học |
| `instructor_id` | INT | NOT NULL, FK -> `users(id)` | ID giảng viên phụ trách |
| `category_id` | INT | NOT NULL, FK -> `categories(id)` | ID danh mục khóa học |
| `title` | NVARCHAR(255) | NOT NULL | Tiêu đề khóa học |
| `description` | NVARCHAR(MAX) | NULL | Mô tả chi tiết nội dung khóa học |
| `thumbnail_url` | NVARCHAR(500) | NULL | Đường dẫn ảnh bìa khóa học |
| `status` | NVARCHAR(20) | NOT NULL, DEFAULT 'DRAFT' | Trạng thái: `'DRAFT'`, `'PENDING'`, `'PUBLISHED'`, `'REJECTED'` |
| `rejection_reason`| NVARCHAR(500) | NULL | Lý do từ chối kiểm duyệt từ Admin |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo khóa học |
| `updated_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm cập nhật |

#### Bảng 4: `chapters` (Chương học trong khóa)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh chương |
| `course_id` | INT | NOT NULL, FK -> `courses(id)` ON DELETE CASCADE | Khóa học chứa chương |
| `title` | NVARCHAR(255) | NOT NULL | Tiêu đề chương học |
| `order_index` | INT | NOT NULL, DEFAULT 1 | Thứ tự hiển thị trong khóa học |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo |

#### Bảng 5: `lessons` (Bài học trong chương)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh bài học |
| `chapter_id` | INT | NOT NULL, FK -> `chapters(id)` ON DELETE CASCADE | Chương chứa bài học |
| `title` | NVARCHAR(255) | NOT NULL | Tiêu đề bài học |
| `lesson_type` | NVARCHAR(20) | NOT NULL | Loại bài: `'VIDEO'` hoặc `'DOCUMENT'` |
| `video_url` | NVARCHAR(500) | NULL | Đường link video YouTube (nếu loại VIDEO) |
| `document_url` | NVARCHAR(500) | NULL | Link tệp tài liệu MinIO (nếu loại DOCUMENT) |
| `duration_seconds`| INT | NOT NULL, DEFAULT 0 | Thời lượng video (giây) |
| `order_index` | INT | NOT NULL, DEFAULT 1 | Thứ tự sắp xếp trong chương |
| `is_free_preview` | BIT | NOT NULL, DEFAULT 0 | Cho phép học thử miễn phí (1: Có, 0: Không) |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo |

#### Bảng 6: `enrollments` (Đăng ký học & Tiến độ tổng thể)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh ghi danh |
| `user_id` | INT | NOT NULL, FK -> `users(id)` | Học viên tham gia |
| `course_id` | INT | NOT NULL, FK -> `courses(id)` | Khóa học đã đăng ký |
| `enrolled_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Ngày giờ đăng ký |
| `status` | NVARCHAR(20) | NOT NULL, DEFAULT 'IN_PROGRESS' | Trạng thái: `'IN_PROGRESS'`, `'COMPLETED'` |
| `progress_percentage` | FLOAT | NOT NULL, DEFAULT 0.0 | Tiến độ hoàn thành (tính theo % từ 0 đến 100) |
| `completed_at` | DATETIME2 | NULL | Thời điểm hoàn thành 100% khóa học |

#### Bảng 7: `lesson_progress` (Ghi nhận tiến độ từng bài học)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã bản ghi tiến độ |
| `enrollment_id`| INT | NOT NULL, FK -> `enrollments(id)` ON DELETE CASCADE | Thuộc lượt đăng ký nào |
| `lesson_id` | INT | NOT NULL, FK -> `lessons(id)` | Bài học được theo dõi |
| `is_completed`| BIT | NOT NULL, DEFAULT 0 | Đã hoàn thành hay chưa (1: Đã xong, 0: Chưa) |
| `last_watched_second` | INT | NOT NULL, DEFAULT 0 | Vị trí giây cuối cùng đã xem |
| `completed_at` | DATETIME2 | NULL | Thời điểm hoàn thành bài học |

#### Bảng 8: `questions` (Ngân hàng câu hỏi trắc nghiệm)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh câu hỏi |
| `instructor_id` | INT | NOT NULL, FK -> `users(id)` | Giảng viên tạo câu hỏi |
| `content` | NVARCHAR(MAX) | NOT NULL | Nội dung câu hỏi trắc nghiệm |
| `question_type` | NVARCHAR(20) | NOT NULL, DEFAULT 'SINGLE_CHOICE' | Loại câu: `'SINGLE_CHOICE'`, `'MULTIPLE_CHOICE'` |
| `explanation` | NVARCHAR(MAX) | NULL | Lời giải thích chi tiết đáp án |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo |

#### Bảng 9: `question_options` (Các lựa chọn đáp án)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh phương án |
| `question_id` | INT | NOT NULL, FK -> `questions(id)` ON DELETE CASCADE | Câu hỏi chứa phương án |
| `content` | NVARCHAR(MAX) | NOT NULL | Nội dung phương án |
| `is_correct` | BIT | NOT NULL, DEFAULT 0 | Đáp án đúng hay sai (1: Đúng, 0: Sai) |
| `order_index` | INT | NOT NULL, DEFAULT 1 | Thứ tự phương án (A, B, C, D) |

#### Bảng 10: `quizzes` (Bài kiểm tra đánh giá)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã định danh bài kiểm tra |
| `course_id` | INT | NOT NULL, FK -> `courses(id)` | Khóa học áp dụng |
| `chapter_id` | INT | NULL, FK -> `chapters(id)` | Chương học (NULL nếu là bài thi cuối khóa) |
| `title` | NVARCHAR(255) | NOT NULL | Tiêu đề bài kiểm tra |
| `description` | NVARCHAR(MAX) | NULL | Mô tả và hướng dẫn làm bài |
| `duration_minutes` | INT | NOT NULL, DEFAULT 15 | Thời gian làm bài (phút) |
| `max_attempts` | INT | NOT NULL, DEFAULT 3 | Số lượt làm bài tối đa cho phép |
| `passing_score` | FLOAT | NOT NULL, DEFAULT 8.0 | Điểm tối thiểu để vượt qua (thang điểm 10) |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm tạo bài kiểm tra |

#### Bảng 11: `quiz_questions` (Liên kết bài kiểm tra với câu hỏi)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã bản ghi liên kết |
| `quiz_id` | INT | NOT NULL, FK -> `quizzes(id)` ON DELETE CASCADE | Bài kiểm tra |
| `question_id` | INT | NOT NULL, FK -> `questions(id)` | Câu hỏi lấy từ ngân hàng |
| `order_index` | INT | NOT NULL, DEFAULT 1 | Vị trí câu hỏi trong đề thi |
| `point` | FLOAT | NOT NULL, DEFAULT 1.0 | Trọng số điểm của câu hỏi |

#### Bảng 12: `quiz_attempts` (Lịch sử các lượt làm bài của học viên)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã lượt thi |
| `quiz_id` | INT | NOT NULL, FK -> `quizzes(id)` | Bài kiểm tra |
| `user_id` | INT | NOT NULL, FK -> `users(id)` | Học viên thực hiện |
| `attempt_number` | INT | NOT NULL, DEFAULT 1 | Lần thi thứ mấy |
| `started_at` | DATETIME2 | NOT NULL, DEFAULT GETDATE() | Thời điểm bắt đầu tính giờ |
| `submitted_at`| DATETIME2 | NULL | Thời điểm nộp bài |
| `score` | FLOAT | NULL | Điểm số đạt được (quy đổi thang 10) |
| `is_passed` | BIT | NOT NULL, DEFAULT 0 | Đạt yêu cầu hay không |
| `status` | NVARCHAR(20) | NOT NULL, DEFAULT 'IN_PROGRESS' | Trạng thái: `'IN_PROGRESS'`, `'SUBMITTED'`, `'TIMEOUT'` |

#### Bảng 13: `quiz_attempt_answers` (Chi tiết câu trả lời của học viên)
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INT | PK, IDENTITY(1,1) | Mã bản ghi |
| `attempt_id` | INT | NOT NULL, FK -> `quiz_attempts(id)` ON DELETE CASCADE | Lượt thi |
| `question_id`| INT | NOT NULL, FK -> `questions(id)` | Câu hỏi được trả lời |
| `selected_option_ids` | NVARCHAR(255) | NULL | Danh sách ID các phương án đã chọn (JSON dạng `[1, 2]`) |

### 3.3 Thiết kế chỉ mục (Indexes) và ràng buộc toàn vẹn
Nhằm đáp ứng yêu cầu phi chức năng về hiệu năng truy vấn dưới 1.0 giây:
- **Index `idx_users_email`** trên `users(email)`: Tối ưu hóa đăng nhập và kiểm tra trùng lặp email.
- **Index `idx_courses_status_cat`** trên `courses(status, category_id)`: Tối ưu bộ lọc tìm kiếm khóa học đã xuất bản trên trang chủ.
- **Index `idx_enrollment_user_course`** trên `enrollments(user_id, course_id)` với ràng buộc `UNIQUE`: Đảm bảo mỗi học viên chỉ có 1 bản ghi ghi danh cho mỗi khóa học.
- **Index `idx_lesson_progress_lookup`** trên `lesson_progress(enrollment_id, lesson_id)` với ràng buộc `UNIQUE`.
- **Index `idx_quiz_attempts_user`** trên `quiz_attempts(quiz_id, user_id, attempt_number)`.

---

## 4 Thiết kế Luồng nghiệp vụ và Sơ đồ tuần tự (Sequence Diagrams)

### 4.1 Quy trình Xác thực & Phân quyền (Authentication & Authorization)
Hệ thống sử dụng cơ chế JWT kép:
- **Access Token:** Hạn dùng ngắn (30 phút), chứa `user_id`, `role`, `email`. Dùng để ủy quyền cho mỗi API request qua header `Authorization: Bearer <token>`.
- **Refresh Token:** Hạn dùng dài (7 ngày), lưu trữ an toàn trong `HttpOnly Cookie`, dùng để gia hạn Access Token mà không bắt người dùng đăng nhập lại.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant Web as Next.js 14 Client
    participant AuthAPI as FastAPI Auth Router
    participant Security as Security Service
    participant DB as SQL Server

    User->>Web: Nhập Email & Mật khẩu, nhấn "Đăng nhập"
    Web->>AuthAPI: POST /api/v1/auth/login {email, password}
    AuthAPI->>DB: Truy vấn user theo email
    DB-->>AuthAPI: Trả về thông tin user & hashed_password
    AuthAPI->>Security: Xác minh mật khẩu (bcrypt.verify)
    alt Mật khẩu không chính xác hoặc User bị khóa (is_active = 0)
        Security-->>AuthAPI: Sai mật khẩu / Tài khoản bị khóa
        AuthAPI-->>Web: Trả về HTTP 401 Unauthorized
        Web-->>User: Hiển thị thông báo lỗi
    else Xác thực thành công
        Security-->>AuthAPI: Mật khẩu hợp lệ
        AuthAPI->>Security: Tạo Access Token (30m) & Refresh Token (7d)
        AuthAPI-->>Web: Trả về 200 OK: Access Token + Set HttpOnly Cookie Refresh Token
        Web-->>User: Lưu Access Token trong bộ nhớ, chuyển hướng vào Dashboard theo vai trò
    end
```

### 4.2 Quy trình Quản lý, Biên soạn và Phê duyệt Khóa học

```mermaid
sequenceDiagram
    autonumber
    actor Instructor as Giảng viên
    participant Web as Next.js Client
    participant CourseAPI as FastAPI Course Service
    participant DB as SQL Server
    actor Admin as Quản trị viên

    Instructor->>Web: Tạo khóa học mới (Tiêu đề, danh mục, mô tả)
    Web->>CourseAPI: POST /api/v1/instructor/courses
    CourseAPI->>DB: Lưu khóa học trạng thái 'DRAFT'
    DB-->>CourseAPI: Khóa học đã tạo
    CourseAPI-->>Web: 201 Created

    Instructor->>Web: Thêm Chương, Bài học, Video YouTube, Tài liệu
    Web->>CourseAPI: POST Chapters / Lessons
    CourseAPI->>DB: Lưu cấu trúc bài học
    
    Instructor->>Web: Nhấn "Gửi yêu cầu phê duyệt"
    Web->>CourseAPI: POST /api/v1/instructor/courses/{id}/submit-review
    CourseAPI->>DB: Kiểm tra số bài học trong khóa học
    alt Khóa học chưa có bài học nào
        CourseAPI-->>Web: 400 Bad Request ("Khóa học phải có ít nhất 1 bài học")
        Web-->>Instructor: Cảnh báo chưa đủ điều kiện
    else Hợp lệ (Số bài học >= 1)
        CourseAPI->>DB: Cập nhật status = 'PENDING'
        CourseAPI-->>Web: 200 OK ("Đã gửi yêu cầu phê duyệt")
        Web-->>Instructor: Hiển thị trạng thái "Chờ duyệt"
        
        Admin->>Web: Truy cập "Khóa học chờ duyệt"
        Web->>CourseAPI: GET /api/v1/admin/courses?status=PENDING
        CourseAPI->>DB: Lấy danh sách khóa học PENDING
        DB-->>CourseAPI: Dữ liệu khóa học
        CourseAPI-->>Web: Trả về danh sách
        Admin->>Web: Xem xét nội dung và chọn Phê duyệt hoặc Từ chối
        alt Admin bấm "Phê duyệt"
            Web->>CourseAPI: POST /api/v1/admin/courses/{id}/approve
            CourseAPI->>DB: Cập nhật status = 'PUBLISHED'
            CourseAPI-->>Web: 200 OK
            Web-->>Admin: Khóa học đã hiển thị ra trang chủ
        else Admin bấm "Từ chối" kèm lý do
            Web->>CourseAPI: POST /api/v1/admin/courses/{id}/reject {reason}
            CourseAPI->>DB: Cập nhật status = 'REJECTED', rejection_reason
            CourseAPI-->>Web: 200 OK
            Web-->>Instructor: Nhận thông báo sửa đổi nội dung
        end
    end
```

### 4.3 Quy trình Học tập & Ghi nhận tiến độ (>80% thời lượng)

```mermaid
sequenceDiagram
    autonumber
    actor Student as Học viên
    participant Player as Next.js Player (YouTube API)
    participant ProgressAPI as FastAPI Progress Service
    participant DB as SQL Server

    Student->>Player: Chọn bài học Video trong khóa học
    Player->>ProgressAPI: GET /api/v1/lessons/{id}/progress
    ProgressAPI->>DB: Lấy vị trí đã xem lần trước (last_watched_second)
    DB-->>ProgressAPI: last_watched_second, is_completed
    ProgressAPI-->>Player: Khôi phục vị trí phát video

    Player->>Player: Khởi chạy YouTube IFrame Player
    loop Học viên xem video
        Player->>Player: Lắng nghe sự kiện onTimeUpdate
        Note over Player: Tính toán % = (currentTime / duration) * 100
    end

    alt Thời lượng xem đạt >= 80% (hoặc bấm "Hoàn thành" đối với tài liệu)
        Player->>ProgressAPI: POST /api/v1/lessons/{id}/complete {last_watched_second}
        ProgressAPI->>DB: Cập nhật lesson_progress (is_completed = 1, completed_at = NOW)
        ProgressAPI->>DB: Đếm tổng số bài đã hoàn thành / Tổng số bài trong khóa học
        ProgressAPI->>DB: Tính toán lại progress_percentage của enrollment
        alt progress_percentage == 100%
            ProgressAPI->>DB: Cập nhật enrollment status = 'COMPLETED', completed_at = NOW
        end
        DB-->>ProgressAPI: Cập nhật thành công
        ProgressAPI-->>Player: 200 OK {progress_percentage, is_course_completed}
        Player-->>Student: Đánh dấu tick xanh bài học & Cập nhật thanh tiến độ
    end
```

### 4.4 Quy trình Làm bài kiểm tra và Chấm điểm tự động an toàn
> [!IMPORTANT]
> **Nguyên tắc bảo mật:** Danh sách câu hỏi trả về cho Client khi làm bài **tuyệt đối không chứa trường `is_correct` hay `explanation`**. Việc tính điểm được thực thi 100% tại Backend khi nộp bài.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Học viên
    participant Web as Next.js Quiz UI
    participant QuizAPI as FastAPI Quiz Service
    participant DB as SQL Server

    Student->>Web: Bấm "Bắt đầu làm bài"
    Web->>QuizAPI: POST /api/v1/quizzes/{id}/start
    QuizAPI->>DB: Kiểm tra số lần đã thi của học viên (count attempt)
    alt Số lần thi >= max_attempts
        QuizAPI-->>Web: 403 Forbidden ("Đã hết số lượt làm bài quy định")
        Web-->>Student: Thông báo hết lượt thi
    else Còn lượt thi hợp lệ
        QuizAPI->>DB: Tạo bản ghi quiz_attempts mới (status = 'IN_PROGRESS', started_at = NOW)
        QuizAPI->>DB: Lấy danh sách câu hỏi và các lựa chọn (LOẠI BỎ is_correct và explanation)
        DB-->>QuizAPI: Dữ liệu câu hỏi an toàn
        QuizAPI-->>Web: 200 OK: attempt_id, duration_minutes, danh sách câu hỏi
        Web->>Web: Bắt đầu bộ đếm ngược thời gian (Client countdown)
        
        Student->>Web: Chọn đáp án và bấm "Nộp bài" (hoặc hết giờ tự động nộp)
        Web->>QuizAPI: POST /api/v1/quizzes/attempts/{attempt_id}/submit {answers: [{question_id, selected_option_ids}]}
        
        QuizAPI->>DB: Lấy đáp án đúng gốc từ question_options
        QuizAPI->>QuizAPI: So khớp câu trả lời, tính tổng điểm (thang 10)
        QuizAPI->>QuizAPI: So sánh với passing_score -> is_passed = (score >= passing_score)
        QuizAPI->>DB: Cập nhật quiz_attempts (score, is_passed, status = 'SUBMITTED', submitted_at = NOW)
        QuizAPI->>DB: Lưu chi tiết đáp án vào quiz_attempt_answers
        
        alt is_passed = true
            QuizAPI->>DB: Cập nhật tiến độ bài quiz vào tiến độ khóa học
        end
        
        QuizAPI-->>Web: 200 OK: {score, is_passed, passing_score, detailed_review: [câu hỏi, đáp án đã chọn, đáp án đúng, lời giải thích]}
        Web-->>Student: Hiển thị bảng điểm, thông báo Đạt/Không đạt và lời giải chi tiết
    end
```

### 4.5 Quy trình Tải lên và Quản lý tài liệu học tập qua MinIO

```mermaid
sequenceDiagram
    autonumber
    actor Instructor as Giảng viên
    participant Web as Next.js Web
    participant StorageAPI as FastAPI Storage Router
    participant MinIOSvc as MinIO Object Storage
    participant DB as SQL Server

    Instructor->>Web: Chọn tệp tài liệu PDF/Slide (< 50MB)
    Web->>StorageAPI: POST /api/v1/storage/upload (Multipart/form-data)
    StorageAPI->>StorageAPI: Kiểm tra định dạng tệp (PDF, DOCX, ZIP) và dung lượng
    StorageAPI->>MinIOSvc: Upload stream tệp vào bucket "materials" (tạo unique object_key bằng UUID)
    MinIOSvc-->>StorageAPI: Upload thành công, trả về Object Name / URL
    StorageAPI-->>Web: 200 OK {file_url: "http://minio:9000/materials/..."}
    Instructor->>Web: Điền thông tin bài học và bấm "Lưu bài học"
    Web->>StorageAPI: POST /api/v1/lessons {chapter_id, title, lesson_type: "DOCUMENT", document_url: file_url}
    StorageAPI->>DB: Lưu thông tin bài học vào bảng lessons
    DB-->>StorageAPI: Hoàn tất
    StorageAPI-->>Web: 201 Created
```

---

## 5 Thiết kế Giao diện lập trình ứng dụng (RESTful API Specification)

### 5.1 Quy chuẩn thiết kế API
- **Base URL:** `/api/v1`
- **Định dạng dữ liệu:** JSON (`Content-Type: application/json`).
- **Xác thực:** Bearer Token trong Header: `Authorization: Bearer <access_token>`.
- **Cấu trúc phản hồi chuẩn (Response Envelope Pattern):**

```json
{
  "success": true,
  "message": "Thao tác thành công",
  "data": {},
  "error": null
}
```

- **Mã lỗi HTTP tiêu chuẩn:**
  - `200 OK`: Thành công (truy vấn, cập nhật).
  - `201 Created`: Tạo mới tài nguyên thành công.
  - `400 Bad Request`: Dữ liệu đầu vào không hợp lệ hoặc vi phạm nghiệp vụ.
  - `401 Unauthorized`: Chưa đăng nhập hoặc token không hợp lệ / hết hạn.
  - `403 Forbidden`: Không có quyền truy cập vào tài nguyên (sai Role).
  - `404 Not Found`: Không tìm thấy tài nguyên.
  - `500 Internal Server Error`: Lỗi máy chủ nội bộ.

---

### 5.2 Nhóm API Xác thực & Người dùng (Auth & Users)

#### `POST /api/v1/auth/register`
- **Mô tả:** Đăng ký tài khoản học viên mới.
- **Quyền hạn:** Công khai (Public).
- **Request Body:**
```json
{
  "email": "student@example.com",
  "password": "Password123@",
  "full_name": "Lê Mạnh Hùng"
}
```
- **Response (201 Created):**
```json
{
  "success": true,
  "message": "Đăng ký tài khoản thành công",
  "data": {
    "user_id": 1,
    "email": "student@example.com",
    "full_name": "Lê Mạnh Hùng",
    "role": "STUDENT"
  }
}
```

#### `POST /api/v1/auth/login`
- **Mô tả:** Đăng nhập hệ thống, cấp Access Token và Refresh Token cookie.
- **Quyền hạn:** Công khai.
- **Request Body:**
```json
{
  "email": "student@example.com",
  "password": "Password123@"
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "message": "Đăng nhập thành công",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "student@example.com",
      "full_name": "Lê Mạnh Hùng",
      "role": "STUDENT"
    }
  }
}
```

#### `GET /api/v1/auth/me`
- **Mô tả:** Lấy thông tin hồ sơ của tài khoản đang đăng nhập.
- **Quyền hạn:** Đã xác thực (Tất cả vai trò).

#### `PUT /api/v1/auth/profile`
- **Mô tả:** Cập nhật họ tên, avatar của người dùng.
- **Quyền hạn:** Đã xác thực.

#### `POST /api/v1/auth/change-password`
- **Mô tả:** Đổi mật khẩu cá nhân.
- **Quyền hạn:** Đã xác thực.

#### `GET /api/v1/admin/users`
- **Mô tả:** Quản trị viên lấy danh sách tài khoản, có phân trang và lọc theo vai trò.
- **Quyền hạn:** `ADMIN`.
- **Query Params:** `?page=1&limit=10&role=STUDENT&search=hung`

#### `PATCH /api/v1/admin/users/{user_id}/status`
- **Mô tả:** Khóa hoặc mở khóa tài khoản người dùng (`is_active: true/false`).
- **Quyền hạn:** `ADMIN`.

#### `PATCH /api/v1/admin/users/{user_id}/role`
- **Mô tả:** Thay đổi quyền hạn người dùng (`STUDENT`, `INSTRUCTOR`, `ADMIN`).
- **Quyền hạn:** `ADMIN`.

---

### 5.3 Nhóm API Danh mục (Categories)

| Endpoint | Method | Role | Mô tả |
|---|---|---|---|
| `/api/v1/categories` | `GET` | Public | Lấy toàn bộ danh mục khóa học |
| `/api/v1/admin/categories` | `POST` | `ADMIN` | Tạo mới danh mục đào tạo |
| `/api/v1/admin/categories/{id}` | `PUT` | `ADMIN` | Cập nhật thông tin danh mục |
| `/api/v1/admin/categories/{id}` | `DELETE` | `ADMIN` | Xóa danh mục (chặn nếu còn khóa học phụ thuộc) |

---

### 5.4 Nhóm API Khóa học & Nội dung (Courses, Chapters, Lessons)

#### `GET /api/v1/courses`
- **Mô tả:** Danh sách khóa học đã xuất bản phục vụ trang chủ và tìm kiếm.
- **Quyền hạn:** Public.
- **Query Params:** `?search=react&category_id=2&page=1&limit=12`.

#### `GET /api/v1/courses/{course_id}`
- **Mô tả:** Xem chi tiết khóa học, đề cương (chương, bài học) và thông tin giảng viên.
- **Quyền hạn:** Public.

#### `POST /api/v1/instructor/courses`
- **Mô tả:** Giảng viên tạo bản nháp khóa học mới.
- **Quyền hạn:** `INSTRUCTOR`, `ADMIN`.
- **Request Body:**
```json
{
  "title": "Lập trình Web hiện đại với Next.js và FastAPI",
  "category_id": 1,
  "description": "Khóa học thực chiến từ cơ bản đến nâng cao",
  "thumbnail_url": "http://minio:9000/thumbnails/course-1.png"
}
```

#### `PUT /api/v1/instructor/courses/{course_id}`
- **Mô tả:** Cập nhật thông tin khóa học của giảng viên.
- **Quyền hạn:** `INSTRUCTOR` (chỉ sửa khóa học do mình tạo).

#### `POST /api/v1/instructor/courses/{course_id}/submit-review`
- **Mô tả:** Gửi yêu cầu phê duyệt khóa học (chuyển trạng thái sang `PENDING`).
- **Quyền hạn:** `INSTRUCTOR`.

#### `POST /api/v1/admin/courses/{course_id}/approve`
- **Mô tả:** Admin duyệt xuất bản khóa học (`PUBLISHED`).
- **Quyền hạn:** `ADMIN`.

#### `POST /api/v1/admin/courses/{course_id}/reject`
- **Mô tả:** Admin từ chối khóa học kèm lý do (`REJECTED`).
- **Quyền hạn:** `ADMIN`.
- **Request Body:** `{"reason": "Cần bổ sung thêm tài liệu bài tập chương 2"}`.

#### `POST /api/v1/instructor/courses/{course_id}/chapters`
- **Mô tả:** Thêm chương học mới vào khóa học.
- **Quyền hạn:** `INSTRUCTOR`.

#### `POST /api/v1/instructor/chapters/{chapter_id}/lessons`
- **Mô tả:** Thêm bài học (Video hoặc Tài liệu) vào chương.
- **Quyền hạn:** `INSTRUCTOR`.
- **Request Body:**
```json
{
  "title": "Bài 1: Giới thiệu kiến trúc hệ thống",
  "lesson_type": "VIDEO",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_seconds": 600,
  "order_index": 1,
  "is_free_preview": true
}
```

---

### 5.5 Nhóm API Học tập & Tiến độ (Enrollment & Progress)

#### `POST /api/v1/courses/{course_id}/enroll`
- **Mô tả:** Học viên đăng ký tham gia khóa học.
- **Quyền hạn:** `STUDENT`.

#### `POST /api/v1/instructor/courses/{course_id}/enroll-student`
- **Mô tả:** Giảng viên thêm trực tiếp một học viên vào khóa học bằng email.
- **Quyền hạn:** `INSTRUCTOR`.
- **Request Body:** `{"student_email": "student2@example.com"}`.

#### `GET /api/v1/courses/{course_id}/progress`
- **Mô tả:** Lấy tổng quan tiến độ của học viên trong khóa học (% hoàn thành, trạng thái từng bài).
- **Quyền hạn:** Học viên đã đăng ký khóa học.

#### `POST /api/v1/lessons/{lesson_id}/complete`
- **Mô tả:** Đánh dấu hoàn thành bài học khi xem video > 80% hoặc xác nhận đọc tài liệu.
- **Quyền hạn:** Học viên đã đăng ký khóa học.
- **Request Body:**
```json
{
  "last_watched_second": 520
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "lesson_id": 10,
    "is_completed": true,
    "course_progress_percentage": 45.5,
    "is_course_completed": false
  }
}
```

#### `GET /api/v1/instructor/courses/{course_id}/students`
- **Mô tả:** Giảng viên xem danh sách học viên đăng ký và tiến độ của từng người.
- **Quyền hạn:** `INSTRUCTOR`.

---

### 5.6 Nhóm API Ngân hàng câu hỏi & Bài kiểm tra (Questions & Quizzes)

#### `POST /api/v1/instructor/questions`
- **Mô tả:** Giảng viên tạo câu hỏi trắc nghiệm mới vào ngân hàng câu hỏi.
- **Quyền hạn:** `INSTRUCTOR`.
- **Request Body:**
```json
{
  "content": "Giao thức nào được sử dụng để truyền tải web an toàn?",
  "question_type": "SINGLE_CHOICE",
  "explanation": "HTTPS mã hóa lưu lượng bằng TLS/SSL.",
  "options": [
    {"content": "HTTP", "is_correct": false, "order_index": 1},
    {"content": "HTTPS", "is_correct": true, "order_index": 2},
    {"content": "FTP", "is_correct": false, "order_index": 3},
    {"content": "SSH", "is_correct": false, "order_index": 4}
  ]
}
```

#### `POST /api/v1/instructor/quizzes`
- **Mô tả:** Tạo bài kiểm tra và gắn câu hỏi từ ngân hàng vào bài thi.
- **Quyền hạn:** `INSTRUCTOR`.
- **Request Body:**
```json
{
  "course_id": 1,
  "chapter_id": 2,
  "title": "Bài kiểm tra Chương 2: Kiến trúc Web",
  "duration_minutes": 15,
  "max_attempts": 3,
  "passing_score": 8.0,
  "question_ids": [101, 102, 103, 104, 105]
}
```

#### `POST /api/v1/quizzes/{quiz_id}/start`
- **Mô tả:** Bắt đầu một lượt làm bài thi (kiểm tra số lượt, tạo attempt, trả về câu hỏi an toàn không kèm đáp án đúng).
- **Quyền hạn:** Học viên đã đăng ký.
- **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "attempt_id": 55,
    "attempt_number": 1,
    "duration_minutes": 15,
    "questions": [
      {
        "id": 101,
        "content": "Giao thức nào được sử dụng để truyền tải web an toàn?",
        "options": [
          {"id": 401, "content": "HTTP"},
          {"id": 402, "content": "HTTPS"},
          {"id": 403, "content": "FTP"},
          {"id": 404, "content": "SSH"}
        ]
      }
    ]
  }
}
```

#### `POST /api/v1/quizzes/attempts/{attempt_id}/submit`
- **Mô tả:** Nộp bài kiểm tra và nhận kết quả chấm điểm tức thì.
- **Quyền hạn:** Học viên sở hữu lượt thi.
- **Request Body:**
```json
{
  "answers": [
    {"question_id": 101, "selected_option_ids": [402]}
  ]
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "score": 10.0,
    "is_passed": true,
    "passing_score": 8.0,
    "submitted_at": "2026-10-10T14:30:00Z",
    "review": [
      {
        "question_id": 101,
        "content": "Giao thức nào được sử dụng để truyền tải web an toàn?",
        "user_selected": [402],
        "correct_options": [402],
        "is_correct": true,
        "explanation": "HTTPS mã hóa lưu lượng bằng TLS/SSL."
      }
    ]
  }
}
```

---

### 5.7 Nhóm API Lưu trữ tệp (Storage)

#### `POST /api/v1/storage/upload`
- **Mô tả:** Tải lên tệp tài liệu học tập (PDF, DOCX) hoặc ảnh đại diện lên MinIO.
- **Quyền hạn:** `INSTRUCTOR`, `ADMIN`.
- **Form Data:** `file: <binary>`, `bucket: "materials"`
- **Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "file_url": "http://localhost:9000/materials/uuid-tailieu-chuong1.pdf",
    "filename": "tailieu-chuong1.pdf",
    "file_size": 2458900
  }
}
```

---

## 6 Thiết kế Kiến trúc Frontend (Next.js 14 Architecture)

### 6.1 Cấu trúc thư mục (Next.js App Router)

```text
frontend/
├── app/
│   ├── (auth)/                     # Nhóm Route xác thực
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (public)/                   # Trang công khai
│   │   ├── page.tsx                # Trang chủ (Danh sách khóa học nổi bật)
│   │   └── courses/
│   │       ├── page.tsx            # Tìm kiếm & Lọc khóa học
│   │       └── [id]/page.tsx       # Chi tiết khóa học (SSR)
│   ├── (student)/                  # Không gian học viên
│   │   ├── dashboard/page.tsx      # Khóa học của tôi & Tiến độ
│   │   └── learn/[courseId]/
│   │       ├── page.tsx            # Không gian học chính (Sidebar + Player)
│   │       └── quiz/[quizId]/page.tsx # Giao diện làm bài kiểm tra
│   ├── (instructor)/               # Bảng điều khiển giảng viên
│   │   ├── instructor/courses/     # Quản lý khóa học, bài học
│   │   ├── instructor/questions/   # Ngân hàng câu hỏi
│   │   └── instructor/students/    # Theo dõi tiến độ học viên
│   ├── (admin)/                    # Bảng quản trị hệ thống
│   │   ├── admin/users/page.tsx    # Quản lý người dùng & Phân quyền
│   │   ├── admin/courses/page.tsx  # Kiểm duyệt khóa học
│   │   └── admin/categories/page.tsx # Quản lý danh mục
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                         # shadcn/ui components (Button, Dialog, Table,...)
│   ├── course/                     # CourseCard, CourseOutline, ChapterList
│   ├── player/                     # YouTubePlayer, DocumentViewer
│   └── quiz/                       # QuizCountdown, QuestionItem, QuizResultModal
├── hooks/
│   ├── use-auth.ts                 # Hook quản lý trạng thái đăng nhập
│   └── use-youtube-tracker.ts      # Hook tính toán thời gian xem video
├── lib/
│   ├── api-client.ts               # Axios / Fetch wrapper tự động gắn Access Token
│   └── utils.ts
└── middleware.ts                   # Next.js Middleware kiểm tra RBAC
```

### 6.2 Cơ chế phân quyền và bảo vệ Route (Client Middleware)
Tệp `middleware.ts` của Next.js chặn các truy cập trái phép ở cấp độ Edge:
- Route `/admin/*`: Chỉ cho phép người dùng có `role === 'ADMIN'`. Nếu sai, chuyển hướng về `/unauthorized` hoặc `/login`.
- Route `/instructor/*`: Chỉ cho phép `role === 'INSTRUCTOR'` hoặc `role === 'ADMIN'`.
- Route `/learn/*`: Yêu cầu người dùng đã đăng nhập và đã được ghi danh vào khóa học.

### 6.3 Thiết kế Module Player học tập tích hợp YouTube IFrame API
Giao diện phát video tích hợp thư viện YouTube IFrame Player để theo dõi quá trình học:

```typescript
// Ý tưởng cài đặt Hook: useYouTubeTracker
import { useEffect, useRef, useState } from "react";

export function useYouTubeTracker({
  videoId,
  duration,
  onComplete,
}: {
  videoId: string;
  duration: number;
  onComplete: () => void;
}) {
  const [watchedSeconds, setWatchedSeconds] = useState(0);
  const [completed, setCompleted] = useState(false);
  const playerRef = useRef<any>(null);

  useEffect(() => {
    // 1. Tải script YouTube IFrame API
    // 2. Khởi tạo player với onStateChange
    // 3. Sử dụng setInterval (mỗi 1 giây) kiểm tra player.getCurrentTime()
    // 4. Nếu currentTime / duration >= 0.8 và chưa completed:
    //    Gọi onComplete() để kích hoạt API POST /lessons/{id}/complete
  }, [videoId, duration]);

  return { playerRef, watchedSeconds, completed };
}
```

### 6.4 Quản lý trạng thái (State Management)
- **Server State:** Sử dụng **TanStack Query (React Query)** để cache dữ liệu từ API, tự động revalidate khi có thao tác thêm/sửa/xóa bài học hoặc nộp bài kiểm tra.
- **Client Global State:** Sử dụng **Zustand** để lưu thông tin phiên người dùng (`userProfile`, `sidebarExpanded`).

---

## 7 Thiết kế Triển khai và Môi trường (Deployment & DevOps)

### 7.1 Sơ đồ triển khai Docker Compose

```mermaid
graph TD
    subgraph HostServer["Máy chủ triển khai (Docker Engine)"]
        subgraph DockerComposeNet["Docker Network: elearning-network"]
            Nginx["Next.js Web Frontend\nContainer: elearning-frontend\nPort: 3000"]
            Backend["FastAPI Backend\nContainer: elearning-backend\nPort: 8000"]
            DB["SQL Server 2022\nContainer: elearning-sqlserver\nPort: 1433"]
            MinIO["MinIO Storage\nContainer: elearning-minio\nPort: 9000 (API), 9001 (Console)"]
        end
        
        Client["Người dùng (Web Browser)"] -->|"Port 3000 (HTTP)"| Nginx
        Client -->|"Port 8000 (API Calls)"| Backend
        Nginx -->|"Internal Call"| Backend
        Backend -->|"Internal TCP 1433"| DB
        Backend -->|"Internal TCP 9000"| MinIO
        Client -.->|"Tải tệp / avatar trực tiếp (Port 9000)"| MinIO
    end
```

### 7.2 Cấu hình dịch vụ (Services Specification)

```yaml
version: '3.8'

services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: elearning-sqlserver
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=YourStrongPassword!2026
      - MSSQL_PID=Developer
    ports:
      - "1433:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql
    networks:
      - elearning-net

  minio:
    image: minio/minio:latest
    container_name: elearning-minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=miniopassword2026
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - elearning-net

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: elearning-backend
    environment:
      - DATABASE_URL=mssql+pyodbc://sa:YourStrongPassword!2026@sqlserver:1433/elearning_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
      - JWT_SECRET_KEY=super-secret-key-project3-2026
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=miniopassword2026
    ports:
      - "8000:8000"
    depends_on:
      - sqlserver
      - minio
    networks:
      - elearning-net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: elearning-frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - elearning-net

volumes:
  sqlserver_data:
  minio_data:

networks:
  elearning-net:
    driver: bridge
```

### 7.3 Quản lý cấu hình và bảo mật môi trường
- Tất cả khóa bí mật (`JWT_SECRET_KEY`, Mật khẩu SA của SQL Server, MinIO credentials) được đặt trong file `.env` tách biệt khỏi Git.
- Dữ liệu cơ sở dữ liệu và lưu trữ MinIO được map qua Docker Volumes (`sqlserver_data`, `minio_data`) đảm bảo tính bền vững khi restart container.
- Toàn bộ kết nối giữa FastAPI và SQL Server được mã hóa cấu hình qua connection string chuẩn ODBC.

---

## 8 Kế hoạch Kiểm thử & Kết luận

### 8.1 Chiến lược kiểm thử
1. **Kiểm thử Đơn vị (Unit Testing):**
   - Viết các test case với `pytest` cho tầng Services và Repositories của Backend: kiểm thử logic tính điểm bài quiz, logic tính % tiến độ hoàn thành khóa học, thuật toán băm mật khẩu.
2. **Kiểm thử Tích hợp (Integration Testing):**
   - Kiểm thử toàn bộ chuỗi Use Case: Đăng ký -> Đăng nhập -> Tạo khóa học -> Phê duyệt -> Đăng ký học -> Học bài -> Thi Quiz -> Hoàn thành khóa học.
3. **Kiểm thử Bảo mật (Security Testing):**
   - Kiểm tra chặn truy cập Endpoint khi token hết hạn hoặc sai Role (ví dụ Student gọi API duyệt khóa học phải trả về HTTP 403 Forbidden).
   - Kiểm tra chống rò rỉ đáp án bài trắc nghiệm trong API `/quizzes/{id}/start`.

### 8.2 Kết luận
Tài liệu Thiết kế Hệ thống này đã cung cấp bản vẽ kỹ thuật toàn diện, chặt chẽ và nhất quán với các yêu cầu đã đặt ra trong tài liệu SRS và Đề xuất Project 3. Kiến trúc hệ thống tận dụng tối đa thế mạnh của Next.js 14, FastAPI, SQL Server, MinIO và YouTube Embed, giúp tối ưu hóa hiệu năng, giảm chi phí lưu trữ hạ tầng và đảm bảo khả năng mở rộng trong giai đoạn phát triển đồ án tốt nghiệp tiếp theo.
