# Test Seed Data

This folder contains reusable seed data for end-to-end/manual testing.

## Files

- `staff-seed.csv`
  - 1 admin + 3 teachers with unique names
  - Columns: `role,name,email,password,must_change_password`
- `students-21-seed.csv`
  - 21 students with unique names in the exact CSV format accepted by `/class/enroll_students`
  - Columns: `id,name,email`

## Quick load workflow (PowerShell)

From repository root:

1. Seed staff users (admin + teachers)

```powershell
./scripts/seed_staff_from_csv.ps1
```

Defaults:
- Admin login used by script: `admin@example.com` / `123456`
- CSV path: `docs/test-data/staff-seed.csv`

2. Enroll 21 students into a class

```powershell
./scripts/enroll_students_from_csv.ps1 -ClassId 1
```

Defaults:
- Teacher login used by script: `teacher@example.com` / `123456`
- CSV path: `docs/test-data/students-21-seed.csv`

## Notes

- Scripts are idempotent-ish for repeated runs:
  - Staff script skips already-existing users.
  - Enroll script relies on backend duplicate-enrollment checks.
- Current backend behavior for new roster-created students uses default password `password123`.
