import os
import json

from web_scraping import WebScraping

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
COUNTRIES_FILE = os.path.join(CURRENT_FOLDER, "countries_states.json")

data = []
scraper = WebScraping()

# All pqges selectors
selectors = {
    "table_base": "table.ppvx_table",
    "row": "tbody tr",
    "name": "td:nth-child(1)",
    "code": "td:nth-child({index})",
    "states_page_content": "div.markdownRendering > article",
}


def get_table_data(
    rows_num: int,
    selector_row_base: str,
    code_index: int = 2,
    code_upper: bool = True,
):
    """ Get table data from paypal table

    Args:
        rows_num (int): rows found in table
        selector_row_base (str): base selector for each row
        code_index (int, optional): Column number of the code value field. Defaults to 2.
        code_upper (bool, optional): Convert code values to upper case. Defaults to True.

    Returns:
        _type_: _description_
    """

    table_data = []

    for row_index in range(1, rows_num + 1):

        # Calculate selectors
        row_selector = f"{selector_row_base}:nth-child({row_index})"
        name_selector = f"{row_selector} {selectors['name']}"
        code_selector = f"{row_selector} {selectors['code']}".replace(
            "{index}", str(code_index)
        )

        # Get values
        key = scraper.get_text(name_selector)
        code = scraper.get_text(code_selector)
        
        # Clean code
        if code_upper:
            code = code.upper()
        code = code.replace(" &amp; ", " ")
        
        table_data.append({"name": key.lower(), "code": code})

    return table_data


# Load countries page
scraper.set_page("https://developer.paypal.com/api/rest/reference/country-codes/")

# Get all countries
rows_num = len(scraper.get_elems(selectors["row"]))
print(f"Found {rows_num} countries")
data = get_table_data(rows_num, selectors["row"])

# Load states page
scraper.set_page("https://developer.paypal.com/api/rest/reference/state-codes/")

# Loop page content
selector_content_item = selectors["states_page_content"] + " > *"
content_items = scraper.get_elems(selector_content_item)
next_is_table = False
current_country = ""
table_selector = f"{selectors['states_page_content']} > {selectors['table_base']}"
content_item_index = 0
for content_item in content_items:
    content_item_index += 1

    item_tag = content_item.tag_name
    if item_tag == "h2":
        # Save country and prepare to scrape states
        next_is_table = True
        current_country = content_item.text.lower()
        if current_country == "usa":
            current_country = "united states"
        print(f"\tScraping states of country '{current_country}'...")
        continue

    if next_is_table:
        # Scrape states of current table
        print(f"\t\tFound {rows_num} states")
        current_table_selector = f"{table_selector}:nth-child({content_item_index})"
        row_base_selector = current_table_selector + " " + selectors["row"]
        rows_num = len(
            scraper.get_elems(current_table_selector + " " + selectors["row"])
        )
        table_data = get_table_data(rows_num, row_base_selector)

        # Save in full data
        country_row = list(
            filter(lambda country: country["name"] == current_country, data)
        )[0]
        country_row["states"] = table_data

    next_is_table = False

# Get lang codes
print("Scraping lang codes...")
scraper.set_page("https://developer.paypal.com/reference/locale-codes/")
rows_num = len(scraper.get_elems(selectors["row"]))
data_langs = get_table_data(rows_num, selectors["row"], 5, False)

# Save lang in each country
for country in data:
    langs = list(
        filter(lambda lang: lang["name"] in country["name"], data_langs)
    )
    langs_codes = [lang["code"] for lang in langs]
    country["langs"] = langs_codes

# Save file
with open(COUNTRIES_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)
    
print("Scraping finished")
