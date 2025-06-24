import os
import re
import csv
import sys
from tqdm import tqdm
import argparse
import pandas as pd

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

def get_splitters_by_year(year):
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

    return patternFrontDict[year], appendixPatternDict[year], yearPatterns[year]

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
    
    if verbose:
        print("CATALOGUE YEAR:", year_string, "\n")

    front_pattern, appendix_pattern, year_variations = get_splitters_by_year(year_string)

    # Get ecb_content and back_matter
    text_raw = re.split(front_pattern, contents)
    if len(text_raw) < 2:
        print("The year that's not working is: ", year_string)
        print(front_pattern)
        raise IndexError(f"No match found for patternFront: {front_pattern} in ecb_content.")

    front_matter = text_raw[0]
    document_page_delta = len(front_matter.split("\f")) - 2

    ecb_content = text_raw[1]

    appendix_list = re.split(appendix_pattern, ecb_content, flags=re.DOTALL)
    if len(appendix_list) < 2:
        print("The year that's not working is: ", year_string)
        print(appendix_pattern)
        raise IndexError(f"No match found for appendix_pattern: {appendix_pattern} in ecb_content.")

    ecb_content = appendix_list[0]

    # Get pages
    ecb_pages = ecb_content.split("\f")
    
    # Apply the function to each page
    ecb_pe = [remove_patterns(page, pattern) for page in ecb_pages]

    entry_terminator_regex = r'(\W({})\.?$)'.format('|'.join(year_variations))
    
    #split up into entires and modify each entry with catalogue page number and document page number 
    ecb_pe = [re.sub(entry_terminator_regex, "<PAGE_NUM:{}><DOCUMENT_PAGE_NUM:{}>\\1<ENTRY_CUT>".format(i, i+document_page_delta), page, flags=re.M) for i, page in enumerate(ecb_pe, start=1)]
    
    # replace year variations with correct year
    # ecb_pe = [re.sub(entry_terminator_regex, " {}<ENTRY_CUT>".format(year_string), page, flags=re.M) for page in ecb_pe]

    #split on year
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
        match = re.search(r"<PAGE_NUM:([0-9]{0,3})><DOCUMENT_PAGE_NUM:([0-9]{0,3})>", entries[index + counter])
        if match:
            page_num, document_page_num = match.group(1), match.group(2)
            entries[index + counter] = re.sub(split_line_mid_re, "<PAGE_NUM:{}><DOCUMENT_PAGE_NUM:{}>\\1<ENTRY_CUT>\\1<ENTRY_CUT>".format(page_num, document_page_num), entries[index + counter])
        else:
            print("main is empty, here's the index", index+counter)
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
        "^\s+",
        "^[^A-Za-z0-9]*$"
        # "^.{0,25}$",
        # "^[^A-ZÆÅ\"“]"
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
        if not front_trunc_re.search(entry)
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
    
    clean_entries_df = create_dataframe_from_clean_enties(clean_entries, year_variations)

    return entries, clean_entries_df, clean_entries_measures, line_mid_entries, front_trunc_entries

