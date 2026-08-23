from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Junction, Sensor, TrafficRecord, Alert, AuditLog
from .services import latest, prediction as traffic_prediction, series, traffic_level, signal_recommendation

main_bp = Blueprint("main", __name__)

def audit(action, details):
    db.session.add(AuditLog(action=action, details=details, user_id=current_user.id))
    db.session.commit()

@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard")) if current_user.is_authenticated else redirect(url_for("auth.login"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    junctions = Junction.query.filter_by(active=True).all()
    data = []
    for j in junctions:
        t = latest(j.id)
        data.append({"id":j.id,"name":j.name,"zone":j.zone,"latitude":j.latitude,"longitude":j.longitude,
                     "vehicles":t["vehicles"],"speed":t["speed"],"density":t["density"],"level":t["level"]})
    vehicles = sum(x["vehicles"] for x in data)
    avg = round(sum(x["density"] for x in data)/len(data),1) if data else 0
    alerts = Alert.query.filter_by(resolved=False).count()
    online = Sensor.query.filter_by(status="ONLINE").count()
    return render_template("dashboard.html", junctions=junctions, data=data, vehicles=vehicles, avg=avg, alerts=alerts, online=online)

@main_bp.route("/monitor")
@login_required
def monitor():
    junctions = Junction.query.filter_by(active=True).all()
    selected = request.args.get("junction", type=int)
    ids = [j.id for j in junctions]
    if selected not in ids: selected = junctions[0].id if junctions else None
    junction = db.session.get(Junction, selected) if selected else None
    records = TrafficRecord.query.filter_by(junction_id=selected).order_by(TrafficRecord.recorded_at.desc()).limit(50).all() if selected else []
    return render_template("monitor.html", junctions=junctions, selected=selected, junction=junction, records=records)

@main_bp.route("/telemetry", methods=["POST"])
@login_required
def telemetry():
    junction_id = request.form.get("junction_id", type=int)
    vehicles = request.form.get("vehicles", type=int)
    speed = request.form.get("speed", type=float)
    density = request.form.get("density", type=float)
    if junction_id is None or vehicles is None or speed is None or density is None:
        flash("All telemetry fields are required.", "danger")
        return redirect(url_for("main.monitor"))
    j = db.session.get(Junction, junction_id)
    if not j:
        flash("Junction not found.", "danger")
        return redirect(url_for("main.monitor"))
    density = max(0,min(100,density))
    db.session.add(TrafficRecord(junction_id=j.id,vehicle_count=max(0,vehicles),average_speed=max(0,speed),density=density))
    if density >= 80 or speed < 15:
        db.session.add(Alert(junction_id=j.id,severity="CRITICAL",message=f"{j.name}: severe congestion detected."))
    elif density >= 60:
        db.session.add(Alert(junction_id=j.id,severity="WARNING",message=f"{j.name}: high traffic density detected."))
    db.session.commit()
    audit("TELEMETRY_RECEIVED",f"{j.name}: vehicles={vehicles}, speed={speed}, density={density}")
    flash("Telemetry received successfully.","success")
    return redirect(url_for("main.monitor", junction=j.id))

@main_bp.route("/prediction")
@login_required
def prediction_page():
    rows=[]
    for j in Junction.query.filter_by(active=True).all():
        current=latest(j.id)
        rows.append({"junction":j,"current":current,"prediction":traffic_prediction(j.id),"signal":signal_recommendation(current["density"])})
    return render_template("prediction.html",rows=rows)

@main_bp.route("/junctions", methods=["GET","POST"])
@login_required
def junctions():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        zone=request.form.get("zone","").strip()
        lat=request.form.get("latitude",type=float)
        lng=request.form.get("longitude",type=float)
        if not name or not zone or lat is None or lng is None:
            flash("Complete all junction fields.","danger")
            return redirect(url_for("main.junctions"))
        if Junction.query.filter_by(name=name).first():
            flash("Junction already exists.","danger")
            return redirect(url_for("main.junctions"))
        db.session.add(Junction(name=name,zone=zone,latitude=lat,longitude=lng))
        db.session.commit()
        audit("JUNCTION_CREATED",f"Created junction: {name}")
        flash("Junction created.","success")
    return render_template("junctions.html",junctions=Junction.query.order_by(Junction.name).all())

