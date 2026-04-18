# US15 – Course Page Shows Assignments

## Summary

Implements US15 by showing assignments on the course page (Class Home) with key metadata (due date and status). Teachers can open a course and immediately see what they have created.

## Capabilities (Checklist)

- Dashboard lists each course created by the teacher
- Course page shows assignments for that course
- Each assignment displays metadata:
	- Due date (or No due date)
	- Status (Upcoming or Overdue)
- Assignment rows are clickable and open the assignment page

## Changes

### Frontend (React/TypeScript)

- Updated [frontend/src/pages/Home.tsx](frontend/src/pages/Home.tsx)
	- Restored dashboard to course cards with assignment counts


- Updated [frontend/src/pages/ClassHome.tsx](frontend/src/pages/ClassHome.tsx)
	- Renders assignment list with due date and status on course page
	- Computes due date display and status
	- Keeps assignment rows linked to `/assignments/<id>`

- Updated [frontend/src/pages/ClassHome.css](frontend/src/pages/ClassHome.css)
	- Styles assignment list and status badges
	- Adds visual distinction for upcoming vs overdue status

### Backend (Flask)

- Existing endpoint already returns assignment metadata used by the course page:
	- `GET /assignment/<course_id>`

- Added tests in [flask_backend/tests/test_assignments.py](flask_backend/tests/test_assignments.py)
	- Assignment list includes `due_date` when set
	- Assignment list includes `due_date: null` when unset

## Testing

Automated (from `flask_backend`):

```powershell
python -m flask --app api init_db
python -m pytest tests/test_assignments.py -k "due_date_metadata or missing_due_date_metadata" -q
```

Frontend checks (from `frontend`):

```powershell
npm run lint
npm run build
```

Manual:

1. Start backend: `python -m flask --app api run`
2. Start frontend: `npm run dev`
3. Open `/home`, then open any course
4. Verify the course page lists assignments with due date + status
5. Click an assignment row and confirm navigation to `/assignments/<id>`

### Manual Verification Matrix

| Check | Expected Result |
|---|---|
| Course page loads assignments | Assignment rows are visible in Class Home |
| Assignment with future due date | Badge shows `Upcoming` |
| Assignment with past due date | Badge shows `Overdue` |
| Assignment with no due date | Due text shows `No due date` and badge reflects no due date state |
| Click assignment row | Navigates to `/assignments/<id>` |