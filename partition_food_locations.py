import sys

import pandas as pd


# @BEGIN partition_food_locations
# @PARAM licensees_locations_input_filename
# @PARAM food_locations_output_filename
# @IN licensees_locations_input_file @URI file://{licensees_locations_input_filename}
# @OUT food_locations_output_file @URI file://{food_locations_output_filename}
def partition_food_locations(licensees_locations_input_filename, food_locations_output_filename):
    # @BEGIN read_licensees_locations_input
    # @IN licensees_locations_input_file @URI file://{licensees_locations_input_filename}
    # @OUT licensees_locations_input_df
    licensees_locations_input_df = pd.read_csv(licensees_locations_input_filename)
    # @END read_licensees_locations_input

    # @BEGIN remove_duplicate_locations
    # @IN licensees_locations_input_df
    # @OUT food_locations_df
    food_locations_df = licensees_locations_input_df[
        ["Address", "City", "State", "Zip", "Latitude", "Longitude"]
    ].copy()
    food_locations_df.drop_duplicates(
        subset=["Address", "City", "State", "Zip"], inplace=True
    )
    # @END remove_duplicate_locations

    print("\nOutput Dataframe:")
    food_locations_df.info()

    # @BEGIN write_food_locations
    # @IN food_locations_df
    # @OUT food_locations_output_file @URI file://{food_locations_output_filename}
    food_locations_df.to_csv(food_locations_output_filename, index=False)
    # @END write_food_locations

# @END main


if __name__ == "__main__":
    partition_food_locations(*sys.argv[1:])
