import sys
import pandas as pd

# @BEGIN partition_dataset
# @PARAM food_inspections_filename
# @PARAM food_licensees_and_locations_filename
# @IN food_inspections_file @FILE {food_inspections_filename}
# @OUT food_licensees_and_locations_file @FILE {food_licensees_and_locations_filename}
# @OUT food_licensee_inspections_file @FILE {food_licensee_inspections_filename}
# @OUT food_inspection_violations_file @FILE {food_inspection_violations_filename}
def partition_dataset(food_inspections_filename, food_licensees_and_locations_filename, food_licensee_inspections_filename, food_inspection_violations_filename):
    # Inspection ID,DBA Name,AKA Name,License #,Facility Type,Risk,Address,City,State,Zip,Inspection Date,Inspection Type,Results,Violations,Latitude,Longitude,Location
    food_inspections_df = pd.read_csv(food_inspections_filename)

    # @BEGIN create_food_licensees_and_locations
    # @DESC CREATE TABLE Food_Licensees_And_Locations AS SELECT `DBA Name`, `AKA Name`, `License #`, `Facility Type`, `Address`, `City`, `State`, `Zip`, `Latitude`, `Longitude` FROM Food_Inspections
    # @IN food_inspections_file @FILE {food_inspections_filename}
    # @OUT food_licensees_and_locations_file @FILE {food_licensees_and_locations_filename}
    food_licensees_and_locations_df = food_inspections_df[["DBA Name", "AKA Name", "License #", "Facility Type", "Address", "City", "State", "Zip", "Latitude", "Longitude"]]
    food_licensees_and_locations_df.to_csv(food_licensees_and_locations_filename, index=False)
    # @END create_food_licensees_and_locations

    # @BEGIN create_food_licensee_inspections
    # @DESC CREATE TABLE Food_Licensee_Inspections AS SELECT `Inspection ID`, `License #`, `Risk`, `Inspection Date`, `Inspection Type`, `Results` FROM Food_Inspections
    # @IN food_inspections_file @FILE {food_inspections_filename}
    # @OUT food_licensee_inspections_file @FILE {food_licensee_inspections_filename}
    food_licensee_inspections_df = food_inspections_df[["Inspection ID", "License #", "Risk", "Inspection Date", "Inspection Type", "Results"]]
    food_licensee_inspections_df.to_csv(food_licensee_inspections_filename, index=False)
    # @END create_food_licensee_inspections

    # @BEGIN create_food_inspection_violations
    # @DESC CREATE TABLE Food_Inspection_Violations AS SELECT `Inspection ID`, `Violations` FROM Food_Inspections
    # @IN food_inspections_file @FILE {food_inspections_filename}
    # @OUT food_inspection_violations_file @FILE {food_inspection_violations_filename}
    food_inspection_violations_df = food_inspections_df[["Inspection ID", "Violations"]]
    food_inspection_violations_df.to_csv(food_inspection_violations_filename, index=False)
    # @END create_food_inspection_violations

# @END partition_dataset

if __name__ == "__main__":
    partition_dataset(*sys.argv[1:])
