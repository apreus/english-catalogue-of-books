import os
import re
import csv
import sys
from tqdm import tqdm
import argparse
import pandas as pd
from strsimpy.cosine import Cosine
import numpy as np
from scipy.signal import argrelextrema
from scipy.signal import find_peaks

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

if __name__ == "__main__":
    # Iterate through Princeton OCR folder
    folder_path = '/princeton_years/'

    # Only cover years 1908 and 1918
    for year in tqdm(range(8,19)):
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
            for page_number in range(len(ecb_pages)):
                page = ecb_pages[page_number]
                for text_index in range(len(page)):
                    segment = [page_number]
                    segment.append(text_index)
                    text = page[text_index: text_index + segment_length]
                    segment.append(text)
                    segments.append(segment)
                #break

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
            
            # Calculate Month String - Segments Consine Similarity Scores
            scores_array = []
            for segment_index in range(len(segments)):
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
            for month_index in range(0, 12):
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
                    while check_left:
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
            for key in month_desirable_sequences:
                desirable_segment_arrays = []
                desirable_sequences = month_desirable_sequences[key]
                for sequence in desirable_sequences:
                    score = sequence[-1]
                    sequence = sequence[:-1]
                    segments_array = []
                    if score > 0.299:
                        for index in range(len(sequence)):
                            sequence_value = sequence[index]
                            segment = segments[sequence_value]
                            segments_array.append(segment)
                    if len(segments_array) > 0:
                        desirable_segment_arrays.append(segments_array)
                desirable_segment_arrays_dict[key] = desirable_segment_arrays
            
            # Get desirable cutoff points
            cutoff_points_dict = {}
            for key in desirable_segment_arrays_dict:
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
                            cutoff_points_array = cutoff_points_dict[segment_page]
                            cutoff_points_array.append(cutoff_point)
                            cutoff_points_dict[segment_page] = cutoff_points_array
            
            # Get entries
            for page_index in range(len(ecb_pages)):
                if page_index in cutoff_points_dict:
                    page = ecb_pages[page_index]
                    cutoff_points_array = cutoff_points_dict[page_index]
                    page_entries = [page[i:j] for i,j in zip(cutoff_points_array, cutoff_points_array[1:]+[None])]
                    #for page_entry in page_entries:
                    #    print(page_entry)
                    #    print("--------------------")
                    entries += page_entries
                #else:
                #    print(f"Page Index {page_index} is not in Cutoff Points Dictionary.")
            print(len(entries))
        break

# General Algorithm For Detecting Dates
    # For each page
        # Split page into string lengths of 10 with significant overlap 
            # (i.e. string 1 should contain 9 of the characters in string 1)
        # For each string length
            # Calculate cosine similarity between each string to all the month strings (month + year)
        # Detect Local Maxima's for each string per month string values
            # (i.e. if you have 5 strings in a row with cosine similarity scores for Dec. 08
            # as 0.3 0.4 0.5 0.5 0.5 0.4 0.3, then we can probably say something about the entire Dec. 08
            # string being located in the strings with 0.6, and almost all of the string being in
            # 0)
            # We also only choose highest maximas per category
                # (i.e. if we have 0.4 0.6 0.6 0.6 for Dec. 08 and 0.5 0.7 0.7 0.7 0.5 for
                # Nov. 08 all for the same sequence of strings next to each other, then we
                # say that this sequence of strings most likely contains Nov. 08 over say
                # Dec. 08)
        # Trim local maximas so that we only get indices containing our most likely strings
            # One idea for this is to cut the ends off of (one of) the local maxima string
            # until we get the highest score that we can possibly get
            # For instance: "  N, Dec." turns into " N, Dec. 08" and "N, Dec. 08" until we get to
            # "Dec. 08"
            #
            #
            # Another idea for this is to get the intersection of all such local maxima in
            # the sequence we are looking at
            # For instance: Local maxima for Dec. 08 are "Dec. 08 ,", "; Dec. 08 ", "; Dec. 08 ", " Dec. 08 ;", "; Dec. 08"
            # and the intersection of this would then be Dec. 08, which is the date we are looking
            # for.