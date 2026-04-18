# API Endpoint Summary

This document summarizes all API endpoints for the **Flask backend** (`flask_backend/`). 

> **Note**: The legacy Node.js backend (`backend/`) is no longer actively maintained. The `endpoints.json` file documents the legacy Node endpoints for reference only.

## Authentication Requirements

All protected endpoints require:

- **HTTPOnly Cookie**: JWT token is automatically included by the browser
- **Credentials**: All fetch requests must include `credentials: 'include'`
- **Admin endpoints**: User must have `role = 'admin'`
- **Teacher endpoints**: User must have `role = 'teacher'` or `role = 'admin'`

Obtain JWT token via `POST /auth/login` with valid credentials. The token is automatically stored in an HTTPOnly cookie.

---

## Public Endpoints

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/auth/login` | `{ email, password }` | `200 { id, name, email, role, must_change_password }` | Sets HTTPOnly cookie with JWT token |
| POST | `/auth/register` | `{ name, email, password }` | `201 { msg, user }` | Creates student account |
| GET | `/hello` | — | `{ message: 'Hello, World!' }` | Healthcheck |

---

## Authentication Endpoints

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/auth/login` | `{ email, password }` | `200 { id, name, email, role, must_change_password }` | ✅ Implemented |
| POST | `/auth/register` | `{ name, email, password }` | `201 { msg, user }` | ✅ Implemented |
| POST | `/auth/logout` | — | `200 { msg }` | ✅ Implemented |
| PUT | `/auth/change-password` | `{ current_password, new_password }` | `200 { msg }` | ✅ Change password (any authenticated user) |

---

## User Endpoints

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/user/` | — | `User { id, name, email, role, must_change_password }` | ✅ Get current user |
| PUT | `/user/` | `{ name? }` | `User` | ✅ Update current user (name only) |
| GET | `/user/<id>` | — | `User` | ✅ Get user by ID (self, teacher, or admin) |
| DELETE | `/user/<id>` | — | `{ msg }` | ✅ Delete user (self or admin) |
| PATCH | `/user/password` | `{ current_password, new_password }` | `{ msg }` | ✅ Change password (requires `must_change_password` flag) |

---

## Admin Endpoints

All require `role = 'admin'`.

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/admin/users` | — | `Array<User>` | ✅ List all users |
| POST | `/admin/users/create` | `{ name, email, password, role }` | `User` | ✅ Create user with any role |
| PUT | `/admin/users/<id>/role` | `{ role }` | `User` | ✅ Update user's role |
| DELETE | `/admin/users/<id>` | — | `{ msg }` | ✅ Delete any user |

---

## Class/Course Endpoints

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/class/classes` | — | `Array<Course>` | ✅ Get user's courses |
| GET | `/class/browse_classes` | — | `Array<Course>` | ✅ Get all courses (admin/teacher) |
| POST | `/class/create_class` | `{ name }` | `201 { msg, course }` | ✅ Create course (teacher) |
| POST | `/class/members` | `{ id }` | `Array<User>` | ✅ Get course members |
| POST | `/class/enroll_students` | `{ class_id, students (CSV) }` | `{ msg }` | ✅ Bulk enroll from CSV |

---

## Assignment Endpoints

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/assignment/<course_id>` | — | `Array<Assignment>` | ✅ Get assignments for course |
| GET | `/assignment/detail/<id>` | — | `Assignment` | ✅ Get single assignment |
| POST | `/assignment/create_assignment` | `{ courseID, name, description?, start_date?, rubric?, due_date?, is_anonymous?, individual_reviews?, group_reviews? }` | `{ msg, assignment }` | ✅ Create assignment (teacher/admin only, must own course) |
| PATCH | `/assignment/edit_assignment/<id>` | `{ name?, description?, start_date?, rubric?, due_date?, is_anonymous?, individual_reviews?, group_reviews? }` | `{ msg, assignment, individual_reviews_deleted?, individual_rubric_deleted?, group_reviews_deleted?, group_rubric_deleted? }` | ✅ Edit assignment (teacher/admin only, must own course). Disabling a review type cascade-deletes its rubric and reviews. |
| DELETE | `/assignment/delete_assignment/<id>` | — | `{ msg }` | ✅ Delete assignment (teacher/admin only, must own course) |

---

## Group Endpoints (Course-Level)

> **Important**: Groups belong to **courses**, not assignments. This is a key architectural decision - students remain in the same group for all assignments in a course.

