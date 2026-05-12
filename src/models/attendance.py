"""Attendance model."""
from app import db
from src.utils.helpers import get_local_now, get_local_date


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=get_local_now)
    date = db.Column(db.Date, default=get_local_date, nullable=False, index=True)
    session = db.Column(db.String(20), default="Morning")  # Morning / Afternoon / Evening
    confidence = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(50), nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(20), default="Auto")  # Auto / Manual
    status = db.Column(db.String(20), default="Present")  # Present / Absent / Late
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_local_now)

    # Relationships
    student = db.relationship("Student", back_populates="attendance_records")
    marker = db.relationship("User", foreign_keys=[marked_by])

    # Composite index for quick cooldown checks
    __table_args__ = (
        db.Index("idx_attendance_student_date", "student_id", "date"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student": {
                "id": self.student.id,
                "student_id": self.student.student_id,
                "name": self.student.name,
                "profile_image": self.student.profile_image,
            } if self.student else None,
            "date": self.date.isoformat() if self.date else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "session": self.session,
            "confidence": self.confidence,
            "location": self.location,
            "image_path": self.image_path,
            "method": self.method,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Attendance student={self.student_id} date={self.date}>"
