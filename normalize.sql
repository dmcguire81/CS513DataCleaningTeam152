PRAGMA foreign_keys = ON;

-- @BEGIN Normalize
-- @IN Cleaned_Food_Licensee_Inspections
-- @IN Repaired_Food_Licensees_and_Locations
-- @IN Cleaned_and_Unnested_Food_Inspection_Violations
-- @OUT Normalized_Food_Inspections @URI file:Normalized_Food_Inspections.sqlite

-- Food Violations
-- @BEGIN Create_Food_Violations_Table
-- @OUT Food_Violations
DROP TABLE IF EXISTS Food_Violations;
CREATE TABLE Food_Violations (
    "Violation ID" INTEGER PRIMARY KEY,
    "Violation Title" TEXT NOT NULL
);
-- @END Create_Food_Violations_Table

-- @BEGIN Insert_Food_Violations
-- @IN Food_Violations
-- @IN Cleaned_and_Unnested_Food_Inspection_Violations
-- @OUT Food_Violations
INSERT INTO Food_Violations
SELECT "Violation ID",
    "Violation Title"
FROM Cleaned_and_Unnested_Food_Inspection_Violations
GROUP BY "Violation ID",
    "Violation Title";
-- @END Insert_Food_Violations


-- Food Locations
-- @BEGIN Create_Food_Locations_Table
-- @OUT Food_Locations
DROP TABLE IF EXISTS Food_Locations;
CREATE TABLE Food_Locations (
    "Address" TINYTEXT NOT NULL,
    "City" TINYTEXT NOT NULL,
    "State" TINYTEXT NOT NULL,
    "Zip" TINYTEXT NOT NULL,
    "Latitude" FLOAT NOT NULL,
    "Longitude" FLOAT NOT NULL,
    PRIMARY KEY ("Address", "City", "State", "Zip")
);
-- @END Create_Food_Locations_Table

-- @BEGIN Insert_Food_Locations
-- @IN Food_Locations
-- @IN Repaired_Food_Licensees_and_Locations
-- @OUT Food_Locations
INSERT INTO Food_Locations
SELECT "Address",
    "City",
    "State",
    "Zip",
    "Latitude",
    "Longitude"
FROM Repaired_Food_Licensees_and_Locations
GROUP BY "Address",
    "City",
    "State",
    "Zip",
    "Latitude",
    "Longitude"
HAVING LENGTH("Address") > 0
    AND LENGTH("City") > 0
    AND LENGTH("State") > 0
    AND LENGTH("Zip") > 0;
-- @END Insert_Food_Locations


-- Food Licensees
-- @BEGIN Create_Food_Licensees_Table
-- @PARAM Food_Locations
-- @OUT Food_Licensees
DROP TABLE IF EXISTS Food_Licensees;
CREATE TABLE Food_Licensees (
    "License #" INTEGER PRIMARY KEY,
    "DBA Name" TINYTEXT NOT NULL,
    "AKA Name" TINYTEXT,
    "Facility Type" TINYTEXT,
    "Address" TINYTEXT NOT NULL,
    "City" TINYTEXT NOT NULL,
    "State" TINYTEXT NOT NULL,
    "Zip" TINYTEXT NOT NULL,
    FOREIGN KEY ("Address", "City", "State", "Zip") REFERENCES Food_Locations ("Address", "City", "State", "Zip")
);
-- @END Create_Food_Licensees_Table

-- @BEGIN Insert_Food_Licensees
-- @IN Food_Licensees
-- @IN Repaired_Food_Licensees_and_Locations
-- @OUT Food_Licensees
INSERT INTO Food_Licensees
SELECT "License #",
    "DBA Name",
    "AKA Name",
    "Facility Type",
    "Address",
    "City",
    "State",
    "Zip"
FROM Repaired_Food_Licensees_and_Locations
GROUP BY "License #"
HAVING COUNT(DISTINCT "DBA Name") == 1
    AND COUNT(DISTINCT "AKA Name") == 1
    AND COUNT(DISTINCT "Facility Type") == 1
    AND COUNT(DISTINCT "Address") == 1
    AND COUNT(DISTINCT "City") == 1
    AND COUNT(DISTINCT "State") == 1
    AND COUNT(DISTINCT "Zip") == 1
    AND LENGTH("Address") > 0
    AND LENGTH("City") > 0
    AND LENGTH("State") > 0
    AND LENGTH("Zip") > 0;
-- @END Insert_Food_Licensees


-- Food Licensee Inspections
-- @BEGIN Create_Food_Licensee_Inspections_Table
-- @PARAM Food_Licensees
-- @OUT Food_Licensee_Inspections
DROP TABLE IF EXISTS Food_Licensee_Inspections;
CREATE TABLE Food_Licensee_Inspections (
    "Inspection ID" INTEGER PRIMARY KEY,
    "License #" INTEGER NOT NULL,
    "Risk" TINYTEXT,
    "Inspection Date" TINYTEXT,
    "Inspection Type" TINYTEXT,
    "Results" TINYTEXT,
    FOREIGN KEY ("License #") REFERENCES Food_Licensees ("License #")
);
-- @END Create_Food_Licensee_Inspections_Table

-- @BEGIN Insert_Food_Licensee_Inspections
-- @IN Food_Licensee_Inspections
-- @IN Cleaned_Food_Licensee_Inspections
-- @OUT Food_Licensee_Inspections
INSERT INTO Food_Licensee_Inspections
SELECT "Inspection ID",
    "License #",
    "Risk",
    "Inspection Date",
    "Inspection Type",
    "Results"
FROM Cleaned_Food_Licensee_Inspections
WHERE "License #" IN (
        SELECT "License #"
        FROM Food_Licensees
    );
-- @END Insert_Food_Licensee_Inspections

-- Food Inspection Violations
-- @BEGIN Create_Food_Inspection_Violations_Table
-- @PARAM Food_Licensee_Inspections
-- @PARAM Food_Violations
-- @OUT Food_Licensee_Inspections
DROP TABLE IF EXISTS Food_Inspection_Violations;
CREATE TABLE Food_Inspection_Violations (
    "Inspection ID" INTEGER NOT NULL,
    "Violation ID" INTEGER NOT NULL,
    "Violation Comments" TEXT NOT NULL,
    FOREIGN KEY ("Inspection ID") REFERENCES Food_Licensee_Inspections ("Inspection ID"),
    FOREIGN KEY ("Violation ID") REFERENCES Food_Violations ("Violation ID")
);
-- @END Create_Food_Inspection_Violations_Table

-- @BEGIN Insert_Food_Inspection_Violations
-- @PARAM Food_Licensee_Inspections
-- @IN Food_Inspection_Violations
-- @IN Cleaned_and_Unnested_Food_Inspection_Violations
-- @OUT Food_Inspection_Violations
INSERT INTO Food_Inspection_Violations
SELECT "Inspection ID",
    "Violation ID",
    "Violation Comments"
FROM Cleaned_and_Unnested_Food_Inspection_Violations
WHERE "Inspection ID" IN (
        SELECT "Inspection ID"
        FROM Food_Licensee_Inspections
    );
-- @END Insert_Food_Inspection_Violations

-- @BEGIN Save
-- @PARAM Food_Violations
-- @PARAM Food_Locations
-- @PARAM Food_Licensees
-- @PARAM Food_Licensee_Inspections
-- @PARAM Food_Inspection_Violations
-- @OUT Normalized_Food_Inspections @URI file:Normalized_Food_Inspections.sqlite
-- @END Save

-- @END Normalize