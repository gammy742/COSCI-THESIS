from flask import Blueprint,jsonify,request
import mysql.connector
from dotenv import load_dotenv
import os
import datetime

join_api = Blueprint('join_api', __name__)

#dbconect
from getdb import get_db

@join_api.route("/join",methods=["POST"])
def join_event():
    try:
        data=request.json
        username=data.get("name")
        id = data.get("id")

        if not username:
            return jsonify({
                "status":"error",
                "message":"กรุณากรอกชื่อ"
            }),400
        
        conn=get_db()
        cursor=conn.cursor(dictionary=True)

        #Search name in database
        cursor.execute("SELECT id,username FROM thesis_users WHERE username=%s AND id=%s",(username,id))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id=existing_user['id']
            message ="ยินดีต้อนรับกลับมา!"
        else:
            cursor.execute("""
                INSERT INTO thesis_users(username)
                VALUES(%s,%s)
            """,(username))
            conn.commit()
            user_id = cursor.lastrowid
            message = "ลงทะเบียนสำเร็จ!"

            cursor.close()
            conn.close()

            return jsonify({
            "status": "success",
            "message": message,
            "user": { "id": user_id, "name": username }
            }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500