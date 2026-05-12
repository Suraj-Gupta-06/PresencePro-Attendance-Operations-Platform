"""Class/Course model."""
from datetime import datetime
from app import db


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    schedule = db.Column(db.Text, nullable=True)  # JSON string
    semester = db.Column(db.String(20), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    students = db.relationship("Student", back_populates="class_", lazy="dynamic")
    teacher = db.relationship("User", foreign_keys=[teacher_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "teacher_id": self.teacher_id,
            "schedule": self.schedule,
            "semester": self.semester,
            "year": self.year,
            "student_count": self.students.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Class {self.name}>"
