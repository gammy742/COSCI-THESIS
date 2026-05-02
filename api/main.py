from flask import Flask,jsonify,request
import mysql.connector
from dotenv import load_dotenv
import os
import datetime
from flask_cors import CORS

load_dotenv()
PORT=int(os.getenv("PY_PORT"))
app=Flask(__name__)
CORS(app)

from adminlogin import admin_api
#ADMIN_login api
app.register_blueprint(admin_api, url_prefix="/api/admin")

from countdown import countdown_api
app.register_blueprint(countdown_api, url_prefix="/api")

from booth import booth_api
app.register_blueprint(booth_api, url_prefix="/api")

#dbconect
def get_db():
    conn =mysql.connector.connect(
        host=os.getenv("DB_HOST","localhost"),
        user=os.getenv("DB_USER","root"),
        port=int(os.getenv("DB_PORT",3306)),
        database=os.getenv("DB_NAME","mydb")
    )
    return conn

#Get_IP
def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For อาจส่งมาหลาย IP ให้เอาตัวแรกสุด
        return forwarded.split(",")[0].strip()
    return request.remote_addr

#API สมาชิกของแต่ละบูท
@app.route("/api/members/<int:booth_id>", methods=["GET"])
def get_users(booth_id):
    try:
        conn=get_db()
        cursor=conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.boothnum,
                b.boothname,
                u.username,
                u.instagram
            FROM booths_members bm
            JOIN thesis_users u ON bm.user_id = u.id
            JOIN thesis_booths b ON bm.booth_id = b.id
            WHERE b.id =%s
        """,(booth_id,))
        users=cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count":len(users),
            "data":users
        }),200
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }),500

#Apiสมาชิกของทุกบูธ
@app.route("/api/members/", methods=["GET"])
def get_allUsers():
    try:
        conn=get_db()
        cursor=conn.cursor(dictionary=True)

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
        allMembers=cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count":len(allMembers),
            "data":allMembers
        }),200
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }),500


if __name__ =='__main__':
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(debug=is_debug,port=PORT)
