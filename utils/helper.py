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


import pandas as pd
import json
import os
import ast
import re
import logging
import pickle
import sqlite3
import itertools
import sqlparse
import copy
from typing import List
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import Session
from _ctypes import PyObj_FromPtr
from utils.prompts import *
from utils.evaluate import *
from operations import *
import yaml
import uuid
import random
import string
import time

#################################################################################################### RUNNING PARAMS ####################################################################################################
# TODO: Currently, for WikiTQ, the max number of rows I input to the model is 100

class Config:
    def __init__(self):
        # Generate a unique run ID
        self.run_unique_id = self._generate_run_id()

        self.project_directory = '/home/giang/Downloads/table-qa-2025/'

        # Load LLM configuration from YAML file
        llm_config_path = os.path.join(self.project_directory, "llm_config.yaml")
        if os.path.exists(llm_config_path):
            with open(llm_config_path, "r") as f:
                self.llm_config = yaml.load(f, Loader=yaml.FullLoader)

            # Set active provider from config
            self.active_provider = self.llm_config.get('active_provider', 'azure_openai')

            # Set LLM name based on active provider and model
            if self.active_provider == 'azure_openai':
                provider_config = self.llm_config['providers']['azure_openai']
                # Find active deployment
                for depl in provider_config['deployments']['regular']:
                    if depl.get('active', False):
                        self.LLM = depl['name']
                        break
                else:
                    self.LLM = 'GPT4-O'  # Default fallback

            elif self.active_provider == 'sambanova':
                provider_config = self.llm_config['providers']['sambanova']
                self.LLM = provider_config.get('model_type', 'qwen')

            elif self.active_provider == 'deepseek':
                provider_config = self.llm_config['providers']['deepseek']
                # Find active model
                for model in provider_config['models']:
                    if model.get('active', False):
                        self.LLM = model['name']
                        break
                else:
                    self.LLM = 'deepseek-chat'  # Default fallback
        else:
            # Default values if config file doesn't exist
            self.LLM = 'GPT4-O'  # the model used for evaluation
            self.active_provider = 'azure_openai'

        self.test_dataset = 'TabFact'
        # self.test_dataset = 'WikiTQ'
        
        self.planning_algorithm = 'static'
        # self.planning_algorithm = 'dynamic'

        # self.result_file_name = f'{self.LLM}_{self.test_dataset}_results_test_run16.json'  # if you want to do caching in running evaluation
        self.result_file_name = os.path.join(self.project_directory, 'result_files', f'{self.LLM}_results_test_run{self.run_unique_id}.json')  # if you want to do caching in running evaluation

        self.tabfact_planning_log_path = os.path.join(self.project_directory, 'result_files', f'logs/{self.LLM}_log_TabFact_test{self.run_unique_id}_run')  # Save logs file for each sample to this path for TabFact
        self.wikitq_planning_log_path = os.path.join(self.project_directory, 'result_files', f'logs/{self.LLM}_log_WikiTQ_test{self.run_unique_id}_run') # Save logs file for each sample to this path for WikiTQ
        
        self.using_sql_for_COT = True
        self.NATURAL_LANGUAGE_PLANNING = True  # Planning with natural language
        
        self.K_plans = 1  # Numer of attempts to solve the problem with PoS
        self.USING_SQL = True
        
        # VIS_STYLE = 4  # Series of highlighted tables
        # VIS_STYLE = 5  # Compact version of attribution
        self.VIS_STYLE = 6  # Color-coding version of Series of highlighted tables
        # self.VIS_PURPOSE = 'DEBUGGING' # Enable this to see the groundtruth in your visualizations
        self.VIS_PURPOSE = 'TEST'
        
        self.USING_SQL_HIST_FINAL_QUERY = self.using_sql_for_COT
        self.USING_SQL_FOR_FINAL_QUERY = self.using_sql_for_COT
        
        if self.NATURAL_LANGUAGE_PLANNING:
            self.OTG_PLANNING = False
        else:
            self.OTG_PLANNING = True
        
        self.XAI_METHOD = os.getenv('XAI_METHOD')
        self.SQL_EXECUTOR = 'SQLite'

        self.idx_tracking_col = 'xai_tracking_idx'

        self.DEBUG = False


    # def _generate_run_id(self):
    #     """Generate an 8-character unique ID with letters and numbers"""
    #     # Method 1: Using random with letters and digits
    #     chars = string.ascii_letters + string.digits
    #     return ''.join(random.choice(chars) for _ in range(8))
    #
    #     # Alternative method using UUID (commented out)
    #     # return uuid.uuid4().hex[:8]

    def _generate_run_id(self):
        """Generate a unique ID using timestamp and random characters"""
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        # Convert to base 36 (using 0-9, a-z) to get a shorter string
        timestamp_str = format(timestamp % 1000000, '06d')  # Last 6 digits of timestamp

        # Add 2 random characters for extra uniqueness
        chars = string.ascii_letters + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(2))

        return timestamp_str + random_part

# Create a config instance
config = Config()

# Export all attributes as global variables
globals().update(vars(config))

print(vars(config))


########################################################################################################################################################################################################

syntax_instr1 = "If using SELECT COUNT(*), SUM, MAX, AVG, you MUST use AS to name the new column."
pd.set_option('display.max_columns', None)  # to show full pandas dataframe for debugging

#################################################################################################### TABLE CONVERSION FUNCTIONS ####################################################################################################


def df2table(df):
    # Get the header from the DataFrame
    header = list(df.columns)
    # Get the rows as lists
    data_rows = df.values.tolist()
    # Combine header and data rows
    result = [header] + data_rows
    return result

# def table2df(table_text, num_rows=100):
#     header, rows = table_text[0], table_text[1:]
#
#     if test_dataset == 'WikiTQ':
#         rows = rows[:num_rows]
#
#     df = pd.DataFrame(data=rows, columns=header)
#
#     # Convert to numeric while explicitly handling errors
#     for col in df.columns:
#         try:
#             df[col] = pd.to_numeric(df[col])
#         except ValueError:
#             pass  # Keep the original data if conversion fails
#
#     return df

def table2df(table_text, num_rows=100):
    header, rows = table_text[0], table_text[1:]

    if test_dataset == 'WikiTQ':
        rows = rows[:num_rows]

    df = pd.DataFrame(data=rows, columns=header)

    # Convert columns to numeric where possible
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            # If conversion fails, leave the column as is
            pass

    return df

def table2string(
    table_text,
    num_rows=100,
    caption=None,
):
    df = table2df(table_text, num_rows)
    linear_table = ""
    if caption is not None:
        linear_table += "table caption : " + caption + "\n"

    header = "col : " + " | ".join(df.columns) + "\n"
    linear_table += header
    rows = df.values.tolist()
    for row_idx, row in enumerate(rows):
        row = [str(x) for x in row]
        line = "row {} : ".format(row_idx + 1) + " | ".join(row)
        if row_idx != len(rows) - 1:
            line += "\n"
        linear_table += line
    return linear_table

