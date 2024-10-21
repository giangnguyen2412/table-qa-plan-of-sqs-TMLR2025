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


import copy
import re
import numpy as np
from utils.helper import *
from utils.verifier import *

from third_party.select_column_row_prompts.select_column_row_prompts import select_row_sql_demo


def select_row_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
    table_str = table2string(table_text, caption=table_caption).strip()

    table_name = 'table_sql'
    prompt = f"Given this table '{table_name}':\n"
    prompt += "/*\n" + table_str + "\n*/\n"
    question = statement
    prompt += "Statement : " + question + "\n"
    
    # print('Table into selecting row prompting:', prompt)

    prompt += "\nConstraints for your SQL:"

    prompt += "\n1.The columns used in your SQL must match "

    if len(table_text[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in table_text[0])
    else:
        existing_cols = f"{table_text[0][0]}"
    prompt += f"{existing_cols}"

    prompt += "\n2.You must NOT use SORT, GROUP, or SELECT COUNT(*)!!!"
    prompt += f"\n3.{syntax_instr1}"
    prompt += "\n4.Your SQL command must be executable by python sqlite3."
    prompt += "\n5.If using FROM, the table to be selected must be table_sql."
    prompt += "\n6.You must look at the cell contents in table_sql to avoid problems of exact matchings in SQL."

    prompt += "\nSQL is:\n"
    return prompt


def select_row_func_sql(sample, table_info, llm, llm_options=None, debug=False):
    op_name = 'select_row'
    table_text = table_info["table_text"]
    table_caption = sample["table_caption"]
    statement = sample["statement"]

    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt
    
    prompt = "" + select_row_sql_demo.rstrip() + "\n\n"
    prompt += select_row_build_prompt(table_text, statement, table_caption)

    # Generate responses
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    # Sort responses by confidence scores (higher to lower)
    responses.sort(key=lambda x: x[1], reverse=True)

    headers = table_text[0]
    rows = table_text[1:]
    table_data = pd.DataFrame(rows, columns=headers)
    is_sql_executable = False
    processed_table = pd.DataFrame()
    
    # print('Selecting row options:', len(responses))

    for response, score in responses:
        if debug:
            print(f'Attempting SQL command with score {score}:')
            print(response)

        # Extract the SQL command
        sql_command = extract_sql_code(response)
                
        if sql_command is not None:
            # sql_command = sql_match.group(1)
        
            try:
                table_name = 'table_sql'  # Assuming fixed table name
                processed_table = apply_sql_to_df(table_data, sql_command, table_name)                
                if VERIFICATION is True:
                    verification, prompt = verify_intermediate_step(sql_command, sample, table_info, llm, llm_options=None, debug=False)
                    if verification is True:
                        pass
                    else:
                        # print(f'Cannot pass LLM verification: {prompt}')
                        continue
                    
                is_sql_executable = True
                
                print(f'Successfully executed SQL: {sql_command}')
                break
            except Exception as e:
                print(f"SQL execution error: {e}")
                print(f"Attempted SQL command: {sql_command}")
        else:
            print("SELECT_row: No SQL command found in the response.")

    # Handling the case where no SQL is executable
    if not is_sql_executable:
        print("Failed to execute any SQL command.")
        # select_row_rank = [()]
        select_row_rank = [(table_data, 'NOT FOUND: LLM cannot generate any error-free SQL', 1.0)]

    # If any SQL is executed successfully
    else:
        select_row_rank = [(processed_table, sql_command, score)]

    operation = {
        "operation_name": "select_row",
        "parameter_and_conf": select_row_rank,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy, is_sql_executable, op_name


def select_row_act_sql(table_info, operation, union_num=2, skip_op=[]):
    table_info = copy.deepcopy(table_info)

    if "select_row" in skip_op:
        failure_table_info = copy.deepcopy(table_info)
        failure_table_info["act_chain"].append("skip f_select_row()")
        return failure_table_info

    real_selected_rows = []

    # print(operation["parameter_and_conf"])
    processed_table = operation["parameter_and_conf"][0][0]

    new_headers = processed_table.columns.tolist()
    new_rows = processed_table.values.tolist()
    new_table = [new_headers] + new_rows

    table_info["table_text"] = new_table

    table_info["act_chain"].append(f"f_select_row()")

    table_info['_real_select_rows'] = f"f_select_row()"
    return table_info
