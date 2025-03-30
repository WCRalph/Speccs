-- schema.sql for Speccs Application

-- Enable UUID generation functions if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables in reverse order of dependency for easy re-runs during dev
DROP TABLE IF EXISTS journal;
DROP TABLE IF EXISTS connections;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS floors;
DROP TABLE IF EXISTS buildings;
DROP TABLE IF EXISTS properties;


-- Top-level entity representing the entire property
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT, -- Can be simple text or potentially structured later
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Buildings within a property (e.g., Main House, Garage)
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    building_type VARCHAR(100), -- e.g., 'House', 'Garage', 'Shed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Floors within a building
CREATE TABLE floors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- e.g., 'First Floor', 'Basement'
    level_order INTEGER DEFAULT 0, -- For sorting floors correctly (0=Ground, 1=First, -1=Basement etc.)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rooms within a floor
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    floor_id UUID NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Reference to the Asset (Door) used as the 0-degree point for this room's circular layout
    -- Initially NULL until set by the user. Must reference an Asset.
    reference_door_asset_id UUID NULL REFERENCES assets(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- The core table for ALL items tracked in the house
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Location context: An asset typically belongs to one primary room
    -- Nullable because some assets might not be room-specific (e.g., main water shutoff)
    -- or represent abstract concepts like warranties not tied to a single physical spot.
    room_id UUID NULL REFERENCES rooms(id) ON DELETE SET NULL,

    asset_type VARCHAR(100) NOT NULL, -- Crucial! e.g., 'Outlet.Duplex', 'Switch.SinglePole', 'Pipe.Copper', 'Paint', 'Warranty', 'Door', 'Window', 'WallSegment'
    name VARCHAR(255), -- Optional user-defined label (e.g., "Living Room Sofa Outlet")
    description TEXT,
    install_date DATE,
    status VARCHAR(20) DEFAULT 'Active', -- e.g., 'Active', 'Replaced', 'Deleted'

    -- Location specifics (using the circular model)
    location_angle_degrees NUMERIC(5, 2), -- e.g., 355.50 degrees
    location_height_percent NUMERIC(5, 2), -- e.g., 60.00 percent from floor
    location_depth_percent NUMERIC(5, 2), -- e.g., 100.00 (wall), 0.00 (center)
    location_notes TEXT,

    -- Wall segment specifics (if asset_type is 'WallSegment' or similar)
    wall_length NUMERIC(10, 2),
    wall_length_unit VARCHAR(10), -- 'ft', 'm', 'in', 'cm'
    wall_height NUMERIC(10, 2),
    wall_height_unit VARCHAR(10),

    -- Flexible attributes store type-specific info (brand, color, voltage, serial#, etc.)
    attributes JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Intermediate table for defining connections between assets ("River Flow")
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    to_asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    -- Type of connection (important for tracing specific systems)
    connection_type VARCHAR(100) NOT NULL, -- e.g., 'ElectricalPower', 'WaterSupply', 'Drainage', 'ControlSignal', 'DataNetwork', 'RoomAccess', 'AttachedTo'
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- Maybe add 'directionality' if needed (e.g., 'Upstream', 'Downstream', 'Bidirectional') ?
    -- For now, assume direction is implied by 'from' -> 'to' and connection_type
);

-- Table for journaling/auditing changes made to assets
CREATE TABLE journal (
    id BIGSERIAL PRIMARY KEY, -- Use BIGSERIAL for automatic incrementing integer ID
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE, -- Which asset was affected
    user_identifier VARCHAR(255) DEFAULT 'System', -- Simple identifier for now
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action VARCHAR(50) NOT NULL, -- e.g., 'Create', 'Update', 'Replace', 'Delete', 'Link', 'Unlink'
    -- Store details about the change (e.g., which fields changed, old/new values, reason)
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- === INDEXES ===
-- Create indexes for commonly queried columns and foreign keys

-- Foreign Keys
CREATE INDEX idx_buildings_property_id ON buildings(property_id);
CREATE INDEX idx_floors_building_id ON floors(building_id);
CREATE INDEX idx_rooms_floor_id ON rooms(floor_id);
CREATE INDEX idx_rooms_reference_door_asset_id ON rooms(reference_door_asset_id);
CREATE INDEX idx_assets_room_id ON assets(room_id);
CREATE INDEX idx_connections_from_asset_id ON connections(from_asset_id);
CREATE INDEX idx_connections_to_asset_id ON connections(to_asset_id);
CREATE INDEX idx_journal_asset_id ON journal(asset_id);

-- Other useful indexes
CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_name ON assets(name); -- Optional, if searching by name is frequent
CREATE INDEX idx_connections_connection_type ON connections(connection_type);
CREATE INDEX idx_journal_timestamp ON journal(timestamp);

-- Consider adding GIN index on assets.attributes if querying JSONB fields frequently
-- CREATE INDEX idx_assets_attributes_gin ON assets USING GIN (attributes);


-- === COMMENTS ===
COMMENT ON COLUMN rooms.reference_door_asset_id IS 'FK to the Asset (type=Door) used as the 0-degree reference for this room.';
COMMENT ON COLUMN assets.room_id IS 'Primary room location for the asset. Nullable for non-room-specific items.';
COMMENT ON COLUMN assets.status IS 'Lifecycle status (Active, Replaced, Deleted).';
COMMENT ON COLUMN assets.attributes IS 'Flexible JSONB field for type-specific attributes (brand, color, serial, etc.).';
COMMENT ON COLUMN connections.connection_type IS 'Type of relationship (ElectricalPower, WaterSupply, AttachedTo, RoomAccess, etc.).';
COMMENT ON TABLE journal IS 'Audit log for changes made to assets.';
