"""SystemConfig model — key-value configuration store."""
from datetime import datetime
from app import db


class SystemConfig(db.Model):
    __tablename__ = "system_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    data_type = db.Column(db.String(20), default="string")  # string / int / float / boolean / json
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_typed_value(self):
        """Return value cast to correct Python type."""
        if self.data_type == "int":
            return int(self.value)
        elif self.data_type == "float":
            return float(self.value)
        elif self.data_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.data_type == "json":
            import json
            return json.loads(self.value)
        return self.value

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.get_typed_value(),
            "data_type": self.data_type,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get(cls, key, default=None):
        record = cls.query.filter_by(key=key).first()
        return record.get_typed_value() if record else default

    @classmethod
    def set(cls, key, value, data_type="string", description=None):
        record = cls.query.filter_by(key=key).first()
        if record:
            record.value = str(value)
            record.data_type = data_type
        else:
            record = cls(key=key, value=str(value), data_type=data_type, description=description)
            db.session.add(record)
        db.session.commit()

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"
