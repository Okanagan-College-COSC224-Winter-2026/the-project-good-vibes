from .db import db


class GradeOverride(db.Model):
    __tablename__ = "GradeOverride"

    id = db.Column(db.Integer, primary_key=True)
    studentID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    courseID = db.Column(db.Integer, db.ForeignKey("Course.id"), nullable=False, index=True)
    override_score = db.Column(db.Float, nullable=False)
    teacherID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "studentID", "assignmentID", "courseID",
            name="uq_student_assignment_course",
        ),
    )

    student = db.relationship("User", foreign_keys=[studentID])
    assignment = db.relationship("Assignment", foreign_keys=[assignmentID])
    course = db.relationship("Course", foreign_keys=[courseID])
    teacher = db.relationship("User", foreign_keys=[teacherID])
