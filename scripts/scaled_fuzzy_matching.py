import os
import re
import csv
import sys
from tqdm import tqdm
import argparse
import pandas as pd
from strsimpy.cosine import Cosine
import numpy as np
from scipy.signal import find_peaks
from create_entries import clean_entries_and_measures_to_csv

CUTOFF_POINT_SCORE = 0.40
CLOSE_INDEX_THRESHOLD = 5

patternFrontDict = {
    "00": r"centimetres.\n.*\n",
    "01": r"centimetres.\n.*\n",
    "02": r"centimetres.\n.*\n",
    "03": r"centimetres.\n.*\n",
    "04": r"centimetres.\n.*\n",
    "05": r"centimetres.\n.*\n",
    "06": r"centimetres.\n.*\n",
    "07": r"centimetres.\n.*\n",
    "08": r"centimetres.\n.*\n",
    "09": r"centimetres.\n.*\n",
    "10": r"THE ENGLISH CATALOGUE\nACHARD\nACTS",
    "11": r"centimetres.\n.*\n",
    "12": r"centimetres.\n.*\n",
    "13": r"centimetres.\n.*\n",
    "14": r"centimetres.\n.*\n",
    "15": r"centimetres.\n.*\n",
    "16": r"centimetres.\n.*\n",
    "17": r"centimetres.\n.*\n",
    "18": r"centin etres.\n.*\n",
    "19": r"centimetres.\n.*\n",
    "20": r"centimetres.\n.*\n.*\n.*\n",
    "22": r"centimetres.*.\n.*\n",
}

appendixPatternDict = {
    "00": r"ENGLISH CATALOGUE APPENDIX\nAN\nBI",
    "01": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1901",
    "02": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1902",
    "03": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1903",
    "04": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1904",
    "05": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1905",
    "06": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1906",
    "07": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1907",
    "08": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1908",
    "09": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1909",
    "10": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1910",
    "11": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1911",
    "12": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1912",
    "13": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1913",
    "14": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1914",
    "15": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1915",
    "16": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1916",
    "17": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1917",
    "18": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1918",
    "19": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1918", # OCR had incorrect year
    "20": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1920",
    "22": r"WITH LISTS OF THEIR\nPUBLICATIONS, 1922",
}

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

