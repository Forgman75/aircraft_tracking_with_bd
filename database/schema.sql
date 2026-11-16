CREATE TABLE IF NOT EXISTS countries (
    country_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    south DOUBLE PRECISION NOT NULL,
    north DOUBLE PRECISION NOT NULL,
    west DOUBLE PRECISION NOT NULL,
    east DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (south >= -90 AND north <= 90 AND south <= north),
    CHECK (west >= -180 AND east <= 180)
);

CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(country_id) ON DELETE CASCADE,
    callsign TEXT NOT NULL,
    speed DOUBLE PRECISION NOT NULL CHECK (speed >= 0),
    altitude DOUBLE PRECISION NOT NULL CHECK (altitude >= 0),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT aircraft_country_callsign_unique UNIQUE (country_id, callsign)
);

CREATE INDEX IF NOT EXISTS idx_aircraft_country_id ON aircraft(country_id);
CREATE INDEX IF NOT EXISTS idx_aircraft_speed ON aircraft(speed);
