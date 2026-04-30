#api admin login
from flask import Blueprint, jsonify, request
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_api = Blueprint('admin_api', __name__)

@admin_api.route("/login",methods=["POST"])
def admin_login():
    try:
        data=request.get_json()

        logger.info(f"Received data: {data}")

        if data is None:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "รูปแบบข้อมูลไม่ถูกต้อง กรุณาส่งเป็น JSON"
            }), 400
        
        admin_pass=data.get("password")
    
        if not admin_pass:
            return jsonify({
                "status":"error",
                "success":False,
                "message":"กรุณากรอกรหัสผ่าน"
            }),400
        
        #admin password
        adminPassword = os.getenv("ADMIN_ID")

        if not adminPassword:
            return jsonify({
                "status":"error",
                "success":False,
                "message":"ยังไม่ได้ตั้งค่ารหัสผ่าน"
            }),500
        
        if admin_pass == adminPassword:
            return jsonify({
                "status":"success",
                "success":True,
                "message":"เข้าสู่ระบบสำเร็จ",
                "data":{
                    "role":"admin",
                    "username":"Admin team"
                }
            }),200
        else:
            return jsonify({
                "status":"error",
                "success":False,
                "message":"รหัสผ่านไม่ถูกต้อง"
            }),401
    except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)

            return jsonify({
                "status":"error",
                "success":False,
                "message":str(e)
            }),500