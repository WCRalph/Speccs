import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import uuid
from sqlalchemy.dialects.postgresql import JSONB # For JSONB type
from sqlalchemy.orm import validates # For potential validation later
import datetime # For date/time types

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")

# Ensure the DATABASE_URL starts with 'postgresql://' if it's just 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Define Models ---

# Helper function for default UUIDs
def default_uuid():
    return str(uuid.uuid4())

class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationship: One-to-Many (Property has many Buildings)
    buildings = db.relationship('Building', backref='property', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Property {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Optionally include related items IDs or full objects
            # 'buildings': [b.id for b in self.buildings]
        }

class Building(db.Model):
    __tablename__ = 'buildings'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    building_type = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationship: One-to-Many (Building has many Floors)
    floors = db.relationship('Floor', backref='building', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Building {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'name': self.name,
            'building_type': self.building_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class Floor(db.Model):
    __tablename__ = 'floors'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    building_id = db.Column(db.String(36), db.ForeignKey('buildings.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    level_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationship: One-to-Many (Floor has many Rooms)
    rooms = db.relationship('Room', backref='floor', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Floor {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'name': self.name,
            'level_order': self.level_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    floor_id = db.Column(db.String(36), db.ForeignKey('floors.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Foreign key to the Asset that is the reference door. Must be deferred until Asset table exists.
    reference_door_asset_id = db.Column(db.String(36), db.ForeignKey('assets.id', use_alter=True, name='fk_room_reference_door'), nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationship: One-to-Many (Room has many Assets)
    assets = db.relationship('Asset', backref='room', lazy='dynamic', foreign_keys='Asset.room_id') # Use lazy='dynamic' for potentially large collections

    # Relationship: One-to-One (Room to its reference door Asset)
    reference_door = db.relationship('Asset', foreign_keys=[reference_door_asset_id], post_update=True)


    def __repr__(self):
        return f'<Room {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'floor_id': self.floor_id,
            'name': self.name,
            'description': self.description,
            'reference_door_asset_id': self.reference_door_asset_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    # Foreign key to the Room this asset primarily belongs to
    room_id = db.Column(db.String(36), db.ForeignKey('rooms.id'), nullable=True)

    asset_type = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    install_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Replaced, Deleted

    # Location specifics
    location_angle_degrees = db.Column(db.Numeric(5, 2), nullable=True)
    location_height_percent = db.Column(db.Numeric(5, 2), nullable=True)
    location_depth_percent = db.Column(db.Numeric(5, 2), nullable=True)
    location_notes = db.Column(db.Text, nullable=True)

    # Wall segment specifics
    wall_length = db.Column(db.Numeric(10, 2), nullable=True)
    wall_length_unit = db.Column(db.String(10), nullable=True)
    wall_height = db.Column(db.Numeric(10, 2), nullable=True)
    wall_height_unit = db.Column(db.String(10), nullable=True)

    # Flexible attributes
    attributes = db.Column(JSONB, default={})

    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationships for Connections (Assets connected FROM this one)
    connections_from = db.relationship('Connection', foreign_keys='Connection.from_asset_id', backref='from_asset', lazy='dynamic', cascade="all, delete-orphan")
    # Relationships for Connections (Assets connected TO this one)
    connections_to = db.relationship('Connection', foreign_keys='Connection.to_asset_id', backref='to_asset', lazy='dynamic', cascade="all, delete-orphan")
    # Relationship for Journal Entries about this asset
    journal_entries = db.relationship('Journal', backref='asset', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Asset {self.id}: {self.asset_type} - {self.name or "Unnamed"}>'

    def to_dict(self, include_connections=False):
        data = {
            'id': self.id,
            'room_id': self.room_id,
            'asset_type': self.asset_type,
            'name': self.name,
            'description': self.description,
            'install_date': self.install_date.isoformat() if self.install_date else None,
            'status': self.status,
            'location_angle_degrees': float(self.location_angle_degrees) if self.location_angle_degrees is not None else None,
            'location_height_percent': float(self.location_height_percent) if self.location_height_percent is not None else None,
            'location_depth_percent': float(self.location_depth_percent) if self.location_depth_percent is not None else None,
            'location_notes': self.location_notes,
            'wall_length': float(self.wall_length) if self.wall_length is not None else None,
            'wall_length_unit': self.wall_length_unit,
            'wall_height': float(self.wall_height) if self.wall_height is not None else None,
            'wall_height_unit': self.wall_height_unit,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_connections:
             data['connections_from'] = [c.to_dict() for c in self.connections_from]
             data['connections_to'] = [c.to_dict() for c in self.connections_to]
        return data


class Connection(db.Model):
    __tablename__ = 'connections'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid)
    from_asset_id = db.Column(db.String(36), db.ForeignKey('assets.id'), nullable=False)
    to_asset_id = db.Column(db.String(36), db.ForeignKey('assets.id'), nullable=False)
    connection_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

    def __repr__(self):
        return f'<Connection {self.id}: {self.from_asset_id} -> {self.to_asset_id} ({self.connection_type})>'

    def to_dict(self):
        return {
            'id': self.id,
            'from_asset_id': self.from_asset_id,
            'to_asset_id': self.to_asset_id,
            'connection_type': self.connection_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Journal(db.Model):
    __tablename__ = 'journal'

    id = db.Column(db.BigInteger, primary_key=True) # Using BigInteger for potential large volume
    asset_id = db.Column(db.String(36), db.ForeignKey('assets.id'), nullable=False)
    user_identifier = db.Column(db.String(255), default='System')
    timestamp = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())
    action = db.Column(db.String(50), nullable=False) # Create, Update, Replace, Delete, Link, Unlink
    details = db.Column(JSONB, default={}) # Store details of the change
    # created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now()) # Redundant with timestamp?

    def __repr__(self):
        return f'<Journal {self.id}: Asset {self.asset_id} - {self.action} @ {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'user_identifier': self.user_identifier,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action': self.action,
            'details': self.details,
        }

# --- Define API Routes ---
# (Keep existing routes, we will add more later)

@app.route('/')
def hello_world():
    return 'Hello, Speccs World! Models Defined.'

@app.route('/db_check')
def db_check():
    try:
        db.session.execute(db.text('SELECT 1')) # Use db.text for raw SQL if needed
        return "Database connection via SQLAlchemy successful!"
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
        return f"Database connection failed: {e}", 500

# --- Example API Endpoint for Properties (Keep this) ---

@app.route('/api/properties', methods=['POST'])
def create_property():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Property name is required"}), 400
    new_property = Property(name=data['name'], address=data.get('address'))
    try:
        db.session.add(new_property)
        db.session.commit()
        return jsonify(new_property.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating property: {e}")
        return jsonify({"error": "Failed to create property"}), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    try:
        properties = Property.query.all()
        return jsonify([prop.to_dict() for prop in properties]), 200
    except Exception as e:
        app.logger.error(f"Error fetching properties: {e}")
        return jsonify({"error": "Failed to fetch properties"}), 500

# --- ADD MORE API ENDPOINTS FOR OTHER MODELS HERE ---
# e.g., /api/buildings, /api/floors, /api/rooms, /api/assets, /api/connections


# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') == 'development'))
