"""System config API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.system_config import SystemConfig
from src.utils.helpers import success_response, error_response
from src.utils.decorators import admin_required

config_bp = Blueprint("config", __name__)


@config_bp.get("/")
@jwt_required()
@admin_required
def get_config():
    all_config = SystemConfig.query.all()
    return jsonify(*success_response({c.key: c.get_typed_value() for c in all_config}))


@config_bp.put("/")
@jwt_required()
@admin_required
def update_config():
    data = request.get_json(silent=True) or {}
    for key, value in data.items():
        existing = SystemConfig.query.filter_by(key=key).first()
        if existing:
            existing.value = str(value)
        else:
            SystemConfig.set(key, value)
    from app import db
    db.session.commit()
    return jsonify(*success_response(message="Configuration updated."))