def df_to_string(df):
    """
    Converts a DataFrame to a string.
    :param df:
    :return:
    """
    # Ensure all text in the DataFrame is in lowercase
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)

    # Convert the DataFrame to a string with a specific format
    formatted_string = df.to_string(index=True, header=True)
    return formatted_string


def df_to_formatted_table(
    df,
    caption=None,
):
    """
    Converts a DataFrame to a formatted table string.
    :param df:
    :param caption:
    :return:
    """
    linear_table = ""
    if caption is not None:
        linear_table += "table caption : " + caption + "\n"

    header = "col : " + " | ".join(df.columns) + "\n"
    linear_table += header
    rows = df.values.tolist()
    for row_idx, row in enumerate(rows):
        row = [str(x) for x in row]
        line = "row {} : ".format(row_idx + 1) + " | ".join(row)
        if row_idx != len(rows) - 1:
            line += "\n"
        linear_table += line
    return linear_table


def list_to_formatted_string(data_list):
    """
    Converts a list to a formatted string.
    :param data_list:
    :return:
    """
    # Create a DataFrame from the list
    headers = data_list[0]  # Extract the headers
    data = data_list[1:]    # Extract the data rows
    df = pd.DataFrame(data, columns=headers)

    # Convert all text entries to lowercase
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)

    # Convert the DataFrame to a string
    formatted_string = df.to_string(index=False, header=True)
    return formatted_string


def list_to_formatted_table(data_list):
    """
    Converts a list to a formatted table string.
    :param data_list:
    :return:
    """
    # Create a DataFrame from the list
    headers = data_list[0]  # Extract the headers
    data = data_list[1:]    # Extract the data rows
    df = pd.DataFrame(data, columns=headers)

    linear_table = ""
    header = "col : " + " | ".join(df.columns) + "\n"
    linear_table += header
    rows = df.values.tolist()
    for row_idx, row in enumerate(rows):
        row = [str(x) for x in row]
        line = "row {} : ".format(row_idx + 1) + " | ".join(row)
        if row_idx != len(rows) - 1:
            line += "\n"
        linear_table += line
    return linear_table


class NoIndent(object):
    """Value wrapper."""

    def __init__(self, value):
        self.value = value


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = "@@{}@@"
    regex = re.compile(FORMAT_SPEC.format(r"(\d+)"))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get("sort_keys", None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (
            self.FORMAT_SPEC.format(id(obj))
            if isinstance(obj, NoIndent)
            else super(MyEncoder, self).default(obj)
        )

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = PyObj_FromPtr(id)
            json_obj_repr = json.dumps(no_indent.value, sort_keys=self.__sort_keys)

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                '"{}"'.format(format_spec.format(id)), json_obj_repr
            )

        return json_repr


def get_act_func(name, using_sql=False):
    try:
        # if ('add_column' in name or 'select_row' in name or 'sort' in name) \
        # and USING_SQL is True:
        # if USING_SQL is True:

        if using_sql is True:
            return eval(f"{name}_act_sql")
        else:
            return eval(f"{name}_act")
    except:

        def _default_act(table_text, *args, **kwargs):
            return copy.deepcopy(table_text)

        if "query" not in name:
            print("Unknown operation: ", name)
        return _default_act


def get_table_info(sample, skip_op=[], first_n_op=None):
    table_text = sample["table_text"]
    chain = sample["chain"]
    if 'using_sql' in sample:
        using_sql = sample["using_sql"]

    if first_n_op is not None:
        chain = chain[:first_n_op]

    table_info = {
        "table_text": table_text,
        "act_chain": [],
    }
    for operation in chain:
        operation_name = operation["operation_name"]

        act_func = get_act_func(operation_name, using_sql)
        if DEBUG:
            print(table_info)
            print(operation)
        table_info = act_func(table_info, operation, skip_op=skip_op)

    return table_info


def get_table_log(sample, skip_op=[], first_n_op=None):
    table_text = sample["table_text"]
    chain = sample["chain"]

    if first_n_op is not None:
        chain = chain[:first_n_op]

    table_log = []

    table_info = {
        "table_text": table_text,
        "act_chain": [],
    }
    table_log.append(table_info)

    for operation in chain:
        operation_name = operation["operation_name"]
        act_func = get_act_func(operation_name)
        table_info = act_func(table_info, operation, skip_op=skip_op)
        if DEBUG:
            print(operation_name)
        if 'row' in operation_name:
            # print('HERE')
            # print(table_info)
            # print('HERE')
            if '_real_select_rows' in table_info:
                table_info['act_chain'][-1] = table_info['_real_select_rows']
            # else:
            #     table_info['act_chain'][-1] = table_info['act_chain']

        if 'query' in operation_name:
            table_info['act_chain'].append(f'{operation_name}()')
            table_info['cotable_result'] = operation['parameter_and_conf'][0][0]
        table_log.append(table_info)

    return table_log

def get_operation_name(string):
    # f_xxxx(...)
    res = re.findall(r"f_(.*?)\(.*\)", string)[0]
    return res


def get_all_operation_names(string):
    if DEBUG:
        print('Here print the operation names:')
        print(string)
    operation_names = []
    parts = string.split("->")
    for part in parts:
        part = part.strip()
        if part == "<END>":
            operation_names.append("<END>")
        else:
            res = re.findall(r"f_(.*?)\(.*\)", part)
            if res:
                operation_names.append(res[0])
    return operation_names

#################################################################################################### SQL FUNCTIONS ####################################################################################################

# Function to extract SQL code from a response
def extract_sql_code(response):
    """
    Extracts SQL code from a response.
    :param response:
    :return:
    """
    # Patterns to match SQL code under different conditions
    patterns = [
        r"```sql\n([\s\S]*?)\n```",  # Handles well-formed fenced code blocks
        r"```sql\n([\s\S]*)",  # Handles missing ending fence
        r"([\s\S]*?)\n```",  # Handles missing starting fence
        r"([\s\S]+)"  # Handles no fences at all, captures until the end or a comment
    ]

    for pattern in patterns:
        sql_match = re.search(pattern, response)
        if sql_match:
            sql_code = sql_match.group(1).strip()
            return sql_code

    return None


# Function to apply SQL to the DataFrame
def apply_sql_to_df(df, sql, table_name):
    """
    Applies SQL to a DataFrame.
    :param df:
    :param sql:
    :param table_name:
    :return:
    """
    # Connect to a SQLite in-memory database
    conn = sqlite3.connect(':memory:')
    df.to_sql(table_name, conn, index=False, if_exists='replace')
    
    # Perform SQL operation
    modified_df = pd.read_sql_query(sql, conn)
    conn.close()
    return modified_df


