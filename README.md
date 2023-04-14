# English Catalogue of Books

## Repository Information

OCR Data from [Hathi Trust's English Catalogue of Books](https://catalog.hathitrust.org/Record/000550349).

Original OCR text files can be found in `/princeton_years`.

Entries can be found in `/entries` (less processing than data in `/dataframes`).

Dataframes can be found in `/dataframes` (more processing than data in `/entries`).

Original Colab Notebook can be found in `/scripts/Parsing_ECB_1912_wi23.ipynb` and all such other Python scripts can be found in `/scripts` (including documentation for Python scripts).

## TODOs

Written for week of 4/12-4/19:

### Done
* Write and Run script up until the finish of John's Google Colab Doc (done)
* Checked for missing major column values and placed them in different CSVs (done)
* Place fronttrunc and linemid entries into separate CSV (done)

### Doing
* Read up on World Cat API and how it could be used to "fill in blanks"

### Haven't Done:
* Check for (number)vo in wrong places (haven't done)
* Check for currency in wrong places (haven't done)
* Check for different/wrong years in entries (haven't done)

### Will Wait
* Check total books vs how many entries captured (wait on this)
    * Have to read total books
    * ~ 30 entries per page
    * Should be getting rid of secondary entries