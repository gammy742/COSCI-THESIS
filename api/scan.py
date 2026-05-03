from flask import Blueprint, jsonify, request
from getdb import get_db

scan_api = Blueprint('scan_api', __name__)

@scan_api.route("/scan", methods=["POST"])
def process_scan():

    # ── Validate Request ───────────────────────────────
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

    user_id = data.get("user_id")
    booth_id = data.get("booth_id")

    # 🔥 FIX: เช็คแบบถูกต้อง
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

    # 🔥 FIX: cast type ให้ชัด
    try:
        user_id = int(user_id)
    except:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "user_id ต้องเป็นตัวเลข",
            "error_code": "INVALID_USER_ID"
        }), 400

    conn = get_db()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)

        # ── Get User ───────────────────────────────
        cursor.execute("""
            SELECT id, username
            FROM thesis_users
            WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "ไม่พบผู้ใช้งานนี้ในระบบ",
                "error_code": "USER_NOT_FOUND"
            }), 404

        username = user['username']

        # ── Get Booth ───────────────────────────────
        cursor.execute("""
            SELECT id, boothname, url, boothnum
            FROM thesis_booths
            WHERE boothnum = %s OR id = %s
        """, (booth_id, booth_id))
        booth = cursor.fetchone()

        if not booth:
            return jsonify({
                "status": "error",
                "success": False,
                "message": f"ไม่พบบูธ {booth_id} ในระบบ",
                "error_code": "BOOTH_NOT_FOUND"
            }), 404
        

        real_booth_id = booth['id']
        boothname     = booth['boothname']
        booth_url     = booth['url']
        boothnum      = booth['boothnum']

        print("booth found:", booth)

        # ── Check Duplicate Scan ─────────────────────
        cursor.execute("""
            SELECT id FROM user_scans
            WHERE user_id = %s
            AND booth_id = %s
            AND DATE(scanned_at) = CURDATE()
        """, (user_id, real_booth_id))  # 🔥 FIX สำคัญ
        existing_scan = cursor.fetchone()

        if existing_scan:
            return jsonify({
                "status": "warning",
                "success": False,
                "message": f"คุณ {username} ได้สแกนฐาน {boothname} ไปแล้ววันนี้ กรุณากลับมาใหม่พรุ่งนี้!",
                "error_code": "ALREADY_SCANNED"
            }), 409
        print("existing_scan:", existing_scan)
        # ── Insert Scan ─────────────────────────────
        cursor.execute("""
            INSERT INTO user_scans (user_id, booth_id)
            VALUES (%s, %s)
        """, (user_id, real_booth_id))
        conn.commit()
        print("inserted! scan_id:", cursor.lastrowid)
        scan_id = cursor.lastrowid

        # ── Count Progress ───────────────────────────
        cursor.execute("""
            SELECT COUNT(DISTINCT booth_id) AS total
            FROM user_scans
            WHERE user_id = %s
            AND DATE(scanned_at) = CURDATE()
        """, (user_id,))
        count = cursor.fetchone()

        total_scanned = count['total'] if count else 0

        # ── Response ────────────────────────────────
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
        if cursor:
            cursor.close()
        if conn:
            conn.close()

progress_api = Blueprint('progress_api', __name__)
@progress_api.route("/progress/<int:user_id>", methods=["GET"])
def get_progress(user_id):
    conn = get_db()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)

        # เช็คว่า user มีอยู่จริง
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

        # ดึง boothnum ที่ scan วันนี้
        cursor.execute("""
            SELECT b.boothnum
            FROM user_scans us
            JOIN thesis_booths b ON us.booth_id = b.id
            WHERE us.user_id = %s
            AND DATE(us.scanned_at) = CURDATE()
        """, (user_id,))
        rows = cursor.fetchall()

        scanned = [row['boothnum'] for row in rows]

        return jsonify({
            "status": "success",
            "scanned": scanned
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "เกิดข้อผิดพลาดในระบบ",
            "error_details": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()