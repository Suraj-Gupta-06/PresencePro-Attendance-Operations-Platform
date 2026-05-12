"""FaceEmbedding model — stores 128-D dlib face encodings."""
import json
from datetime import datetime
from app import db


class FaceEmbedding(db.Model):
    __tablename__ = "embeddings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    # Store embedding as JSON text (128 floats, ~1KB per row)
    embedding_json = db.Column(db.Text, nullable=False)
    model_version = db.Column(db.String(20), default="dlib-v1")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    student = db.relationship("Student", back_populates="embeddings")

    @property
    def embedding(self):
        """Return embedding as a Python list of floats."""
        return json.loads(self.embedding_json)

    @embedding.setter
    def embedding(self, value):
        """Accept list/numpy array and serialise to JSON."""
        if hasattr(value, "tolist"):
            value = value.tolist()
        self.embedding_json = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<FaceEmbedding student={self.student_id}>"
