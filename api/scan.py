from flask import Blueprint, jsonify, request
from getdb import get_db

scan_api = Blueprint('scan_api', __name__)
progress_api = Blueprint('progress_api', __name__)


def get_total_booths(cursor):
    cursor.execute("SELECT COUNT(*) FROM thesis_booths")
    return cursor.fetchone()[0]


@scan_api.route("/scan", methods=["POST"])
def process_scan():

    if not request.is_json:
        return jsonify({
            "status": "error", "success": False,
            "message": "กรุณาส่งข้อมูลในรูปแบบ JSON",
            "error_code": "INVALID_CONTENT_TYPE"
        }), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "status": "error", "success": False,
            "message": "รูปแบบ JSON ไม่ถูกต้อง",
            "error_code": "INVALID_JSON_FORMAT"
        }), 400

    user_id = data.get("user_id")
    booth_id = data.get("booth_id")

    if user_id is None or str(user_id).strip() == "":
        return jsonify({
            "status": "error", "success": False,
            "message": "กรุณาระบุ user_id", "error_code": "MISSING_USER_ID"
        }), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({
            "status": "error", "success": False,
            "message": "user_id ต้องเป็นตัวเลข", "error_code": "INVALID_USER_ID"
        }), 400

    if booth_id is None or str(booth_id).strip() == "":
        return jsonify({
            "status": "error", "success": False,
            "message": "กรุณาระบุ booth_id", "error_code": "MISSING_BOOTH_ID"
        }), 400

    booth_id = str(booth_id).strip()

    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username FROM thesis_users WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                "status": "error", "success": False,
                "message": "ไม่พบผู้ใช้งานนี้ในระบบ", "error_code": "USER_NOT_FOUND"
            }), 404

        columns = [desc.name for desc in cursor.description]
        user = dict(zip(columns, row))
        username = user["username"]

        cursor.execute("""
            SELECT id, boothname, url, boothnum
            FROM thesis_booths WHERE boothnum = %s
        """, (booth_id,))
        row = cursor.fetchone()

        if not row and booth_id.isdigit():
            cursor.execute("""
                SELECT id, boothname, url, boothnum
                FROM thesis_booths WHERE id = %s
            """, (int(booth_id),))
            row = cursor.fetchone()

        if not row:
            return jsonify({
                "status": "error", "success": False,
                "message": f"ไม่พบบูธ {booth_id} ในระบบ", "error_code": "BOOTH_NOT_FOUND"
            }), 404

        columns = [desc.name for desc in cursor.description]
        booth = dict(zip(columns, row))
        real_booth_id = booth["id"]
        boothname = booth["boothname"]
        booth_url = booth["url"]
        boothnum = booth["boothnum"]

        total_booths = get_total_booths(cursor)

        cursor.execute("BEGIN")
        cursor.execute("""
            SELECT id FROM user_scans
            WHERE user_id = %s AND booth_id = %s
              AND scanned_at >= CURRENT_DATE
              AND scanned_at <  CURRENT_DATE + INTERVAL '1 day'
            FOR UPDATE
        """, (user_id, real_booth_id))
        existing_scan = cursor.fetchone()

        if existing_scan:
            conn.rollback()
            return jsonify({
                "status": "warning", "success": False,
                "message": f"คุณ {username} ได้สแกนฐาน {boothname} ไปแล้ววันนี้!",
                "error_code": "ALREADY_SCANNED"
            }), 409

        cursor.execute("""
            INSERT INTO user_scans (user_id, booth_id) VALUES (%s, %s) RETURNING id
        """, (user_id, real_booth_id))
        scan_id = cursor.fetchone()[0]
        conn.commit()

        cursor.execute("""
            SELECT COUNT(DISTINCT booth_id) FROM user_scans
            WHERE user_id = %s
              AND scanned_at >= CURRENT_DATE
              AND scanned_at <  CURRENT_DATE + INTERVAL '1 day'
        """, (user_id,))
        total_scanned = cursor.fetchone()[0]

        return jsonify({
            "status": "success", "success": True,
            "message": f"สแกนสำเร็จ! ยินดีต้อนรับคุณ {username}",
            "data": {
                "scan_id": scan_id, "user_id": user_id, "username": username,
                "booth_id": real_booth_id, "boothname": boothname,
                "boothnum": boothnum, "booth_url": booth_url,
                "total_scanned": total_scanned, "total_booths": total_booths,
                "remaining": max(0, total_booths - total_scanned)
            }
        }), 201

    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        print("SCAN API ERROR:", e)
        return jsonify({
            "status": "error", "success": False,
            "message": "เกิดข้อผิดพลาดในระบบ"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@progress_api.route("/progress/<int:user_id>", methods=["GET"])
def get_progress(user_id):

    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM thesis_users WHERE id = %s", (user_id,))

        if not cursor.fetchone():
            return jsonify({
                "status": "error", "message": "ไม่พบผู้ใช้งานนี้",
                "error_code": "USER_NOT_FOUND"
            }), 404

        total_booths = get_total_booths(cursor)

        cursor.execute("""
            SELECT b.boothnum FROM user_scans us
            JOIN thesis_booths b ON us.booth_id = b.id
            WHERE us.user_id = %s
              AND us.scanned_at >= CURRENT_DATE
              AND us.scanned_at <  CURRENT_DATE + INTERVAL '1 day'
        """, (user_id,))
        scanned = [row[0] for row in cursor.fetchall()]

        return jsonify({
            "status": "success", "scanned": scanned, "total": len(scanned),
            "total_booths": total_booths,
            "remaining": max(0, total_booths - len(scanned))
        }), 200

    except Exception as e:
        print("PROGRESS API ERROR:", e)
        return jsonify({
            "status": "error", "message": "เกิดข้อผิดพลาดในระบบ"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()