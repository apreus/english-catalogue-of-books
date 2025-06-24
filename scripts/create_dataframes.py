import os
import re
import csv
import sys
from tqdm import tqdm
import pandas as pd
from create_entries import argparse_create

def create_dataframes(file_path, year_string):
    """
    Create more subsidiary dataframes and measures, and save to the /dataframes/ directory.

    Arguments:
        file_path: String; path to the clean entry file to be analyzed.
        year_string: String; represents what (19)year is being analyzed.

    Returns:
        full_df: Pandas Dataframe; object that contains all extracted information from all of the 
                 clean_entries.
    """
    with open(file_path, mode="r", newline='', errors="ignore",
        encoding="utf-8") as f:
        reader = csv.reader(f)
        clean_entries = list(reader)

    # When reading through CSVs from /clean_entries, some rows begin and end with "
    clean_entries = [entry[0].replace("\"", "") for entry in clean_entries]

    pub_date_pattern = fr"[A-ZÀ-ž][A-ZÀ-ž\.\s&,'\-]+,\W\w[^A-ZÀ-ž]+(?:\.|,)?\W{year_string}\.?$"

    main_entries = [entry for entry in clean_entries if re.search(pub_date_pattern, entry)]

    print("\nMain entries:", len(main_entries))
    
    # sys.exit("Clean and main entries testing")

    entries = pd.Series(main_entries)

    # Replace I with 1 when in close juncture with a number
    entries = entries.str.replace(r"I(\d)", "1\\1", regex=True)
    entries = entries.str.replace(r"(\d)I", "\\1\1", regex=True)

    # Replace I with 1 before publishing formats
    entries = entries.str.replace(r"I([tmv]o)", "1\\1", regex=True)

    # Replace word-separated cases of IS with 1s
    entries = entries.str.replace(r"(\W)IS(\W)", "\\1\1s\\2", regex=True)

    # Replace word-separated cases of I/TIS with 11s
    entries = entries.str.replace(r"(\W)[TI]IS(\W)", "\\1\1\1s\\2", regex=True)

    # Replace I with 1 before shillings and pence
    entries = entries.str.replace(r"I(d|s)", "1\\1", regex=True)

    # Make sure the shilling "s" is lowercase
    entries = entries.str.replace(r"(\d)S", "\\1s", regex=True)

    # Make floating I 1 before the above cases
    entries = entries.str.replace(r"I\s+(\d+(?:d|s|[tmv]o))", "1\\1", regex=True)

    # Replace digits followed by 5. as digits followed by s.
    entries = entries.str.replace(r"(\d+)5\.", "\\1s.", regex=True)

    back_pat = r"(?P<front>.*?)"
    
    # Publisher capture group
    back_pat += r"(?P<publisher>[A-ZÀ-ž][A-ZÀ-ž\.\s&,'\-]+)(?:,\W)" # add hyphen

    # Date capture group
    back_pat += fr"(?P<date>\w[^A-ZÀ-ž]+(?:\.|,)?\W{year_string})\.?$"
    entry_backs = entries.str.extract(back_pat)

    # print("Number of entries with publisher and date:", len(entry_backs))

    # Front capture group
    front_pat = r"^(?P<creators>(?:"
    front_pat += r"(?:[^()—\s]+\s){1,3}"
    front_pat += r"\((?![Tt]he|post free)[^\)]+\)"
    front_pat += r"(?:\sand\s|,?\ssee.*?\.(?![^\(]*\))\s*)?"
    front_pat += r")+)?"
    front_pat += r"\.?\s*(?P<is_editor>eds?\.,?)?"
    front_pat += r"[\-—\s]*(?![\-—\s]+)(?P<middle>.*)"

    entry_fronts = entry_backs["front"].str.extract(front_pat)
  
    full_df = pd.DataFrame()

    # Set columns
    full_df["entry"] = entries
    full_df["catalogue_year"] = 1900 + int(year_string)
    full_df["front"] = entry_backs["front"]
    full_df["publisher"] = entry_backs["publisher"]
    full_df["date"] = entry_backs["date"]
    full_df["creators"] = entry_fronts["creators"]
    full_df["is_editor"] = entry_fronts["is_editor"]
    full_df["middle"] = entry_fronts["middle"]
    full_df = full_df[["entry", "front", "creators", "is_editor", "middle", "publisher", "date", "catalogue_year"]]

    # Substitute "Surname (Name1) and Surname (Name 2)" for "Surname (Name1 and 2)"
    full_df["creators"] = full_df["creators"].str.replace(
        r"([^()]+)\(([^)]+) and ([^)]+)\)", "\\1(\\2) and \\1(\\3)", regex=True
    )

    # Remove full cross-reference "see [other header]." expressions.
    # Takes everything from "see" to the first period not in parenthesis.
    full_df["creators"] = full_df["creators"].str.replace(
        r"see.*\.(?![^(]*\))\s*", " and ", regex=True
    )

    # Get rid of any trailing ands.
    full_df["creators"] = full_df["creators"].str.replace(r"\s+and\s+$", "", regex=True)

    # Split each entry into a list of authors by " and " not in parenthesis.
    full_df["creators"] = full_df["creators"].str.split(r"\s+(?:and)(?![^(]*\))\s+")
    
    # Get last name and first name column values.
    head_names = full_df["creators"].apply(lambda x: x[0] if isinstance(x, list) else x)
    head_names = head_names.str.extract(r"^(?P<last_name>[^()]+)\s\((?P<first_name>[^)]+)\)$")
    full_df["last_name"] = head_names["last_name"]
    full_df["first_name"] = head_names["first_name"]

    # Get medial information
    full_df["title"] = full_df["middle"].str.extract(
        r"(?!^(?:No\.|Cr\.|Vo\.|fo\.|\d+\s?\}?\w|Illus\.|Ryl\.).*)"
        + r"^[^\dA-ZÀ-ž]*([\dA-ZÀ-ž].+?)"
        + r"(?:(?<!\W[A-ZÀ-ž]|No|id|pp)\.|"
        + r"[,.]?\W(?=No\.|Cr\.|Vo\.|fo\.|\d+\s?\}?\w|Illus\.|Ryl\.))"
    )

    # Extract English Publishing Formats
    full_df["format"] = full_df["middle"].str.extract(
        r"\W(fo\.|\d+[tvm]o[,.]?)\W"
    )

    # Extract Price Information.
    price_df = full_df["middle"].str.extract(
        r"(?P<price>\d+s\.?,?\s*\d+d\.?,?|\d+s\.?,?|\d+d\.?,?)"
        + r"\s*(?P<is_net>net)?"
        + r"(?!.*\1)(?=(?:\s*\([^\)]+\))*[\s.]*$)"
    )
    full_df["price_dirty"] = price_df["price"]
    full_df["is_net"] = price_df["is_net"]
    full_df["price"] = full_df["price_dirty"].str.replace(r"([ds]),", "\\1.", regex=True)
    full_df["price"] = full_df["price"].str.replace(r"s\.?\s+", "s. ", regex=True)
    full_df["price"] = full_df["price"].str.strip(",\s")
    # full_df["shillings"] = full_df["price"].str.extract(r"(\d+)s").fillna(0).astype(int)
    # full_df["pence"] = full_df["price"].str.extract(r"(\d+)d").fillna(0).astype(int)
    # full_df["price_in_pounds"] = full_df["pence"] / 240 + full_df["shillings"] / 20

    full_df["original_entry"] = pd.Series(main_entries)
    full_df["author_name"] = full_df["first_name"].str.cat(full_df["last_name"], sep=" ")
    full_df = full_df[
        [
            "entry",
            "last_name",
            "first_name",
            "title",
            "publisher",
            "price",
            # "price_in_pounds",
            "format",
            "original_entry",
            "author_name",
            # new fields
            "creators",
            "is_editor",
            "date",
            "catalogue_year",
            "is_net"
        ]
    ]

    missing_publisher_df = full_df[full_df["publisher"].isna()]
    total_missing_publisher = len(missing_publisher_df.index)
    print(total_missing_publisher)

    # sys.exit("Stop create_dataframes")

    return full_df

