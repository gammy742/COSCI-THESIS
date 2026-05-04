import psycopg2
import mysql.connector
from dotenv import load_dotenv
import os
load_dotenv()

def get_db():
    conn =psycopg2.connect(os.getenv("DB_URL"))
    return conn