import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()

def get_db():
    conn =psycopg2.connect(os.getenv("DB_URL"),sslmode="require")
    
    return conn