def save_dataframes(full_df, df_paths, verbose):
    """
    Create more subsidiary dataframes and measures, and save to the /dataframes/ directory.

    Arguments:
        full_df: Pandas Dataframe; object that contains all extracted information from all of the 
                 clean_entries.
        df_paths: Array; object that contains all target CSV and txt file paths.
    """

    full_df_path = df_paths[0]
    missing_first_df_path = df_paths[1]
    missing_format_df_path = df_paths[2]
    missing_last_df_path = df_paths[3]
    missing_price_df_path = df_paths[4]
    missing_publisher_df_path = df_paths[5]
    missing_title_df_path = df_paths[6]
    clean_df_path = df_paths[7]
    full_data_measures_path = df_paths[8]
    missing_title_and_publisher_path = df_paths[9]

    catalogue_year = full_df["catalogue_year"][1]

    total_full = len(full_df.index)
    full_df.to_csv(full_df_path, index=False)

    missing_first_name_df = full_df[full_df["first_name"].isna()]
    total_missing_first_name = len(missing_first_name_df.index)
    percent_missing_first_name = total_missing_first_name / total_full
    missing_first_name_df.to_csv(missing_first_df_path, index=False)

    missing_format_df = full_df[full_df["format"].isna()]
    total_missing_format = len(missing_format_df.index)
    percent_missing_format = total_missing_format / total_full
    missing_format_df.to_csv(missing_format_df_path, index=False)

    missing_last_name_df = full_df[full_df["last_name"].isna()]
    total_missing_last_name = len(missing_last_name_df.index)
    percent_missing_last_name = total_missing_last_name / total_full
    missing_last_name_df.to_csv(missing_last_df_path, index=False)

    missing_price_df = full_df[full_df["price"].isna()]
    total_missing_price = len(missing_price_df.index)
    percent_missing_price = total_missing_price / total_full
    missing_price_df.to_csv(missing_price_df_path, index=False)

    missing_publisher_df = full_df[full_df["publisher"].isna()]
    total_missing_publisher = len(missing_publisher_df.index)
    percent_missing_publisher = total_missing_publisher / total_full
    missing_publisher_df.to_csv(missing_publisher_df_path, index=False)

    missing_title_df = full_df[full_df["title"].isna()]
    total_missing_title = len(missing_title_df.index)
    percent_missing_title = total_missing_title / total_full
    missing_title_df.to_csv(missing_title_df_path, index=False)

    # Filter for Rows with No Null Values in Any Column
    clean_df = full_df[full_df["publisher"].notnull() & full_df["title"].notnull()]
    total_clean = len(clean_df.index)
    percent_clean = total_clean / total_full
    clean_df.to_csv(clean_df_path)

    missing_title_and_publisher = full_df[full_df["publisher"].isnull() | full_df["title"].isnull()]
    missing_title_and_publisher.to_csv(missing_title_and_publisher_path)

    if verbose:
        print(f"Total Missing First Name Rows: {total_missing_first_name}")
        print(f"Percent Missing First Name Rows: {percent_missing_first_name}")
        print(f"Total Missing Last Name Rows: {total_missing_last_name}")
        print(f"Percent Missing Last Name Rows: {percent_missing_last_name}")
        print(f"Total Missing Format Rows: {total_missing_format}")
        print(f"Percent Missing Format Rows: {percent_missing_format}")
        print(f"Total Missing Price Rows: {total_missing_price}")
        print(f"Percent Missing Price Rows: {percent_missing_price}")
        print(f"Total Missing Publisher Rows: {total_missing_publisher}")
        print(f"Percent Missing Publisher Rows: {percent_missing_publisher}")
        print(f"Total Missing Title Rows: {total_missing_title}")
        print(f"Percent Missing Title Rows: {percent_missing_title}")
        print(f"Total Clean Dataframe Rows: {total_clean}")
        print(f"Percent Clean Dataframe Rows: {percent_clean}")
        print(f"Total Dataframe Rows: {total_full}")
        print(f"Catalogue Year: {catalogue_year}")

    with open(full_data_measures_path, "w", newline='', encoding="utf-8", errors="ignore") as f:
        f.write(f"Total Missing First Name Rows: {total_missing_first_name}\n")
        f.write(f"Percent Missing First Name Rows: {percent_missing_first_name}\n\n")
        f.write(f"Total Missing Last Name Rows: {total_missing_last_name}\n")
        f.write(f"Percent Missing Last Name Rows: {percent_missing_last_name}\n\n")
        f.write(f"Total Missing Format Rows: {total_missing_format}\n")
        f.write(f"Percent Missing Format Rows: {percent_missing_format}\n\n")
        f.write(f"Total Missing Price Rows: {total_missing_price}\n")
        f.write(f"Percent Missing Price Rows: {percent_missing_price}\n\n")
        f.write(f"Total Missing Publisher Rows: {total_missing_publisher}\n")
        f.write(f"Percent Missing Publisher Rows: {percent_missing_publisher}\n\n")
        f.write(f"Total Missing Title Rows: {total_missing_title}\n")
        f.write(f"Percent Missing Title Rows: {percent_missing_title}\n\n")
        f.write(f"Total Clean Dataframe Rows: {total_clean}\n")
        f.write(f"Percent Clean Dataframe Rows: {percent_clean}\n\n")
        f.write(f"Total Dataframe Rows: {total_full}")
    
