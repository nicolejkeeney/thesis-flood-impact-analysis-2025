"""
add_admin_units_emdat.py

Generate Admin Units column by matching strings from manually generated Admin Names column to their appropriate Admin Code from the GAUL shapefiles
Exports CSV with new column

"""

import pandas as pd
import ast
import geopandas as gpd

DATA_DIR = "../data/"
GAUL_L1_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_1"
GAUL_L2_FILEPATH = f"{DATA_DIR}GAUL_2015/g2015_2014_2"
EMDAT_FILEPATH = f"{DATA_DIR}emdat/emdat-missing-admin-units.csv"
EMDAT_OUTPUT_FILEPATH = f"{DATA_DIR}emdat/emdat-missing-admin-units-formatted.csv"  # Where to save the new file to


def main():
    # Read in data
    emdat_df = pd.read_csv(EMDAT_FILEPATH)
    gaul_l1 = gpd.read_file(GAUL_L1_FILEPATH)
    gaul_l2 = gpd.read_file(GAUL_L2_FILEPATH)

    for i, row in emdat_df.iterrows():
        # Convert the string representation of the list of dictionaries into an actual list
        try:
            admin_units = ast.literal_eval(row["Admin Names"])
        except:
            print(
                f"Admin Names for event ID: {row['id']} could not be read: {row['Admin Names']}"
            )
            continue

        # Subset GAUL to country
        country_mapping = {
            "Türkiye": "Turkey",
            "Côte d’Ivoire": "Côte d'Ivoire",  # This one seems redundant
            "Bolivia (Plurinational State of)": "Bolivia",
            "Iran (Islamic Republic of)": "Iran  (Islamic Republic of)",  # Also redundant
            "Democratic People's Republic of Korea": "Dem People's Rep of Korea",
        }
        country = country_mapping.get(row["Country"], row["Country"])
        gaul_l1_country = gaul_l1[gaul_l1["ADM0_NAME"] == country]
        gaul_l2_country = gaul_l2[gaul_l2["ADM0_NAME"] == country]

        # Loop through each dictionary and grab the admin code that corresponds to the admin name
        updated_list = []  # Empty list for putting the updated dictionaries in
        for unit in admin_units:
            # Grab code if it's an admin 1
            adm1_name = unit.get("adm1_name") or None
            if adm1_name is not None:
                adm1_code = gaul_l1_country[gaul_l1_country["ADM1_NAME"] == adm1_name][
                    "ADM1_CODE"
                ].iloc[0]
                unit_with_code = {"adm1_code": int(adm1_code), **unit}

            # Grab code if it's an admin 2
            adm2_name = unit.get("adm2_name") or None
            if adm2_name is not None:
                adm2_code = gaul_l2_country[gaul_l2_country["ADM2_NAME"] == adm2_name][
                    "ADM2_CODE"
                ].iloc[0]
                unit_with_code = {"adm2_code": int(adm2_code), **unit}

            updated_list.append(unit_with_code)

        # Put the updated list in the Admin Units column
        emdat_df.loc[i, "Admin Units"] = str(updated_list)

    # Save the csv
    emdat_df.to_csv(EMDAT_OUTPUT_FILEPATH, encoding="utf-8-sig", index=False)
    print(f"Saved file to: {EMDAT_OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