def scaled_fuzzy_matching(file_path, year_string):
    """
    Gets clean entries via fuzzy matching from a single Princeton OCR file's year.

    Arguments:
        file_path: String; Princeton OCR full file path.
        year_string: String; string representation of year.

    Returns:
        full_entries: array; object containing all entries.
        clean_entries: array; object containing clean entries.
        clean_entries_measures: array; object containing clean entries measures.
        line_mid_entries: array; object containing entries with dates in the middle.
        front_trunc_entries: array; object containing entries with front truncation.
    """

    entries = []
    infile = open(file_path, "r", encoding="utf-8", errors="ignore")
    contents = infile.read()
    infile.close()

    # Get ecb_content and back_matter
    patternFront = patternFrontDict[year_string]
    text_raw = re.split(patternFront, contents)
    #front_matter = text_raw[0]
    ecb_content = text_raw[1]
    appendix_pattern = appendixPatternDict[year_string]
    appendix_list = re.split(appendix_pattern, ecb_content, flags=re.DOTALL)
    ecb_content = appendix_list[0]

    # Split into pages
    ecb_pages = ecb_content.split("\f")

    # Iterate through pages to get all segments
    segments = []
    segment_length = 10
    for page_number in tqdm(range(len(ecb_pages)), desc="Get all page segments"):
        page = ecb_pages[page_number]
        for text_index in range(len(page)):
            segment = [page_number]
            segment.append(text_index)
            text = page[text_index: text_index + segment_length]
            segment.append(text)
            segments.append(segment)
        # break

    # Create Month Strings to be matched
    month_strings = []
    for index in range(len(month_abbrvs)):
        month_string = f"{month_abbrvs[index]} {year_string}"
        month_strings.append(month_string)

    # Calculate Month String Cosine Profiles
    cosine = Cosine(2)
    month_string_profiles = []
    for month_string_index in range(len(month_strings)):
            month_string = month_strings[month_string_index]
            month_string_profile = cosine.get_profile(month_string)
            month_string_profiles.append(month_string_profile)
    
    # Calculate Month String - Segments Cosine Similarity Scores
    scores_array = []
    for segment_index in tqdm(range(len(segments)), desc="Calculate Month - Segment Cosine Scores"):
        segment_text = segments[segment_index][2]
        segment_profile = cosine.get_profile(segment_text)
        scores = []
        for profile_index in range(len(month_string_profiles)):
            month_string_profile = month_string_profiles[profile_index]
            try:
                score = round(cosine.similarity_profiles(segment_profile, month_string_profile),3)
            except:
                score = 0
            scores.append(score)
        scores_array.append(scores)
    
    # Get Potential Sequences
    month_desirable_sequences = {}
    for month_index in tqdm(range(0, 12), desc="Get Potential Sequences"):
        month_scores = []
        for index in range(len(scores_array)):
            score = scores_array[index][month_index]
            month_scores.append(score)
        np_month_scores = np.array(month_scores)

        # Find Peaks
        peaks = find_peaks(np_month_scores)[0].tolist()
        peak_scores = np_month_scores[peaks].tolist()

        # Iterate through peaks to find desirable sequences of strings
        desirable_sequences = []
        for index in range(len(peaks)):
            peak_index = peaks[index]
            peak_score = peak_scores[index]
            desirable_sequence = [peak_index]

            # Check Left
            check_left = True
            left_counter = 1
            while check_left:
                index_to_check = peak_index - left_counter
                if index_to_check in range(len(month_scores)):
                    if month_scores[index_to_check] == peak_score:
                        desirable_sequence.append(index_to_check)
                    else:
                        check_left = False
                else:
                    check_left = False
                left_counter += 1

            # Check Right
            check_right = True
            right_counter = 1
            while check_right:
                index_to_check = peak_index + right_counter
                if index_to_check in range(len(month_scores)):
                    if month_scores[index_to_check] == peak_score:
                        desirable_sequence.append(index_to_check)
                    else:
                        check_right = False
                else:
                    check_right = False
                right_counter += 1

            # Sort Desirable Sequence
            desirable_sequence.sort()
            desirable_sequence.append(peak_score)
            desirable_sequences.append(desirable_sequence)

        month_desirable_sequences[month_index] = desirable_sequences
    
    # Iterate through desirable sequences to locate desirable sequences of segments
    desirable_segment_arrays_dict = {}
    for key in tqdm(month_desirable_sequences, desc="Locate desirable sequences of segments"):
        desirable_segment_arrays = []
        desirable_sequences = month_desirable_sequences[key]
        for sequence in desirable_sequences:
            score = sequence[-1]
            sequence = sequence[:-1]
            segments_array = []
            if score > CUTOFF_POINT_SCORE:
                for index in range(len(sequence)):
                    sequence_value = sequence[index]
                    segment = segments[sequence_value]
                    segments_array.append(segment)
            if len(segments_array) > 0:
                desirable_segment_arrays.append(segments_array)
        desirable_segment_arrays_dict[key] = desirable_segment_arrays
    
    # Get desirable cutoff points
    cutoff_points_dict = {}
    score_cutoff_points_dict = {}
    for key in tqdm(desirable_segment_arrays_dict, desc="Get Desirable Cutoff Points"):
        desirable_segment_arrays = desirable_segment_arrays_dict[key]
        for segment_array in desirable_segment_arrays:
            if len(segment_array) > 0:
                segment = segment_array[-1]
                segment_page = segment[0]
                segment_start_index = segment[1]
                segment_string = segment[2]
                segment_string_length = len(segment_string)
                keep_searching = True
                left_counter = 0
                month_string_profile = month_string_profiles[key]
                segment_profile = cosine.get_profile(segment_string)
                best_score = round(cosine.similarity_profiles(segment_profile, 
                                                                month_string_profile),3)
                #print(f"{segment_string}: {segment_start_index + segment_string_length - left_counter}")
                while keep_searching:
                    left_counter += 1
                    next_string = segment_string[:segment_string_length - left_counter]
                    #print(f"{next_string}: {segment_start_index + segment_string_length - left_counter}")
                    next_segment_profile = cosine.get_profile(next_string)
                    try:
                        score = round(cosine.similarity_profiles(next_segment_profile, 
                                                                month_string_profile),3)
                    except:
                        score = 0
                    if score > best_score and left_counter < segment_string_length:
                        best_score = score
                    else:
                        left_counter -= 1
                        keep_searching = False
                cutoff_point = segment_start_index + segment_string_length - left_counter
                #print(cutoff_point)
                #print("-------------------")
                if best_score > 0:
                    if segment_page not in cutoff_points_dict:
                        cutoff_points_dict[segment_page] = []
                    if segment_page not in score_cutoff_points_dict:
                        score_cutoff_points_dict[segment_page] = []
                    cutoff_points_array = cutoff_points_dict[segment_page]
                    score_cutoff_points_array = score_cutoff_points_dict[segment_page]
                    if cutoff_point not in cutoff_points_array:
                        exists_close = False
                        replaced = False
                        # Remove low score points that are close to high score points
                        for cutoff_point_index in range(len(cutoff_points_array)):
                            examining_cutoff_point = cutoff_points_array[cutoff_point_index]
                            examining_cutoff_point_score = score_cutoff_points_array[cutoff_point_index]
                            if abs(cutoff_point - examining_cutoff_point) < CLOSE_INDEX_THRESHOLD \
                                                    and best_score <= examining_cutoff_point_score:
                                exists_close = True
                            if abs(cutoff_point - examining_cutoff_point) < CLOSE_INDEX_THRESHOLD \
                                                    and best_score > examining_cutoff_point_score:
                                cutoff_points_array[cutoff_point_index] = cutoff_point
                                score_cutoff_points_array[cutoff_point_index] = best_score
                                replaced = True
                        if not exists_close and not replaced:
                            cutoff_points_array.append(cutoff_point)
                            score_cutoff_points_array.append(best_score)
                    cutoff_points_dict[segment_page] = cutoff_points_array
                    score_cutoff_points_dict[segment_page] = score_cutoff_points_array
    
    # Get entries
    for page_index in tqdm(range(len(ecb_pages)), desc="Get Entries"):
        if page_index in cutoff_points_dict:
            page = ecb_pages[page_index]
            cutoff_points_array = cutoff_points_dict[page_index]
            # TODO investigate the below line
            #print(zip(cutoff_points_array, cutoff_points_array[1:]+[None]))
            cutoff_points_array.sort()
            page_entries = [page[i:j] for i,j in zip(cutoff_points_array, cutoff_points_array[1:]+[None])]
            cleaned_page_entries = []
            for page_entry_index in range(len(page_entries)):
                page_entry = page_entries[page_entry_index]
                if len(page_entry) > 0:
                    page_entry = "".join(page_entry.splitlines())
                    cleaned_page_entries.append(page_entry)
            entries += cleaned_page_entries

    # Get line mid entries  
    line_mid_re = re.compile(r".*({})\.?\W00\.?[^\.]+".format("|".join(month_abbrvs)))
    line_mid_entries = [entry for entry in tqdm(entries, desc="Get Line Mid Entries") \
                        if line_mid_re.search(entry)]
    len_line_mid_entries = len(line_mid_entries)
    percent_line_mid_entries = len(line_mid_entries) / len(entries)

    # Get front trunc entries
    front_trunc_re = re.compile(r"^[^A-ZÆ\"“]")
    front_trunc_entries = [entry for entry in tqdm(entries, desc="Get Front Trunc Entries") \
                           if front_trunc_re.search(entry)]
    len_front_trunc_entries = len(front_trunc_entries)
    percent_front_trunc_entries = len(front_trunc_entries) / len(entries)

    # Get clean entries
    clean_entries = [
        entry
        for entry in tqdm(entries, desc="Get Clean Entries")
        if not (line_mid_re.search(entry) or front_trunc_re.search(entry))
    ]
    len_clean_entries = len(clean_entries)
    percent_clean_entries = len_clean_entries / len(entries)
    
    # Get total entries
    total_clean_entries = len(entries)
    full_entries = entries

    # Conglomerate clean entries
    clean_entries_measures = [len_line_mid_entries, percent_line_mid_entries, 
                            len_front_trunc_entries, percent_front_trunc_entries, 
                            len_clean_entries, percent_clean_entries, 
                            total_clean_entries]

    return full_entries, clean_entries, clean_entries_measures, line_mid_entries, front_trunc_entries

