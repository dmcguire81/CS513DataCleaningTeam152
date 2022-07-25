DROP TABLE IF EXISTS Repaired_Food_Licensees_and_Locations;

CREATE TABLE Repaired_Food_Licensees_and_Locations (
    "DBA Name" TINYTEXT,
    "AKA Name" TINYTEXT,
    "License #" INT,
    "Facility Type" TINYTEXT,
    "Address" TINYTEXT,
    "City" TINYTEXT,
    "State" TINYTEXT,
    "Zip" TINYTEXT,
    "Latitude" FLOAT,
    "Longitude" FLOAT
);

.import -csv -skip 1 ./Repaired_Food_Licensees_and_Locations.csv Repaired_Food_Licensees_and_Locations