def build_new_prompt_for_sql_correction(sql_command, table_text, cleaned_statement, error_log):
    """
    Build a new prompt asking the LLM to correct the previous SQL command.
    :param sql_command:
    :param table_text:
    :param cleaned_statement:
    :param error_log:
    :return:
    """
    # Build a new prompt asking the LLM to correct the previous SQL command
    new_prompt = f"Based on this table table_sql: {table_text}\n and Statement: {cleaned_statement}\n,\
    please revise the following SQL to make it run correctly and without errors on the Table.\n\
    The wrong SQL is:\n```sql\n{sql_command}\n```"
    new_prompt += f"\nThe error when running the wrong SQL is: \n{error_log}.\n"

    new_prompt += f"\nConstraints for your SQL:"

    new_prompt += "\n1.If must use column "
    if len(table_text[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in table_text[0])
    else:
        existing_cols = f"{table_text[0][0]}"
    new_prompt += f"{existing_cols} in writing your SQL."

    new_prompt += "\n2.Your SQL command must be executable by python sqlite3.\n"


    new_prompt += "Your revised SQL is:\n"

    # print('New prompt:', new_prompt)
    # print('%'*140)
    
    return new_prompt


# A more generic method than parse_sql_columns_from_where
def extract_columns(sql_query, original_columns):
    """
    Extracts column names from a SQL query.
    :param sql_query:
    :param original_columns:
    :return:
    """
    # Remove comments and normalize whitespace
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    sql_query = ' '.join(sql_query.split())

    columns = set()

    # Extract column names from SELECT clause
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
    if select_match:
        select_columns = select_match.group(1)
        # Extract columns used in functions
        function_cols = re.findall(r'\b\w+\s*\((.*?)\)', select_columns)
        for func_col in function_cols:
            cols = re.findall(r'(\w+)', func_col)
            columns.update(cols)
        # Extract regular columns and aliases
        cols = re.findall(r'(\w+)(?:\s+AS\s+(\w+))?', select_columns)
        for col in cols:
            columns.add(col[0])  # Add the column name

    # Extract column names from WHERE clause
    where_columns = re.findall(r'WHERE\s+(.*?)(?:$|ORDER BY|GROUP BY|LIMIT)', sql_query, re.IGNORECASE)
    if where_columns:
        cols = re.findall(r'(\w+)\s*(?:=|LIKE|>|<|>=|<=|!=)', where_columns[0])
        columns.update(cols)

    # Extract column names from ORDER BY clause
    order_columns = re.findall(r'ORDER BY\s+(.*?)(?:$|LIMIT)', sql_query, re.IGNORECASE)
    if order_columns:
        cols = re.findall(r'(\w+)', order_columns[0])
        columns.update(cols)

    # Remove 'DISTINCT' if present
    columns.discard('DISTINCT')

    extracted_columns = list(columns)
    filtered_columns = [col for col in extracted_columns if col in original_columns]
    return filtered_columns


# parse_sql_columns_from_where
def parse_sql_columns_from_where(sql: str) -> List[str]:
    """
    Extracts column names from the WHERE clause of a SQL query.
    :param sql:
    :return:
    """
    def extract_where_clause(sql: str) -> str:
        parsed = sqlparse.parse(sql)[0]
        where_clause = ''
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.Where):
                where_clause = str(token)
                break
        return where_clause

    def extract_columns_from_where_clause(where_clause: str) -> List[str]:
        # Define the regex pattern to match column names before comparison operators
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*(=|!=|<|>|<=|>=|LIKE|IN|IS|BETWEEN)'
        columns = re.findall(pattern, where_clause)
        return [col[0] for col in columns]

    where_clause = extract_where_clause(sql)
    if where_clause:
        columns = extract_columns_from_where_clause(where_clause)
        return list(set(columns))  # Remove duplicates
    return ['*']


def get_column_indices(columns):
    return {col: idx for idx, col in enumerate(columns)}


def intersection_of_2d_indices(list1, list2):
    """
    Find the intersection of two lists of 2D indices.
    :param list1:
    :param list2:
    :return:
    """
    # Convert sublists to tuples for set operations
    set1 = set(tuple(sublist) for sublist in list1)
    set2 = set(tuple(sublist) for sublist in list2)
    
    # Find the intersection of the two sets
    intersection_set = set1.intersection(set2)
    
    # Convert the result back to list of lists
    intersection_list = [list(item) for item in intersection_set]
    
    return intersection_list


def transform_table_with_sql(intermediate_table, sql, table_name):
    """
    Transform a table using SQL.
    :param intermediate_table:
    :param sql:
    :param table_name:
    :return:
    """
    # Convert the intermediate table to a DataFrame
    df = table2df(intermediate_table)

    column_indices = get_column_indices(df.columns)
    original_columns = df.columns.values.tolist()

    # Add an index column to track original row indices
    df[idx_tracking_col] = df.index

    # print('table before:\n', df)

    # Connect to a SQLite in-memory database
    conn = sqlite3.connect(':memory:')
    df.to_sql(table_name, conn, index=False, if_exists='replace')

    ################## PARSE from WHERE
    # TODO: Need to implement checking for HAVING as well
    # print('SQL run:\n', sql)
    sql_columns = extract_columns(sql, original_columns)
    # print('SQL cols:\n', sql_columns)
    if '*' in sql_columns:
        sql_columns = column_indices
    ##############################

    # Perform SQL operation
    modified_df = pd.read_sql_query(sql, conn)
    conn.close()

    # print('table after:\n', modified_df)

    if idx_tracking_col in modified_df:
        selected_row_indices = modified_df[idx_tracking_col].tolist()
    else:
        selected_row_indices = []

    if idx_tracking_col in modified_df:
        # Drop the index column from the result DataFrame
        modified_df.drop(columns=[idx_tracking_col], inplace=True)

    modified_columns = modified_df.columns.values.tolist()

    # Convert the DataFrame back to the format needed
    modified_table = df2table(modified_df)

    # Extract the row indices from the result
    if modified_df.empty or df.empty:
        return modified_table, []

    # Create the 2D indices list
    pd_selected_indices = []
    for row_idx in selected_row_indices:
        for col in modified_df.columns:
            # 1. Ignore the indexing column
            # 2. Ignore new added columns
            if col != idx_tracking_col and col in column_indices:
                col_idx = column_indices[col]
                pd_selected_indices.append([row_idx, col_idx])

    # Create the 2D indices list
    sql_selected_indices = []
    for row_idx in selected_row_indices:
        for col in sql_columns:
            if col != idx_tracking_col:
                col_idx = column_indices[col]
                sql_selected_indices.append([row_idx, col_idx])

    # If using add column, reset the selected_indices to reparse
    if len(modified_columns) > len(original_columns):
        selected_indices = []
    else:
        selected_indices = intersection_of_2d_indices(pd_selected_indices, sql_selected_indices)

    # Check if the selected_indices is empty and if this step is last step in the plan: having verification_result or comparison_result column
    if len(selected_indices) == 0 and ('verification_result' in modified_df or 'comparison_result' in modified_df):
        if idx_tracking_col in df:
            # Drop the index column from the original DataFrame
            df.drop(columns=[idx_tracking_col], inplace=True)

        # Get number of rows and columns
        num_rows = df.shape[0]
        num_cols = df.shape[1]

        # Generate all 2D numerical indices
        all_indices = list(itertools.product(range(num_rows), range(num_cols)))
        selected_indices = [list(index) for index in all_indices]
        

    # Getting attribution for adding columns
    # Check if the selected_indices is empty and the new table has more columns than the original one
    if len(selected_indices) == 0 and len(modified_columns) > len(original_columns):
        selected_columns = extract_columns(sql, original_columns)
        selected_indices = []
        # Get number of rows and columns
        num_rows = df.shape[0]
        num_cols = df.shape[1]

        for row_idx in range(num_rows):
            for col in selected_columns:
                if col != idx_tracking_col:
                    col_idx = column_indices[col]
                    selected_indices.append([row_idx, col_idx])

    return modified_table, selected_indices


