"""
Assignment resource model for teacher supporting documents.
"""

from datetime import datetime, timezone

from .db import db


class AssignmentResource(db.Model):
    """Supporting document uploaded by teacher for an assignment."""

    __tablename__ = "AssignmentResource"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    uploaderID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    assignment = db.relationship("Assignment", back_populates="resources", lazy="joined")
    uploader = db.relationship("User", lazy="joined")

    def __init__(self, assignmentID, uploaderID, original_name, path):
        self.assignmentID = assignmentID
        self.uploaderID = uploaderID
        self.original_name = original_name
        self.path = path

    @classmethod
    def get_by_id(cls, resource_id):
        return db.session.get(cls, int(resource_id))

    @classmethod
    def get_for_assignment(cls, assignment_id):
        return (
            cls.query.filter_by(assignmentID=int(assignment_id))
            .order_by(cls.created_at.desc(), cls.id.desc())
            .all()
        )

    @classmethod
    def create(cls, resource):
        db.session.add(resource)
        db.session.commit()
        return resource

    def delete(self):
        db.session.delete(self)
        db.session.commit()