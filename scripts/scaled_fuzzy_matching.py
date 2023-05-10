import os
import re
import csv
import sys
from tqdm import tqdm
import argparse
import pandas as pd
from strsimpy.jaro_winkler import JaroWinkler # Don't use this
from strsimpy import SIFT4 # Maybe use this....experimental
from strsimpy.cosine import Cosine

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

def levenshteinDistance(A, B):
    N, M = len(A), len(B)
    # Create an array of size NxM
    dp = [[0 for i in range(M + 1)] for j in range(N + 1)]

    # Base Case: When N = 0
    for j in range(M + 1):
        dp[0][j] = j
    # Base Case: When M = 0
    for i in range(N + 1):
        dp[i][0] = i
    # Transitions
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            if A[i - 1] == B[j - 1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j], # Insertion
                    dp[i][j-1], # Deletion
                    dp[i-1][j-1] # Replacement
                )

    return dp[N][M]

if __name__ == "__main__":
    # Iterate through Princeton OCR folder
    folder_path = '/princeton_years/'

    # Only cover years 1908 and 1918
    for year in tqdm(range(8,19)):
        if year != 21:
            if year < 10:
                year = "0" + str(year)

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
            # Create Segment Dataframe
            segment_df = pd.DataFrame(segments, columns = ["page_number", "text_index", "text"])

            # Create Month Strings to be matched
            month_strings = []
            for index in range(len(month_abbrvs)):
                month_string = f"{month_abbrvs[index]} {year_string}"
                month_strings.append(month_string)
            months_strings_df = pd.DataFrame(month_strings, columns = ["month_string"])
            segment = "  N, Dec. 08"
            segment_more = "  N, Dec. 08 sd;"
            month_string = month_strings[11]
            segment_switched = "Dec. 08 N,"
            #jarowinkler = JaroWinkler()
            #print(month_string)
            #s = SIFT4()
            #print(s.distance(segment, month_string))
            #print(s.distance(segment_more, month_string))
            #print(s.distance("fsdfsdfs random", month_strings[10]))
            cosine = Cosine(2)
            p0 = cosine.get_profile(segment)
            p1 = cosine.get_profile(month_string)
            p2 = cosine.get_profile(segment_more)
            p3 = cosine.get_profile("randomness")
            p4 = cosine.get_profile(segment_switched)
            print("----")
            print(cosine.similarity_profiles(p0, p1))
            print(cosine.similarity_profiles(p2, p1))
            print(cosine.similarity_profiles(p2, p3))
            print(cosine.similarity_profiles(p4, p1))
            print(cosine.similarity_profiles(p4, p0))
            print("----")
            break

    # General Algorithm For Detecting Dates
        # For each page
            # Split page into string lengths of 10 with significant overlap 
                # (i.e. string 1 should contain 9 of the characters in string 1)
            # For each string length
                # Calculate cosine similarity between each string to all the month strings (month + year)
            # Detect Local Maxima's for each string per month string values
                # (i.e. if you have 5 strings in a row with cosine similarity scores for Dec. 08
                # as 0.4 0.6 0.6 0.6 0.4, then we can probably say something about the entire Dec. 08
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
                # For instance: "  N, Dec. 08" turns into " N, Dec. 08" and "N, Dec. 08" until we get to
                # "Dec. 08"
                #
                #
                # Another idea for this is to get the intersection of all such local maxima in
                # the sequence we are looking at
                # For instance: Local maxima for Dec. 08 are "; Dec. 08", ";Dec. 08 ", "Dec. 08 ;"
                # and the intersection of this would then be Dec. 08, which is the date we are looking
                # for.