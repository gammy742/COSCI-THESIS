from flask import Blueprint, jsonify, request
import os
import logging
from datetime import datetime 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

countdown_api = Blueprint('countdown_api', __name__)


@countdown_api.route("/countdown",methods=["GET"])
def activity_countdown():
    now=datetime.now()
    y=now.year
    m=now.month
    d=now.day

    opening_date=datetime(now.year,month=5,day=17)

    event_start=datetime(2026, 5, 17, 0, 0, 0)
    event_end=datetime(2026, 5, 18, 23, 59, 59)

    is_ongoing = event_start <= now <= event_end  # อยู่ในช่วงงาน
    is_expired = now > event_end #timeout

    return jsonify({
        "is_ongoing":   is_ongoing,
        "is_expired":   is_expired,
        "event_start":  event_start.isoformat(),
        "event_end":    event_end.isoformat()
    })


