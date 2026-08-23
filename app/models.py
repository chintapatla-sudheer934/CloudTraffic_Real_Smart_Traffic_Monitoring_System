from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="ADMIN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Junction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    zone = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    signal_mode = db.Column(db.String(40), default="ADAPTIVE")
    active = db.Column(db.Boolean, default=True)

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_code = db.Column(db.String(50), unique=True, nullable=False)
    junction_id = db.Column(db.Integer, db.ForeignKey("junction.id"), nullable=False)
    sensor_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default="ONLINE")
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    junction = db.relationship("Junction", backref="sensors")

class TrafficRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    junction_id = db.Column(db.Integer, db.ForeignKey("junction.id"), nullable=False)
    vehicle_count = db.Column(db.Integer, nullable=False)
    average_speed = db.Column(db.Float, nullable=False)
    density = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    junction = db.relationship("Junction")

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    junction_id = db.Column(db.Integer, db.ForeignKey("junction.id"), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    junction = db.relationship("Junction")

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
