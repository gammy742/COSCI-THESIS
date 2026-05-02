from flask import Blueprint,jsonify,request
import mysql.connector
from dotenv import load_dotenv
import os
import datetime

scan_api = Blueprint('scan_api', __name__)

#dbconect
from getdb import get_db

@scan_api.route("/scan",methods=["POST"])
def process_scan():
    try:
        data=request.json
        user_id=data.get("user_id")
        booth_id = data.get("user_id")

        if not user_id or not booth_id:
            return jsonify({
                "status":"error",
                "message":"ข้อมูลไม่ครบถ้วน (ต้องการ user_id และ booth_id)"
            }),400
        
        conn=get_db()
        cursor=conn.cursor(dictionary=True)

        #Search name in databasec and current date
        cursor.execute("""
            SELECT id FROM user_scans 
            WHERE user_id = %s 
            AND booth_id = %s 
            AND DATE(scanned_at) = CURDATE()    
        """, (user_id, booth_id))

        existing_scan = cursor.fetchone()

        if existing_scan:
            # ถ้าวันนี้เคยสแกนไปแล้ว ไม่ต้องบันทึกซ้ำ ให้แจ้งเตือนกลับไป
            cursor.close()
            conn.close()
            return jsonify({
                "status": "warning", 
                "message": "วันนี้คุณได้สแกนฐานนี้ไปแล้ว กรุณากลับมาใหม่พรุ่งนี้!"
            }), 200
        else:
            cursor.execute("""
                INSERT INTO user_scans (user_id, booth_id) 
                VALUES (%s, %s)
            """,(user_id, booth_id))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
            "status": "success",
            "message": "สแกนสำเร็จ! บันทึกข้อมูลเรียบร้อย"
            }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500