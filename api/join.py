from flask import Blueprint, jsonify, request

join_api = Blueprint('join_api', __name__)

#dbconect
from getdb import get_db

@join_api.route("/join", methods=["POST"])
def join_event():
    data=request.get_json()
    displayName=data.get('name','').strip()

    if not displayName:
        return jsonify({
            "status":"error",
            "success":False,
            "message":"กรุณากรอกชื่อก่อนเข้าใช้งาน"
        }),400
    
    conn=get_db()
    cursor=None

    try:
        cursor=conn.cursor()

        sql_query="INSERT INTO thesis_users(username)VALUES(%s)"
        cursor.execute( sql_query,(displayName,))
        conn.commit()
        user_id = cursor.lastrowid

        return jsonify({
            "status":"success",
            "success":True,
            "message":"เข้าร่วมกิจกรรมสำเร็จ",
            "data":{
                "id":user_id,
                "name":displayName
            }
        }),200
    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "status":"error",
            "success":False,
            "message":"เกิดข้อผิดพลาดในระบบ ไม่สามารถเข้าร่วมได้",
            "error_details": str(e)
        }),500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()