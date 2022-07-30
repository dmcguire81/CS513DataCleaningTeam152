import sys
import re
import sqlite3
import pandas as pd

def repair_referential_IC(
    food_licensee_inspections,
    food_licensees, 
    food_inspection_violations,
    food_violations,
    food_locations,
    connection):

    template= f"""
    BEGIN TRANSACTION;

        CREATE TABLE IF NOT EXISTS Cleaned_{food_licensee_inspections} AS 
        SELECT * 
        FROM {food_licensee_inspections} T1 
        WHERE T1."License #" IN (
            SELECT DISTINCT  T2."License #" FROM {food_licensees} T2
        );

        CREATE TABLE IF NOT EXISTS  Cleaned_{food_inspection_violations} AS 
        SELECT * FROM {food_inspection_violations} t1
        WHERE t1."Inspection ID" IN (
            SELECT DISTINCT t2."Inspection ID" FROM {food_licensee_inspections} t2
        ) AND t1."Violation ID" IN (
            SELECT DISTINCT t3."Violation ID" FROM {food_violations} t3
        );

        CREATE TABLE IF NOT EXISTS Cleaned_{food_licensees} AS 
        SELECT * 
        FROM {food_licensees} T1
        WHERE EXISTS (
        SELECT 1
        FROM {food_locations} T2
        WHERE T1.Address = T2.Address AND 
                T1.Zip = T2.Zip AND 
                T1.State = T2.State AND 
                T1.City = T2.City
        );

        CREATE TABLE IF NOT EXISTS Cleaned_{food_violations} AS 
        SELECT * 
        FROM {food_violations};

        CREATE TABLE IF NOT EXISTS Cleaned_{food_locations} AS 
        SELECT * 
        FROM {food_locations};

    COMMIT TRANSACTION;
    """
    connection.executescript(template)

