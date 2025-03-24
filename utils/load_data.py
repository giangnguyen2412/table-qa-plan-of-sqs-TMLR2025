# Copyright 2024 The Chain-of-Table authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import ast
from tqdm import tqdm
import copy
from tqdm import tqdm

def load_tabfact_dataset(
    dataset_path,
    raw2clean_path,
    tag="test",
    first_n=-1,
):
    tabfact_statement_raw2clean_dict = {}
    with open(raw2clean_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            info = json.loads(line)
            tabfact_statement_raw2clean_dict[info["statement"]] = info["cleaned_statement"]

    dataset = []
    if first_n != -1:
        all_lines = []
        for line in open(dataset_path):
            all_lines.append(line)
            if len(all_lines) >= first_n: break
    else:
        all_lines = open(dataset_path).readlines()
    for i, line in tqdm(enumerate(all_lines), total=len(all_lines), desc=f"Loading tabfact-{tag} dataset"):
        info = json.loads(line)
        info["id"] = f"{tag}-{i}"
        info["chain"] = []
        if info["statement"] in tabfact_statement_raw2clean_dict:
            info["cleaned_statement"] = tabfact_statement_raw2clean_dict[
                info["statement"]
            ]
        else:
            info["cleaned_statement"] = info["statement"]
        dataset.append(info)
    return dataset

##############################################

import ast

def identify_date_columns_prompt(table_headers, sample_row):
    # Providing examples within the prompt
    examples = (
        "Example 1: For headers ['Game No.', 'Date', 'Opponent', 'Score'] "
        "and the first row ['1', 'Sept 20, 2023', 'Team A', '3-1'], "
        "the columns that contain dates would be listed as: ['Date'].\n"
        "Example 2: For headers ['Event ID', 'Start Date', 'End Date', 'Duration'] "
        "and the first row ['123', 'aug 1993', 'jun 2000', '24 hours'], "
        "the columns that contain dates would be listed as: ['Start Date', 'End Date'].\n"
        "Example 3: For headers ['Transaction', 'Timestamp', 'Amount', 'Status'] "
        "and the first row ['0001', '2023-05-20', '$100', 'Completed'], "
        "the columns that contain dates would be listed as: ['Timestamp'].\n"
        "Example 4: For headers ['game', 'result', 'venue', 'record'] "
        "and the first row ['april 20', '3', 'w', 'yes'], "
        "the columns that contain dates would be listed as: ['game'].\n"
        "Example 5: For headers ['Game', 'Score', 'Venue', 'Attendance'] "
        "and the first row ['1', '13-0', 'New York', '20000'], "
        "the columns that contain dates would be listed as: [].\n"
        "Example 6: For headers ['Department', 'Employee', 'Service Year', 'Salary'] "
        "and the first row ['IT', 'John Doe', '10', '300000'], "
        "the columns that contain dates would be listed as: [].\n"
        "Example 7: For headers ['June', 'July', 'August', 'September'] "
        "and the first row ['win', 'loss', 'win', 'tie'], "
        "the columns that contain dates would be listed as: [].\n"
        "Example 8: For headers ['2000', '2001', '2002', '2004'] "
        "and the first row ['3r', '1r', 'a', 'qf'], "
        "the columns that contain dates would be listed as: [].\n"
    )

    prompt = ""
    prompt += examples
    prompt += "Identify which of these columns likely contain dates: " + ", ".join(table_headers) + "."
    prompt += f"\nHere is the first row in the Table for your reference: {sample_row}\n."
    prompt += "A list of columns that contain dates from is:\n"

    # prompt += "### Here come to your actual task!!"
    # prompt += f"Example 9: For headers {str(table_headers)} "
    # prompt += f"and the first row {str(sample_row)}, "
    # prompt += f"the columns that contain dates would be listed as: "

    
    return prompt

def build_date_standardization_prompt(date_str):
    # Providing examples within the prompt
    examples = (
        "Example 1: Given the date 'Sept 20, 2023', the standardized date should be '2023-09-20'.\n"
        "Example 2: Given the date '2023', missing month and day, the standardized date should be '2023-01-01'.\n"
        "Example 3: Given the date 'July 2022', missing only the day, the standardized date should be '2022-07-01'.\n"
        "Example 4: Given the date 'August', missing day and year, the standardized date should be '9999-08-01' (assuming the current year is 9999).\n"
    )

    prompt = f"Convert the following date '{date_str}' to a standardized format (YYYY-MM-DD).\n"
    prompt += "If the date or month is missing, fill them with '01'. If the year is missing, fill it with '9999'.\n"
    prompt += "\n" + examples
    prompt += f"Return a string that contains the standardized date only. The standardized date for '{date_str}' is:\n"
    
    return prompt


def standardize_dates_in_table(table, llm):
    headers = table[0]
    sample_row = table[1]
    identify_prompt = identify_date_columns_prompt(headers, sample_row)

    llm_options = llm.get_model_options(temperature=0.0, per_example_max_decode_steps=200, per_example_top_p=1.0)
    identify_response = llm.generate_plus_with_score(identify_prompt, options=llm_options)
    identified_columns = identify_response[0][0]

    try:
        identified_columns = ast.literal_eval(identified_columns)
        date_columns = [headers.index(col) for col in identified_columns if col in headers]

    except Exception as e:
        date_columns = []


    for row in table[1:]:  # Skip the header row
        for col_index in date_columns:
            date_str = row[col_index]
            standardization_prompt = build_date_standardization_prompt(date_str)
            response = llm.generate_plus_with_score(standardization_prompt, options=llm_options)
            standardized_date = response[0][0]

            row[col_index] = standardized_date  # Update the date in the row

    return table

def standardize_dates(dataset, llm):
    standardized_entries = []
    for idx, entry in enumerate(tqdm(dataset)):
        new_entry = copy.deepcopy(entry)
        headers = entry['table_text'][0]

        new_headers = []
        for header in headers:
            new_col = header.replace(' ','_')
            new_headers.append(new_col)
        # entry['standard_table_text'] = standardize_dates_in_table(new_entry['table_text'], llm)
        entry['table_text'] = standardize_dates_in_table(new_entry['table_text'], llm)
        entry['table_text'][0] = new_headers

        standardized_entries.append(entry)
    return standardized_entries


import re

def clean_text(text):
    """Standardize text by converting to lowercase, trimming whitespaces, and removing special characters."""
    # text = re.sub(r'[^\w\s]', '', text)  # Remove special characters except for word characters and spaces
    return text.strip().lower()

import random
import string

# def clean_column_names(column_names):
#     """Ensure column names are SQL-friendly by removing or replacing special characters and replacing spaces with underscores."""
#     # Create a dictionary to count occurrences of cleaned column names
#     cleaned_name_counts = {}
#
#     # Create a list to store the final cleaned column names
#     cleaned_column_names = []
#
#     for column_name in column_names:
#         orig_col = copy.deepcopy(column_name)
#
#         # Generate random name for empty column name
#         if len(column_name) == 0:
#             # Generate a random letter from a-z
#             column_name = random.choice(string.ascii_lowercase)
#
#         # Replace periods, parentheses, and other non-alphanumeric characters (except underscores) with underscores
#         cleaned_name = re.sub(r'[^\w\s]', '_', column_name.replace(' ', '_')).strip('_')
#
#         if len(cleaned_name) == 0:
#             cleaned_name = random.choice(string.ascii_lowercase)
#
#         if cleaned_name[0].isdigit():
#             cleaned_name = 'c_' + cleaned_name
#
#         cleaned_name = cleaned_name.lower()
#
#         # Check if the cleaned name already exists in the dictionary
#         if cleaned_name in cleaned_name_counts:
#             # Increment the count for this cleaned name
#             cleaned_name_counts[cleaned_name] += 1
#             # Append the count to the cleaned name to make it unique
#             unique_cleaned_name = f"{cleaned_name}_{cleaned_name_counts[cleaned_name]}"
#         else:
#             # Add the cleaned name to the dictionary with a count of 0
#             cleaned_name_counts[cleaned_name] = 0
#             unique_cleaned_name = cleaned_name
#
#         # Add the unique cleaned name to the final list
#         cleaned_column_names.append(unique_cleaned_name)
#
#     return cleaned_column_names

# def clean_column_name(column_name):
#     """Ensure column names are SQL-friendly by removing or replacing special characters and replacing spaces with underscores."""
#     # orig_col = copy.deepcopy(column_name)
#     # Generate random name for empty column name
#     if len(column_name) == 0:
#         # Generate a random letter from a-z
#         column_name = random.choice(string.ascii_lowercase)
#
#     # Replace periods, parentheses, and other non-alphanumeric characters (except underscores) with underscores
#     cleaned_name = re.sub(r'[^\w\s]', '_', column_name.replace(' ', '_'))
#
#     if len(cleaned_name) == 0:
#         return cleaned_name.lower()
#
#     if cleaned_name[0].isdigit():
#         cleaned_name = 'c_' + cleaned_name
#
#     # Trim any trailing underscores that might have been added
#     # cleaned_name = cleaned_name.strip('_')
#     # Optionally convert to lowercase to avoid case sensitivity issues in SQL
#     return cleaned_name.lower()

def clean_column_name(column_name, existing_columns=None):
    """Ensure column names are SQL-friendly and unique by removing special characters and replacing spaces with underscores."""
    if existing_columns is None:
        existing_columns = []

    # Generate random name for empty column name
    if len(column_name) == 0:
        column_name = random.choice(string.ascii_lowercase)

    # Replace special characters with underscores
    cleaned_name = re.sub(r'[^\w\s]', '_', column_name.replace(' ', '_'))

    if len(cleaned_name) == 0:
        cleaned_name = random.choice(string.ascii_lowercase)

    if cleaned_name[0].isdigit():
        cleaned_name = 'c_' + cleaned_name

    # Convert to lowercase
    cleaned_name = cleaned_name.lower()

    # Ensure the name is unique
    original_cleaned = cleaned_name
    counter = 1
    while cleaned_name in existing_columns:
        cleaned_name = f"{original_cleaned}_{counter}"
        counter += 1

    return cleaned_name

def clean_column_names(column_names):
    """
    Clean all column names at once to make them SQL-friendly and ensure uniqueness.

    Args:
        column_names: A list of original column names

    Returns:
        A list of cleaned, unique column names
    """
    cleaned_names = []
    name_counts = {}  # To track occurrences of each cleaned name

    for col in column_names:
        # Initial cleaning
        if len(col) == 0:
            cleaned = random.choice(string.ascii_lowercase)
        else:
            # Replace special characters and spaces
            cleaned = re.sub(r'[^\w\s]', '_', col.replace(' ', '_'))

            if len(cleaned) == 0:
                cleaned = random.choice(string.ascii_lowercase)

            if cleaned[0].isdigit():
                cleaned = 'c_' + cleaned

            cleaned = cleaned.lower()

        # Handle duplicates
        if cleaned in name_counts:
            name_counts[cleaned] += 1
            cleaned = f"{cleaned}_{name_counts[cleaned]}"
        else:
            name_counts[cleaned] = 0

        cleaned_names.append(cleaned)

    return cleaned_names

def clean_table_text(table):
    """Apply text cleaning to each cell in a 2D table array, including column names."""
    cleaned_table = []
    if table:
        # Clean column names on the first row
        # column_names = [clean_column_name(col) for col in table[0]]
        column_names = clean_column_names(table[0])
        cleaned_table.append(column_names)
        # Clean the rest of the table data
        for row in table[1:]:
            cleaned_row = [clean_text(cell) for cell in row]
            cleaned_table.append(cleaned_row)
    return cleaned_table


def preprocess_entry(data_entry):
    """Preprocess the data entry for consistent SQL operations."""
    new_entry = copy.deepcopy(data_entry)
    if 'table_caption' in data_entry:
        new_entry['table_caption'] = clean_text(data_entry['table_caption'])

    new_entry['table_text'] = clean_table_text(data_entry['table_text'])
    new_entry['statement'] = clean_text(data_entry['statement'])

    return new_entry