if __name__ == "__main__":
    # Iterate through Princeton OCR folder
    folder_path = '/princeton_years/'

    # Only cover years 1908 and 1918
    for year in tqdm(range(8,19)):
    #for year in tqdm(range(10,19)):
        if year != 21:
            if year < 10:
                year = "0" + str(year)

            # Initialize entries
            entries = []

            # Get appropriate paths 
            year_string = str(year)
            file_name = "ecb_19" + str(year) + ".txt" 
            cwd_path = os.path.abspath(os.getcwd()).replace("scripts", "")
            file_path = cwd_path + os.path.join(folder_path, file_name)

            # Initialize Directories
            full_entries_directory = "/entries_fuzzy/full_entries/"
            clean_entries_directory = "/entries_fuzzy/clean_entries/"
            clean_entries_measures_directory = "/entries_fuzzy/entries_measures/"
            front_trunc_entries_directory = "/entries_fuzzy/front_trunc_entries/"
            line_mid_entries_directory = "/entries_fuzzy/line_mid_entries/"

            # Run scaled fuzzy matching
            full_entries, clean_entries, clean_entries_measures, \
            line_mid_entries, front_trunc_entries = scaled_fuzzy_matching(file_path, year_string)

            clean_entries_and_measures_to_csv(full_entries, clean_entries, clean_entries_measures, 
                                        line_mid_entries, front_trunc_entries,
                                        year_string, cwd_path, full_entries_directory,
                                        clean_entries_directory,
                                        clean_entries_measures_directory,
                                        front_trunc_entries_directory,
                                        line_mid_entries_directory)