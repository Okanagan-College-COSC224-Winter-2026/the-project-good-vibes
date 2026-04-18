# Peer Evaluation App — Project Overview

## What Is This?

A web application that lets teachers create courses and assignments where students peer-review each other's work. Teachers get a gradebook with aggregated scores, students get feedback from their peers. The app supports both **individual reviews** (student reviews student) and **group reviews** (group reviews group).

---

## Tech Stack at a Glance

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Flask (Python) | Lightweight web framework for building REST APIs |
| **ORM** | SQLAlchemy | Maps Python classes to database tables — no raw SQL needed |
| **Serialization** | Marshmallow | Converts database objects to/from JSON for API responses |
| **Auth** | Flask-JWT-Extended | Secure authentication via JSON Web Tokens stored in httpOnly cookies |
| **Database (dev)** | SQLite | Zero-config file-based database, great for local development |
| **Database (prod)** | PostgreSQL | Production-grade relational database, runs in Docker |
| **Frontend** | React 18 + TypeScript | Component-based UI with type safety |
| **Build Tool** | Vite | Fast development server and production bundler |
| **Styling** | Tailwind CSS | Utility-first CSS — style directly in JSX with class names |
| **Server State** | TanStack React Query | Caches API data, handles refetching, loading states, and mutations |
| **Forms** | React Hook Form | Manages form state, validation, and submission |
| **Routing** | React Router | Client-side page navigation without full page reloads |
| **Testing** | Pytest (backend), Vitest (frontend) | Automated test suites |
| **Containerization** | Docker + Docker Compose | Packages the entire app (DB + backend + frontend) into containers |
| **Web Server** | Gunicorn (backend), Nginx (frontend) | Production-grade servers for serving the app |

---

## How the Pieces Fit Together

```
Browser (React app on localhost:8080)
    |
    |  HTTP requests (fetch with credentials: "include")
    v
Flask Backend (localhost:5000)
    |
    |  SQLAlchemy ORM queries
    v
Database (SQLite locally, PostgreSQL in Docker)
```

- The **React frontend** is a single-page application (SPA). It makes API calls to the Flask backend.
- The **Flask backend** handles authentication, business logic, and database operations. It exposes a REST API.
- The **database** stores all persistent data. SQLAlchemy lets us swap between SQLite and PostgreSQL without changing code.
- **Authentication** uses JWT tokens stored in httpOnly cookies. The browser automatically sends these with every request via `credentials: "include"`.

---

## Backend Architecture

### App Factory Pattern

The Flask app is created via `create_app()` in `flask_backend/api/__init__.py`. This pattern allows:
- Different configurations for development, testing, and production
- Clean initialization of extensions (database, auth, CORS)
- Easy testing with isolated app instances

### Controllers (Blueprints)

Flask uses **blueprints** to organize routes into modules. Each controller handles a specific domain:

| Controller | URL Prefix | Purpose |
|-----------|-----------|---------|
| `auth_controller` | `/auth` | Login, logout, registration, password changes |
| `user_controller` | `/user` | Profile management, avatar uploads |
| `admin_controller` | `/admin` | Create teachers, manage users (admin only) |
| `class_controller` | `/class` | Course CRUD, enrollment, roster CSV upload |
| `assignment_controller` | `/assignment` | Assignment CRUD, lists assignments per course |
| `rubric_controller` | `/rubric` | Rubric + criteria CRUD for assignments |
| `review_controller` | `/review` | Submit/edit/view peer reviews, progress tracking |
| `submission_controller` | `/submission` | Student file uploads for assignments |
| `gradebook_controller` | `/gradebook` | Teacher gradebook, grade overrides |
| `group_controller` | `/group` | Create/edit groups, manage members |
| `assignment_resource_controller` | `/resource` | Teacher-uploaded assignment resources |

### Models (Database Tables)

The database has 12 tables mapped to Python classes via SQLAlchemy:

**Users & Enrollment:**
- `User` — id, name, email, hashed password, role (student/teacher/admin)
- `User_Course` — links students to courses (many-to-many)
- `Group_Members` — links students to groups (many-to-many)

**Courses & Assignments:**
- `Course` — id, name, teacherID
- `Assignment` — id, name, description, due date, anonymous setting, review type toggles
- `CourseGroup` — groups within a course (Alpha, Beta, etc.)
- `AssignmentResource` — teacher-uploaded files for assignments

**Reviews & Rubrics:**
- `Rubric` — per-assignment, typed as "individual" or "group"
- `CriteriaDescription` — questions within a rubric (e.g., "Code Quality", scoreMax: 10)
- `Review` — a submitted peer review (reviewer, reviewee, type, comments)
- `Criterion` — individual score for one criteria question within a review

