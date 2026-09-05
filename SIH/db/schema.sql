-- ============================================================
-- SCHEMA: Central Ministries + State Departments
-- ============================================================


-- CENTRAL MINISTRIES (Union Government)
CREATE TABLE IF NOT EXISTS ministries (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    type             TEXT NOT NULL DEFAULT 'central',   -- always 'central' here
    state            TEXT DEFAULT NULL,                  -- always NULL for this table
    parent_ministry  INTEGER DEFAULT NULL,                -- self-reference: sub-department under a ministry
    FOREIGN KEY (parent_ministry) REFERENCES ministries(id)
);

-- STATE / UT DEPARTMENTS
CREATE TABLE IF NOT EXISTS state_departments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    type             TEXT NOT NULL DEFAULT 'state',      -- always 'state' here
    state            TEXT NOT NULL,                        -- e.g. 'Punjab', 'Kerala'
    parent_ministry  INTEGER DEFAULT NULL,                -- self-reference: sub-dept under a state dept
    FOREIGN KEY (parent_ministry) REFERENCES state_departments(id)
);

CREATE INDEX IF NOT EXISTS idx_state_departments_state ON state_departments(state);
