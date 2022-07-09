DROP TABLE IF EXISTS Food_Inspections_Violations;

CREATE TABLE Food_Inspections_Violations (
    "Inspection ID" INT NOT NULL,
    "Violation ID" INT NOT NULL,
    "Violation Title" TEXT NOT NULL,
    "Violation Comments" LONGTEXT
);

.import -csv -skip 1 ./Food_Inspections_Violations.csv Food_Inspections_Violations