All group endpoints require teacher or admin role.

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/groups/create` | `{ courseID, name }` | `201 { msg, group }` | ✅ Create empty group |
| GET | `/groups/course/<course_id>` | — | `Array<Group>` | ✅ List groups in course |
| GET | `/groups/course/<course_id>/my-group` | — | `{ group, members }` or `404` | ✅ Get student's group & peers |
| GET | `/groups/<group_id>/members` | — | `Array<User>` | ✅ List group members |
| POST | `/groups/members/add` | `{ groupID, userID }` | `{ msg, member }` | ✅ Add student to group |
| POST | `/groups/members/remove` | `{ groupID, userID }` | `{ msg }` | ✅ Remove student from group |
| DELETE | `/groups/<group_id>` | — | `{ msg }` | ✅ Delete group |
| GET | `/groups/course/<course_id>/unassigned` | — | `Array<User>` | ✅ List students not in any group |

### Group Response Shapes

**Group object:**
```json
{
  "id": 1,
  "name": "Group A",
  "courseID": 1
}
```

**Member object (from `/groups/<id>/members`):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}
```

**My-group response:**
```json
{
  "group": { "id": 1, "name": "Group A", "courseID": 1 },
  "members": [
    { "id": 2, "name": "Jane Doe", "email": "jane@example.com" }
  ]
}
```

---

## Rubric Endpoints

Rubrics belong to **assignments** and contain multiple **criteria descriptions** (questions) for peer evaluation. Each assignment can have one **individual** rubric and one **group** rubric, distinguished by `rubric_type`.

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| POST | `/rubric/create` | `{ assignmentID, canComment?, rubric_type? }` | `201 { msg, rubric }` | ✅ Create rubric (teacher). `rubric_type` defaults to `"individual"` |
| GET | `/rubric/<id>` | — | `Rubric { id, assignmentID, canComment, rubric_type }` | ✅ Get rubric by ID |
| GET | `/rubric/assignment/<assignment_id>?rubric_type=X` | — | `Rubric` | ✅ Get rubric for assignment. `rubric_type` defaults to `"individual"` |
| DELETE | `/rubric/<id>` | — | `{ msg }` | ✅ Delete rubric + cascade criteria (teacher) |
| POST | `/rubric/<rubric_id>/criteria` | `{ question, scoreMax?, hasScore? }` | `201 { msg, criterion }` | ✅ Add criterion (teacher) |
| GET | `/rubric/<rubric_id>/criteria` | — | `Array<CriteriaDescription>` | ✅ List criteria for rubric |

### Rubric Response Shapes

**Rubric object:**
```json
{
  "id": 1,
  "assignmentID": 1,
  "canComment": true,
  "rubric_type": "individual"
}
```

**CriteriaDescription object:**
```json
{
  "id": 1,
  "rubricID": 1,
  "question": "How well did the student communicate?",
  "scoreMax": 10,
  "hasScore": true
}
```

---

## Review Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/review/submit` | JWT (any) | Submit a review with criteria (atomic) |
| `PUT` | `/review/<id>` | JWT (any) | Update an existing review (replace criteria atomically) |
| `GET` | `/review/lookup?assignmentID=X&revieweeID=Y&review_type=Z` | JWT (any) | Look up an existing review |
| `GET` | `/review/<id>` | JWT (any) | Get a single review with its criteria |
| `GET` | `/review/assignment/<id>?review_type=X` | JWT (any) | List reviews for an assignment, optionally filtered by type |
| `GET` | `/review/course/<id>/summary` | JWT (any) | Grade summary with individual/group/weighted averages |

**Authorization notes:**
- `submit`: Reviewer is derived from the JWT token (prevents impersonation). Cannot review yourself (individual) or your own group (group). Duplicate reviews return 409. For group reviews, duplicates are checked across all members of the submitter's group. Returns 400 if the assignment has disabled the requested `review_type` (e.g., submitting an individual review when `individual_reviews` is false).
- `PUT /<id>`: For individual reviews, only the original reviewer can edit. For group reviews, any member of the reviewer's group can edit. Replaces all criteria atomically.
- `lookup`: Reviewer is derived from JWT. For group reviews, any group member can look up the review. Returns 404 if no review exists.
- `GET /<id>`: Students can only view reviews they authored or received. Teachers can view any.
- `assignment/<id>`: Teachers see all reviews. Students only see reviews they received. Optional `review_type` filter (`individual` or `group`).
- **Anonymous reviews (US3):** When `assignment.is_anonymous` is `true`, the reviewer identity is replaced with `{ id: null, name: "Anonymous", email: null }` for the reviewee. Teachers always see the real reviewer.
- `course/<id>/summary`: Students see averages based on reviews they received. Teachers see aggregate across all reviews. Teachers can pass `?studentID=X` to get a specific student's summary.

### Review Request Shapes

**POST /review/submit (individual):**
```json
{
  "assignmentID": 1,
  "revieweeID": 3,
  "comments": "Great teamwork overall!",
  "criteria": [
    { "criterionRowID": 5, "grade": 4, "comments": "" },
    { "criterionRowID": 6, "grade": 8, "comments": "" }
  ]
}
```

**POST /review/submit (group):**
```json
{
  "assignmentID": 1,
  "revieweeID": 7,
  "review_type": "group",
  "comments": "Solid presentation by this group.",
  "criteria": [
    { "criterionRowID": 10, "grade": 4, "comments": "" }
  ]
}
```

