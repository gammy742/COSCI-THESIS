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
from getdb import get_db

#join api
from join import join_api
app.register_blueprint(join_api, url_prefix="/api")

#scan api
from scan import scan_api
app.register_blueprint(scan_api, url_prefix="/api")

#scan api
from scan import progress_api
app.register_blueprint(progress_api, url_prefix="/api")

#excel-export api
from excel import excel_api
app.register_blueprint(excel_api, url_prefix="/api")

#allmember api
from member import all_members_api
app.register_blueprint(all_members_api, url_prefix="/api")

#boothmember api
from member import booth_members_api
app.register_blueprint(booth_members_api, url_prefix="/api")

#reward
from rewardy import reward_api
app.register_blueprint(reward_api, url_prefix="/api")

#Get_IP
def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For อาจส่งมาหลาย IP ให้เอาตัวแรกสุด
        return forwarded.split(",")[0].strip()
    return request.remote_addr


if __name__ =='__main__':
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0",debug=is_debug,port=PORT)
