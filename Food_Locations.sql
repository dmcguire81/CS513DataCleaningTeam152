DROP TABLE IF EXISTS Food_Locations;

CREATE TABLE Food_Locations (
    "Address" TINYTEXT,
    "City" TINYTEXT,
    "State" TINYTEXT,
    "Zip" TINYTEXT,
    "Latitude" FLOAT,
    "Longitude" FLOAT,
    PRIMARY KEY (Address, City, State, Zip)
);

.import -csv -skip 1 ./Food_Locations.csv Food_Locations