**PUT /review/<id> (update):**
```json
{
  "assignmentID": 1,
  "revieweeID": 3,
  "comments": "Updated comment",
  "criteria": [
    { "criterionRowID": 5, "grade": 5, "comments": "" }
  ]
}
```

> **Note:** The `comments` field at the top level is the overall review comment (stored on the Review model). Per-criterion `comments` fields exist in the schema but are not currently used by the frontend.

### Review Response Shapes

**Review object (from GET endpoints):**
```json
{
  "id": 1,
  "assignmentID": 1,
  "review_type": "individual",
  "comments": "Great teamwork overall!",
  "reviewer": { "id": 2, "name": "Alice", "email": "alice@test.com" },
  "reviewee": { "id": 3, "name": "Bob", "email": "bob@test.com" },
  "criteria": [
    { "id": 1, "reviewID": 1, "criterionRowID": 5, "criterion_name": "Communication", "score_max": 5, "grade": 4, "comments": "" }
  ]
}
```

**Group review reviewee shape:**
```json
{
  "reviewee": { "id": 7, "name": "Group B", "type": "group" }
}
```

**Submit response (POST /review/submit):**
```json
{
  "msg": "Review submitted",
  "id": 1
}
```

**Update response (PUT /review/<id>):**
```json
{
  "msg": "Review updated"
}
```

**Course grade summary (GET /review/course/<id>/summary):**
```json
{
  "assignments": [
    {
      "id": 1,
      "name": "Peer Review HW",
      "individualReviewCount": 3,
      "individualAverage": 12.5,
      "individualMax": 15,
      "groupReviewCount": 2,
      "groupAverage": 8.0,
      "groupMax": 10
    }
  ],
  "courseAverage": 10.25,
  "courseMax": 12.5,
  "individualAverage": 12.5,
  "individualMax": 15.0,
  "groupAverage": 8.0,
  "groupMax": 10.0
}
```

> **Note:** `courseAverage` is a 50/50 weighted average of `individualAverage` and `groupAverage`. If only one type has reviews, only that type contributes to the course average.

**Query parameters:**
- `studentID` (optional, teacher/admin only): Scope the summary to a specific student's received reviews
- `review_type` (optional, on `/review/assignment/<id>` and `/review/lookup`): Filter by `"individual"` or `"group"`

---

## Submission Endpoints

File upload/download for student assignment submissions.

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/submission/<assignment_id>/mine` | — | `Submission` or `404` | ✅ Get own or group member's submission |
| GET | `/submission/<assignment_id>/student/<student_id>` | — | `{ submission }` or `{ submission: null }` | ✅ View another student's submission (teacher: always, student: must be enrolled) |
| POST | `/submission/<assignment_id>/mine` | `file` (multipart) | `{ msg, submission }` | ✅ Upload/replace own or group submission |
| DELETE | `/submission/<assignment_id>/mine` | — | `{ msg }` | ✅ Delete own or group submission |
| GET | `/submission/file/<submission_id>` | — | File download | ✅ Download own or group member's file |

---

## Assignment Resource Endpoints

Teacher-uploaded supporting documents for assignments (e.g., instructions, rubric PDFs).

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/assignment-resource/assignment/<assignment_id>` | — | `Array<Resource>` | ✅ List resources for assignment |
| POST | `/assignment-resource/assignment/<assignment_id>` | `file` (multipart) | `{ msg, resource }` | ✅ Upload resource (teacher) |
| DELETE | `/assignment-resource/<resource_id>` | — | `{ msg }` | ✅ Delete resource (teacher) |
| GET | `/assignment-resource/file/<resource_id>` | — | File download | ✅ Download resource file |

---

## Gradebook Endpoints

Teacher-facing gradebook with grade overrides for all students in a course.

| Method | Path | Body | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/gradebook/course/<course_id>` | — | `{ assignments, students }` | ✅ Full gradebook data (teacher only) |
| PUT | `/gradebook/course/<course_id>/override` | `{ studentID, assignmentID, overrideScore }` | `{ msg, overrideScore }` | ✅ Set/update grade override |
| DELETE | `/gradebook/course/<course_id>/override` | `{ studentID, assignmentID }` | `{ msg }` | ✅ Clear grade override |
| GET | `/gradebook/course/<course_id>/reviews?studentID=X&assignmentID=Y` | — | `{ individualReviews, groupReviews }` | ✅ Reviews for student+assignment |

---

## Not Yet Implemented (Planned)

These endpoints are planned based on the database schema but not yet implemented in Flask:

| Feature | Endpoints | Notes |
|---------|-----------|-------|
| *(none currently)* | — | — |

---

## Notes

- All endpoints return JSON
- Error responses follow format: `{ "msg": "error message" }` or `{ "error": "message" }`
- HTTPOnly cookies are used for authentication (not Bearer tokens)
- Frontend must always use `credentials: 'include'` for fetch requests
