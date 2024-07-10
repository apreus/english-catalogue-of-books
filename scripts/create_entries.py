import os
import re
import csv
import sys
from tqdm import tqdm
import argparse

def argparse_create(args):
    """
    Parser to parse this script's arguments that pertain to the running of this code.

    Arguments:
        args: User inputted arguments that have yet to be parsed.

    Returns:
        parsed_args: Parsed user inputted arguments.
    """

    parser = argparse.ArgumentParser(description='Argument parser for creating the genereated dataset CSVs.')

    parser.add_argument("--verbose", type=str,
            help="Prints out clean entry metrics into the CLI.",
            default="False")


    # Parse arguments.
    parsed_args = parser.parse_args(args)

    return parsed_args

# Function to remove patterns from a page
def remove_patterns(page, patterns):
    for pattern in patterns:
        page = re.sub(pattern, '', page, flags=re.MULTILINE)
    return page

def get_clean_entries(year_string, file_path, pattern, verbose):
    """
    Gets clean entries from a single new_text_files OCR file's year.

    Arguments:
        year_string: String; string representation of year.
        file_path: String; new_text_files OCR full file path.
        pattern: Raw String; header pattern string.
        verbose: Boolean; If true, prints out metrics into CLI, and if false, does not print out entries.
    
    Returns:
        full_entries: array; object containing all entries.
        clean_entries: array; object containing clean entries.
        clean_entries_measures: array; object containing clean entries measures.
        line_mid_entries: array; object containing entries with dates in the middle.
        front_trunc_entries: array; object containing entries with front truncation.
    """
    # Get file contents
    infile = open(file_path, "r", encoding="utf-8", errors="ignore")
    contents = infile.read()
    infile.close()

    # Load splitters (patternFrontDict, appendixPatternDict, and yearPatterns) from splitters.txt
    splitters_file_path = "splitters.txt"

    try:
        with open(splitters_file_path, "r") as file:
            splitters = file.read()
        exec(splitters, globals())
        
        # Ensure the dictionaries are defined
        if 'patternFrontDict' not in globals():
            raise NameError("patternFrontDict is not defined in splitters.txt")
        if 'appendixPatternDict' not in globals():
            raise NameError("appendixPatternDict is not defined in splitters.txt")
        if 'yearPatterns' not in globals():
            raise NameError("yearPatterns is not defined in splitters.txt")

    except FileNotFoundError:
        print(f"Error: The file {splitters_file_path} was not found.")
    except NameError as ne:
        print(f"Error: {ne}")
    
    # Get ecb_content and back_matter
    patternFront = patternFrontDict[year_string]
    text_raw = re.split(patternFront, contents)

    if len(text_raw) < 2:
        print("The year that's not working is: ", year_string)
        print(patternFront)
        raise IndexError(f"No match found for patternFront: {patternFront} in ecb_content.")


    #front_matter = text_raw[0]
    ecb_content = text_raw[1]
    appendix_pattern = appendixPatternDict[year_string]
    appendix_list = re.split(appendix_pattern, ecb_content, flags=re.DOTALL)

    if len(appendix_list) < 2:
        print("The year that's not working is: ", year_string)
        print(appendix_pattern)
        raise IndexError(f"No match found for appendix_pattern: {appendix_pattern} in ecb_content.")

    ecb_content = appendix_list[0]
 
    #back_matter = appendix_list[1]

    # Get pages
    ecb_pages = ecb_content.split("\f")

    #print(len(ecb_pages))
    
    # Find best pattern
    whole_ecb = "\f".join(ecb_pages)
    """
    pat1_matches = re.findall(pat1, whole_ecb, flags=re.M)
    
    pat2_matches = re.findall(pat2, whole_ecb, flags=re.M)
    
    pat3_matches = re.findall(pat3, whole_ecb, flags=re.M)
    
    patterns = [pat1, pat2, pat3]
    pattern_matches = [pat1_matches, pat2_matches, pat3_matches]
    """
    
    # Apply the function to each page
    ecb_pe = [remove_patterns(page, pattern) for page in ecb_pages]

    # ecb_pe = [
    #     re.sub(pattern, "", page, flags=re.M)  # this flag is for multiline regex
    #     for page in ecb_pages
    # ]
    
    entry_terminator_regex = r'(\W({})\.?$)'.format('|'.join(yearPatterns[year_string]))
    ecb_pe = [re.sub(entry_terminator_regex, "\\1<ENTRY_CUT>", page, flags=re.M) for page in ecb_pe]
    ecb_pe = [re.split(r"<ENTRY_CUT>", page, flags=re.M) for page in ecb_pe] 

    entries = [
        re.sub(r"\n", " ", entry.strip()) for entries in ecb_pe for entry in entries
    ]

    total_entries = len(entries)

    if verbose:
        print(f"Total Entries: {total_entries}")

    month_abbrvs = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "June",
        "July",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
    ]

    line_mid_re = re.compile(r".*({})\.?\W{}\.?[^\.]+".format("|".join(month_abbrvs),year))
    line_mid_entries = [entry for entry in entries if line_mid_re.search(entry)]

    len_line_mid_entries = len(line_mid_entries)
    percent_line_mid_entries = len(line_mid_entries) / len(entries)

    if verbose:
        print(f"\nTotal Line Mid Entries: {len_line_mid_entries}")
        print(f"Percent Line Mid Entries: {percent_line_mid_entries}")

    # Corrects line mid entries by splitting entries using month + year regex pattern
    
    split_line_mid_re = re.compile(r"(({})\.?\W{}\.?(?!$))".format("|".join(month_abbrvs), year))
    line_mid_index = [entries.index(entry) for entry in line_mid_entries]

    counter = 0
    for index in line_mid_index:
        entries[index + counter] = re.sub(split_line_mid_re, "\\1<ENTRY_CUT>", entries[index + counter])
        new_entry = re.split(r"<ENTRY_CUT>", entries[index + counter], flags=re.M)
        new_entry[1] = re.sub(r"^\W+(?=[A-Z])", "", new_entry[1])
        entries[index + counter] = new_entry[1]
        entries.insert(index + counter, new_entry[0])
        counter += 1

    new_total_entries = len(entries)

    if verbose:
        print(f"\nNew Total Entries After Line Mid Correction: {new_total_entries}")

    # Finds truncated entries: entries with length <25 characters and entries that don't begin with a capital letter

    truncated_entry_regex_patterns = [
        "^.{0,25}$",
        "^[^A-ZÆÅ\"“]"
    ]

    front_trunc_re = re.compile(r'({})'.format('|'.join(truncated_entry_regex_patterns)))

    front_trunc_entries = [entry for entry in entries if front_trunc_re.search(entry)]
    
    len_front_trunc_entries = len(front_trunc_entries)
    percent_front_trunc_entries = len(front_trunc_entries) / len(entries)

    if verbose:
        print(f"\nTotal Trunc Entries: {len_front_trunc_entries}")

    if verbose:
        print(f"Percent Trunc Entries: {percent_front_trunc_entries}")

    # extracts clean entries from full entries by checking if entry is 
    # front truncated or line mid (latter check no longer necessary after fix)
        
    clean_entries = [
        entry
        for entry in entries
        if not (line_mid_re.search(entry) or front_trunc_re.search(entry))
    ]
    len_clean_entries = len(clean_entries)

    if verbose:
        print(f"\nTotal Clean Entries: {len_clean_entries}")

    percent_clean_entries = len_clean_entries / len(entries)

    if verbose:
        print(f"Percent Clean Entries: {percent_clean_entries}")


    clean_entries_measures = [len_line_mid_entries, percent_line_mid_entries, 
                              len_front_trunc_entries, percent_front_trunc_entries, 
                                len_clean_entries, percent_clean_entries, 
                                new_total_entries]
    
    return entries, clean_entries, clean_entries_measures, line_mid_entries, front_trunc_entries

