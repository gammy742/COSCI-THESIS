import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask,jsonify,request
from dotenv import load_dotenv
import os
import datetime
from flask_cors import CORS

load_dotenv()
PORT=int(os.getenv("PY_PORT",8000))
app=Flask(__name__)
CORS(app)


from adminlogin import admin_api
app.register_blueprint(admin_api, url_prefix="/api/admin")

from countdown import countdown_api
app.register_blueprint(countdown_api, url_prefix="/api")

from booth import booth_api
app.register_blueprint(booth_api, url_prefix="/api")

from getdb import get_db

from join import join_api
app.register_blueprint(join_api, url_prefix="/api")

from scan import scan_api
app.register_blueprint(scan_api, url_prefix="/api")

from scan import progress_api
app.register_blueprint(progress_api, url_prefix="/api")

from excel import excel_api
app.register_blueprint(excel_api, url_prefix="/api")

from member import all_members_api
app.register_blueprint(all_members_api, url_prefix="/api")

from member import booth_members_api
app.register_blueprint(booth_members_api, url_prefix="/api")

from rewardy import reward_api
app.register_blueprint(reward_api, url_prefix="/api")


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr

@app.route("/")
def home():
    return {
        "status": "running",
        "platform": "Vercel"
    }

if __name__ =='__main__':
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0",debug=is_debug,port=PORT)