if __name__ == "__main__":

    # Parse args
    args = argparse_create((sys.argv[1:]))
    verbose_string = args.verbose
    if verbose_string == "True":
        verbose = True
    else:
        verbose = False

    # Iterate through Clean Entries Folder
    folder_path = '/entries/clean_entries/'

    # Only cover years 1902 and 1922
    for year in tqdm(range(2,23)):
        if year < 10:
            year = "0" + str(year)
        
    # Get appropriate paths.

        year_string = str(year)
        file_name = "entries_19" + str(year) + ".csv" 
        cwd_path = os.path.abspath(os.getcwd()).replace("scripts", "")
        file_path = cwd_path + os.path.join(folder_path, file_name)

        full_dataframe_directory = "/full_dataframe/"
        full_df_path = f"{cwd_path}/dataframes/{full_dataframe_directory}/df_19{year_string}.csv"

        missing_first_dataframe_directory = "/missing_first_name/"
        missing_first_df_path = f"{cwd_path}/dataframes/{missing_first_dataframe_directory}/df_19{year_string}.csv"
        
        missing_format_dataframe_directory = "/missing_format/"
        missing_format_df_path = f"{cwd_path}/dataframes/{missing_format_dataframe_directory}/df_19{year_string}.csv"

        missing_last_dataframe_directory = "/missing_last_name/"
        missing_last_df_path = f"{cwd_path}/dataframes/{missing_last_dataframe_directory}/df_19{year_string}.csv"

        missing_price_dataframe_directory = "/missing_price/"
        missing_price_df_path = f"{cwd_path}/dataframes/{missing_price_dataframe_directory}/df_19{year_string}.csv"

        missing_publisher_dataframe_directory = "/missing_publisher/"
        missing_publisher_df_path = f"{cwd_path}/dataframes/{missing_publisher_dataframe_directory}/df_19{year_string}.csv"

        missing_title_dataframe_directory = "/missing_title/"
        missing_title_df_path = f"{cwd_path}/dataframes/{missing_title_dataframe_directory}/df_19{year_string}.csv"

        clean_dataframe_directory = "/clean_dataframe/"
        clean_df_path = f"{cwd_path}/dataframes/{clean_dataframe_directory}/df_19{year_string}.csv"

        full_data_measures_directory = "dataframe_measures"
        full_data_measures_path = f"{cwd_path}/dataframes/{full_data_measures_directory}/df_measures_19{year_string}.txt"

        missing_title_and_publisher_directory = "missing_title_and_publisher_dataframes"
        missing_title_and_publisher_path = f"{cwd_path}/dataframes/{missing_title_and_publisher_directory}/df_measures_19{year_string}.csv"

        df_paths = [full_df_path, missing_first_df_path,
                    missing_format_df_path,
                    missing_last_df_path,
                    missing_price_df_path,
                    missing_publisher_df_path,
                    missing_title_df_path,
                    clean_df_path,
                    full_data_measures_path,
                    missing_title_and_publisher_path]
        
        # Create dataframes
        full_df = create_dataframes(file_path, year_string)

        # Save dataframes (and relevant dataframe measures)
        save_dataframes(full_df, df_paths, verbose)