def clean_entries_and_measures_to_csv(full_entries, clean_entries, clean_entries_measures, 
                                      line_mid_entries, front_trunc_entries,
                                      year_string, cwd_path, full_entries_directory,
                                      clean_entries_directory,
                                      clean_entries_measures_directory,
                                      front_trunc_entries_directory,
                                      line_mid_entries_directory,
                                      pattern = ""):
    """
    Prints clean entries from a single new_text_files OCR file's year to a CSV file and
    prints clean entries measures from a single new_text_files OCR file's year to a text
    file.

    Arguments:
        full_entries: array; object containing all entries.
        clean_entries: array; object containing clean entries.
        clean_entries_measures: array; object containing clean entries measures.
        line_mid_entries: array; object containing entries with dates in the middle.
        front_trunc_entries: array; object containing entries with front truncation.
        year_string: String; string representation of year.
        cwd_path: String; current working directory path.
        full_entries_directory: String; full_entries directory.
        clean_entries_directory: String; clean entries directory.
        clean_entries_measures_directory: String; clean entries measures directory.
        line_mid_entries_directory: String; clean entries directory.
        front_trunc_entries_directory: String; clean entries directory.
        pattern: Raw String; header pattern string.
    """
    # Make sure entries directory exists
    if not os.path.exists(f"{cwd_path}/{full_entries_directory}"):
        os.makedirs(f"{cwd_path}/{full_entries_directory}")

    # Make sure clean entries directory exists
    if not os.path.exists(f"{cwd_path}/{clean_entries_directory}"):
        os.makedirs(f"{cwd_path}/{clean_entries_directory}")

    # Make sure measures directory exists
    if not os.path.exists(f"{cwd_path}/{clean_entries_measures_directory}"):
        os.makedirs(f"{cwd_path}/{clean_entries_measures_directory}")

    # Make sure line mid directory exists
    if not os.path.exists(f"{cwd_path}/{line_mid_entries_directory}"):
        os.makedirs(f"{cwd_path}/{line_mid_entries_directory}")

    # Make sure front trunc directory exists
    if not os.path.exists(f"{cwd_path}/{front_trunc_entries_directory}"):
        os.makedirs(f"{cwd_path}/{front_trunc_entries_directory}")

    with open(f"{cwd_path}/{full_entries_directory}/entries_19{year_string}.csv", 
        "w", newline='', encoding="utf-8", errors="ignore") as f:
        csv_writer = csv.writer(f, quotechar='"')
        for entry in full_entries:
            csv_writer.writerow([entry])

    with open(f"{cwd_path}/{clean_entries_directory}/entries_19{year_string}.csv", 
            "w", newline='', encoding="utf-8", errors="ignore") as f:
        csv_writer = csv.writer(f, quotechar='"')
        for entry in clean_entries:
            csv_writer.writerow([entry])
    
    with open(f"{cwd_path}/{line_mid_entries_directory}/entries_19{year_string}.csv", 
        "w", newline='', encoding="utf-8", errors="ignore") as f:
        csv_writer = csv.writer(f, quotechar='"')
        for entry in line_mid_entries:
            csv_writer.writerow([entry])

    with open(f"{cwd_path}/{front_trunc_entries_directory}/entries_19{year_string}.csv", 
        "w", newline='', encoding="utf-8", errors="ignore") as f:
        csv_writer = csv.writer(f, quotechar='"')
        for entry in front_trunc_entries:
            csv_writer.writerow([entry])

    len_line_mid_entries = clean_entries_measures[0]
    percent_line_mid_entries = clean_entries_measures[1]
    len_front_trunc_entries = clean_entries_measures[2]
    percent_front_trunc_entries = clean_entries_measures[3]
    len_clean_entries = clean_entries_measures[4]
    percent_clean_entries = clean_entries_measures[5]
    len_full_entries = clean_entries_measures[6]
    with open(f"{cwd_path}/{clean_entries_measures_directory}/entries_measures_19{year_string}.txt", 
            "w", newline='', encoding="utf-8", errors="ignore") as f:
        f.write(f"Total Line Mid Entries: {len_line_mid_entries}\n")
        f.write(f"Percent of Line Mid Entries: {percent_line_mid_entries}\n\n")
        f.write(f"Total Front Trunc Entries: {len_front_trunc_entries}\n")
        f.write(f"Percent Front Trunc Entries: {percent_front_trunc_entries}\n\n")
        f.write(f"Total Clean Entries: {len_clean_entries}\n")
        f.write(f"Percent Clean Entries: {percent_clean_entries}\n\n")
        f.write(f"Total Full Entries: {len_full_entries}\n\n")
        if len(pattern) > 0:
            f.write(f"Pattern: {pattern}")

