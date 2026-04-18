"""
Group management endpoints for course-level groups.

Groups belong to COURSES (not assignments), allowing the same groups
to be used across all assignments in a course.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import User, Course, CourseGroup, Group_Members, User_Course, CourseGroupSchema, UserSchema
from .auth_controller import jwt_teacher_required

bp = Blueprint("groups", __name__, url_prefix="/groups")


# ============================================================================
# CREATE GROUP
# ============================================================================

@bp.route("/create", methods=["POST"])
@jwt_teacher_required
def create_group():
    """
    Create a new group for a course.
    Only teachers (who own the course) can create groups.
    
    Request body:
        - courseID: int (required)
        - name: str (required)
    
    Returns:
        - 201: Group created successfully
        - 400: Missing required fields
        - 403: Not authorized (not the course teacher)
        - 404: Course not found
    """
    data = request.get_json()
    course_id = data.get("courseID")
    name = data.get("name")
    
    # Validate required fields
    if not course_id:
        return jsonify({"msg": "courseID is required"}), 400
    if not name or not name.strip():
        return jsonify({"msg": "name is required"}), 400
    name = name.strip()
    if len(name) > 50:
        return jsonify({"msg": "name must be 50 characters or fewer"}), 400
    
    # Check course exists
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404
    
    # Verify the teacher owns this course
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if course.teacherID != user.id:
        return jsonify({"msg": "You are not authorized to create groups in this course"}), 403
    
    # Create the group
    group = CourseGroup(name=name, courseID=course_id)
    CourseGroup.create_group(group)
    
    return jsonify({
        "id": group.id,
        "name": group.name,
        "courseID": group.courseID
    }), 201


# ============================================================================
# LIST GROUPS
# ============================================================================

@bp.route("/course/<int:course_id>", methods=["GET"])
@jwt_required()
def list_groups(course_id):
    """
    List all groups for a course.
    
    Returns:
        - 200: List of groups
        - 404: Course not found
    """
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404
    
    groups = CourseGroup.query.filter_by(courseID=course_id).all()
    schema = CourseGroupSchema(many=True)
    
    return jsonify(schema.dump(groups)), 200


# ============================================================================
# GROUP MEMBERS - ADD
# ============================================================================

@bp.route("/members/add", methods=["POST"])
@jwt_teacher_required
def add_member():
    """
    Add a student to a group.
    Student must be enrolled in the course.
    
    Request body:
        - groupID: int (required)
        - userID: int (required)
    
    Returns:
        - 200: Member added successfully
        - 400: Missing fields, student not enrolled, or already in group
        - 404: Group or user not found
    """
    data = request.get_json()
    group_id = data.get("groupID")
    user_id = data.get("userID")
    
    if not group_id or not user_id:
        return jsonify({"msg": "groupID and userID are required"}), 400
    
    # Check group exists
    group = CourseGroup.get_by_id(group_id)
    if not group:
        return jsonify({"msg": "Group not found"}), 404
    
    # Check user exists
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Check user is enrolled in the course
    enrollment = User_Course.get(user_id, group.courseID)
    if not enrollment:
        return jsonify({"msg": "Student is not enrolled in this course"}), 400
    
    # Check if already a member
    existing = Group_Members.get(user_id, group_id)
    if existing:
        return jsonify({"msg": "Student is already in this group"}), 400
    
    # Add member
    membership = Group_Members(userID=user_id, groupID=group_id)
    Group_Members.create_group_member(user_id, group_id)
    
    return jsonify({"msg": "Member added successfully"}), 200


# ============================================================================
# GROUP MEMBERS - REMOVE
# ============================================================================

@bp.route("/members/remove", methods=["POST"])
@jwt_teacher_required
def remove_member():
    """
    Remove a student from a group.
    
    Request body:
        - groupID: int (required)
        - userID: int (required)
    
    Returns:
        - 200: Member removed successfully
        - 400: Missing fields
        - 404: Membership not found
    """
    data = request.get_json()
    group_id = data.get("groupID")
    user_id = data.get("userID")
    
    if not group_id or not user_id:
        return jsonify({"msg": "groupID and userID are required"}), 400
    
    # Find the membership
    membership = Group_Members.get(user_id, group_id)
    if not membership:
        return jsonify({"msg": "Member not found in group"}), 404
    
    # Remove member
    membership.delete()
    
    return jsonify({"msg": "Member removed successfully"}), 200


# ============================================================================
# LIST GROUP MEMBERS
# ============================================================================

@bp.route("/<int:group_id>/members", methods=["GET"])
@jwt_required()
def list_group_members(group_id):
    """
    List all members of a group.
    
    Returns:
        - 200: List of members with user info
        - 404: Group not found
    """
    group = CourseGroup.get_by_id(group_id)
    if not group:
        return jsonify({"msg": "Group not found"}), 404
    
    # Get all memberships for this group
    memberships = Group_Members.query.filter_by(groupID=group_id).all()
    
    # Get user details for each member
    members = []
    for membership in memberships:
        user = User.get_by_id(membership.userID)
        if user:
            members.append({
                "id": user.id,
                "name": user.name,
                "email": user.email
            })
    
    return jsonify(members), 200


# ============================================================================
# LIST UNASSIGNED STUDENTS
# ============================================================================

@bp.route("/course/<int:course_id>/unassigned", methods=["GET"])
@jwt_required()
def list_unassigned_students(course_id):
    """
    List all students enrolled in a course who are not in any group.
    
    Returns:
        - 200: List of unassigned students
        - 404: Course not found
    """
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404
    
    # Get all enrolled students
    enrollments = User_Course.query.filter_by(courseID=course_id).all()
    enrolled_user_ids = [e.userID for e in enrollments]
    
    # Get all groups for this course
    course_groups = CourseGroup.query.filter_by(courseID=course_id).all()
    group_ids = [g.id for g in course_groups]
    
    # Get all students who are in any group for this course
    if group_ids:
        assigned_memberships = Group_Members.query.filter(
            Group_Members.groupID.in_(group_ids)
        ).all()
        assigned_user_ids = {m.userID for m in assigned_memberships}
    else:
        assigned_user_ids = set()
    
    # Find unassigned students
    unassigned = []
    for user_id in enrolled_user_ids:
        if user_id not in assigned_user_ids:
            user = User.get_by_id(user_id)
            if user:
                unassigned.append({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                })
    
    return jsonify(unassigned), 200


# ============================================================================
# DELETE GROUP
# ============================================================================

@bp.route("/<int:group_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_group(group_id):
    """
    Delete a group and all its memberships.
    
    Returns:
        - 200: Group deleted successfully
        - 404: Group not found
    """
    group = CourseGroup.get_by_id(group_id)
    if not group:
        return jsonify({"msg": "Group not found"}), 404
    
    # Delete the group (cascade will remove memberships)
    group.delete()
    
    return jsonify({"msg": "Group deleted successfully"}), 200


# ============================================================================
# STUDENT VIEW OWN GROUP
# ============================================================================

@bp.route("/course/<int:course_id>/my-group", methods=["GET"])
@jwt_required()
def get_my_group(course_id):
    """
    Get the current student's group in a course.
    
    Returns:
        - 200: Group info with members
        - 404: Not in any group or course not found
    """
    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Course not found"}), 404
    
    # Get current user
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Get all groups for this course
    course_groups = CourseGroup.query.filter_by(courseID=course_id).all()
    group_ids = [g.id for g in course_groups]
    
    if not group_ids:
        return jsonify({"msg": "Not in any group"}), 404
    
    # Find which group the user is in
    membership = Group_Members.query.filter(
        Group_Members.userID == user.id,
        Group_Members.groupID.in_(group_ids)
    ).first()
    
    if not membership:
        return jsonify({"msg": "Not in any group"}), 404
    
    # Get group details
    group = CourseGroup.get_by_id(membership.groupID)
    
    # Get all members of this group
    group_memberships = Group_Members.query.filter_by(groupID=group.id).all()
    members = []
    for m in group_memberships:
        member_user = User.get_by_id(m.userID)
        if member_user:
            members.append({
                "id": member_user.id,
                "name": member_user.name,
                "email": member_user.email
            })
    
    return jsonify({
        "id": group.id,
        "name": group.name,
        "courseID": group.courseID,
        "members": members
    }), 200
