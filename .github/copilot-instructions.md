# Copilot / AI agent instructions — Peer-Evaluation-App-V1

These notes help AI agents be productive quickly in this repo. Keep edits small, lean on existing tests, and don't touch secrets.

## Big picture — dual backend architecture
**Important**: This repo has TWO separate backends in transition:
1. **`flask_backend/`** (Python Flask) — Active backend, use this for new work
   - JWT auth via HTTPOnly cookies (Flask-JWT-Extended)
   - SQLAlchemy ORM + Marshmallow schemas
   - Dev DB: SQLite (instance/app.sqlite), Prod: PostgreSQL
2. **`backend/`** (Node.js/Fastify + Sequelize) — Legacy/reference implementation
   - MariaDB backend (via docker-compose)
   - Do NOT modify unless explicitly requested

**`frontend/`** (React + TypeScript + Vite) talks to Flask backend at `http://localhost:5000` (dev) via `frontend/src/util/api.ts` (BASE_URL constant).

## Role-based access control (RBAC)
System uses three roles (`student`, `teacher`, `admin`) stored in `User.role` field:
- **Students**: Can register via `/auth/register`, view own profile, submit work, upload attachments
- **Teachers**: All student perms + create courses/assignments, manage groups, upload resources, create rubrics, view any user profile
- **Admins**: All perms + user management via `/admin/*` endpoints, cannot self-delete/demote

Key files: `flask_backend/api/models/user_model.py` (role validation + helper methods `is_teacher()`, `is_admin()`, `has_role(*roles)`), `flask_backend/api/controllers/auth_controller.py` (decorators: `jwt_role_required`, `jwt_admin_required`, `jwt_teacher_required`).

## Files to know (Flask backend only)
- Entry point: `flask_backend/api/__init__.py` (Flask app factory, CORS, JWT cookie config, blueprint registration)
- Controllers: `flask_backend/api/controllers/{auth_controller.py,user_controller.py,admin_controller.py,class_controller.py,assignment_controller.py,assignment_resource_controller.py,group_controller.py,rubric_controller.py,submission_controller.py,review_controller.py,gradebook_controller.py}`
- Models: `flask_backend/api/models/{db.py,user_model.py,course_model.py,user_course_model.py,assignment_model.py,assignment_resource_model.py,group_model.py,group_members_model.py,submission_model.py,review_model.py,rubric_model.py,criteria_description_model.py,criterion_model.py,grade_override_model.py,schemas.py}`
- Services (reusable business logic): `flask_backend/api/services/{grade_service.py,progress_service.py,review_masking.py,review_tracking.py,group_service.py}` — Grade calculation, review progress tracking, anonymity/identity masking, and group utilities extracted from controllers for modularity and reuse
- Tests (truth): `flask_backend/tests/{conftest.py,test_login.py,test_user.py,test_model.py,test_assignments.py,test_assignment_resources.py,test_assignment_schema.py,test_change_password.py,test_classes.py,test_course_schema.py,test_groups.py,test_group_reviews.py,test_review_schema.py,test_reviews.py,test_rubrics.py,test_submissions.py,test_submission_access.py,test_gradebook.py,test_review_settings_cascade.py}` — pytest with in-memory SQLite
- CLI: `flask_backend/api/cli/database.py` — commands: `flask init_db`, `flask drop_db`, `flask add_users`, `flask add_sample_courses`, `flask create_admin`, `flask ensure_admin`, `flask migrate_assignment_columns`, `flask migrate_assignment_resources`, `flask migrate_review_comments`, `flask migrate_group_reviews`, `flask migrate_course_image`, `flask migrate_user_avatar`
- Frontend contract: `frontend/src/util/api.ts` (all fetch calls include `credentials: 'include'` for cookies), `frontend/src/util/login.ts` (role helpers: `getUserRole()`, `isAdmin()`, `isTeacher()`)