# @BEGIN normalize_dataset
# @IN food_licensee_inspections_file @URI file://{food_licensee_inspections_filename}
# @IN food_inspection_violations_file @URI file://{food_inspection_violations_filename}
# @IN food_violations_file @URI file://{food_violations_filename}
# @IN food_licensees_file @URI file://{food_licensees_filename}
# @IN food_locations_file @URI file://{food_locations_filename}
# @IN dirty_food_inspections @URI file://{dirty_food_inspections_filename}
# @param sqlite_db_file
# @OUT sqllite_db_file @URI file://{sqlite_db_filename} 
def main(
        food_licensee_inspections_filename, 
        food_inspection_violations_filename,
        food_violations_filename,
        food_licensees_filename,
        food_locations_filename,
        dirty_food_inspections_filename,
        sqlite_db_filename
    ):

    """Load and filter out bad data"""
    # @BEGIN food_licensee_inspections_input
    # @IN food_licensee_inspections_file @URI file://{food_licensee_inspections_filename}
    # @OUT food_licensee_inspections
    food_licensee_inspections = pd.read_csv(food_licensee_inspections_filename)
    # @END food_licensee_inspections_input

    # @BEGIN food_inspection_violations_input
    # @IN food_inspection_violations_file @URI file://{food_inspection_violations_filename}
    # @OUT food_inspection_violations
    food_inspection_violations = pd.read_csv(food_inspection_violations_filename)
    food_inspection_violations = food_inspection_violations.drop_duplicates(subset=["Inspection ID", "Violation ID", "Violation Comments"])  
    # @END food_inspection_violations_input

    # @BEGIN food_violations_input
    # @IN food_violations_file @URI file://{food_violations_filename}
    # @OUT food_violations
    food_violations = pd.read_csv(food_violations_filename)
    # @END food_violations_input

    # @BEGIN food_licensees_input
    # @IN food_licensees_file @URI file://{food_licensees_filename}
    # @OUT food_licensees
    food_licensees = pd.read_csv(food_licensees_filename)
    food_licensees["DBA Name"] = food_licensees["DBA Name"].str.upper()
    food_licensees["AKA Name"] = food_licensees["AKA Name"].str.upper()
    food_licensees["State"] = food_licensees["State"].str.upper()
    food_licensees["City"] = food_licensees["City"].str.upper()
    food_licensees["Address"] = food_licensees["Address"].str.upper()
    food_licensees = food_licensees.dropna(subset=['License #', 'Address', 'Zip'])
    food_licensees = food_licensees.drop_duplicates(subset=['License #'])
    # @END food_licensees_input

    # @BEGIN food_locations_input
    # @IN food_locations_file @URI file://{food_locations_filename}
    # @OUT food_locations
    food_locations = pd.read_csv(food_locations_filename)
    food_locations["State"] = food_locations["State"].str.upper()
    food_locations["City"] = food_locations["City"].str.upper()
    food_locations["Address"] = food_locations["Address"].str.upper()
    food_locations = food_locations.dropna(subset=['Address', 'Zip', 'City', 'State'])
    food_locations = food_locations.drop_duplicates(subset=['Address', 'Zip', 'City', 'State'])
    # @END food_locations_input

    # @BEGIN dirty_food_inspections_input
    # @IN food_licensee_inspections_file @URI file://{dirty_food_inspections_filename}
    # @OUT dirty_food_inspections
    dirty_food_inspections = pd.read_csv(dirty_food_inspections_filename)
    # @END dirty_food_inspections

    # @BEGIN create_or_connect_to_sqlite_db
    # @IN sqllite_db_file @URI file://{sqllite_db_filename}
    # @OUT conn
    conn = sqlite3.connect(sqlite_db_filename)
    # @END create_or_connect_to_sqlite_db

    # @BEGIN food_licensee_inspections_to_sql
    # @IN food_licensee_inspections 
    # @param food_licensee_inspections_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_licensee_inspections_table
    food_licensee_inspections.to_sql('Food_Licensee_Inspections',con=conn,if_exists='replace', index=False)
    # @END food_licensee_inspections_to_sql

    # @BEGIN food_inspection_violations_to_sql
    # @IN food_inspection_violations 
    # @param food_inspection_violations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_inspection_violations_table
    food_inspection_violations.to_sql('Food_Inspection_Violations',con=conn,if_exists='replace', index=True)
    # @END food_inspection_violations_to_sql

    # @BEGIN food_violations_to_sql
    # @IN food_violations 
    # @param food_violations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_violations_table
    food_violations.to_sql('Food_Violations',con=conn,if_exists='replace', index=False)
    # @END food_violations_to_sql

    # @BEGIN food_licensees_to_sql
    # @IN food_licensees 
    # @param food_licensees_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_licensees_table
    food_licensees.to_sql('Food_Licensees',con=conn,if_exists='replace', index=False)
    # @END food_licensees_to_sql

    # @BEGIN food_locations_to_sql
    # @IN food_locations 
    # @param food_locations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_locations_table
    food_locations.to_sql('Food_Locations',con=conn,if_exists='replace', index=False)
    # @END food_locations_to_sql

    # @BEGIN dirty_food_inspections_to_sql
    # @IN dirty_food_inspections 
    # @param dirty_food_inspections_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT sqlite_db_file
    dirty_food_inspections.to_sql('Food_Inspections',con=conn,if_exists='replace', index=False)
    # @END dirty_food_inspections_to_sql

    # @BEGIN repair_referential_IC
    # @IN food_licensee_inspections_table
    # @IN food_licensees_table
    # @IN food_inspection_violations_table
    # @IN food_violations_table
    # @IN food_locations_table
    # @param conn 
    # @OUT sqlite_db_file
    repair_referential_IC(
        "Food_Licensee_Inspections",
        "Food_Licensees", 
        "Food_Inspection_Violations",
        "Food_Violations",
        "Food_Locations",
        conn
    )
    # @END repair_referential_IC

# @END normalize_dataset

if __name__=="__main__":
    #main(*sys.argv[1:])
    main(
        "Cleaned_Food_Licensee_Inspections.csv", 
        "Cleaned_Food_Inspection_Violations.csv",
        "Cleaned_Food_Violations.csv",
        "repaired/Repaired_Food_Licensees_and_Locations.csv",
        "repaired/Food_Locations.csv",
        "repaired/Food_Inspections.csv",
        "test_database.db"
    )