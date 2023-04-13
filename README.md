# English Catalogue of Books

## Repository Information

OCR Data from [Hathi Trust's English Catalogue of Books](https://catalog.hathitrust.org/Record/000550349).

Original OCR text files can be found at `/princeton_years`.

Original Colab Notebook can be found in `Parsing_ECB_1912_wi23.ipynb`.

Clean Entries can be found at `/clean_entries`.

Clean Entry measures can be found at `/clean_entries_measures`. These text files provide metrics that help understand said data.

## Installation Requirements

Make sure to have at least [Python 3.7](https://www.python.org/downloads/) installed on the device you wish to run this on.

Once this is done and you have and have cloned this repository ([tutorial to cloning repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)), install the necessary requirements from your command line interface:

Run ``(python prefix) pip install -r requirements.txt``

Python prefixes depend on device, but the most common ones are: py, py3, python, and python3.

## Getting Clean Entries from Scratch

To print out entry metrics during the running process:
``(python prefix) clean_entries.py --verbose True``

To not print out entry metrics during the running process:
``(python prefix) clean_entries.py --verbose False``

## TODOs

Written for week of 4/12-4/19:

* Check for (number)vo in wrong places
* Check for currency in wrong places
    * Expected format: Lastname FirstName - Title "All Else" Publisher Month
        * May not follow if multiple editions or multiple titles
    * Should be after Title and Author, before Publisher and Year
* Check for different/wrong years in entries
* Place fronttrunc and linemid entries into separate CSV
* Check total books vs how many entries captured (wait on this)
    * Have to read total books
    * ~ 30 entries per page
    * Should be getting rid of secondary entries