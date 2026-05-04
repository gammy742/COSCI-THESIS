from flask import Blueprint, jsonify, request
from getdb import get_db

reward_api = Blueprint('reward_api', __name__)

@reward_api.route("/reward/claim", methods=["POST"])
def claim_reward():
    data = request.get_json(silent=True)
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "กรุณาระบุ user_id"}), 400

    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM user_rewards
            WHERE user_id = %s AND DATE(claimed_at) = CURRENT_DATE
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


@reward_api.route("/reward/dashboard", methods=["GET"])
def get_dashboard():
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM thesis_users")
        total_users = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) AS total
            FROM user_rewards
            WHERE DATE(claimed_at) = CURRENT_DATE
        """)
        claimed_today = cursor.fetchone()[0]

        cursor.execute("""
            SELECT b.boothname, b.boothnum,
                   COUNT(DISTINCT us.user_id) AS scan_count
            FROM thesis_booths b
            LEFT JOIN user_scans us ON b.id = us.booth_id
                AND DATE(us.scanned_at) = CURRENT_DATE
            GROUP BY b.id, b.boothname, b.boothnum
            ORDER BY b.boothnum
        """)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        booth_stats = [dict(zip(columns, row)) for row in rows]

        cursor.execute("""
            SELECT COUNT(*) AS total FROM (
                SELECT user_id
                FROM user_scans
                WHERE DATE(scanned_at) = CURRENT_DATE
                GROUP BY user_id
                HAVING COUNT(DISTINCT booth_id) >= (SELECT COUNT(*) FROM thesis_booths)
            ) AS completed
        """)
        completed_all = cursor.fetchone()[0]

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