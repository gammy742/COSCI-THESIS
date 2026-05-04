from flask import Blueprint, jsonify, request
import os
import logging
from datetime import datetime 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

booth_api = Blueprint('booth_api', __name__)

#dbconect
from getdb import get_db

@booth_api.route("/booths", methods=["GET"])
def get_booths():
    try:
        conn=get_db()
        cursor=conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.boothnum,
                b.boothname,
                b.url,
                GROUP_CONCAT(u.username SEPARATOR '||')AS members,
                GROUP_CONCAT(COALESCE(u.instagram,'')SEPARATOR '||')AS instagrams
            FROM booths_members bm
            JOIN thesis_users u ON bm.user_id=u.id
            JOIN  thesis_booths b ON bm.booth_id = b.id
            GROUP BY b.id, b.boothnum,b.boothname,b.url
        """)
        users=cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count":len(users),
            "data":users
        }),200
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }),500
