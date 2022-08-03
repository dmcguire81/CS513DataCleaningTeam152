import sys
import re
import sqlite3
import pandas as pd


def get_create_table_string(tablename, connection):
    sql = """
    select * from sqlite_master where name = "{}" and type = "table"
    """.format(tablename) 
    result = connection.execute(sql)
    create_table_string = result.fetchmany()[0][4]
    return create_table_string

def add_pk_to_create_table_string(create_table_string, colname):
    regex = "(\n*[\"]*{}[\"]*\s+[^,]+)([,)])".format(colname)
    # The schema change persist in the database. If the primary key was already added,
    # we can't have more than one primary key. Check before add primary key
    matched = re.search(regex,create_table_string).group()
    if "PRIMARY KEY" in matched:
        return create_table_string
    return re.sub(regex, "\\1 PRIMARY KEY,",  create_table_string, count=1)

def add_pk_to_sqlite_table(tablename, index_column, connection):
    cts = get_create_table_string(tablename, connection)
    cts = add_pk_to_create_table_string(cts, index_column)
    template = """
    PRAGMA foreign_keys=off;

    BEGIN TRANSACTION;
        ALTER TABLE {tablename} RENAME TO {tablename}_old_;

        {cts};

        INSERT INTO {tablename} SELECT * FROM {tablename}_old_;

        DROP TABLE IF EXISTS {tablename}_old_;

    COMMIT TRANSACTION;

    PRAGMA foreign_keys=on;
    """

    create_and_drop_sql = template.format(tablename = tablename, cts = cts)
    connection.executescript(create_and_drop_sql)

def add_fk_to_create_table_string(create_table_string, colname, parent_tablename):
    # When the parent table is renamed, it automatically renames this part. It may leave the
    # the old name in the child table schema. This takes care of that. 
    if "_old_" in create_table_string:
        regex = '(["]*(\w+(?=_old_))_old_["]*)'
        create_table_string = re.sub(regex, "\\2",  create_table_string, count=1)

    # Ensure duplicate foreign key constraint is not added for the same col. 
    fk_template = f',FOREIGN KEY ("{colname}") REFERENCES {parent_tablename}("{colname}"))'
    if fk_template in create_table_string:
        return create_table_string 

    last_bracket_regex = "([)]$)"
    return re.sub(last_bracket_regex, fk_template,  create_table_string, count=1)

def add_fk_to_sqlite_table(tablename, fk_colname, parent_tablename, connection):
    cts = get_create_table_string(tablename, connection)
    cts = add_fk_to_create_table_string(cts, fk_colname, parent_tablename)
    
    template = """
    PRAGMA foreign_keys=on;

    BEGIN TRANSACTION;
        ALTER TABLE {tablename} RENAME TO {tablename}_old_;

        {cts};

        INSERT INTO {tablename} SELECT * FROM {tablename}_old_;

        DROP TABLE IF EXISTS {tablename}_old_;

    COMMIT TRANSACTION;

    PRAGMA foreign_keys=off;
    """
    
    create_and_drop_sql = template.format(tablename = tablename, cts = cts)
    connection.executescript(create_and_drop_sql)

def add_composite_pk_to_create_table_string(create_table_string, pk_cols):
    pk_cols_str = ""
    for i in range(len(pk_cols)-1):
        pk_cols_str +=f'"{pk_cols[i]}",'
    pk_cols_str +=f'"{pk_cols[len(pk_cols)-1]}"'
    composite_pk_template = f',PRIMARY KEY({pk_cols_str}))'
    # The schema change persist in the database. If the primary key was already added,
    # we can't have more than one primary key. Check before add primary key
    if composite_pk_template in create_table_string:
        return create_table_string
    return re.sub("([)]$)", composite_pk_template,  create_table_string, count=1)

def add_composite_pk_to_sqlite_table(tablename, pk_cols, connection):
    cts = get_create_table_string(tablename, connection)
    cts = add_composite_pk_to_create_table_string(cts, pk_cols)
    template = """
    BEGIN TRANSACTION;
        ALTER TABLE {tablename} RENAME TO {tablename}_old_;

        {cts};

        INSERT INTO {tablename} SELECT * FROM {tablename}_old_;

        DROP TABLE IF EXISTS {tablename}_old_;

    COMMIT TRANSACTION;
    """
    create_and_drop_sql = template.format(tablename = tablename, cts = cts)
    connection.executescript(create_and_drop_sql)

def add_composite_fk_to_create_table_string(create_table_string, pk_cols, parent_tablename):
    # When the parent table is renamed, it automatically renames this part. It may leave the
    # the old name in the child table schema. This takes care of that. 
    if "_old_" in create_table_string:
        regex = '(["]*(\w+(?=_old_))_old_["]*)'
        create_table_string = re.sub(regex, "\\2",  create_table_string, count=1)
        
    pk_cols_str = ""
    for i in range(len(pk_cols)-1):
        pk_cols_str +=f'"{pk_cols[i]}",'
    pk_cols_str +=f'"{pk_cols[len(pk_cols)-1]}"'  

    # Ensure duplicate foreign key constraint is not added for the same col.  
    composite_fk_tamplate = f',FOREIGN KEY ({pk_cols_str}) REFERENCES {parent_tablename} ({pk_cols_str}))'
    if composite_fk_tamplate in create_table_string:
        return create_table_string
    return re.sub("([)]$)", composite_fk_tamplate,  create_table_string, count=1)


