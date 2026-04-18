from marshmallow import fields, validate

from .assignment_model import Assignment
from .course_group_model import CourseGroup
from .course_model import Course
from .criteria_description_model import CriteriaDescription
from .criterion_model import Criterion
from .db import db, ma
from .group_members_model import Group_Members
from .review_model import Review
from .rubric_model import Rubric
from .submission_model import Submission
from .user_course_model import User_Course
from .user_model import User

# ============================================================
# USER SCHEMAS
# ============================================================


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Full user schema for serialization (excludes password)"""

    class Meta:
        model = User
        load_instance = True
        include_fk = False  # Don't expose raw foreign keys
        sqla_session = db.session
        exclude = ("hash_pass",)

    # Explicit fields for clarity and validation
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    role = fields.Str(
        dump_default="student", validate=validate.OneOf(["student", "teacher", "admin"])
    )
    must_change_password = fields.Bool(dump_default=False)
    avatar_url = fields.Method("get_avatar_url", dump_only=True)

    def get_avatar_url(self, obj):
        return f"/user/avatar/{obj.id}" if getattr(obj, "avatar_path", None) else None


class UserRegistrationSchema(ma.Schema):
    """Schema for user registration input"""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))


class UserLoginSchema(ma.Schema):
    """Schema for login credentials"""

    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserListSchema(ma.SQLAlchemyAutoSchema):
    """Lightweight user schema for lists (minimal fields)"""

    class Meta:
        model = User
        fields = ("id", "name", "email", "role")
        dump_only = ("id",)


# ============================================================
# COURSE SCHEMAS
# ============================================================


class CourseSchema(ma.SQLAlchemyAutoSchema):
    """Full course schema with nested teacher and students.

    Note: To avoid N+1 queries, use Course.get_by_id_with_relations() or
    Course.get_all_with_relations() when fetching courses for serialization.
    """

    class Meta:
        model = Course
        load_instance = True
        include_fk = False
        sqla_session = db.session

    teacher = fields.Nested(UserListSchema, dump_only=True)
    students = fields.List(fields.Nested(UserListSchema), dump_only=True)


class CourseListSchema(ma.SQLAlchemyAutoSchema):
    """Lightweight course schema for lists"""

    class Meta:
        model = Course
        fields = ("id", "name", "teacherID")
        dump_only = ("id",)
        include_fk = True  # Allow teacherID to be serialized


# ============================================================
# ASSIGNMENT SCHEMAS
# ============================================================


class AssignmentSchema(ma.SQLAlchemyAutoSchema):
    """Full assignment schema"""

    class Meta:
        model = Assignment
        load_instance = True
        include_fk = True  # Include courseID in serialization
        sqla_session = db.session

    course = fields.Nested(CourseListSchema, dump_only=True)


# ============================================================
# RUBRIC & CRITERIA SCHEMAS
# ============================================================


class RubricSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Rubric
        load_instance = True
        include_fk = True
        sqla_session = db.session


class CriteriaDescriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CriteriaDescription
        load_instance = True
        include_fk = True
        sqla_session = db.session


class CriterionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Criterion
        load_instance = True
        include_fk = True
        sqla_session = db.session

    # Pull the human-readable criterion name from the related CriteriaDescription
    criterion_name = fields.Method("get_criterion_name")
    score_max = fields.Method("get_score_max")

    def get_criterion_name(self, obj):
        """Return the question text from the linked CriteriaDescription row."""
        if obj.criterion_row:
            return obj.criterion_row.question
        return None

    def get_score_max(self, obj):
        """Return the maximum possible score from the linked CriteriaDescription row."""
        if obj.criterion_row:
            return obj.criterion_row.scoreMax
        return None


# ============================================================
# REVIEW SCHEMAS
# ============================================================


class ReviewSchema(ma.SQLAlchemyAutoSchema):
    """Full review schema with nested relationships.

    Handles both individual reviews (reviewee is a User) and group reviews
    (reviewee is a CourseGroup).  The ``reviewee`` field is serialized
    manually based on ``review_type``.
    """

    class Meta:
        model = Review
        load_instance = True
        include_fk = False
        sqla_session = db.session

    review_type = fields.Str(dump_only=True)
    reviewer = fields.Nested(UserListSchema, dump_only=True)
    reviewee = fields.Method("get_reviewee")
    assignment = fields.Nested(AssignmentSchema, dump_only=True)

    def get_reviewee(self, obj):
        """Return User data for individual reviews, CourseGroup data for group reviews."""
        if obj.review_type == "group":
            group = CourseGroup.get_by_id(obj.revieweeID)
            if group:
                return {"id": group.id, "name": group.name, "type": "group"}
            return {"id": obj.revieweeID, "name": "Unknown Group", "type": "group"}
        # Individual review — look up User
        user = User.get_by_id(obj.revieweeID)
        if user:
            return UserListSchema().dump(user)
        return {"id": obj.revieweeID, "name": "Unknown User"}


class ReviewListSchema(ma.SQLAlchemyAutoSchema):
    """Lightweight review schema for list endpoints.

    Uses minimal nested data to reduce query complexity.
    For list views, we don't need full assignment details with nested course.
    """

    class Meta:
        model = Review
        fields = ("id", "assignmentID", "comments", "review_type", "reviewer", "reviewee")
        dump_only = ("id",)
        include_fk = True

    review_type = fields.Str(dump_only=True)
    reviewer = fields.Nested(UserListSchema, dump_only=True)
    reviewee = fields.Method("get_reviewee")

    def get_reviewee(self, obj):
        if obj.review_type == "group":
            group = CourseGroup.get_by_id(obj.revieweeID)
            if group:
                return {"id": group.id, "name": group.name, "type": "group"}
            return {"id": obj.revieweeID, "name": "Unknown Group", "type": "group"}
        user = User.get_by_id(obj.revieweeID)
        if user:
            return UserListSchema().dump(user)
        return {"id": obj.revieweeID, "name": "Unknown User"}


# ============================================================
# GROUP SCHEMAS
# ============================================================


class CourseGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CourseGroup
        load_instance = True
        include_fk = True  # Include courseID in serialization
        sqla_session = db.session


class GroupMembersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Group_Members
        load_instance = True
        include_fk = True  # Include userID and groupID in serialization
        sqla_session = db.session


# ============================================================
# JUNCTION TABLE SCHEMAS
# ============================================================


class UserCourseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User_Course
        load_instance = True
        include_fk = False
        sqla_session = db.session


class SubmissionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Submission
        load_instance = True
        include_fk = False
        sqla_session = db.session
