"""
Tests for course-level group management functionality.

Groups belong to COURSES (not assignments), allowing the same groups
to be used across all assignments in a course.

TDD: These tests are written FIRST before implementation.
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import User, Course, CourseGroup, Group_Members, User_Course
from api.models.db import db as _db


# ============================================================================
# FIXTURES - Setup helpers for tests
# ============================================================================

@pytest.fixture
def teacher(db):
    """Create a teacher user"""
    teacher = User(
        name="Test Teacher",
        email="teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher"
    )
    db.session.add(teacher)
    db.session.commit()
    return teacher


@pytest.fixture
def students(db):
    """Create 5 student users for testing group assignments"""
    student_list = []
    for i in range(5):
        student = User(
            name=f"Student {i+1}",
            email=f"student{i+1}@test.com",
            hash_pass=generate_password_hash("password123"),
            role="student"
        )
        db.session.add(student)
        student_list.append(student)
    db.session.commit()
    return student_list


@pytest.fixture
def course(db, teacher):
    """Create a course owned by the teacher"""
    course = Course(teacherID=teacher.id, name="Test Course")
    db.session.add(course)
    db.session.commit()
    return course


@pytest.fixture
def enrolled_students(db, course, students):
    """Enroll all students in the course"""
    for student in students:
        enrollment = User_Course(userID=student.id, courseID=course.id)
        db.session.add(enrollment)
    db.session.commit()
    return students


@pytest.fixture
def auth_teacher(test_client, teacher):
    """Login as teacher and return the authenticated client"""
    test_client.post("/auth/login", json={
        "email": "teacher@test.com",
        "password": "password123"
    })
    return test_client


@pytest.fixture
def auth_student(test_client, students):
    """Login as the first student and return the authenticated client"""
    test_client.post("/auth/login", json={
        "email": "student1@test.com",
        "password": "password123"
    })
    return test_client


# ============================================================================
# TEST: Create Group
# ============================================================================

def test_create_group_as_teacher(auth_teacher, course):
    """
    GIVEN a teacher is logged in and owns a course
    WHEN they create a new group for that course
    THEN the group should be created successfully
    """
    response = auth_teacher.post("/groups/create", json={
        "courseID": course.id,
        "name": "Group Alpha"
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["name"] == "Group Alpha"
    assert data["courseID"] == course.id


def test_create_group_unauthorized_student(auth_student, course):
    """
    GIVEN a student is logged in
    WHEN they try to create a group
    THEN they should be denied (403 Forbidden)
    """
    response = auth_student.post("/groups/create", json={
        "courseID": course.id,
        "name": "Sneaky Group"
    })
    
    assert response.status_code == 403


def test_create_group_missing_name(auth_teacher, course):
    """
    GIVEN a teacher is logged in
    WHEN they try to create a group without a name
    THEN they should get a 400 Bad Request
    """
    response = auth_teacher.post("/groups/create", json={
        "courseID": course.id
    })
    
    assert response.status_code == 400


# ============================================================================
# TEST: List Groups
# ============================================================================

def test_list_groups_for_course(auth_teacher, course, db):
    """
    GIVEN a course has multiple groups
    WHEN the teacher requests the group list
    THEN all groups should be returned
    """
    # Create groups directly in DB for this test
    group1 = CourseGroup(name="Group A", courseID=course.id)
    group2 = CourseGroup(name="Group B", courseID=course.id)
    db.session.add_all([group1, group2])
    db.session.commit()
    
    response = auth_teacher.get(f"/groups/course/{course.id}")
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    names = [g["name"] for g in data]
    assert "Group A" in names
    assert "Group B" in names


def test_list_groups_empty_course(auth_teacher, course):
    """
    GIVEN a course has no groups
    WHEN the teacher requests the group list
    THEN an empty list should be returned
    """
    response = auth_teacher.get(f"/groups/course/{course.id}")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data == []


# ============================================================================
# TEST: Add Member to Group
# ============================================================================

def test_add_member_to_group(auth_teacher, course, enrolled_students, db):
    """
    GIVEN a group exists and a student is enrolled in the course
    WHEN the teacher adds the student to the group
    THEN the student should become a group member
    """
    # Create a group
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    student = enrolled_students[0]
    
    response = auth_teacher.post("/groups/members/add", json={
        "groupID": group.id,
        "userID": student.id
    })
    
    assert response.status_code == 200
    
    # Verify membership in database
    membership = Group_Members.query.filter_by(
        groupID=group.id, 
        userID=student.id
    ).first()
    assert membership is not None


def test_add_non_enrolled_student_to_group(auth_teacher, course, students, db):
    """
    GIVEN a group exists but a student is NOT enrolled in the course
    WHEN the teacher tries to add them to the group
    THEN it should fail with 400 Bad Request
    """
    # Create a group (students are NOT enrolled in this test)
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    response = auth_teacher.post("/groups/members/add", json={
        "groupID": group.id,
        "userID": students[0].id  # Not enrolled
    })
    
    assert response.status_code == 400
    assert "not enrolled" in response.get_json()["msg"].lower()


# ============================================================================
# TEST: Remove Member from Group
# ============================================================================

def test_remove_member_from_group(auth_teacher, course, enrolled_students, db):
    """
    GIVEN a student is in a group
    WHEN the teacher removes them
    THEN the student should no longer be in the group
    """
    # Create group and add member
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    student = enrolled_students[0]
    membership = Group_Members(userID=student.id, groupID=group.id)
    db.session.add(membership)
    db.session.commit()
    
    response = auth_teacher.post("/groups/members/remove", json={
        "groupID": group.id,
        "userID": student.id
    })
    
    assert response.status_code == 200
    
    # Verify removal
    membership = Group_Members.query.filter_by(
        groupID=group.id, 
        userID=student.id
    ).first()
    assert membership is None


# ============================================================================
# TEST: List Group Members
# ============================================================================

def test_list_group_members(auth_teacher, course, enrolled_students, db):
    """
    GIVEN a group has multiple members
    WHEN the teacher requests the member list
    THEN all members should be returned with their info
    """
    # Create group and add members
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    for student in enrolled_students[:3]:  # Add first 3 students
        membership = Group_Members(userID=student.id, groupID=group.id)
        db.session.add(membership)
    db.session.commit()
    
    response = auth_teacher.get(f"/groups/{group.id}/members")
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3


# ============================================================================
# TEST: List Unassigned Students
# ============================================================================

def test_list_unassigned_students(auth_teacher, course, enrolled_students, db):
    """
    GIVEN some students are in groups and some are not
    WHEN the teacher requests unassigned students
    THEN only students not in any group should be returned
    """
    # Create a group and add only 2 of 5 students
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    for student in enrolled_students[:2]:  # Add first 2 students to group
        membership = Group_Members(userID=student.id, groupID=group.id)
        db.session.add(membership)
    db.session.commit()
    
    response = auth_teacher.get(f"/groups/course/{course.id}/unassigned")
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3  # 5 enrolled - 2 in group = 3 unassigned


def test_list_unassigned_all_students(auth_teacher, course, enrolled_students):
    """
    GIVEN no groups exist (all students unassigned)
    WHEN the teacher requests unassigned students
    THEN all enrolled students should be returned
    """
    response = auth_teacher.get(f"/groups/course/{course.id}/unassigned")
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 5  # All 5 students are unassigned


# ============================================================================
# TEST: Delete Group
# ============================================================================

def test_delete_group(auth_teacher, course, db):
    """
    GIVEN a group exists
    WHEN the teacher deletes it
    THEN the group should be removed
    """
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    group_id = group.id
    
    response = auth_teacher.delete(f"/groups/{group_id}")
    
    assert response.status_code == 200
    
    # Verify deletion
    deleted_group = CourseGroup.query.get(group_id)
    assert deleted_group is None


def test_delete_group_removes_memberships(auth_teacher, course, enrolled_students, db):
    """
    GIVEN a group has members
    WHEN the teacher deletes the group
    THEN all memberships should also be removed (cascade)
    """
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    # Add members
    for student in enrolled_students[:2]:
        membership = Group_Members(userID=student.id, groupID=group.id)
        db.session.add(membership)
    db.session.commit()
    group_id = group.id
    
    response = auth_teacher.delete(f"/groups/{group_id}")
    
    assert response.status_code == 200
    
    # Verify memberships are gone too
    memberships = Group_Members.query.filter_by(groupID=group_id).all()
    assert len(memberships) == 0


# ============================================================================
# TEST: Student View Own Group
# ============================================================================

def test_student_view_own_group(test_client, course, enrolled_students, db):
    """
    GIVEN a student is in a group
    WHEN they request their group info
    THEN they should see their group and groupmates
    """
    # Create group and add members
    group = CourseGroup(name="Group A", courseID=course.id)
    db.session.add(group)
    db.session.commit()
    
    for student in enrolled_students[:3]:
        membership = Group_Members(userID=student.id, groupID=group.id)
        db.session.add(membership)
    db.session.commit()
    
    # Login as one of the students in the group
    test_client.post("/auth/login", json={
        "email": "student1@test.com",
        "password": "password123"
    })
    
    response = test_client.get(f"/groups/course/{course.id}/my-group")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Group A"
    assert len(data["members"]) == 3


def test_student_not_in_group(test_client, course, enrolled_students, db):
    """
    GIVEN a student is enrolled but not in any group
    WHEN they request their group info
    THEN they should get a 404 or empty response
    """
    # Login as student (who is not in any group)
    test_client.post("/auth/login", json={
        "email": "student1@test.com",
        "password": "password123"
    })
    
    response = test_client.get(f"/groups/course/{course.id}/my-group")
    
    assert response.status_code == 404
