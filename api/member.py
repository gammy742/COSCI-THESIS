from flask import Blueprint, jsonify, request

all_members_api = Blueprint('allmembers', __name__)
booth_members_api = Blueprint('booth_members_api', __name__)

from getdb import get_db

@booth_members_api.route("/members/<int:booth_id>", methods=["GET"])
def get_users(booth_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                b.boothnum,
                b.boothname,
                u.username,
                u.instagram
            FROM booths_members bm
            JOIN thesis_users u ON bm.user_id = u.id
            JOIN thesis_booths b ON bm.booth_id = b.id
            WHERE b.id = %s
        """, (booth_id,))

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        users = [dict(zip(columns, row)) for row in rows]

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(users),
            "data": users
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@all_members_api.route("/members", methods=["GET"])
def get_allUsers():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                b.boothnum,
                b.boothname,
                u.username,
                u.instagram
            FROM booths_members bm
            JOIN thesis_users u ON bm.user_id = u.id
            JOIN thesis_booths b ON bm.booth_id = b.id
            WHERE u.role IN ('admin', 'member')
            ORDER BY b.boothnum ASC, u.username ASC
        """)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        allMembers = [dict(zip(columns, row)) for row in rows]

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(allMembers),
            "data": allMembers
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500