## Dev workflows (local — Flask backend)
**Windows (PowerShell):**
```powershell
cd flask_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
pip install -r requirements-dev.txt
flask init_db              # Create database
flask add_users            # Add sample users (student, teacher, admin)
flask --app api run        # Start server on http://localhost:5000
```
**macOS/Linux:**
```bash
cd flask_backend
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
flask init_db
flask add_users
flask run                  # Port 5000
```
**Tests:** `cd flask_backend && pytest` (or `pytest tests/test_login.py -v` for specific tests)

**Frontend (same across all OS):**
```bash
cd frontend
npm install                # or: pnpm install (pnpm-workspace.yaml exists but npm works too)
npm run dev                # http://localhost:3000 (strict port, fails if busy)
```

**Docker (entire stack):**
```bash
docker-compose up          # Starts mariadb (port 33123), legacy backend (8081), frontend (3000)
```
Note: Docker uses the legacy Node backend at port 8081, not Flask at 5000. For local dev, run Flask + frontend separately.

## Auth pattern (HTTPOnly cookies + JWT)
**Critical security change (see `docs/HTTPONLY_COOKIES_MIGRATION.md`):**
- Tokens stored in **HTTPOnly cookies** (not localStorage), preventing XSS theft
- `/auth/login` returns `UserSchema` dump: `{ id, name, email, role, must_change_password }` (NO `access_token` in JSON)
- `/auth/logout` clears cookies via `unset_jwt_cookies()`
- All frontend requests include `credentials: 'include'` (axios/fetch)
- **Never** send `Authorization: Bearer` headers — cookies auto-attach
- Test client (`flask.testing.FlaskClient`) handles cookies automatically

Example flow:
```python
# Backend: flask_backend/api/controllers/auth_controller.py
response = jsonify(role=user.role, user_id=user.id, name=user.name)
set_access_cookies(response, access_token)  # Sets httponly cookie
```
```typescript
// Frontend: frontend/src/util/api.ts
const response = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
  credentials: 'include'  // Must include for cookies
});
```

## Conventions and patterns
- **Blueprints per feature:** Register in `flask_backend/api/__init__.py` (e.g., `app.register_blueprint(auth_controller.bp)`)
- **Marshmallow schemas:** Use for JSON serialization (see `UserSchema(exclude=['password'])` in controllers)
- **Never expose passwords:** Always exclude from schemas and responses
- **Tests as contract:** Changes must pass existing tests (`test_login.py`, `test_user.py`, `test_model.py`) — no guessing
- **Keep docs in sync:** When adding or modifying models, controllers, endpoints, or CLI commands, update the corresponding documentation:
  - New/changed model → `docs/schema/database-schema.md`
  - New/changed endpoint → `docs/dev-guidelines/ENDPOINT_SUMMARY.md`
  - New/changed controller or model file → `Files to know` section in this file
  - New CLI command → CLI list in this file
  - Structural changes → `docs/ARCHITECTURE_OVERVIEW.md`
- **Role checks:** Use decorators (`@jwt_role_required('admin')`) or model methods (`user.is_admin()`, `user.has_role('teacher', 'admin')`)
- **Config hierarchy:** Defaults in `api/__init__.py`, overrides in `api/config.py` (not committed), env vars for secrets

## Database schema changes
When adding new columns to a SQLAlchemy model, **always** provide a migration path so existing dev databases don't break:
1. Add the column to the model as `nullable=True` (so old rows survive)
2. Write (or extend) a CLI migration command in `flask_backend/api/cli/database.py` that uses `ALTER TABLE ... ADD COLUMN` for each new column (idempotent — check if the column exists first)
3. Register the command in `init_app()` and document it in this file's CLI list above
4. Mention the migration command in your PR description so other developers know to run it

**Never** tell developers to drop and recreate the database as the first option. Always check `flask_backend/api/cli/database.py` for an existing migration command first (e.g., `flask migrate_assignment_columns`). Only use `flask drop_db` + `flask init_db` as a last resort.

