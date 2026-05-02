from flask import Blueprint,jsonify,request

scan_api = Blueprint('scan_api', __name__)

#dbconect
from getdb import get_db

@scan_api.route("/scan",methods=["POST"])
def process_scan():

    data=request.get_json()

    #Check content type
    if not request.is_json:
        return jsonify({
            "status":"error",
            "success":False,
            "message":"กรุณาส่งข้อมูลในรูปแบบ JSON",
            "error_code": "INVALID_CONTENT_TYPE"
        }),400
    
    if data is None:
        return jsonify({
            "status":"error",
            "success":False,
            "message":"รูปแบบ JSON ไม่ถูกต้อง",
            "error_code": "INVALID_JSON_FORMAT"
        }),400

    #check field
    user_id=data.get("user_id")
    booth_id = data.get("booth_id")

    if not booth_id:
        return jsonify({
            "status":"error",
            "success":False,
            "message":"กรุณาระบุ booth_id",
            "error_code": "MISSING_BOOTH_ID"
        }), 400
    
    if not user_id:
        return jsonify({
            "status":"error",
            "success":False,
            "message":"กรุณาระบุ user_id",
            "error_code": "MISSING_USER_ID"
        })
    
    conn = get_db()
    cursor=None

    try:
        cursor=conn.cursor(dictionary=True)

        #Get user from database
        cursor.execute("""
            SELECT id,username
            FROM thesis_users
            WHERE id=%s
        """,(user_id,))
        user=cursor.fetchone()

        #if user not found
        if not user:
            return jsonify({
                "status":"error",
                "success":False,
                "message":"ไม่พบผู้ใช้งานนี้ในระบบ",
                "error_code": "USER_NOT_FOUND"
            }),404
        
        username=user['username']

        #Scanned Check
        cursor.execute("""
            SELECT id FROM user_scans
            WHERE user_id=%s
            AND booth_id=%s
            AND DATE(scanned_at)=CURDATE()
        """, (user_id, booth_id))
        existing_scan = cursor.fetchone()

        if existing_scan:
            return jsonify({
                "status":"warning",
                "success":False,
                "message":f"คุณ {username} ได้สแกนฐานนี้ไปแล้ววันนี้ กรุณากลับมาใหม่พรุ่งนี้!",
                "error_code": "ALREADY_SCANNED"
            }), 409  # 409 Conflict
        
        #saving scan
        cursor.execute("""
            INSERT INTO user_scans(user_id,booth_id)
            VALUES(%s,%s)
        """, (user_id, booth_id))
        conn.commit()

        scan_id=cursor.lastrowid
        return jsonify({
            "status":"success",
            "success":True,
            "message": f"สแกนสำเร็จ! ยินดีต้อนรับคุณ {username}",
            "data":{
                "scan_id":scan_id,
                "user_id":user_id,
                "username":username,
                "booth_id":booth_id
            }
        }),201
    
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "status": "error", 
            "success":False,
            "message":"เกิดข้อผิดพลาดในระบบ",
            "error_details": str(e)
        }),500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()