def transform_table_with_sqlalchemy(intermediate_table, sql, table_name):
    """
    Transform a table using SQL with SQLAlchemy.
    :param intermediate_table:
    :param sql:
    :param table_name:
    :return:
    """
    # Convert the intermediate table to a DataFrame
    df = table2df(intermediate_table)

    print('entry: ', df)
    column_indices = get_column_indices(df.columns)
    original_columns = df.columns.values.tolist()

    # Add an index column to track original row indices

    print('table before:\n', df)

    # Create an SQLAlchemy engine for an in-memory SQLite database
    engine = create_engine('sqlite:///:memory:')

    ################## PARSE from WHERE
    # TODO: Need to implement checking for HAVING as well
    print('SQL run:\n', sql)
    # sql_columns = parse_sql_columns_from_where(str(sql))
    sql_columns = extract_columns(sqlstr(sql), original_columns)

    print('SQL cols:\n', sql_columns)
    if '*' in sql_columns:
        sql_columns = column_indices
    ##############################

    # Convert DataFrame to SQL table
    with engine.begin() as conn:
        df.to_sql(table_name, conn, index=True, if_exists='replace', index_label=idx_tracking_col)

    # Use a session to handle the SQL transaction
    with Session(engine) as session:
        # Execute SQL query using SQLAlchemy within the session
        result_proxy = session.execute(sql)  # sql can be a string or a SQLAlchemy SQL expression

        # Fetch results into a DataFrame
        modified_df = pd.DataFrame(result_proxy.fetchall(), columns=result_proxy.keys())

        print('table after:\n', modified_df)

    if idx_tracking_col in modified_df:
        selected_row_indices = modified_df[idx_tracking_col].tolist()
    else:
        selected_row_indices = []

    if idx_tracking_col in modified_df:
        # Drop the index column from the result DataFrame
        modified_df.drop(columns=[idx_tracking_col], inplace=True)

    modified_columns = modified_df.columns.values.tolist()

    # Convert the DataFrame back to the format needed
    modified_table = df2table(modified_df)

    # Extract the row indices from the result
    if modified_df.empty or df.empty:
        return modified_table, []

    # Create the 2D indices list
    pd_selected_indices = []
    for row_idx in selected_row_indices:
        for col in modified_df.columns:
            # 1. Ignore the indexing column
            # 2. Ignore new added columns
            if col != idx_tracking_col and col in column_indices:
                col_idx = column_indices[col]
                pd_selected_indices.append([row_idx, col_idx])
    print('pd_selected_indices: ', pd_selected_indices)

    # Create the 2D indices list
    sql_selected_indices = []
    for row_idx in selected_row_indices:
        for col in sql_columns:
            if col != idx_tracking_col:
                col_idx = column_indices[col]
                sql_selected_indices.append([row_idx, col_idx])
    print('sql_selected_indices: ', sql_selected_indices)

    # If using add column, reset the selected_indices to reparse
    if len(modified_columns) > len(original_columns):
        selected_indices = []
    else:
        selected_indices =  intersection_of_2d_indices(pd_selected_indices, sql_selected_indices)

    # Check if the selected_indices is empty and if this step is last step in the plan: having verification_result or comparison_result column
    if len(selected_indices) == 0 and ('verification_result' in modified_df or 'comparison_result' in modified_df):
        if idx_tracking_col in df:
        # Drop the index column from the original DataFrame
            df.drop(columns=[idx_tracking_col], inplace=True)

        # Get number of rows and columns
        num_rows = df.shape[0]
        num_cols = df.shape[1]

        # Generate all 2D numerical indices
        all_indices = list(itertools.product(range(num_rows), range(num_cols)))
        selected_indices = [list(index) for index in all_indices]
        print('Final steps pd:')
        print(df)
        print(selected_indices)

    # Getting attribution for adding columns
    # Check if the selected_indices is empty  and the new table has more columns than the original one
    if len(selected_indices) == 0 and len(modified_columns) > len(original_columns):
        print('addd')
        print(len(modified_columns), len(original_columns))
        
        selected_columns = extract_columns(str(sql), original_columns)
        print('cols used for adding:', selected_columns)
        selected_indices = []
         # Get number of rows and columns
        num_rows = df.shape[0]
        num_cols = df.shape[1]

        for row_idx in range(num_rows):
            for col in selected_columns:
                if col != idx_tracking_col:
                    col_idx = column_indices[col]
                    selected_indices.append([row_idx, col_idx])

        print(df)
        print('adding sql:', str(sql))
        print(selected_indices)
        
    return modified_table, selected_indices


#################################################################################################### DATASET SAVING/LOADING FUNCTIONS ####################################################################################################
def save_dataset_to_pkl(dataset, filepath):
    """Save dataset to a pickle file."""
    with open(filepath, 'wb') as file:
        pickle.dump(dataset, file)


def load_dataset_from_pkl(filepath):
    """Load dataset from a pickle file."""
    with open(filepath, 'rb') as file:
        dataset = pickle.load(file)
    return dataset

##### LOGGING UTILITIES ########

def setup_logger(sample_id):
    """Set up the logger for each sample."""
    if config.test_dataset == 'TabFact':
        log_directory = config.tabfact_planning_log_path
    elif config.test_dataset == 'WikiTQ':
        log_directory = config.wikitq_planning_log_path
    else:
        raise ValueError("Invalid test dataset specified.")

    os.makedirs(log_directory, exist_ok=True)  # Ensure the directory exists
    log_filename = os.path.join(log_directory, f"log_{sample_id}.txt")

    # Create a custom logger
    logger = logging.getLogger(str(sample_id))
    logger.setLevel(logging.DEBUG)  # Set log level

    # Create handlers
    f_handler = logging.FileHandler(log_filename)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    # f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(message)s')
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(f_handler)

    return logger, log_filename

def wikitq_setup_logger(sample_id):
    """Set up the logger for each sample."""
    log_directory = config.wikitq_planning_log_path
    os.makedirs(log_directory, exist_ok=True)  # Ensure the directory exists
    log_filename = os.path.join(log_directory, f"log_{sample_id}.txt")

    # Create a custom logger
    logger = logging.getLogger(str(sample_id))
    logger.setLevel(logging.DEBUG)  # Set log level

    # Create handlers
    f_handler = logging.FileHandler(log_filename)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    # f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(message)s')
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(f_handler)

    return logger, log_filename

##### LOGGING UTILITIES ########

