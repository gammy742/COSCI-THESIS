from flask import Blueprint, jsonify, request
from getdb import get_db

reward_api = Blueprint('reward_api', __name__)

# บันทึกการรับรางวัล
@reward_api.route("/reward/claim", methods=["POST"])
def claim_reward():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "กรุณาระบุ user_id"}), 400

    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        # เช็คว่ารับไปแล้วหรือยัง
        cursor.execute("""
            SELECT id FROM user_rewards
            WHERE user_id = %s AND DATE(claimed_at) = CURDATE()
        """, (user_id,))
        existing = cursor.fetchone()

        if existing:
            return jsonify({"status": "warning", "message": "รับรางวัลไปแล้ววันนี้"}), 409

        cursor.execute("""
            INSERT INTO user_rewards (user_id) VALUES (%s)
        """, (user_id,))
        conn.commit()

        return jsonify({"status": "success", "message": "บันทึกการรับรางวัลสำเร็จ"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Dashboard — สถิติรวม
@reward_api.route("/reward/dashboard", methods=["GET"])
def get_dashboard():
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        # จำนวน user ทั้งหมด
        cursor.execute("SELECT COUNT(*) AS total FROM thesis_users")
        total_users = cursor.fetchone()["total"]

        # จำนวนคนที่รับรางวัลวันนี้
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) AS total
            FROM user_rewards
            WHERE DATE(claimed_at) = CURDATE()
        """)
        claimed_today = cursor.fetchone()["total"]

        # จำนวน scan แต่ละบูธวันนี้
        cursor.execute("""
            SELECT b.boothname, b.boothnum,
                   COUNT(DISTINCT us.user_id) AS scan_count
            FROM thesis_booths b
            LEFT JOIN user_scans us ON b.id = us.booth_id
                AND DATE(us.scanned_at) = CURDATE()
            GROUP BY b.id, b.boothname, b.boothnum
            ORDER BY b.boothnum
        """)
        booth_stats = cursor.fetchall()

        # คนที่ scan ครบทุกบูธวันนี้
        cursor.execute("""
            SELECT COUNT(*) AS total FROM (
                SELECT user_id
                FROM user_scans
                WHERE DATE(scanned_at) = CURDATE()
                GROUP BY user_id
                HAVING COUNT(DISTINCT booth_id) >= (SELECT COUNT(*) FROM thesis_booths)
            ) AS completed
        """)
        completed_all = cursor.fetchone()["total"]

        return jsonify({
            "status": "success",
            "data": {
                "total_users": total_users,
                "claimed_today": claimed_today,
                "completed_all": completed_all,
                "booth_stats": booth_stats
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()