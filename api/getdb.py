
import mysql.connector
from dotenv import load_dotenv
import os
load_dotenv()

def get_db():
    conn =mysql.connector.connect(
        host=os.getenv("DB_HOST","localhost"),
        user=os.getenv("DB_USER","root"),
        port=int(os.getenv("DB_PORT",3306)),
        database=os.getenv("DB_NAME","mydb")
    )
    return conn