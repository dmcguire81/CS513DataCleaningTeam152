DROP TABLE IF EXISTS Cleaned_Food_Licensee_Inspections;

CREATE TABLE Cleaned_Food_Licensee_Inspections (
    "Inspection ID" INT NOT NULL,
    "License #" INT,
    "Risk" TINYTEXT,
    "Inspection Date" TINYTEXT,
    "Inspection Type" TINYTEXT,
    "Results" TINYTEXT
);

.import -csv -skip 1 ./Cleaned_Food_Licensee_Inspections.csv Cleaned_Food_Licensee_Inspections