def add_composite_fk_to_sqlite_table(tablename, pk_cols, parent_tablename, connection):
    cts = get_create_table_string(tablename, connection)
    cts = add_composite_fk_to_create_table_string(cts, pk_cols,parent_tablename)
    template = """
    BEGIN TRANSACTION;
        ALTER TABLE {tablename} RENAME TO {tablename}_old_;

        {cts};

        INSERT INTO {tablename} SELECT * FROM {tablename}_old_;

        DROP TABLE {tablename}_old_;

    COMMIT TRANSACTION;
    """
    create_and_drop_sql = template.format(tablename = tablename, cts = cts)
    connection.executescript(create_and_drop_sql)


def repair_primary_key_constraint_violation(df, pk_colnames):
    # The primary key column values can't be null
    # There can't duplicate values in the PK column. 
    deduped_df = df.drop_duplicates(subset=pk_colnames)
    return deduped_df


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
# @IN dirty_food_inspections_file @URI file://{dirty_food_inspections_filename}
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
    # @BEGIN food_licensee_inspections_input @desc load the food licensee inspections data data from csv.
    # @IN food_licensee_inspections_file @URI file://{food_licensee_inspections_filename}
    # @OUT food_licensee_inspections
    food_licensee_inspections = pd.read_csv(food_licensee_inspections_filename)
    food_licensee_inspections["License #"] = food_licensee_inspections["License #"].astype('Int64')
    # @END food_licensee_inspections_input

    # @BEGIN food_inspection_violations_input @desc read food inspection violations data from csv, and drop duplicate records.
    # @IN food_inspection_violations_file @URI file://{food_inspection_violations_filename}
    # @OUT food_inspection_violations
    food_inspection_violations = pd.read_csv(food_inspection_violations_filename)
    food_inspection_violations = food_inspection_violations.drop_duplicates(subset=["Inspection ID", "Violation ID", "Violation Comments"])  
    # @END food_inspection_violations_input

    # @BEGIN food_violations_input @desc read the food violations data from csv.
    # @IN food_violations_file @URI file://{food_violations_filename}
    # @OUT food_violations
    food_violations = pd.read_csv(food_violations_filename)
    # @END food_violations_input

    # @BEGIN food_licensees_input @desc read the food licensees data spreadsheet, normalize casing different, drop null values and duplicate records.
    # @IN food_licensees_file @URI file://{food_licensees_filename}
    # @OUT food_licensees
    food_licensees = pd.read_csv(food_licensees_filename)
    food_licensees["DBA Name"] = food_licensees["DBA Name"].str.upper()
    food_licensees["AKA Name"] = food_licensees["AKA Name"].str.upper()
    food_licensees["State"] = food_licensees["State"].str.upper()
    food_licensees["City"] = food_licensees["City"].str.upper()
    food_licensees["Address"] = food_licensees["Address"].str.upper()
    food_licensees["License #"] = food_licensees["License #"].astype('Int64')
    food_licensees = food_licensees.dropna(subset=['License #', 'Address', 'Zip'])
    food_licensees = food_licensees.drop_duplicates(subset=['License #'])
    # @END food_licensees_input

    # @BEGIN food_locations_input @desc load food locations data from csv, drop null values and duplicate records.
    # @IN food_locations_file @URI file://{food_locations_filename}
    # @OUT food_locations
    food_locations = pd.read_csv(food_locations_filename)
    food_locations["State"] = food_locations["State"].str.upper()
    food_locations["City"] = food_locations["City"].str.upper()
    food_locations["Address"] = food_locations["Address"].str.upper()
    food_locations = food_locations.dropna(subset=['Address', 'Zip', 'City', 'State'])
    food_locations = food_locations.drop_duplicates(subset=['Address', 'Zip', 'City', 'State'])
    # @END food_locations_input

    # @BEGIN dirty_food_inspections_input @desc load the original data data from csv.
    # @IN dirty_food_inspections_file @URI file://{dirty_food_inspections_filename}
    # @OUT dirty_food_inspections
    dirty_food_inspections = pd.read_csv(dirty_food_inspections_filename)
    # @END dirty_food_inspections

    # @BEGIN create_or_connect_to_sqlite_db
    # @IN sqllite_db_file @URI file://{sqllite_db_filename}
    # @OUT conn
    conn = sqlite3.connect(sqlite_db_filename)
    # @END create_or_connect_to_sqlite_db

    # @BEGIN food_licensee_inspections_to_sql @desc write the food licensee inspections data to SQL database table. 
    # @IN food_licensee_inspections 
    # @param food_licensee_inspections_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_licensee_inspections_table
    food_licensee_inspections.to_sql('Food_Licensee_Inspections',con=conn,if_exists='replace', index=False)
    # @END food_licensee_inspections_to_sql

    # @BEGIN food_inspection_violations_to_sql @desc write the food inspection violations data to SQL database.
    # @IN food_inspection_violations 
    # @param food_inspection_violations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_inspection_violations_table
    food_inspection_violations.to_sql('Food_Inspection_Violations',con=conn,if_exists='replace', index=True)
    # @END food_inspection_violations_to_sql

    # @BEGIN food_violations_to_sql @desc write the food violations data to SQL database.
    # @IN food_violations 
    # @param food_violations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_violations_table
    food_violations.to_sql('Food_Violations',con=conn,if_exists='replace', index=False)
    # @END food_violations_to_sql

    # @BEGIN food_licensees_to_sql @desc write the food licensees data to SQL database.
    # @IN  food_licensees
    # @param food_licensees_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_licensees_table
    food_licensees.to_sql('Food_Licensees',con=conn,if_exists='replace', index=False)
    # @END food_licensees_to_sql

    # @BEGIN food_locations_to_sql @desc write the food locations data to SQL database.
    # @IN food_locations 
    # @param food_locations_tablename
    # @param conn 
    # @param if_exists
    # @param index
    # @OUT food_locations_table
    food_locations.to_sql('Food_Locations',con=conn,if_exists='replace', index=False)
    # @END food_locations_to_sql

    # @BEGIN dirty_food_inspections_to_sql @desc write original data(dirty data) to SQL database.
    # @IN dirty_food_inspections 
    # @param dirty_food_inspections_tablename
    # @param conn 
    # @param if_exists
    # @param index
    dirty_food_inspections.to_sql('Food_Inspections',con=conn,if_exists='replace', index=False)
    # @END dirty_food_inspections_to_sql

    # @BEGIN repair_referential_IC @desc remove (orphan) reocrds which violate referential integrity. 
    # @IN food_licensee_inspections_table
    # @IN food_licensees_table
    # @IN food_inspection_violations_table
    # @IN food_violations_table
    # @IN food_locations_table
    # @OUT cleaned_and_normalized_tables
    # @param conn 
    repair_referential_IC(
        "Food_Licensee_Inspections",
        "Food_Licensees", 
        "Food_Inspection_Violations",
        "Food_Violations",
        "Food_Locations",
        conn
    )
    # @END repair_referential_IC

    """Check single primary key constrainst"""
    # @BEGIN primary_key_constraint_check @desc set and enforce single primary key constraints.
    # @PARAM sql_tablename
    # @PARAM primary_keys_colnames
    # @PARAM cleaned_and_normalized_tables
    # @PARAM conn
    add_pk_to_sqlite_table("Cleaned_Food_Licensee_Inspections", "Inspection ID", conn)
    add_pk_to_sqlite_table("Cleaned_Food_Violations", "Violation ID", conn)
    add_pk_to_sqlite_table("Cleaned_Food_Licensees", "License #", conn) 
    add_pk_to_sqlite_table("Cleaned_Food_Inspection_Violations", "index", conn) 
    # @END primary_key_constraint_check

    """Check single foreign key constrainst"""
    # @BEGIN foreign_key_constraint_check @desc set and enforce single foreign key constraints.
    # @PARAM sql_tablename
    # @PARAM foreign_keys_colnames
    # @PARAM cleaned_and_normalized_tables
    # @PARAM conn
    add_fk_to_sqlite_table("Cleaned_Food_Licensee_Inspections", "License #", "Cleaned_Food_Licensees", conn)
    add_fk_to_sqlite_table("Cleaned_Food_Inspection_Violations", "Violation ID", "Cleaned_Food_Violations", conn)
    #add_fk_to_sqlite_table("Cleaned_Food_Inspection_Violations", "Inspection ID", "Cleaned_Food_Licensee_Inspections", conn)
    # @END foreign_key_constraint_check

    """Check composite Primary foreign key constraints"""
    # @BEGIN composeite_primary_key_constraint_check @desc set and enforce composite primary key constraints.
    # @PARAM sql_tablename
    # @PARAM primary_keys_colnames
    # @PARAM cleaned_and_normalized_tables
    # @PARAM conn
    add_composite_pk_to_sqlite_table("Cleaned_Food_Locations", ["Address","City","State","Zip"],conn)
    # @END foreign_key_constraint_check


    """Check composite foreign key constraints"""
    # @BEGIN composite_foreign_key_constraint_check @desc set and enforce composite foreign key constraints.
    # @PARAM sql_tablename
    # @PARAM composite_foreign_keys_colnames
    # @PARAM cleaned_and_normalized_tables
    # @PARAM conn
    add_composite_fk_to_sqlite_table("Cleaned_Food_Licensees", ["Address","City","State","Zip"],"Cleaned_Food_Locations",conn)
    # @END composite_foreign_key_constraint_check

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