def combine_files_from_directory(directory, false_log_files):
    """
    Combine log files from a directory into a single file.
    :param directory:
    :param false_log_files:
    :return:
    """
    output_file = directory.split('/')[1] + '.txt'
    separator = '\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n\n'

    if false_log_files:
        file_list = [os.path.join(directory, fname) for fname in os.listdir(directory) if fname.endswith('.txt') and fname in false_log_files]
    else:
        file_list = [os.path.join(directory, fname) for fname in os.listdir(directory) if fname.endswith('.txt')]

    with open(output_file, 'w') as outfile:
        for i, fname in enumerate(file_list):
            with open(fname, 'r') as infile:
                contents = infile.read()
                outfile.write(contents)
                if i < len(file_list) - 1:  # Add separator if it's not the last file
                    outfile.write(separator)

############################################################################################################################################################################################################################
############################################################################################################################################################################################################################

# Process Chain-of-Table log
def process_COT_log(log):
    # Step 1: Collect all intermediate tables and their corresponding operations, ignoring the first entry
    intermediate_tables = [(entry['table_text'], entry['act_chain'], entry.get('group_sub_table')) for entry in log[1:]]
    # breakpoint()
    # Step 2: Get the final table before the first f_group_column call if it exists
    table_before_group = log[-1]['table_text'] if 'table_text' in log[-1] else None

    # Step 3: Create the initial mapping of cell values to their positions in the original table
    original_table = log[0]['input_table']
    intermediate_tables = [[original_table, None, None]] + intermediate_tables
    cell_position_map = {}
    for orig_i, orig_row in enumerate(original_table):
        for orig_j, orig_cell in enumerate(orig_row):
            cell_position_map[(orig_i, orig_j)] = orig_cell

    # Step 4: Process the act_chain to create relevant indices
    relevant_indices = []
    current_table = original_table
    selected_indices = set()
    for entry in log[1:]:
        previous_table = current_table
        action = entry['act_chain'][-1]
        # for action in entry['act_chain']:

        if action.startswith('f_select_row'):
            if action == 'f_select_row(*)':
                row_indices = range(1, len(current_table))
            else:
                # Extract the row indices from the action string and convert to zero-based index
                row_indices = [int(x.split()[1])+1 for x in action.split('(')[1].strip(')').split(', ')]
            selected_indices = {(i, j) for i in row_indices for j in range(len(current_table[0]))}

        elif action.startswith('f_select_column'):
            # Extract the column names from the action string
            column_names = [x.strip() for x in action.split('(')[1].strip(')').split(',')]
            column_indices = [current_table[0].index(col) for col in column_names if col in current_table[0]]
            selected_indices = {(i, j) for i in range(1, len(current_table)) for j in column_indices}

        elif action.startswith('f_group_column') or action.startswith('f_sort_column'):
            # Extract the selected column name from the action string
            selected_column = action.split('(')[1].strip(')').split(',')[0].strip()
            if selected_column in current_table[0]:
                selected_col_index = current_table[0].index(selected_column)
                selected_indices = {(i, selected_col_index) for i in range(1, len(current_table))}

        current_table = entry['table_text']
        
        # Map the current selected indices to the previous table
        current_selected_indices = set()
        for i, j in selected_indices:
            if i < len(previous_table) and j < len(previous_table[0]):
                current_selected_indices.add((i, j))
        # Append the current set of selected indices to relevant_indices
        # relevant_indices.append([])
        relevant_indices.append(current_selected_indices)

    # breakpoint()
    return table_before_group, selected_indices, intermediate_tables, relevant_indices


#######################################################################################
# WIKITQ util functions

def clean_element(element: str) -> str:
    """
    Cleans an element by removing leading and trailing quotes and extra whitespace.

    Args:
        element (str): The input string to clean.

    Returns:
        str: The cleaned element.
    """
    # Remove leading/trailing whitespace and double quotes
    element = element.strip()
    if element.startswith('"') and element.endswith('"'):
        return element[1:-1]
    return element.strip('"')


def merge_elements(elements):
    """
    Merges elements that are part of the same string, separated by a comma.
    :param elements:
    :return:
    """
    if len(elements) == 2 and elements[0].startswith('"') and elements[1].endswith('"'):
        return [clean_element(elements[0] + ', ' + elements[1])]
    return [clean_element(element) for element in elements]

def process_string(line):
    """
    Process a string line to extract elements.
    :param line:
    :return:
    """
    line = line.strip()
    # Check if the line is already a list (like ['2', '5', '12'])
    if line.startswith('[') and line.endswith(']'):
        try:
            # Safely evaluate the list string to an actual list
            line_list = ast.literal_eval(line)
            # Ensure all elements are strings and clean up any quotes
            line_list = merge_elements([str(elem) for elem in line_list])
            return line_list
        except (ValueError, SyntaxError):
            # Handle cases where the input is like [indenpendent]
            if line.count('[') == 1 and line.count(']') == 1:
                cleaned_line = line.strip('[]').strip()
                return [cleaned_line]
            return [clean_element(line)]
    else:
        # Handle lines that are not lists
        return [clean_element(line)]

def is_list_of_strings(variable):
    # Check if the variable is a list
    if isinstance(variable, list):
        # Check if all elements in the list are strings
        return all(isinstance(item, str) for item in variable)
    return False

#######################################################################################


# Visualize explanations for debugging or human study

def common_write_html_file(file, statement, answer, prediction, table_caption, intermediate_tables, highlighted_tables,
                           highlights):
    file.write('<html><head>\n')
    file.write('<style>\n')
    file.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
    file.write('h1 { text-align: center; }\n')
    file.write('.cot-title { color: blue; }\n')
    file.write('.pos-title { color: green; }\n')
    file.write('h2 { color: black; text-align: left; }\n')
    file.write('h3 { color: black; text-align: left; }\n')
    file.write('h4 { color: darkslategray; }\n')
    file.write('table { width: 100%; border-collapse: collapse; margin: 20px 0; }\n')
    file.write('table, th, td { border: 1px solid #ddd; padding: 8px; }\n')
    file.write('th { background-color: #f2f2f2; }\n')
    file.write('tr:nth-child(even) { background-color: #f9f9f9; }\n')
    file.write('.highlight { background-color: #ffffcc; }\n')
    file.write('.true { color: green; }\n')
    file.write('.false { color: red; }\n')
    file.write('.highlighted-cell { background-color: yellow; cursor: pointer; }\n')
    file.write(
        '.step-title { background-color: #f1f1f1; color: #444; padding: 10px; margin: 10px 0; font-size: 18px; border-left: 4px solid #888; }\n')
    file.write('.step { display: block; }\n')
    file.write('</style>\n')
    file.write('</head><body>\n')

    if VIS_PURPOSE == 'DEBUGGING':
        if XAI_METHOD == 'COT':
            file.write('<h1 class="cot-title">Chain-of-Table (Wang et al.)</h1>\n')
        elif XAI_METHOD == 'POS':
            file.write('<h1 class="pos-title">Plan-of-SQLs (Ours)</h1>\n')

    file.write('<hr>\n')
    if test_dataset == 'WikiTQ':
        file.write(f'<h3><span>Question:</span> {statement}</h3>\n')
    else:
        file.write(f'<h3><span>Statement:</span> {statement}</h3>\n')

    if XAI_METHOD == 'COT':
        answer = 'TRUE' if answer == 'True' else 'FALSE'

    if VIS_PURPOSE == 'DEBUGGING':
        file.write(f'<h3>Ground-truth:</span> {answer}</h3>\n')

    if test_dataset == 'WikiTQ':
        file.write(f'<h3>Input Table:</h3>\n')
    else:
        file.write(f'<h3>Input Table: {table_caption}</h3>\n')



    file.write('<div class="step">\n')
    return file


