"""FaceImage model — stores paths to student face images."""
from datetime import datetime
from app import db


class FaceImage(db.Model):
    __tablename__ = "face_images"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=False)
    angle = db.Column(db.String(20), nullable=True)  # front / left / right
    quality_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    student = db.relationship("Student", back_populates="face_images")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "image_path": self.image_path,
            "angle": self.angle,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<FaceImage student={self.student_id} angle={self.angle}>"