if __name__ == "__main__":

    args = argparse_create((sys.argv[1:]))

    #verbose_string = args.verbose
    verbose_string = "True"

    if verbose_string == "True":
        verbose = True
    else:
        verbose = False

    # Iterate through Princeton OCR folder
    old_data_folder_path = '/princeton_years/'

    # Iterate through new_text_files OCR folder
    new_data_folder_path = '/new_text_files/'

    # # Initiate patterns
    # pat1 = r"^#(?s:.*?)^[A-Z]+(?s:.*?)^[A-Z]+(?s:.*?)^[A-Z]+$"
    # pat2 = r"^##(?s:.*?)^THE ENGLISH CATALOGUE(?s:.*?)^[A-Z]{3,}(?s:.*?)^[A-Z]{3,}$"
    # caps_header = r"^(?:[A-Z\-\'\sÈ]+)"
    # pat3 = r"^#(?s:.*?){}(?s:.*?){}(?s:.*?){}$".format(
    #     caps_header, caps_header, caps_header
    # )
    # pat4 = fr"{pat1}|{pat2}"
    # pat5 = fr"{pat2}|{pat3}"
    # pat6 = fr"{pat1}|{pat3}"

    # # Currently using this one as it is the most consistent
    # pat7 = fr"{pat1}|{pat2}|{pat3}"

    # Only cover years 1902 and 1922
    for year in tqdm(range(2,23)):
        if year < 10:
            year = "0" + str(year)
        
        # Get appropriate paths 
        year_string = str(year)

        cwd_path = os.path.abspath(os.getcwd()).replace("scripts", "")

        if int(year) < 8:
            file_name = "ecb_19" + year_string + "_princeton_070724.txt"
            file_path = cwd_path + os.path.join(new_data_folder_path, file_name)
            
        elif year == 19 or year == 21:
            file_name = "ecb_19" + year_string + "_nypl_070724.txt"
            file_path = cwd_path + os.path.join(new_data_folder_path, file_name)

        else:
            file_name = "ecb_19" + year_string + ".txt" 
            file_path = cwd_path + os.path.join(old_data_folder_path, file_name)
            
        full_entries_directory = "/entries/full_entries/"
        clean_entries_directory = "/entries/clean_entries/"
        clean_entries_measures_directory = "/entries/entries_measures/"
        front_trunc_entries_directory = "/entries/front_trunc_entries/"
        line_mid_entries_directory = "/entries/line_mid_entries/"
        
        # Define multiple header patterns
        header_patterns = [
            r"(^\b[A-Z ]+\b\s?\n)",  # Capital heading pattern
            r"(##(?s:.*?)$)",  # Page number pattern
            r"(^.?19{}.?\n)".format(year), # Header year pattern
            r"(^\d+\n)", # Random page numbers
        ]

        pattern = header_patterns
        full_entries, clean_entries, clean_entries_measures, line_mid_entries, front_trunc_entries = get_clean_entries(year_string, 
                                                                                                    file_path, 
                                                                                                    pattern, verbose)   
        clean_entries_and_measures_to_csv(full_entries, clean_entries, clean_entries_measures, 
                                line_mid_entries, front_trunc_entries, 
                                year_string, cwd_path, full_entries_directory,
                                clean_entries_directory,
                                clean_entries_measures_directory, 
                                front_trunc_entries_directory,
                                line_mid_entries_directory, pattern)