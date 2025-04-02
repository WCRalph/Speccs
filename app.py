import os
from flask import Flask, jsonify, request # Added jsonify and request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import uuid # For generating UUIDs in models

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable tracking modifications, saves resources

# --- Initialize Extensions ---
db = SQLAlchemy(app) # Initialize SQLAlchemy ORM
migrate = Migrate(app, db) # Initialize Flask-Migrate

# --- Define Models ---
# (We'll define models here for now, usually moved to models.py later)

class Property(db.Model):
    __tablename__ = 'properties' # Explicitly set table name

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # Using String for UUID portability
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Define relationship to Buildings (if Building model existed)
    # buildings = db.relationship('Building', backref='property', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Property {self.id}: {self.name}>'

    # Helper method to convert model to dictionary for JSON responses
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# --- Define API Routes ---

@app.route('/')
def hello_world():
    return 'Hello, Speccs World! ORM Initialized.'

@app.route('/db_check')
def db_check():
    try:
        # Use SQLAlchemy's connection handling
        db.session.execute('SELECT 1')
        return "Database connection via SQLAlchemy successful!"
    except Exception as e:
        # Log the error for debugging
        app.logger.error(f"Database connection failed: {e}")
        return f"Database connection failed: {e}", 500

# --- Example API Endpoint for Properties ---

@app.route('/api/properties', methods=['POST'])
def create_property():
    """Creates a new property."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Property name is required"}), 400

    new_property = Property(
        name=data['name'],
        address=data.get('address') # Optional address
    )
    try:
        db.session.add(new_property)
        db.session.commit()
        return jsonify(new_property.to_dict()), 201 # 201 Created status code
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating property: {e}")
        return jsonify({"error": "Failed to create property"}), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """Gets a list of all properties."""
    try:
        properties = Property.query.all()
        return jsonify([prop.to_dict() for prop in properties]), 200
    except Exception as e:
        app.logger.error(f"Error fetching properties: {e}")
        return jsonify({"error": "Failed to fetch properties"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') == 'development'))
