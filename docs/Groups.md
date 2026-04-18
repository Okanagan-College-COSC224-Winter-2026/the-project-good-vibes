# Group Management

Groups belong to **courses** (not assignments), allowing the same groups to be used across all assignments in a course.

## ⚠️ Database Migration Required

This feature changed the database schema. If you have an existing database, you must drop and recreate it:

```bash
cd flask_backend
source venv/bin/activate
flask --app api drop_db      # Confirm with 'y'
flask --app api init_db
flask --app api add_users    # Recreate sample users
flask --app api add_sample_courses  # Optional: add sample courses
```

**What changed:**
- `CourseGroup` table: `assignmentID` column replaced with `courseID`
- `Group_Members` table: `assignmentID` column removed (groups are now course-level)

---

## Implementation Summary

### Backend Changes

| File | Change |
|------|--------|
| `models/course_group_model.py` | Changed `assignmentID` → `courseID`, updated relationships |
| `models/group_members_model.py` | Removed `assignmentID` column |
| `models/course_model.py` | Added `groups` relationship |
| `models/assignment_model.py` | Removed `groups` and `group_members` relationships |
| `models/schemas.py` | Updated schemas with `include_fk = True` (CourseGroup, GroupMembers, Assignment) |
| `controllers/group_controller.py` | **New file** with 8 group management endpoints |
| `controllers/assignment_controller.py` | Added `GET /assignment/detail/<id>` endpoint |
| `api/__init__.py` | Registered `group_controller` blueprint |

### Frontend Changes

| File | Change |
|------|--------|
| `util/api.ts` | Updated group functions to use `courseId`; added `getAssignment()` |
| `App.tsx` | Changed route from `/assignments/:id/group` to `/classes/:id/groups` |
| `pages/Group.tsx` | Rewrote component for course-level groups |
| `pages/ClassHome.tsx` | Added "Groups" tab to navigation |
| `pages/Assignment.tsx` | Fixed group member loading for peer reviews; removed broken "Group" tab |

### Tests

| File | Status |
|------|--------|
| `tests/test_groups.py` | **15 tests, all passing** |
| `tests/test_assignments.py` | **21 tests, all passing** (added 2 for `get_assignment`) |

---

## API Endpoints

### Group Management (`/groups/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| `POST` | `/groups/create` | Create a new group | Teacher |
| `GET` | `/groups/course/<id>` | List groups for a course | Any |
| `POST` | `/groups/<id>/members` | Add member to group | Teacher |
| `DELETE` | `/groups/<id>/members/<user_id>` | Remove member from group | Teacher |
| `GET` | `/groups/<id>/members` | List group members | Any |
| `GET` | `/groups/course/<id>/unassigned` | List unassigned students | Teacher |
| `DELETE` | `/groups/<id>` | Delete a group | Teacher |
| `GET` | `/groups/course/<id>/my-group` | Student gets their own group | Student |

### Assignment (new endpoint)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| `GET` | `/assignment/detail/<id>` | Get single assignment (includes `courseID`) | Any |

---

## Test Coverage

### Fixtures (Setup Helpers)

| Fixture | Purpose |
|---------|---------|
| `teacher` | Creates a teacher user |
| `students` | Creates 5 student users |
| `course` | Creates a course owned by the teacher |
| `enrolled_students` | Enrolls all students in the course |
| `auth_teacher` | Logs in as teacher (for authenticated requests) |
| `auth_student` | Logs in as student (for permission tests) |

### Tests (15 total)

| Test | What It Verifies |
|------|------------------|
| `test_create_group_as_teacher` | Teacher can create a group |
| `test_create_group_unauthorized_student` | Students cannot create groups |
| `test_create_group_missing_name` | Creating without name fails |
| `test_list_groups_for_course` | List all groups in a course |
| `test_list_groups_empty_course` | Empty list when no groups |
| `test_add_member_to_group` | Add enrolled student to group |
| `test_add_non_enrolled_student_to_group` | Can't add non-enrolled student |
| `test_remove_member_from_group` | Remove student from group |
| `test_list_group_members` | List members of a group |
| `test_list_unassigned_students` | Find students not in any group |
| `test_list_unassigned_all_students` | All students unassigned initially |
| `test_delete_group` | Delete a group |
| `test_delete_group_removes_memberships` | Deleting group removes members |
| `test_student_view_own_group` | Student can see their groupmates |
| `test_student_not_in_group` | 404 if student not in a group |

---

## Implementation Status

- [x] Update `CourseGroup` model (change `assignmentID` → `courseID`)
- [x] Update `Group_Members` model (remove `assignmentID`)
- [x] Create `group_controller.py` with 8 endpoints
- [x] Add `GET /assignment/detail/<id>` endpoint for fetching assignment with `courseID`
- [x] Register blueprint in `__init__.py`
- [x] Update frontend routing and API calls
- [x] Fix `Assignment.tsx` to load group members for peer reviews
- [x] All 88 tests passing (15 group + 21 assignment + others)
- [x] Manual testing verified (teacher can create groups, add/remove students)
- [x] Documentation updated (`schema.sql`, `ENDPOINT_SUMMARY.md`, `database-schema.md`)

## Related Documentation

- **API Reference**: See `docs/dev-guidelines/ENDPOINT_SUMMARY.md` for full endpoint docs
- **Database Schema**: See `docs/schema/database-schema.md` for table definitions
- **SQL Reference**: See `schema.sql` for raw SQL (kept in sync)
