DROP TABLE IF EXISTS Cleaned_and_Unnested_Food_Inspection_Violations;

CREATE TABLE Cleaned_and_Unnested_Food_Inspection_Violations (
    "Inspection ID" INT NOT NULL,
    "Violation ID" INT NOT NULL,
    "Violation Title" TEXT NOT NULL,
    "Violation Comments" LONGTEXT
);

.import -csv -skip 1 ./Cleaned_and_Unnested_Food_Inspection_Violations.csv Cleaned_and_Unnested_Food_Inspection_Violations
