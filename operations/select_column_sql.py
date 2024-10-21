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
import copy
import re
import numpy as np
# from utils.helper import table2df, NoIndent, MyEncoder
from utils.helper import *
from utils.verifier import *

from third_party.select_column_row_prompts.select_column_row_prompts import select_column_demo_sql


def twoD_list_transpose(arr, keep_num_rows=3):
    arr = arr[: keep_num_rows + 1] if keep_num_rows + 1 <= len(arr) else arr
    return [[arr[i][j] for i in range(len(arr))] for j in range(len(arr[0]))]


def select_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
#     df = table2df(table_text, num_rows=num_rows)
#     tmp = df.values.tolist()
#     list_table = [list(df.columns)] + tmp
#     list_table = twoD_list_transpose(list_table, len(list_table))
#     if table_caption is not None:
#         dic = {
#             "table_caption": table_caption,
#             "columns": NoIndent(list(df.columns)),
#             "table_column_priority": [NoIndent(i) for i in list_table],
#         }
#     else:
#         dic = {
#             "columns": NoIndent(list(df.columns)),
#             "table_column_priority": [NoIndent(i) for i in list_table],
#         }
#     linear_dic = json.dumps(
#         dic, cls=MyEncoder, ensure_ascii=False, sort_keys=False, indent=2
#     )

#     table_name = 'table_sql'
#     prompt = f"Given this table '{table_name}':\n"
#     prompt += "/*\ntable = " + linear_dic + "\n*/\n"
#     prompt += "Statement : " + statement + ".\n"
    
    
    num_rows = 3
    table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)

    table_name = 'table_sql'
    prompt = f"Given this table '{table_name}':\n"
    
    prompt += "/*\n" + table_str + "\n*/\n"
    prompt += "Statement: " + statement + "\n"
    
    # print('Table into selecting column prompting:', prompt)

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


def select_column_func_sql(sample, table_info, llm, llm_options, debug=False, num_rows=100):
    op_name = 'select_column'
    table_text = table_info["table_text"]
    table_caption = sample["table_caption"]
    statement = sample["statement"]
    
    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt

    prompt = "" + select_column_demo_sql.rstrip() + "\n\n"
    prompt += select_column_build_prompt(
        table_text, statement, table_caption, num_rows=num_rows
    )

    print('prompt to select col:', prompt)

    # Generate responses
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    print('response to select col:', responses)


    # Sort responses by confidence scores (higher to lower)
    responses.sort(key=lambda x: x[1], reverse=True)

    headers = table_text[0]
    rows = table_text[1:]
    table_data = pd.DataFrame(rows, columns=headers)
    is_sql_executable = False
    processed_table = pd.DataFrame()
    
    # print('Selecting col options:', len(responses))
    
    for response, score in responses:
        if debug:
            print(f'Attempting SQL command with score {score}:')
            print(response)

        # Extract the SQL command
        sql_command = extract_sql_code(response)
                
        if sql_command is not None:
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
            print("No SQL command found in the response.")

    # Handling the case where no SQL is executable
    if not is_sql_executable:
        print("SELECT_column: Failed to execute any SQL command.")
        # select_col_rank = [()]
        select_col_rank = [(table_data, 'NOT FOUND: LLM cannot generate any error-free SQL', 1.0)]

    # If any SQL is executed successfully
    else:
        select_col_rank = [(processed_table, sql_command, score)]

    operation = {
        "operation_name": "select_column",
        "parameter_and_conf": select_col_rank,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy, is_sql_executable, op_name


def select_column_act_sql(table_info, operation, union_num=2, skip_op=[]):
    table_info = copy.deepcopy(table_info)

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_select_column()")

    if "select_column" in skip_op:
        return failure_table_info

    
    real_selected_columns = []

    processed_table = operation["parameter_and_conf"][0][0]

    new_headers = processed_table.columns.tolist()
    new_rows = processed_table.values.tolist()
    new_table = [new_headers] + new_rows

    table_info["table_text"] = new_table
    table_info["act_chain"].append(
        f"f_select_column({', '.join(real_selected_columns)})"
    )

    return table_info
