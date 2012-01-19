-- Schema for storage of membership payments in Base48 hackerspace
-- DB used: SQLite3 (members.db)

DROP TABLE IF EXISTS Members;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS UpdateHistory;

CREATE TABLE Members(
    id INTEGER PRIMARY KEY, -- this is equal to the memberID used for payments
    nick TEXT,
    name TEXT,
    member_since DATE DEFAULT CURRENT_DATE,
    payments_offset INT DEFAULT 0,
    member_to DATE DEFAULT NULL, -- WHERE member_to NOT NULL: active members
    is_student BOOLEAN DEFAULT FALSE,
    xmpp TEXT,
    mail TEXT,
    phone TEXT
);

-- This corresponds to a format of the Fio bank transparent account display
-- see: https://www.fio.cz/scgi-bin/hermes/dz-transparent.cgi?ID_ucet=2900086515
CREATE TABLE Payments(
    id INTEGER PRIMARY KEY,
    arrival DATE,
    amount REAL,
    payment_type TEXT,
    KS INTEGER,
    VS INTEGER,
    SS INTEGER,
    identification TEXT,
    message TEXT,

    -- this should be equal to VS or, if VS is missing, deduced from
    -- identification or message.
    -- Note: there are also other payments possible (f.e. money withdrawal),
    -- so for these cases, member_id should be NULL.
    member_id INTEGER DEFAULT NULL REFERENCES Members(id) ON DELETE NO ACTION,

    -- Payment identification (f.e. "payment for april and march 2011")
    -- is deduced from message, which has mandatory format, see:
    -- http://undergroundlab.cz/hackerspace/wiki/legal
    -- Errornous messages (not in this format) can be corrected by db admin
    -- by hand using field message_correct.
    message_corrected TEXT DEFAULT NULL
);

CREATE TABLE UpdateHistory(
    t DATETIME PRIMARY KEY
);

