import os
import re
import csv
import sys
from tqdm import tqdm
import argparse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
#import numpy as np
#from scipy.sparse import csr_matrix
#import sparse_dot_topn.sparse_dot_topn as ct
#from scipy.sparse import coo_matrix
#from nltk import ngrams
from sklearn.neighbors import NearestNeighbors
#import spatial.distance

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

def find_ngrams(input_list, n=3):
  return zip(*[input_list[i:] for i in range(n)])

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

            # Text Vectorized
            text_df = org_names = segment_df['text']
            vectorizer = TfidfVectorizer(min_df=1, analyzer=find_ngrams, lowercase = False)
            transformed_text_df = vectorizer.fit_transform(text_df.to_list()) 

            # Months Vectorized
            transformed_months_df = vectorizer.transform(months_strings_df["month_string"].to_list())

            # Initialize KNN
            nbrs = NearestNeighbors(n_neighbors=12, n_jobs=-1).fit(transformed_text_df)
            queryTFIDF_ = vectorizer.transform(transformed_months_df)
            distances, indices = nbrs.kneighbors(queryTFIDF_)

            #print(indices)
            count = 0
            for index in range(len(distances)):
                distance_array = distances[index]
                distance_size = 0
                for distance in distance_array:
                    distance_size += distance
                if distance_size > 0:
                    print(indices[index])
                    count = count + 1
            print(count)
            #print(matches)
            break