"""Student model."""
from datetime import datetime
from app import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    department = db.Column(db.String(50), nullable=True, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True)
    roll_no = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="student")
    class_ = db.relationship("Class", back_populates="students")
    attendance_records = db.relationship("Attendance", back_populates="student", lazy="dynamic", cascade="all, delete-orphan")
    face_images = db.relationship("FaceImage", back_populates="student", lazy="dynamic", cascade="all, delete-orphan")
    embeddings = db.relationship("FaceEmbedding", back_populates="student", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_stats=False):
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "class_id": self.class_id,
            "roll_no": self.roll_no,
            "dob": self.dob.isoformat() if self.dob else None,
            "gender": self.gender,
            "profile_image": self.profile_image,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_stats:
            total = self.attendance_records.count()
            data["attendance_count"] = total
        return data

    def __repr__(self):
        return f"<Student {self.student_id} — {self.name}>"
