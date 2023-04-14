# Python Scripts

## Installation Requirements

Make sure to have at least [Python 3.7](https://www.python.org/downloads/) installed on the device you wish to run this on.

Once this is done and you have and have cloned this repository ([tutorial to cloning repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)), install the necessary requirements from your command line interface:

Run ``(python prefix) pip install -r requirements.txt``

Python prefixes depend on device, but the most common ones are: py, py3, python, and python3.

## Creating Clean Entries from scratch

To print out entry metrics during the running process:
``(python prefix) create_clean_entries.py --verbose True``

To not print out entry metrics during the running process:
``(python prefix) create_clean_entries.py --verbose False`` or simply ``(python prefix) create_clean_entries.py``

## Creating Dataframe data from scratch

To print out Dataframe row metrics during the running process:
``(python prefix) create_dataframes.py --verbose True``

To not print out Dataframe row metrics during the running process:
``(python prefix) create_clean_entries.py --verbose False`` or simply ``(python prefix) create_clean_entries.py``