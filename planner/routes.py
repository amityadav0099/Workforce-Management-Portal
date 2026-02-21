from flask import Blueprint, request, jsonify, session
from planner.models import CalendarEvent
from extensions import db
from accounts.decorators import login_required
from datetime import datetime

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

@planner_bp.route('/add_event', methods=['POST'])
@login_required
def add_event():
    data = request.json
    try:
        # Convert HTML time strings to Python time objects
        t_start = datetime.strptime(data.get('start'), '%H:%M').time() if data.get('start') else None
        t_end = datetime.strptime(data.get('end'), '%H:%M').time() if data.get('end') else None

        new_event = CalendarEvent(
            user_id=session.get('user_id'),
            reason=data.get('reason'),
            event_date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            time_start=t_start,
            time_end=t_end
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@planner_bp.route('/get_events')
@login_required
def get_events():
    user_id = session.get('user_id')
    role = session.get('role')
    
    if role == 'hr':
        events = CalendarEvent.query.all()
    else:
        events = CalendarEvent.query.filter_by(user_id=user_id).all()
    
    event_list = []
    for e in events:
        reason_lower = e.reason.lower()
        
        # Color Logic
        if 'remote' in reason_lower or 'home' in reason_lower:
            bg_color = "#10b981"
        elif 'break' in reason_lower or 'personal' in reason_lower:
            bg_color = "#f59e0b"
        elif 'doctor' in reason_lower or 'sick' in reason_lower:
            bg_color = "#ef4444"
        else:
            bg_color = "#6366f1"

        # Format time string for the title
        time_display = ""
        if e.time_start and e.time_end:
            time_display = f" [{e.time_start.strftime('%I:%M %p')} - {e.time_end.strftime('%I:%M %p')}]"

        prefix = f"{e.user.username}: " if role == 'hr' else ""
        
        event_list.append({
            "title": f"{prefix}{e.reason}{time_display}",
            "start": e.event_date.isoformat(),
            "allDay": True,
            "backgroundColor": bg_color,
            "borderColor": bg_color
        })
    
    return jsonify(event_list)