**Grading:**
- `GradeOverride` — teacher can override a student's computed grade for an assignment

### Services Layer

Business logic is separated from controllers into service modules:

- **`grade_service.py`** — Computes averages, course summaries, handles the equal-weight grading formula
- **`progress_service.py`** — Calculates how many reviews each student has completed vs. required
- **`group_service.py`** — Looks up which group a student belongs to in a course
- **`review_masking.py`** — Anonymizes reviewer names when assignments are set to anonymous

### Authentication Flow

1. Student POSTs email + password to `/auth/login`
2. Backend verifies credentials, creates a JWT token
3. JWT is set as an **httpOnly cookie** (browser stores it automatically, JavaScript can't read it — prevents XSS attacks)
4. Every subsequent request includes the cookie automatically via `credentials: "include"`
5. Backend decorators (`@jwt_required()`, `@jwt_teacher_required`) validate the token and enforce roles

---

## Frontend Architecture

### Project Structure

```
frontend/src/
  App.tsx              — Route definitions
  types.d.ts           — TypeScript interfaces (Course, Assignment, User, etc.)
  services/            — API call functions (one file per backend domain)
  features/            — Feature modules, each with components + hooks
    authentication/    — Login, signup, auth context
    dashboard/         — Course list (home page after login)
    classes/           — Class home, members, settings
    assignments/       — Assignment detail, submission, review forms
    reviews/           — Review display, rubric display, progress
    gradebook/         — Teacher gradebook table, grade cells, review modal
    groups/            — Group manager
    account/           — Profile, avatar
  ui/                  — Reusable components (Modal, Button, Tabs, etc.)
  util/                — Helper functions (date formatting, auth checks)
  layouts/             — Page layouts (ClassLayout with tabs, ProtectedLayout)
```

### How Data Flows

1. **API Services** (`services/`) — Functions that call `fetch()` to the backend. Each returns a promise.
2. **React Query Hooks** (`features/*/use*.ts`) — Wrap API calls in `useQuery` (for reads) or `useMutation` (for writes). Handles caching, loading states, and automatic refetching.
3. **Components** (`features/*/*.tsx`) — Consume hooks, render UI. When a mutation succeeds, React Query automatically invalidates related queries so the UI updates.

Example flow for submitting a review:
```
ReviewForm component
  → calls useSubmitReview() mutation hook
    → calls submitReview() API service
      → POST /review/submit to Flask backend
        → Backend creates Review + Criterion records
  → on success, invalidates ["reviews", assignmentId] query
    → React Query refetches review data
      → UI updates automatically
```

### Styling with Tailwind CSS

Instead of writing CSS files, styles are applied directly via class names:
```jsx
<button className="px-4 py-2 bg-btn-primary text-white rounded-lg hover:brightness-110">
  Submit
</button>
```

This means: padding x=4 y=2, blue background, white text, rounded corners, brighter on hover. All styling is visible in the JSX — no jumping between files.

### React Query (TanStack Query)

This is the key state management tool. It replaces manual `useEffect` + `useState` patterns for API data:

```typescript
// Fetching data — automatic caching, loading state, error handling
const { data, isLoading } = useQuery({
  queryKey: ["assignments", courseId],
  queryFn: () => listAssignments(courseId),
});

// Mutating data — with automatic cache invalidation
const { mutate } = useMutation({
  mutationFn: submitReview,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["reviews"] });
  },
});
```

---

## Key Features

### Peer Reviews (Individual + Group)

- **Individual**: Student A reviews Student B. Each student reviews multiple classmates.
- **Group**: Group Alpha reviews Group Beta. Any group member can submit on behalf of the group.
- Reviews contain scores for each rubric criterion plus optional comments.
- Submissions are atomic — the review and all criterion scores are saved in one transaction.
- Assignments can be **anonymous** (reviewer identity hidden from students).

### Rubrics

Each assignment can have two rubrics:
- **Individual rubric** — used for individual peer reviews
- **Group rubric** — used for group peer reviews

Each rubric contains criteria (questions) with a max score. When a student submits a review, they provide a score for each criterion.

### Equal-Weight Grading

The grading formula treats individual and group review types equally:

```
per_assignment_pct = average(individual_pct, group_pct)
course_total = average of all per_assignment_pcts
```

This prevents a rubric with a high max score from dominating the grade. A 5/10 individual score and a 9/10 group score gives `(50% + 90%) / 2 = 70%`, not `14/20 = 70%` (which happens to be the same here, but diverges when max scores differ).

### Teacher Gradebook

- Table view: students as rows, assignments as columns
- Each cell shows the equal-weight percentage for that student+assignment
- Toggle between **Grades** view and **Reviews** view (shows X/Y review completion)
- Click a cell to override the grade or view detailed reviews
- Course total column averages all assignment percentages

### Student Evaluations Page ("My Evaluations")

- Single assignment list showing combined grade per assignment
- Eye icon opens a modal with both individual and group reviews received
- Course total at the bottom matches the gradebook calculation

### Assignment Status Badges

Students see context-aware badges:
- **Submitted** (blue) — student has uploaded a submission
- **Upcoming** (green) — due date in the future, no submission
- **Overdue** (red) — past due date, no submission
- **No due date** (gray) — teacher hasn't set a due date

---

## Database

### SQLite vs PostgreSQL

The app uses **SQLAlchemy ORM**, which abstracts the database. The same Python code works with both:

- **Local development**: SQLite — a single file (`instance/app.sqlite`), zero setup
- **Docker/Production**: PostgreSQL — robust, concurrent, runs as a separate service

Switching is just a configuration change (`DATABASE_URL` environment variable). No code changes needed.

### Key Relationships

```
User ──teaches──→ Course ──has──→ Assignment ──has──→ Rubric ──has──→ CriteriaDescription
  |                  |                |                                       |
  |──enrolled in─────┘                |──has──→ Review ──has──→ Criterion ────┘
  |                                   |                    (scores per criteria)
  |──member of──→ CourseGroup ────────┘
  |                (revieweeID can point to User OR CourseGroup)
  |
  |──submitted──→ Submission
```

---

## Testing

### Backend Tests (Pytest)

Located in `flask_backend/tests/`. Key patterns:

- **conftest.py** — Shared fixtures: test app (in-memory SQLite), database session, test client, helper functions
- **Fixtures** — Each test gets a clean database. Fixtures create users, courses, assignments, etc. as needed.
- **TDD approach** — Tests are written first, then implementation to make them pass.
- **268+ tests** covering models, endpoints, authorization, edge cases

Run tests:
```bash
cd flask_backend
python -m pytest tests/ -v
```

### Frontend Tests (Vitest)

- Component and hook tests using Vitest (Vite-native test runner)
- Similar API to Jest but faster (uses Vite's transform pipeline)

---

## Docker Setup

### Three Containers

```
docker-compose.yml
├── postgres (PostgreSQL 15)     — Database
├── flask_backend (Python/Flask) — API server (Gunicorn)
└── frontend (React/Nginx)       — Static file server
```

### How to Run

```bash
# Start everything
docker-compose up --build

# Seed demo data (in a second terminal)
docker exec -it peereval-flask flask --app api seed_demo

# Stop
docker-compose down

# Stop and wipe database
docker-compose down -v
```

### What Happens on Startup

1. **PostgreSQL** starts and creates the `peereval` database
2. **Flask backend** waits for Postgres health check, then:
   - Runs `flask init_db` (creates all tables)
   - Runs `flask ensure_admin` (creates admin if env vars set)
   - Starts Gunicorn (production WSGI server)
3. **Frontend** serves the built React app via Nginx

### Dockerfiles

**Backend** (`flask_backend/Dockerfile`):
- Multi-stage build: installs dependencies in a builder stage, copies only the virtual environment to the final image
- Runs as non-root user (security best practice)
- Includes PostgreSQL client libraries

**Frontend** (`frontend/Dockerfile`):
- Multi-stage build: compiles TypeScript + Vite in Node.js, copies static files to Nginx
- Final image is just Nginx + static HTML/JS/CSS

---

## CLI Commands

```bash
flask --app api init_db                    # Create database tables
flask --app api add_users                  # Add sample teacher/student/admin
flask --app api seed_demo                  # Seed full demo dataset
flask --app api add_sample_courses         # Add sample courses
flask --app api create_admin               # Interactive admin creation
flask --app api migrate_assignment_columns # Add new columns (idempotent)
flask --app api migrate_group_reviews      # Add group review columns
```

---

## Demo Credentials

After running `flask seed_demo`:

| Role | Email | Password |
|------|-------|----------|
| Teacher | teacher@demo.com | password |
| Admin | admin@demo.com | password |
| Student | alice@demo.com | password |
| Student | bob@demo.com | password |
| Student | carol@demo.com | password |
| Student | david@demo.com | password |
| Student | emma@demo.com | password |
| Student | frank@demo.com | password |