## Documentation updates (mandatory)
When you change **models, endpoints, request/response shapes, or CLI commands**, you **must** update the matching documentation in the same set of edits — not as a follow-up. Treat this the same as writing tests: the feature is not done until the docs match the code.

**Checklist — review every item on every change:**
1. `docs/dev-guidelines/ENDPOINT_SUMMARY.md` — request/response examples, auth notes, endpoint tables
2. `docs/schema/database-schema.md` — entity field lists and descriptions
3. `docs/schema/schema.puml` — PlantUML ER diagram (entity fields + relationships)
4. `docs/schema/database-schema.puml` — UML class diagram (class fields)
5. `docs/ARCHITECTURE_OVERVIEW.md` — data flow examples, entity descriptions, workflow diagrams
6. `.github/copilot-instructions.md` — CLI command list, "Files to know" paths, conventions

**Not every file will need a change every time** — but you must check all six. If a file doesn't need updating, move on. If it does, update it in the same commit/PR as the code change.

## Known gaps and integration points
- **Endpoints.json vs reality:** `docs/dev-guidelines/endpoints.json` is a legacy Node API spec (for reference only). Many routes exist in Node `backend/src/routes/` but NOT in Flask. When implementing missing endpoints, use Flask patterns (blueprints + Marshmallow) and add tests.
- **Review endpoints not yet built:** The Review model exists but there is no review controller yet. Frontend review submission calls will 404 until implemented.
- **Frontend assumes Node backend shape:** Some frontend code may expect responses matching Node routes. Check `endpoints.json` for field names when implementing Flask equivalents.
- **Port confusion:** Frontend `BASE_URL` points to 5000 (Flask), but Docker runs Node backend on 8081. Adjust per deployment.

## Quick reference
**Add a new Flask route:**
1. Create handler in `flask_backend/api/controllers/your_controller.py` (or add to existing)
2. Use decorators: `@bp.route('/path', methods=['POST'])`, `@jwt_role_required('teacher')`
3. Register blueprint in `flask_backend/api/__init__.py` if new controller
4. Write test in `flask_backend/tests/test_your_feature.py` (use `client.post()`, assertions on `response.get_json()`)

**Add a user via CLI:**
```bash
flask create_admin              # Prompts for name, email, password (creates admin)
flask add_users                 # Adds sample student/teacher/admin users
```

**Check database:**
```bash
sqlite3 flask_backend/instance/app.sqlite
.tables
SELECT id, name, email, role FROM User;
```

**Migrate legacy Node endpoint to Flask:**
1. Read `backend/src/routes/your_route.ts` for logic
2. Translate Sequelize queries to SQLAlchemy (e.g., `User.findOne()` → `User.query.filter_by().first()`)
3. Match response shape from `endpoints.json` using Marshmallow schema
4. Add test covering Node behavior
5. Update frontend if response differs

## Git Workflow

- **Base branch:** Always use `dev` as the base branch. Never touch `main`.
- **Branch naming:** Use prefixes like `feature/`, `bug/`, `fix/`, `chore/`.
- **Commits:** Use conventional commit messages (e.g., `fix(frontend): ...`, `feat(api): ...`).
- **Pull requests:** Each PR should address one thing (single responsibility).
- **Before creating a branch:** Always pull latest from `dev` first.

## Learning Mode

This project is being used as a learning environment. When assisting:

1. **Explain the "why"** — Don't just provide code; explain the reasoning behind decisions
2. **Teach concepts** — When introducing new patterns, tools, or commands, briefly explain what they do
3. **Offer alternatives** — Show different approaches when relevant (e.g., "You could also do X, but Y is better here because...")
4. **Encourage understanding** — Before running commands, explain what they will do
5. **Build on prior knowledge** — Reference concepts we've covered before rather than re-explaining from scratch
6. **Ask clarifying questions** — When the user's intent is unclear, ask rather than assume
7. **Highlight gotchas** — Point out common mistakes or edge cases related to what we're doing

