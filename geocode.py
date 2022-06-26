import os
import sys
import googlemaps
import pandas as pd
import numpy as np

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
    state_abbreviation = get_address_component_by_type(address_components, "administrative_area_level_1")
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
        if np.isnan(location_coordinate_pair[0]) or np.isnan(location_coordinate_pair[1]):
            return EMPTY_ADDRESS 

        results = gmaps.reverse_geocode(location_coordinate_pair)

        if not results:
            return EMPTY_ADDRESS

        return unpack_address(results[0]["address_components"])
    except googlemaps.exceptions.HTTPError as e:
        print(e, file=sys.stderr)
        return EMPTY_ADDRESS

def unpack_location(location):
    return dict(
        Latitude=location["lat"],
        Longitude=location["lng"]
    )

def geocode(full_address):
    try:
        return unpack_location(gmaps.geocode(full_address)[0]["geometry"]["location"])
    except googlemaps.exceptions.HTTPError as e:
        print(e, file=sys.stderr)
        return dict(
            Latitude=None,
            Longitude=None,
        )


# @BEGIN main
# @param food_inspections_input_filename
# @param geocoding_output_filename
# @IN food_inspections_input_file @URI file://{food_inspections_input_filename}
# @OUT geocoding_output_file @URI file://{geocoding_output_filename}
def main(food_inspections_input_filename, geocoding_output_filename):
    # @BEGIN read_food_inspections_input
    # @param food_inspections_input_filename
    # @IN food_inspections_input_file @URI file://{food_inspections_input_filename}
    # @OUT food_inspections_df
    food_inspections_input_df = pd.read_csv(food_inspections_input_filename)
    food_inspections_df = food_inspections_input_df[
        food_inspections_input_df.Address.isna() | 
        food_inspections_input_df.City.isna() |
        food_inspections_input_df.State.isna() |
        food_inspections_input_df.Zip.isna() |
        food_inspections_input_df.Latitude.isna() |
        food_inspections_input_df.Longitude.isna()
    ].copy().reset_index()
    # @END read_food_inspections_input

    # @BEGIN extract_inspection_ids
    # @IN food_inspections_df
    # @OUT inspection_ids
    food_inspections_df.Zip.fillna(0, inplace=True)
    food_inspections_df.Zip = food_inspections_df.Zip.astype(int)
    inspection_ids = food_inspections_df["Inspection ID"]
    # @END extract_inspection_ids

    # @BEGIN extract_address_parts
    # @IN food_inspections_df
    # @OUT address_parts_df
    food_inspections_df.Zip.fillna(0, inplace=True)
    food_inspections_df.Zip = food_inspections_df.Zip.astype(int)
    address_parts_df = food_inspections_df[["Address", "City", "State", "Zip"]]
    # @END extract_address_parts

    # @BEGIN geocode_addresses
    # @IN address_parts_df
    # @OUT location_df
    full_addresses = address_parts_df.apply(lambda address_parts: " ".join([str(part) for part in address_parts if part]), axis=1).tolist()
    location_results = [geocode(full_address) for full_address in full_addresses]
    location_df = pd.DataFrame.from_dict(location_results)
    # @END geocode_addresses

    # @BEGIN extract_location_coordinates
    # @IN food_inspections_df
    # @IN location_df
    # @OUT location_coordinates_df
    location_coordinates_df = food_inspections_df[["Latitude", "Longitude"]].copy()
    location_coordinates_df.fillna(location_df, inplace=True)
    # @END extract_location_coordinates

    # @BEGIN reverse_geocode_locations
    # @IN location_coordinates_df
    # @IN address_parts_df
    # @OUT address_df
    location_coordinate_pairs = location_coordinates_df.apply(lambda location_coordinates: tuple(location_coordinates), axis=1).tolist()
    address_results = [reverse_geocode(location_coordinate_pair) for location_coordinate_pair in location_coordinate_pairs]
    address_df = pd.DataFrame.from_dict(address_results)
    address_df.fillna(address_parts_df, inplace=True)
    # @END reverse_geocode_locations

    # @BEGIN join_geocoding_results
    # @IN inspection_ids
    # @IN address_df
    # @IN location_df
    # @OUT geocoding_df
    geocoding_df = pd.DataFrame()
    geocoding_df["Inspection ID"] = inspection_ids
    geocoding_df["Address"] = address_df["Address"]
    geocoding_df["City"] = address_df["City"]
    geocoding_df["State"] = address_df["State"]
    geocoding_df["Zip"] = address_df["Zip"]
    geocoding_df["Latitude"] = location_df["Latitude"]
    geocoding_df["Longitude"] = location_df["Longitude"]
    # @END join_geocoding_results

    # @BEGIN write_geocoding_output
    # @IN geocoding_df
    # @OUT geocoding_output_file @URI file://{geocoding_output_filename}
    geocoding_df.to_csv(geocoding_output_filename, index=False)
    # @END write_geocoding_output

# @END main

if __name__ == "__main__":
    main(*sys.argv[1:])
