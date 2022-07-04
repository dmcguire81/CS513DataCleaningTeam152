DROP TABLE IF EXISTS Food_Inspections;

CREATE TABLE Food_Inspections (
    "Inspection ID" INT NOT NULL,
    "DBA Name" TINYTEXT,
    "AKA Name" TINYTEXT,
    "License #" INT,
    "Facility Type" TINYTEXT,
    "Risk" TINYTEXT,
    "Address" TINYTEXT,
    "City" TINYTEXT,
    "State" TINYTEXT,
    "Zip" TINYTEXT,
    "Inspection Date" TINYTEXT,
    "Inspection Type" TINYTEXT,
    "Results" TINYTEXT,
    "Violations" LONGTEXT,
    "Latitude" FLOAT,
    "Longitude" FLOAT,
    "Location" TINYTEXT
);

.import -csv -skip 1 ./Food_Inspections.csv Food_Inspections