def create_dataframe_from_clean_enties(clean_entries, year_variations):
    entries = pd.Series(clean_entries)

    df = pd.DataFrame()

    page_data = entries.str.extract(r"<PAGE_NUM:([0-9]{0,3})><DOCUMENT_PAGE_NUM:([0-9]{0,3})>")
    pages = page_data[0]
    document_pages = page_data[1]

    if not (len(pages) == len(document_pages) == len(entries)):
        raise ValueError("pages, document_pages, and entries not same length")

    entries = entries.str.replace("<PAGE_NUM:[0-9]{0,3}><DOCUMENT_PAGE_NUM:[0-9]{0,3}>", "", regex=True)

    pub_date_pattern = fr"[A-ZÀ-ž][A-ZÀ-ž\.\s&,'\-]+,\W\w[^A-ZÀ-ž]+(?:\.|,)?\W({'|'.join(year_variations)})\.?$"
    
    # pub_pattern_for_doubling is pub_date_pattern without the "$" end of line check so we can check for two publishers
    pub_pattern_for_doubling = fr"[A-ZÀ-ž][A-ZÀ-ž\.\s&,'\-]+,\W\w[^A-ZÀ-ž]+(?:\.|,)?\W({'|'.join(year_variations)})\.?"
    double_pub_pattern = fr"{pub_pattern_for_doubling}\b.*?\b{pub_pattern_for_doubling}$"

    entries_len = len(entries)

    main_entries = [False] * entries_len
    flag_for_manual_correction = [False] * entries_len

    two_parentheses = [False] * entries_len
    two_publishers = [False] * entries_len
    see = [False] * entries_len
    see_regex_pattern = r"see "

    net = [False] * entries_len
    net_regex_pattern = r"(.*?\bnet\b){2,}"

    multiple_ellipses = [False] * entries_len
    multiple_ellipses_regex_pattern = r"\.{5,}|\…{1,}"

    double_author_regex = "(\([A-Z]+.*\)).*(\([A-Z]+.*\))"

    floaty_bits_regex = "^.{0,30}$"
    floaty_bits = [False] * entries_len

    begins_with_numbers_regex = "^[0-9].*$"
    begins_with_numbers = [False] * entries_len

    for i, entry in enumerate(entries):
        if re.search(pub_date_pattern, entry):
            main_entries[i] = True

        if re.search(double_pub_pattern, entry):
            flag_for_manual_correction[i] = True
            two_publishers[i] = True

        if re.search(double_author_regex, entry):
            flag_for_manual_correction[i] = True
            two_parentheses[i] = True

        if re.search(see_regex_pattern, entry):
            flag_for_manual_correction[i] = True
            see[i] = True

        if re.search(net_regex_pattern, entry):
            flag_for_manual_correction[i] = True
            net[i] = True

        if re.search(multiple_ellipses_regex_pattern, entry):
            flag_for_manual_correction[i] = True
            multiple_ellipses[i] = True

        if re.search(floaty_bits_regex, entry):
            flag_for_manual_correction[i] = True
            floaty_bits[i] = True
        
        if re.search(begins_with_numbers_regex, entry):
            flag_for_manual_correction[i] = True
            begins_with_numbers[i] = True

    if not (len(main_entries) == len(entries)):
        raise ValueError("main_entries and entries not same length")

    #Set columns
    df["entry"] = entries
    # df["page_num"] = pages
    # df["doc_page_num"] = document_pages
    # df["main_entry"] = main_entries
    # # df["flagged"] = flag_for_manual_correction
    # df["two_publishers"] = two_publishers
    # df["see"] = see
    # df["two_parentheses"] = two_parentheses
    # df["net"] = net
    # df["ellipses"] = multiple_ellipses
    # df["floaty_bits"] = floaty_bits
    # df["begins_with_numbers"] = begins_with_numbers

    return df

def clean_entries_and_measures_to_csv(full_entries, clean_entries_df, clean_entries_measures, 
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
        clean_entries_df: dataframe containing entries and few categories.
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

    # with open(f"{cwd_path}/{clean_entries_directory}/entries_19{year_string}.csv", 
    #         "w", newline='', encoding="utf-8", errors="ignore") as f:
    #     csv_writer = csv.writer(f, quotechar='"')
    #     for entry in clean_entries_df:
    #         csv_writer.writerow([entry])

    clean_entries_df.to_csv(f"{cwd_path}/{clean_entries_directory}/entries_19{year_string}.csv", 
                        index=False, encoding="utf-8", quotechar='"')
    
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

    full_entries_directory = "/entries/full_entries/"
    clean_entries_directory = "/entries/clean_entries/"
    clean_entries_measures_directory = "/entries/entries_measures/"
    front_trunc_entries_directory = "/entries/front_trunc_entries/"
    line_mid_entries_directory = "/entries/line_mid_entries/"

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

        full_entries, clean_entries_df, clean_entries_measures, line_mid_entries, front_trunc_entries = get_clean_entries(year_string, 
                                                                                                    file_path, 
                                                                                                    pattern, verbose)   
                
        clean_entries_and_measures_to_csv(full_entries, clean_entries_df, clean_entries_measures, 
                                line_mid_entries, front_trunc_entries, 
                                year_string, cwd_path, full_entries_directory,
                                clean_entries_directory,
                                clean_entries_measures_directory, 
                                front_trunc_entries_directory,
                                line_mid_entries_directory, pattern)