def common_generate_html_table(table):
    html = '<table>\n'
    for row in table:
        html += '<tr>\n'
        for cell in row:
            html += f'<td>{cell}</td>\n'
        html += '</tr>\n'
    html += '</table>\n'
    return html


if VIS_STYLE == 4:
    def highlight_cells(input_table, indices):
        highlighted_table = [row[:] for row in input_table]
        for i, j in indices:
            highlighted_table[i][
                j] = f'<span class="highlighted-cell" title="Used in transformation">{highlighted_table[i][j]}</span>'
        return highlighted_table


    def write_html_file(filename, original_table, statement, answer, prediction, intermediate_tables,
                        highlighted_tables, table_caption, highlights):
        with open(filename, 'w') as file:
            file = common_write_html_file(file, statement, answer, prediction, table_caption, intermediate_tables,
                                          highlighted_tables, highlights)

            first_step = intermediate_tables[1][1]
            step_title = f"Step 1: {first_step[-1]}" if XAI_METHOD == 'COT' else f"Step 1: {first_step.split(': ')[1].strip()}"
            step_id = "step-1"
            file.write(f'<div class="step">\n')
            file.write(f'<div class="step-title">{step_title}</div>\n')
            file.write(f'<div id="{step_id}" class="content">\n')
            file.write(common_generate_html_table(highlighted_tables[0]))
            file.write('</div>\n')

            file.write('<hr>\n')

            for idx, int_table in enumerate(intermediate_tables):
                intermediate_tables[idx] = list(intermediate_tables[idx])
                if idx == len(intermediate_tables) - 1:
                    intermediate_tables[idx][1] = None
                else:
                    intermediate_tables[idx][1] = intermediate_tables[idx + 1][1]

            intermediate_tables = intermediate_tables[1:]
            highlights = highlights[1:]
            highlighted_tables = highlighted_tables[1:]

            for idx, (table, actions, group_sub_table) in enumerate(intermediate_tables):
                if XAI_METHOD == 'COT' and actions:
                    actions = [action for action in actions if 'skip' not in action]

                if actions:
                    step_title = f"Step {idx + 2}: {actions[-1]}" if XAI_METHOD == 'COT' else f"Step {idx + 2}: {actions.split(': ')[1].strip()}"
                    step_id = f"step-{idx}"
                    file.write(f'<div class="step">\n')
                    file.write(f'<div class="step-title">{step_title}</div>\n')
                    file.write(f'<div id="{step_id}" class="content">\n')

                if XAI_METHOD == 'COT' and idx == len(intermediate_tables) - 1:
                    file.write('<h2>This Table is being processed by LLM for the final answer >>> </h2>\n')
                else:
                    if XAI_METHOD == 'COT' and 'f_group_column' not in actions[-1]:
                        file.write(common_generate_html_table(highlighted_tables[idx]))
                    elif XAI_METHOD == 'POS':
                        file.write(common_generate_html_table(highlighted_tables[idx]))

                if group_sub_table:
                    group_column, sub_table_data = group_sub_table
                    sub_table_header = [group_column, 'Count']
                    sub_table = [sub_table_header] + [[value, count] for value, count in sub_table_data]
                    file.write('<h4>Group Sub Table</h4>\n')
                    file.write(common_generate_html_table(sub_table))

                file.write('</div>\n')
                file.write('</div>\n')
                file.write('<hr>\n')

            # prediction = 'TRUE' if prediction == 'YES' else 'FALSE'
            prediction_class = 'true' if prediction == answer else 'false'

            if VIS_PURPOSE == 'DEBUGGING':
                file.write(f'<h3><span class="{prediction_class}">Prediction: {prediction} </span></h3>\n')
                file.write(f'<h3>Ground-truth:</span> {answer}</h3></div>\n')
            else:
                file.write(f'<h3>Prediction:</span> {prediction}</h3>\n')

            file.write('</body></html>\n')

        if VIS_PURPOSE != 'DEBUGGING':
            json_filename = f'{project_directory}/visualization/Tabular_LLMs_human_study_vis_{VIS_STYLE}_{XAI_METHOD}.json'
            entry = {
                'filename': os.path.basename(filename),
                'statement': statement,
                'answer': answer,
                'prediction': prediction,
                # 'intermediate_tables': intermediate_tables,
                # 'highlighted_tables': highlighted_tables,
                'table_caption': table_caption,
                'method': XAI_METHOD,
            }

            if os.path.exists(json_filename):
                with open(json_filename, 'r') as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            key = f'{XAI_METHOD}_' + os.path.basename(filename)
            data[key] = entry

            with open(json_filename, 'w') as json_file:
                json.dump(data, json_file, indent=4)

