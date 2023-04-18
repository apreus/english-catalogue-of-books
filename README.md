# English Catalogue of Books

## General Repository Information

OCR Data from [Hathi Trust's English Catalogue of Books](https://catalog.hathitrust.org/Record/000550349).

Original OCR text files can be found in `/princeton_years`.

Entries can be found in `/entries` (less processing than data in `/dataframes`).

Dataframes can be found in `/dataframes` (more processing than data in `/entries`).

Original Colab Notebook can be found in `/scripts/Parsing_ECB_1912_wi23.ipynb` and all such other Python scripts can be found in `/scripts` (including documentation for Python scripts).

## Data Schema

Schema files can be found in `\schema`. The Lucid Chart document can be found [here](https://lucid.app/lucidchart/4d30c38e-c769-443d-8c82-fdf6894c5a80/edit?invitationId=inv_f8bb8f35-4b80-400a-8e9b-d774e9de7dbf). Included below is an image of the schema.

![Schema](./schema/English_Catalogue_of_Books_Data_Schema.png)

## TODOs

Written for week of 4/12-4/19:

### Done
* Write and Run script up until the finish of John's Google Colab Doc (done)
* Checked for missing major column values and placed them in different CSVs (done)
* Place fronttrunc and linemid entries into separate CSV (done)

### Doing
* Read up on World Cat API and how it could be used to "fill in blanks" and fill up even more information that the English Catalogue does not contain
    * The (get) /bibs request looks to be the most promising: [WorldCat Search API v2](https://developer.api.oclc.org/wcv2#/Bibliographic%20Resources) (in the Bibliographic Resources section)
        * Input query can include the following:
            * Publisher
            * Title
            * Author
            * Keyword
        * We can get these query values from even "incomplete" row values
        * The "datePublished" entry will help us significantly in reducing the results
        * Returns a dictionary of records for a bunch of books with a lot of values:
            * Publisher
            * Subject
            * Title
            * Author
            * Date
        * Can probably come up with some probabilistic or deterministic method that helps us find the returned entry that matches the value with blanks
    * Potential Python Wrapper Library that helps with making World Cat API requests: [bookops-worldcat](https://pypi.org/project/bookops-worldcat/)
        * [Documentation](https://bookops-cat.github.io/bookops-worldcat/0.5/)
        * Supports only OCLC OAuth 2.0 endpoints and flows

### Haven't Done:
* Check for (number)vo in wrong places (haven't done)
* Check for currency in wrong places (haven't done)
* Check for different/wrong years in entries (haven't done)

### Will Wait
* Check total books vs how many entries captured (wait on this)
    * Have to read total books
    * ~ 30 entries per page
    * Should be getting rid of secondary entries