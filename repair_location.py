import os
import sys

import googlemaps
import numpy as np
import pandas as pd

api_key = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=api_key)


def get_address_component_by_type(address_components, type):
    matches = [
        component["short_name"]
        for component in address_components
        if type in component["types"]
    ]

    if not matches:
        return None

    return matches[0]


def unpack_address(address_components):
    street_number = get_address_component_by_type(address_components, "street_number")
    formatted_street_number = street_number if street_number else ""
    route = get_address_component_by_type(address_components, "route")
    formatted_route = route if route else ""
    formatted_address = f"{formatted_street_number} {formatted_route}".lstrip().rstrip()
    city = get_address_component_by_type(address_components, "locality")
    state_abbreviation = get_address_component_by_type(
        address_components, "administrative_area_level_1"
    )
    postal_code = get_address_component_by_type(address_components, "postal_code")
    return dict(
        Address=formatted_address if formatted_address else None,
        City=city,
        State=state_abbreviation,
        Zip=postal_code,
    )


EMPTY_ADDRESS = dict(
    Address=None,
    City=None,
    State=None,
    Zip=None,
)


def reverse_geocode(location_coordinate_pair):
    try:
        if np.isnan(location_coordinate_pair[0]) or np.isnan(
            location_coordinate_pair[1]
        ):
            return EMPTY_ADDRESS

        results = gmaps.reverse_geocode(location_coordinate_pair)

        if not results:
            return EMPTY_ADDRESS

        return unpack_address(results[0]["address_components"])
    except (googlemaps.exceptions.HTTPError, IndexError) as e:
        print(f"{e}: {location_coordinate_pair}", file=sys.stderr)
        return EMPTY_ADDRESS


def unpack_location(location):
    return dict(Latitude=location["lat"], Longitude=location["lng"])


def geocode(full_address):
    try:
        return unpack_location(gmaps.geocode(full_address)[0]["geometry"]["location"])
    except (googlemaps.exceptions.HTTPError, IndexError) as e:
        print(f"{e}: {full_address}", file=sys.stderr)
        return dict(
            Latitude=None,
            Longitude=None,
        )


# @BEGIN repair_location
# @PARAM food_inspections_input_filename
# @PARAM geocoding_output_filename
# @IN food_inspections_input_file @URI file://{food_inspections_input_filename}
# @OUT geocoding_output_file @URI file://{geocoding_output_filename}
def repair_location(food_inspections_input_filename, geocoding_output_filename):
    # @BEGIN read_food_inspections_input
    # @IN food_inspections_input_file @URI file://{food_inspections_input_filename}
    # @OUT food_inspections_input_df
    food_inspections_input_df = pd.read_csv(food_inspections_input_filename)
    # @END read_food_inspections_input

    # @BEGIN query_missing_locations
    # @IN food_inspections_input_df
    # @OUT missing_location_df
    missing_location_df = food_inspections_input_df[
        food_inspections_input_df["Latitude"].isna()
        | food_inspections_input_df["Longitude"].isna()
    ].copy()
    missing_location_df["Zip"].fillna(0, inplace=True)
    missing_location_df["Zip"] = missing_location_df["Zip"].astype(int)
    # @END query_missing_locations

    # @BEGIN geocode_addresses
    # @IN missing_location_df
    # @OUT repaired_location_df
    address_parts_df = missing_location_df[["Address", "City", "State", "Zip"]].dropna()
    full_addresses = address_parts_df.apply(
        lambda address_parts: " ".join([str(part) for part in address_parts]),
        axis=1,
    ).tolist()
    location_results = [geocode(full_address) for full_address in full_addresses]
    repaired_location_df = pd.DataFrame.from_records(location_results)
    repaired_location_df.index = address_parts_df.index
    # @END geocode_addresses

    # @BEGIN repair_locations
    # @IN repaired_location_df
    # @IN food_inspections_input_df
    # @OUT repaired_location_food_inspections_df
    repaired_location_food_inspections_df = food_inspections_input_df.copy()
    repaired_location_food_inspections_df[
        ["Latitude", "Longitude"]
    ] = repaired_location_food_inspections_df[["Latitude", "Longitude"]].fillna(
        repaired_location_df
    )
    # @END repair_locations

    # @BEGIN query_missing_address_parts
    # @IN repaired_location_food_inspections_df
    # @OUT missing_address_part_df
    missing_address_part_df = repaired_location_food_inspections_df[
        (
            repaired_location_food_inspections_df["City"].isna()
            | repaired_location_food_inspections_df["Zip"].isna()
        )
        & repaired_location_food_inspections_df["Latitude"].notna()
        & repaired_location_food_inspections_df["Longitude"].notna()
    ].copy()
    # @END query_missing_address_parts

    # @BEGIN extract_location_coordinates
    # @IN missing_address_part_df
    # @OUT location_coordinate_pairs
    location_coordinate_pairs = (
        missing_address_part_df[["Latitude", "Longitude"]]
        .apply(lambda location_coordinates: tuple(location_coordinates), axis=1)
        .tolist()
    )
    # @END extract_location_coordinates

    # @BEGIN reverse_geocode_locations
    # @IN location_coordinate_pairs
    # @IN missing_address_part_df
    # @OUT repaired_address_part_df
    address_results = [
        reverse_geocode(location_coordinate_pair)
        for location_coordinate_pair in location_coordinate_pairs
    ]
    repaired_address_part_df = pd.DataFrame.from_records(address_results)
    repaired_address_part_df.index = missing_address_part_df.index
    # @END reverse_geocode_locations

    # @BEGIN repair_address_parts
    # @IN repaired_address_part_df
    # @IN repaired_location_food_inspections_df
    # @OUT repaired_food_inspections_df
    repaired_food_inspections_df = repaired_location_food_inspections_df.copy()
    repaired_food_inspections_df[["City", "Zip"]] = repaired_food_inspections_df[
        ["City", "Zip"]
    ].fillna(repaired_address_part_df)
    # @END repair_address_parts

    print("\nInput Dataframe:")
    food_inspections_input_df.info()
    print("\nOutput Dataframe:")
    repaired_food_inspections_df.info()

    # @BEGIN write_geocoding_output
    # @IN repaired_food_inspections_df
    # @OUT geocoding_output_file @URI file://{geocoding_output_filename}
    repaired_food_inspections_df.to_csv(geocoding_output_filename, index=False)
    # @END write_geocoding_output

# @END main


if __name__ == "__main__":
    repair_location(*sys.argv[1:])