if VIS_STYLE == 5:
    def highlight_cells(input_table, indices):
        highlighted_table = [row[:] for row in input_table]
        for i, j in indices:
            if i == 0:
                continue
            highlighted_table[i][
                j] = f'<span class="highlighted-cell" title="Used in transformation">{highlighted_table[i][j]}</span>'
        return highlighted_table


    def collect_highlights_from_highlights(highlights, original_table_columns, intermediate_tables):
        highlighted_indices = set()
        original_table = intermediate_tables[0][0]

        num_cols = len(original_table_columns)
        num_rows = len(original_table)

        col_indices = set()
        if XAI_METHOD == 'POS':
            for i, highlight_set in enumerate(highlights[:-2]):
                for highlight in highlight_set:
                    existing_cols = intermediate_tables[i][0][0]
                    current_col = existing_cols[highlight[1]]
                    if current_col in original_table_columns:
                        col_indices.add(original_table_columns.index(current_col))

        if XAI_METHOD == 'COT':
            for i, highlight_set in enumerate(highlights[:-1]):
                cot_col_ids = set(highlight[1] for highlight in highlight_set)
                if len(cot_col_ids) == len(original_table_columns):
                    cot_row_hls = highlight_set
                    continue
                for highlight in highlight_set:
                    existing_cols = intermediate_tables[i][0][0]
                    current_col = existing_cols[highlight[1]]
                    if current_col in original_table_columns:
                        col_indices.add(original_table_columns.index(current_col))

        row_indices = set()
        for idx, (current_table, _, _) in enumerate(intermediate_tables[1:]):
            if len(current_table) < len(original_table):
                break
        row_indices.update(hl[0] for hl in highlights[idx])

        for i in row_indices:
            for j in range(num_cols):
                highlighted_indices.add((i, j))

        for i in range(num_rows):
            for j in col_indices:
                highlighted_indices.add((i, j))

        if XAI_METHOD == 'COT' and cot_row_hls:
            highlighted_indices.update(cot_row_hls)
        return highlighted_indices


    def write_html_file(filename, original_table, statement, answer, prediction, intermediate_tables,
                        highlighted_tables, table_caption, highlights):
        original_table_columns = original_table[0]
        highlighted_indices = collect_highlights_from_highlights(highlights, original_table_columns,
                                                                 intermediate_tables)
        highlighted_original_table = highlight_cells(original_table, highlighted_indices)

        with open(filename, 'w') as file:
            file = common_write_html_file(file, statement, answer, prediction, table_caption, intermediate_tables,
                                          highlighted_tables, highlights)

            file.write(common_generate_html_table(highlighted_original_table))
            file.write('</div>\n')

            file.write('<hr><hr><hr>\n')

            intermediate_tables = intermediate_tables[1:]
            highlighted_tables = highlighted_tables[1:]

            for idx, (table, actions, group_sub_table) in enumerate(intermediate_tables):
                if XAI_METHOD == 'COT' and actions:
                    actions = [action for action in actions if 'skip' not in action]

                step_title = f"Step {idx + 1}: {actions[-1]}" if XAI_METHOD == 'COT' else f"Step {idx + 1}: {actions.split(': ')[1].strip()}"
                step_id = f"step-{idx}"
                file.write(f'<div class="step">\n')
                file.write(f'<div class="step-title">{step_title}</div>\n')
                file.write(f'<div id="{step_id}" class="content">\n')

                file.write('</div>\n')
                file.write('</div>\n')
                file.write('<hr>\n')

            # prediction = 'TRUE' if prediction == 'YES' else 'FALSE'

            prediction_class = 'true' if prediction == answer else 'false'

            if VIS_PURPOSE == 'DEBUGGING':
                file.write(f'<h3><span class="{prediction_class}">Prediction: {prediction} </span></h3>\n')
                file.write(f'<h3>Ground-truth:</span> {answer}</h3></div>\n')
            else:
                file.write(f'<h3>Prediction:</span> {prediction}</h3>\n')

            file.write('</body></html>\n')

        if VIS_PURPOSE != 'DEBUGGING':
            json_filename = f'{project_directory}/visualization/Tabular_LLMs_human_study_vis_{VIS_STYLE}_{XAI_METHOD}.json'
            entry = {
                'filename': os.path.basename(filename),
                'statement': statement,
                'answer': answer,
                'prediction': prediction,
                # 'intermediate_tables': intermediate_tables,
                # 'highlighted_tables': highlighted_tables,
                'table_caption': table_caption,
                'method': XAI_METHOD,
            }

            if os.path.exists(json_filename):
                with open(json_filename, 'r') as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            key = f'{XAI_METHOD}_' + os.path.basename(filename)
            data[key] = entry

            with open(json_filename, 'w') as json_file:
                json.dump(data, json_file, indent=4)

