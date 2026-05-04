from flask import Blueprint, jsonify, request
from getdb import get_db

scan_api = Blueprint('scan_api', __name__)

@scan_api.route("/scan", methods=["POST"])
def process_scan():
    if not request.is_json:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "กรุณาส่งข้อมูลในรูปแบบ JSON",
            "error_code": "INVALID_CONTENT_TYPE"
        }), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "รูปแบบ JSON ไม่ถูกต้อง",
            "error_code": "INVALID_JSON_FORMAT"
        }), 400

    user_id  = data.get("user_id")
    booth_id = data.get("booth_id")

    if user_id is None:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "กรุณาระบุ user_id",
            "error_code": "MISSING_USER_ID"
        }), 400

    if not booth_id:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "กรุณาระบุ booth_id",
            "error_code": "MISSING_BOOTH_ID"
        }), 400

    try:
        user_id = int(user_id)
    except:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "user_id ต้องเป็นตัวเลข",
            "error_code": "INVALID_USER_ID"
        }), 400

    conn   = get_db()
    cursor = None
    try:
        cursor = conn.cursor()

        # ── หา User ──
        cursor.execute("""
            SELECT id, username
            FROM thesis_users
            WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "ไม่พบผู้ใช้งานนี้ในระบบ",
                "error_code": "USER_NOT_FOUND"
            }), 404

        columns  = [desc.name for desc in cursor.description]  # ✅ แก้
        user     = dict(zip(columns, row))
        username = user['username']

        # ── หา Booth ──
        cursor.execute("""
            SELECT id, boothname, url, boothnum
            FROM thesis_booths
            WHERE boothnum = %s OR id = %s
        """, (booth_id, booth_id))
        row = cursor.fetchone()
        if not row:
            return jsonify({
                "status": "error",
                "success": False,
                "message": f"ไม่พบบูธ {booth_id} ในระบบ",
                "error_code": "BOOTH_NOT_FOUND"
            }), 404

        columns       = [desc.name for desc in cursor.description]  # ✅ แก้
        booth         = dict(zip(columns, row))
        real_booth_id = booth['id']
        boothname     = booth['boothname']
        booth_url     = booth['url']
        boothnum      = booth['boothnum']

        # ── เช็คสแกนซ้ำ ──
        cursor.execute("""
            SELECT id FROM user_scans
            WHERE user_id = %s
            AND booth_id = %s
            AND DATE(scanned_at) = CURRENT_DATE
        """, (user_id, real_booth_id))
        existing_scan = cursor.fetchone()
        if existing_scan:
            return jsonify({
                "status": "warning",
                "success": False,
                "message": f"คุณ {username} ได้สแกนฐาน {boothname} ไปแล้ววันนี้!",
                "error_code": "ALREADY_SCANNED"
            }), 409

        # ── บันทึก ──
        cursor.execute("""
            INSERT INTO user_scans (user_id, booth_id)
            VALUES (%s, %s)
            RETURNING id
        """, (user_id, real_booth_id))
        conn.commit()
        scan_id = cursor.fetchone()

        # ── นับจำนวน ──
        cursor.execute("""
            SELECT COUNT(DISTINCT booth_id)
            FROM user_scans
            WHERE user_id = %s
            AND DATE(scanned_at) = CURRENT_DATE
        """, (user_id,))
        total_scanned = cursor.fetchone()

        return jsonify({
            "status": "success",
            "success": True,
            "message": f"สแกนสำเร็จ! ยินดีต้อนรับคุณ {username}",
            "data": {
                "scan_id":       scan_id,
                "user_id":       user_id,
                "username":      username,
                "booth_id":      real_booth_id,
                "boothname":     boothname,
                "boothnum":      boothnum,
                "booth_url":     booth_url,
                "total_scanned": total_scanned,
                "remaining":     max(0, 10 - total_scanned)
            }
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "status": "error",
            "success": False,
            "message": "เกิดข้อผิดพลาดในระบบ",
            "error_details": str(e)
        }), 500
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()


progress_api = Blueprint('progress_api', __name__)

@progress_api.route("/progress/<int:user_id>", methods=["GET"])
def get_progress(user_id):
    conn   = get_db()
    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM thesis_users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({
                "status": "error",
                "message": "ไม่พบผู้ใช้งานนี้",
                "error_code": "USER_NOT_FOUND"
            }), 404

        cursor.execute("""
            SELECT b.boothnum
            FROM user_scans us
            JOIN thesis_booths b ON us.booth_id = b.id
            WHERE us.user_id = %s
            AND DATE(us.scanned_at) = CURRENT_DATE
        """, (user_id,))
        rows    = cursor.fetchall()
        scanned = [row for row in rows]  # ✅ อันนี้ปกติ ไม่ต้องแก้

        return jsonify({
            "status":  "success",
            "scanned": scanned
        }), 200

    except Exception as e:
        return jsonify({
            "status":       "error",
            "message":      "เกิดข้อผิดพลาดในระบบ",
            "error_details": str(e)
        }), 500
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()