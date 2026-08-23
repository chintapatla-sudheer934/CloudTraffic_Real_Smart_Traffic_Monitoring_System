from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config["SECRET_KEY"] = "cloudtraffic-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(Path(app.instance_path) / "cloudtraffic.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    from .auth import auth_bp
    from .routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        from .models import User, Junction, Sensor, TrafficRecord
        db.create_all()

        if not User.query.filter_by(email="admin@cloudtraffic.local").first():
            db.session.add(User(
                name="System Administrator",
                email="admin@cloudtraffic.local",
                password_hash=generate_password_hash("Admin@123"),
                role="ADMIN"
            ))

        if Junction.query.count() == 0:
            names = [
                ("Central Junction", "North Zone", 13.0827, 80.2707),
                ("College Junction", "East Zone", 13.0732, 80.2609),
                ("Market Junction", "Central Zone", 13.0878, 80.2785),
                ("Bus Stand Junction", "West Zone", 13.0695, 80.2526),
                ("Industrial Junction", "South Zone", 13.0550, 80.2440)
            ]
            for name, zone, lat, lng in names:
                db.session.add(Junction(name=name, zone=zone, latitude=lat, longitude=lng))
            db.session.commit()

        if Sensor.query.count() == 0:
            for i, j in enumerate(Junction.query.all(), 1):
                db.session.add(Sensor(
                    sensor_code=f"SNS-{1000+i}",
                    junction_id=j.id,
                    sensor_type=["CAMERA","RADAR","LOOP","CAMERA","RADAR"][i-1],
                    status="ONLINE",
                    last_seen=datetime.utcnow()
                ))

        if TrafficRecord.query.count() == 0:
            now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            for h in range(24):
                for i, j in enumerate(Junction.query.all()):
                    hour = (now - timedelta(hours=h)).hour
                    rush = 1.55 if hour in (8,9,17,18,19) else 0.8
                    vehicles = int((85 + i*18) * rush + ((h*7+i*5) % 15))
                    speed = max(12, round(55 - vehicles/7, 1))
                    density = min(100, round(vehicles/3, 1))
                    db.session.add(TrafficRecord(
                        junction_id=j.id,
                        vehicle_count=vehicles,
                        average_speed=speed,
                        density=density,
                        recorded_at=now - timedelta(hours=h)
                    ))

        db.session.commit()

    return app