if VIS_STYLE == 6:
    def highlight_cells(header_hl, input_table, indices, row_col_color='yellow', intersection_color='red'):
        highlighted_table = [row[:] for row in input_table]

        rows_to_highlight = set(i for i, _ in indices)
        cols_to_highlight = set(j for _, j in indices)

        for i, row in enumerate(highlighted_table):
            if i == 0:
                continue
            for j, cell in enumerate(row):
                if [i, j] in indices:
                    highlighted_table[i][
                        j] = f'<span class="highlighted-cell" title="Used in transformation" style="background-color:{intersection_color};">{highlighted_table[i][j]}</span>'
                elif (i in rows_to_highlight or j in cols_to_highlight) and [i, j] not in indices:
                    highlighted_table[i][
                        j] = f'<span class="highlighted-cell" title="Used in transformation" style="background-color:{row_col_color};">{highlighted_table[i][j]}</span>'
        return highlighted_table


    def write_html_file(filename, original_table, statement, answer, prediction, intermediate_tables,
                        highlighted_tables, table_caption, highlights):
        with open(filename, 'w') as file:
            file = common_write_html_file(file, statement, answer, prediction, table_caption, intermediate_tables,
                                          highlighted_tables, highlights)

            # Handle the NO_XAI method
            if XAI_METHOD == 'NO_XAI':
                file.write(common_generate_html_table(original_table))
                file.write('</body></html>\n')
            else:
                first_step = intermediate_tables[1][1]
                step_title = f"Step 1: {first_step[-1]}" if XAI_METHOD == 'COT' else f"Step 1: {first_step.split(': ')[1].strip()}"
                step_id = "step-1"
                file.write(f'<div class="step">\n')
                file.write(f'<div class="step-title">{step_title}</div>\n')
                file.write(f'<div id="{step_id}" class="content">\n')

                if XAI_METHOD == 'COT':
                    file.write(common_generate_html_table(highlighted_tables[0]))
                else:
                    file.write(common_generate_html_table(
                        highlight_cells(True, original_table, highlights[0], 'yellow', '#90EE90')))

                file.write('</div>\n')
                file.write('<hr>\n')

                for idx, int_table in enumerate(intermediate_tables):
                    intermediate_tables[idx] = list(intermediate_tables[idx])
                    if idx == len(intermediate_tables) - 1:
                        intermediate_tables[idx][1] = None
                    else:
                        intermediate_tables[idx][1] = intermediate_tables[idx + 1][1]

                intermediate_tables = intermediate_tables[1:]
                highlights = highlights[1:]
                highlighted_tables = highlighted_tables[1:]

                for idx, (table, actions, group_sub_table) in enumerate(intermediate_tables):
                    if XAI_METHOD == 'COT' and actions:
                        actions = [action for action in actions if 'skip' not in action]

                    if actions:
                        step_title = f"Step {idx + 2}: {actions[-1]}" if XAI_METHOD == 'COT' else f"Step {idx + 2}: {actions.split(': ')[1].strip()}"
                        step_id = f"step-{idx}"
                        file.write(f'<div class="step">\n')
                        file.write(f'<div class="step-title">{step_title}</div>\n')
                        file.write(f'<div id="{step_id}" class="content">\n')

                    if XAI_METHOD == 'COT' and idx == len(intermediate_tables) - 1:
                        file.write('<h2>Prompting LLM for the final answer... >>> </h2>\n')
                    else:
                        if XAI_METHOD == 'COT' and 'f_group_column' not in actions[-1]:
                            file.write(common_generate_html_table(highlighted_tables[idx]))
                        elif XAI_METHOD == 'POS':
                            if idx < len(intermediate_tables) - 2:
                                file.write(common_generate_html_table(
                                    highlight_cells(True, table, highlights[idx], 'yellow', '#90EE90')))
                            elif idx == len(intermediate_tables) - 2:
                                file.write(common_generate_html_table(
                                    highlight_cells(False, table, highlights[idx], '#90EE90', '#90EE90')))
                            elif idx == len(intermediate_tables) - 1:
                                file.write(common_generate_html_table(highlighted_tables[idx]))
                            else:
                                file.write(common_generate_html_table(highlighted_tables[idx]))

                    if group_sub_table:
                        group_column, sub_table_data = group_sub_table
                        sub_table_header = [group_column, 'Count']
                        sub_table = [sub_table_header] + [[value, count] for value, count in sub_table_data]
                        file.write('<h4>Group Sub Table</h4>\n')
                        file.write(common_generate_html_table(sub_table))

                    file.write('</div>\n')
                    file.write('</div>\n')
                    file.write('<hr>\n')

            prediction_class = 'true' if prediction == answer else 'false'

            if VIS_PURPOSE == 'DEBUGGING':
                file.write(f'<h3><span class="{prediction_class}">Prediction: {prediction} </span></h3>\n')
                file.write(f'<h3>Ground-truth:</span> {answer}</h3></div>\n')
            else:
                file.write(f'<h3>Prediction:</span> {prediction.upper()}</h3>\n')

            file.write('</body></html>\n')

        if VIS_PURPOSE != 'DEBUGGING':
            json_filename = f'{project_directory}/visualization/Tabular_LLMs_human_study_vis_{VIS_STYLE}_{XAI_METHOD}.json'
            entry = {
                'filename': os.path.basename(filename),
                'statement': statement,
                'answer': answer,
                'prediction': prediction,
                # 'intermediate_tables': intermediate_tables,
                # 'highlighted_tables': highlighted_tables,
                'table_caption': table_caption,
                'method': XAI_METHOD,
            }

            if os.path.exists(json_filename):
                with open(json_filename, 'r') as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            key = f'{XAI_METHOD}_' + os.path.basename(filename)
            data[key] = entry

            with open(json_filename, 'w') as json_file:
                json.dump(data, json_file, indent=4)


    def wikitq_write_html_file(filename, original_table, statement, answer, prediction, intermediate_tables,
                        highlighted_tables, table_caption, highlights):
        with open(filename, 'w') as file:
            file = common_write_html_file(file, statement, answer, prediction, table_caption, intermediate_tables,
                                          highlighted_tables, highlights)

            # Handle the NO_XAI method
            if XAI_METHOD == 'NO_XAI':
                file.write(common_generate_html_table(original_table))
                file.write('</body></html>\n')
            else:
                first_step = intermediate_tables[1][1]
                step_title = f"Step 1: {first_step[-1]}" if XAI_METHOD == 'COT' else f"Step 1: {first_step.split(': ')[1].strip()}"
                step_id = "step-1"
                file.write(f'<div class="step">\n')
                file.write(f'<div class="step-title">{step_title}</div>\n')
                file.write(f'<div id="{step_id}" class="content">\n')

                if XAI_METHOD == 'COT':
                    file.write(common_generate_html_table(highlighted_tables[0]))
                else:
                    file.write(common_generate_html_table(
                        highlight_cells(True, original_table, highlights[0], 'yellow', '#90EE90')))

                file.write('</div>\n')
                file.write('<hr>\n')

                for idx, int_table in enumerate(intermediate_tables):
                    intermediate_tables[idx] = list(intermediate_tables[idx])
                    if idx == len(intermediate_tables) - 1:
                        intermediate_tables[idx][1] = None
                    else:
                        intermediate_tables[idx][1] = intermediate_tables[idx + 1][1]

                intermediate_tables = intermediate_tables[1:]
                highlights = highlights[1:]
                highlighted_tables = highlighted_tables[1:]

                for idx, (table, actions, group_sub_table) in enumerate(intermediate_tables):
                    if XAI_METHOD == 'COT' and actions:
                        actions = [action for action in actions if 'skip' not in action]

                    if actions:
                        step_title = f"Step {idx + 2}: {actions[-1]}" if XAI_METHOD == 'COT' else f"Step {idx + 2}: {actions.split(': ')[1].strip()}"
                        step_id = f"step-{idx}"
                        file.write(f'<div class="step">\n')
                        file.write(f'<div class="step-title">{step_title}</div>\n')
                        file.write(f'<div id="{step_id}" class="content">\n')

                    if XAI_METHOD == 'COT' and idx == len(intermediate_tables) - 1:
                        file.write('<h2>Prompting LLM for the final answer... >>> </h2>\n')
                    else:
                        # Always display the table, regardless of conditions
                        if XAI_METHOD == 'POS':
                            file.write(common_generate_html_table(
                                highlight_cells(True, table, highlights[idx], 'yellow', '#90EE90')))
                        else:
                            file.write(common_generate_html_table(highlighted_tables[idx]))

                    if group_sub_table:
                        group_column, sub_table_data = group_sub_table
                        sub_table_header = [group_column, 'Count']
                        sub_table = [sub_table_header] + [[value, count] for value, count in sub_table_data]
                        file.write('<h4>Group Sub Table</h4>\n')
                        file.write(common_generate_html_table(sub_table))

                    file.write('</div>\n')
                    file.write('</div>\n')
                    file.write('<hr>\n')

            # dummy value to define color for debugging
            prediction_class = 'true'

            if VIS_PURPOSE == 'DEBUGGING':
                file.write(f'<h3><span class="{prediction_class}">Prediction: {prediction} </span></h3>\n')
                file.write(f'<h3>Ground-truth:</span> {answer}</h3></div>\n')
            else:
                # import ast
                # prediction = ast.literal_eval(prediction)
                # if len(prediction[0]) > 1:
                #     file.write(f'<h3>Prediction:</span> {prediction[0]}</h3>\n')
                # else:
                file.write(f'<h3>Prediction:</span> {prediction}</h3>\n')


            file.write('</body></html>\n')

        if VIS_PURPOSE != 'DEBUGGING':
            json_filename = f'{project_directory}/visualization/Tabular_LLMs_human_study_vis_{VIS_STYLE}_{XAI_METHOD}.json'
            entry = {
                'filename': os.path.basename(filename),
                'statement': statement,
                'answer': answer,
                'prediction': prediction,
                # 'intermediate_tables': intermediate_tables,
                # 'highlighted_tables': highlighted_tables,
                'table_caption': table_caption,
                'method': XAI_METHOD,
            }

            if os.path.exists(json_filename):
                with open(json_filename, 'r') as json_file:
                    data = json.load(json_file)
            else:
                data = {}

            key = f'{XAI_METHOD}_' + os.path.basename(filename)
            data[key] = entry


def generate_html_table(table):
    html = '<table>\n'
    for row in table:
        html += '<tr>\n'
        for cell in row:
            html += f'<td>{cell}</td>\n'
        html += '</tr>\n'
    html += '</table>\n'
    return html

#######################################################

def count_table_tokens(entry):
    table_text = entry['table_text']
    token_count = 0

    for row in table_text:
        for cell in row:
            # Split the cell content into tokens
            tokens = str(cell).split()
            token_count += len(tokens)

    return token_count

def get_operation_name(string):
    # f_xxxx(...)
    res = re.findall(r"f_(.*?)\(.*\)", string)[0]
    return res