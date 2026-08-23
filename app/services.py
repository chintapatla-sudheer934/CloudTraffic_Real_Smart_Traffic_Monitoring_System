from .models import TrafficRecord

def traffic_level(density):
    if density < 30: return "LOW"
    if density < 60: return "MODERATE"
    if density < 80: return "HIGH"
    return "SEVERE"

def latest(junction_id):
    r = TrafficRecord.query.filter_by(junction_id=junction_id).order_by(TrafficRecord.recorded_at.desc()).first()
    if not r:
        return {"vehicles":0,"speed":0,"density":0,"level":"LOW"}
    return {"vehicles":r.vehicle_count,"speed":round(r.average_speed,1),"density":round(r.density,1),"level":traffic_level(r.density)}

def prediction(junction_id):
    rows = TrafficRecord.query.filter_by(junction_id=junction_id).order_by(TrafficRecord.recorded_at.desc()).limit(8).all()
    if not rows:
        return {"vehicles":0,"density":0,"level":"LOW"}
    weights = list(range(len(rows),0,-1))
    total = sum(weights)
    vehicles = round(sum(r.vehicle_count*w for r,w in zip(rows,weights))/total)
    density = round(sum(r.density*w for r,w in zip(rows,weights))/total,1)
    return {"vehicles":vehicles,"density":density,"level":traffic_level(density)}

def series(junction_id):
    rows = TrafficRecord.query.filter_by(junction_id=junction_id).order_by(TrafficRecord.recorded_at.asc()).limit(24).all()
    return [{"label":r.recorded_at.strftime("%H:%M"),"vehicles":r.vehicle_count,"density":r.density} for r in rows]

def signal_recommendation(density):
    if density >= 80: return ("EXTENDED GREEN","Increase green phase by 25%.")
    if density >= 60: return ("ADAPTIVE GREEN","Increase green phase by 15%.")
    if density >= 30: return ("BALANCED","Maintain adaptive timing.")
    return ("NORMAL","No signal adjustment required.")
