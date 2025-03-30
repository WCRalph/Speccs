import os
from flask import Flask
from dotenv import load_dotenv
import psycopg2 # Import the connector

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

@app.route('/')
def hello_world():
    return 'Hello, Speccs World!'

@app.route('/db_check')
def db_check():
    conn = None
    try:
        print(f"Attempting to connect to: {DATABASE_URL}") # Debug print
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return "Database connection successful!"
    except Exception as e:
        print(f"Database connection failed: {e}") # Debug print
        return f"Database connection failed: {e}", 500
    finally:
        if conn is not None:
            conn.close()

# Add more routes/blueprints for your application logic here...

if __name__ == '__main__':
    # Note: `flask run` command uses this block if executed directly,
    # but docker uses the CMD ["flask", "run", "--host=0.0.0.0"]
    app.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') == 'development'))