@main_bp.route("/sensors", methods=["GET","POST"])
@login_required
def sensors():
    if request.method=="POST":
        code=request.form.get("sensor_code","").strip()
        jid=request.form.get("junction_id",type=int)
        stype=request.form.get("sensor_type","CAMERA")
        if not code or jid is None:
            flash("Sensor code and junction are required.","danger")
            return redirect(url_for("main.sensors"))
        if Sensor.query.filter_by(sensor_code=code).first():
            flash("Sensor code already exists.","danger")
            return redirect(url_for("main.sensors"))
        db.session.add(Sensor(sensor_code=code,junction_id=jid,sensor_type=stype,status="ONLINE"))
        db.session.commit()
        audit("SENSOR_REGISTERED",f"Registered sensor: {code}")
        flash("Sensor registered.","success")
    return render_template("sensors.html",sensors=Sensor.query.order_by(Sensor.sensor_code).all(),junctions=Junction.query.order_by(Junction.name).all())

@main_bp.route("/alerts")
@login_required
def alerts():
    return render_template("alerts.html",alerts=Alert.query.order_by(Alert.created_at.desc()).limit(100).all())

@main_bp.route("/alert/<int:id>/resolve",methods=["POST"])
@login_required
def resolve(id):
    a=Alert.query.get_or_404(id)
    a.resolved=True
    db.session.commit()
    audit("ALERT_RESOLVED",f"Resolved alert {id}")
    flash("Alert resolved.","success")
    return redirect(url_for("main.alerts"))

@main_bp.route("/analytics")
@login_required
def analytics():
    junctions=Junction.query.filter_by(active=True).all()
    selected=request.args.get("junction",type=int)
    ids=[j.id for j in junctions]
    if selected not in ids: selected=junctions[0].id if junctions else None
    junction=db.session.get(Junction,selected) if selected else None
    return render_template("analytics.html",junctions=junctions,selected=selected,junction=junction,series=series(selected) if selected else [])

@main_bp.route("/audit")
@login_required
def audit_logs():
    return render_template("audit.html",logs=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(150).all())

@main_bp.route("/api/live")
@login_required
def api_live():
    result=[]
    for j in Junction.query.filter_by(active=True).all():
        t=latest(j.id)
        result.append({"id":j.id,"junction":j.name,"zone":j.zone,"latitude":j.latitude,"longitude":j.longitude,
                       "vehicles":t["vehicles"],"speed":t["speed"],"density":t["density"],"level":t["level"]})
    return jsonify(result)

@main_bp.route("/api/predictions")
@login_required
def api_predictions():
    result=[]
    for j in Junction.query.filter_by(active=True).all():
        p=traffic_prediction(j.id)
        result.append({"id":j.id,"junction":j.name,"zone":j.zone,"vehicles":p["vehicles"],"density":p["density"],"level":p["level"]})
    return jsonify(result)

@main_bp.route("/api/telemetry",methods=["POST"])
@login_required
def api_telemetry():
    data=request.get_json(silent=True) or {}
    required=["junction_id","vehicles","speed","density"]
    missing=[x for x in required if x not in data]
    if missing: return jsonify({"error":"Missing fields","missing":missing}),400
    j=db.session.get(Junction,int(data["junction_id"]))
    if not j: return jsonify({"error":"Junction not found"}),404
    density=max(0,min(100,float(data["density"])))
    db.session.add(TrafficRecord(junction_id=j.id,vehicle_count=int(data["vehicles"]),average_speed=float(data["speed"]),density=density))
    db.session.commit()
    audit("API_TELEMETRY",f"API telemetry for {j.name}")
    return jsonify({"status":"accepted","junction":j.name,"level":traffic_level(density)}),201
