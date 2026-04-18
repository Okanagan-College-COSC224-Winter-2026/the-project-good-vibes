"""
Review model for the peer evaluation app.

Supports two review types:
  - "individual": a student reviews another student (revieweeID → User.id)
  - "group": a group reviews another group (reviewerID → User.id who submitted,
    revieweeID → CourseGroup.id). Duplicate prevention checks the submitter's
    group so only one review per source-group/target-group/assignment exists.
"""

from sqlalchemy.orm import joinedload

from .db import db


class Review(db.Model):
    """Review model representing peer evaluations"""

    __tablename__ = "Review"

    id = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey("Assignment.id"), nullable=False, index=True)
    reviewerID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False, index=True)
    # revieweeID intentionally has NO foreign-key constraint because it can
    # reference either a User (individual review) or a CourseGroup (group review).
    revieweeID = db.Column(db.Integer, nullable=False, index=True)
    review_type = db.Column(db.String(20), nullable=False, default="individual")  # "individual" | "group"
    comments = db.Column(db.String(500), nullable=True)

    # relationships
    assignment = db.relationship("Assignment", back_populates="reviews", lazy="joined")
    reviewer = db.relationship(
        "User", foreign_keys=[reviewerID], back_populates="reviews_made", lazy="joined"
    )
    # NOTE: no 'reviewee' relationship — for individual reviews, resolve manually
    # via User.get_by_id(); for group reviews, via CourseGroup.get_by_id().
    criteria = db.relationship(
        "Criterion", back_populates="review", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, assignmentID, reviewerID, revieweeID, review_type="individual", comments=None):
        self.assignmentID = assignmentID
        self.reviewerID = reviewerID
        self.revieweeID = revieweeID
        self.review_type = review_type
        self.comments = comments

    def __repr__(self):
        return f"<Review id={self.id} assignmentID={self.assignmentID}>"

    @classmethod
    def get_by_id(cls, review_id):
        """Get review by ID (relationships are eagerly loaded via lazy='joined')"""
        return db.session.get(cls, int(review_id))

    @classmethod
    def get_by_id_with_relations(cls, review_id):
        """Get review by ID with all relationships explicitly loaded.
        Use this when you need to ensure assignment's course is also loaded."""
        return (
            cls.query.options(joinedload(cls.assignment).joinedload("course"))
            .filter_by(id=int(review_id))
            .first()
        )

    @classmethod
    def get_all_with_relations(cls):
        """Get all reviews with relationships loaded.
        Assignment relationships (reviewer, reviewee, assignment) are
        automatically loaded via lazy='joined'."""
        return cls.query.options(joinedload(cls.assignment).joinedload("course")).all()

    @classmethod
    def create_review(cls, review):
        """Add a new review to the database"""
        db.session.add(review)
        db.session.commit()
        return review

    def update(self):
        """Update review in the database"""
        db.session.commit()

    def delete(self):
        """Delete review from the database"""
        db.session.delete(self)
        db.session.commit()
