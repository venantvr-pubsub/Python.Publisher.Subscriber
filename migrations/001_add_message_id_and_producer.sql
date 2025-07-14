-- Create new messages table with new columns
DROP TABLE IF EXISTS messages;

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    message_id TEXT,
    message TEXT,
    producer TEXT,
    timestamp REAL
);

-- Create new consumptions table with message_id
DROP TABLE IF EXISTS consumptions;

CREATE TABLE consumptions (
    consumer TEXT,
    topic TEXT,
    message_id TEXT,
    message TEXT,
    timestamp REAL
);

-- Subscriptions table remains unchanged
CREATE TABLE IF NOT EXISTS subscriptions (
    sid TEXT,
    consumer TEXT,
    topic TEXT,
    connected_at REAL,
    PRIMARY KEY (sid, topic)
);
