from flask import Blueprint, jsonify, request, send_file
import pandas as pd
import io
from datetime import datetime

excel_api = Blueprint('excel_api', __name__)

from getdb import get_db

@excel_api.route("/export-excel", methods=["GET"])
def export_excel():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        query_all = """
            SELECT
                u.username AS "ชื่อผู้ใช้งาน",
                u.role AS "ประเภทผู้ใช้",
                b.boothnum AS "เลขฐาน",
                b.boothname AS "ชื่อฐานกิจกรรม",
                s.scanned_at AS "วันเวลาที่สแกน"
            FROM user_scans s
            JOIN thesis_users u ON s.user_id = u.id
            JOIN thesis_booths b ON s.booth_id = b.id
            ORDER BY s.scanned_at DESC
        """

        cursor.execute(query_all)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()

        df_all = pd.DataFrame(rows, columns=columns)

        if df_all.empty:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "ไม่มีข้อมูล export",
                "error_code": "NO_DATA"
            }), 404

        df_summary = (
            df_all.groupby(["ชื่อผู้ใช้งาน", "ประเภทผู้ใช้"])
            .size()
            .reset_index(name="จำนวนฐานที่สแกนรวม")
            .sort_values("จำนวนฐานที่สแกนรวม", ascending=False)
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='สรุปยอดรายคน', index=False)
            df_all.to_excel(writer, sheet_name='ประวัติการสแกนทั้งหมด', index=False)

        output.seek(0)

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "เกิดข้อผิดพลาดในระบบ",
            "error_details": str(e)
        }), 500
    finally:
        if conn:
            conn.close()