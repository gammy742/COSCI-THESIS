from flask import Blueprint,jsonify,request
import pandas as pd
from flask import send_file
import io

excel_api = Blueprint('excel_api', __name__)

#dbconect
from getdb import get_db

@excel_api.route("/export-excel",methods=["GET"])
def export_excel():
    try:
        conn=get_db()

        query_all = """
            SELECT 
                u.username AS 'ชื่อผู้ใช้งาน',
                u.role AS 'ประเภทผู้ใช้',
                b.boothnum AS 'เลขฐาน',
                b.boothname AS 'ชื่อฐานกิจกรรม',
                s.scanned_at AS 'วันเวลาที่สแกน'
            FROM user_scans s
            JOIN thesis_users u ON s.user_id = u.id
            JOIN thesis_booths b ON s.booth_id = b.id
            ORDER BY s.scanned_at DESC
        """
        df_all = pd.read_sql(query_all, conn)

        # 2. สร้างตารางสรุปยอด (ใครสแกนไปแล้วกี่ฐาน)
        df_summary = df_all.groupby(['ชื่อผู้ใช้งาน', 'ประเภทผู้ใช้']).size().reset_index(name='จำนวนฐานที่สแกนรวม')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='สรุปยอดรายคน', index=False)
            df_all.to_excel(writer, sheet_name='ประวัติการสแกนทั้งหมด', index=False)

        output.seek(0)
        conn.close()

        # ตั้งชื่อไฟล์ตามวันที่ปัจจุบัน
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500