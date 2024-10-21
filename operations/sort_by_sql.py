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

sort_column_demo_sql = """To determine if a statement is true or false, we can sort the values in a column to understand 
the order of the items, in ascending or descending order.

The columns suitable for sorting include:
1. Numerical: Numbers that can be sorted.
2. DateType: Dates that can be arranged chronologically.
3. String: Text that can be alphabetically sorted.


/*
col : position | club | played | points | wins | draws | losses | goals_for | goals_against | goal_difference
row 1 : 1 | Malaga CF | 42 | 79 | 22 | 13 | 7 | 72 | 47 | +25
row 2 : 2 | CP Merida | 42 | 59 | 15 | 14 | 13 | 48 | 41 | +7
row 3 : 3 | CD Numancia | 42 | 73 | 21 | 10 | 11 | 68 | 40 | +28
Statement: CD Numancia placed in the last position.
The existing columns are: position, club, played, points, wins, draws, losses, goals_for, goals_against, goal_difference.
*/
Statement: CD Numancia placed in the last position.
The existing columns are: position, club, played, points, wins, draws, losses, goals_for, goals_against, goal_difference.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY position DESC
LIMIT 1;
-- This SQL query sorts the position column using the descending order because the fist position has the smallest value (here  is 1), to easily see the team in the last position. The team having the largest value for position will be placed last.
```

/*
col : position | club | played | points | wins | draws | losses | goals_for | goals_against | goal_difference
row 1 : 1 | Malaga CF | 42 | 79 | 22 | 13 | 7 | 72 | 47 | +25
row 2 : 2 | CP Merida | 42 | 59 | 15 | 14 | 13 | 48 | 41 | +7
row 3 : 3 | CD Numancia | 42 | 73 | 21 | 10 | 11 | 68 | 40 | +28
*/
Statement: CD Numancia placed in the second last position.
The existing columns are: position, club, played, points, wins, draws, losses, goals_for, goals_against, goal_difference.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY position DESC
LIMIT 2;
-- This SQL query sorts the position column using the descending order because the fist position has the smallest value (here  is 1), to easily see the team in the last position. The team having the largest value for position will be placed last.
```

/*
col : year | team | games | combined_tackles | tackles | assisted_tackles
row 1 : 2004 | Hou | 16 | 63 | 51 | 12
row 2 : 2005 | Hou | 12 | 35 | 24 | 11
row 3 : 2006 | Hou | 15 | 26 | 19 | 7
*/
Statement: In 2006 Babin had the least amount of tackles.
The existing columns are: year, team, games, combined_tackles, tackles, assisted_tackles.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY tackles ASC
LIMIT 1;
-- This SQL query sorts the tackles column in asscending order to find the player with the least tackles.
```

/*
col : year | team | games | combined_tackles | tackles | assisted_tackles
row 1 : 2004 | Hou | 16 | 63 | 51 | 12
row 2 : 2005 | Hou | 12 | 35 | 24 | 11
row 3 : 2006 | Hou | 15 | 26 | 19 | 7
*/
Statement: In 2005 Babin had the most amount of tackles.
The existing columns are: year, team, games, combined_tackles, tackles, assisted_tackles.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY tackles DESC
LIMIT 1;
-- This SQL query sorts the tackles column in descending order to find the player with the most tackles.
```

/*
col : year | team | games | score
row 1 : 2004 | Hou | 16 | 34
row 2 : 2005 | Hou | 12 | 16
row 3 : 2006 | Hou | 15 | 120
*/
Statement: In 2006 Babin had the best score.
The existing columns are: year, team, games, score.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY score DESC
LIMIT 1;
-- This SQL query sorts the score column in descending order to find the player with the best score.
```

/*
col : event | start_date | location
row 1 : Conference | 2024-06-01 | New York
row 2 : Workshop | 2023-05-15 | San Francisco
row 3 : Seminar | 2024-01-20 | Chicago
*/
Statement: The earliest event is the workshop.
The existing columns are: event, start_date, location.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY start_date ASC
LIMIT 1;
-- This SQL query sorts the start_date column in ascending order to identify the earliest event.
```

/*
col : event | start_date | location
row 1 : Conference | 2024-06-01 | New York
row 2 : Workshop | 2023-05-15 | San Francisco
row 3 : Seminar | 2024-01-20 | Chicago
*/
Statement: The latest event is the seminar.
The existing columns are: event, start_date, location.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY start_date DESC
LIMIT 1;
-- This SQL query sorts the start_date column in descending order to identify the latest event.
```
"""

def only_keep_num_and_first_dot(s):
    # print('Here coming to sorting function!!!')
    # print(s)

    if not isinstance(s, str):
        s = str(s)

    if s.strip() and s.strip()[0] == "-":
        minus = True
    else:
        minus = False
    ns = ""
    dot = False
    for c in s:
        if c in "0123456789":
            ns += c
        if c == ".":
            if dot == False:
                ns += c
                dot = True
    if ns == ".":
        return ""
    if ns == "":
        return ""
    if minus:
        ns = "-" + ns
    return ns


def sort_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
    table_str = table2string(
        table_text, caption=table_caption, num_rows=num_rows
    ).strip()

    table_name = 'table_sql'
    prompt = f"Given this table '{table_name}':\n"
    prompt += "/*\n" + table_str + "\n*/\n"
    prompt += "Statement: " + statement + "\n"
    
    # print('Table into sorting column prompting:', prompt)

    prompt += "\nConstraints for your SQL:"

    prompt += "\n1.The columns used in your SQL must match "

    if len(table_text[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in table_text[0])
    else:
        existing_cols = f"{table_text[0][0]}"
    prompt += f"{existing_cols}"
    
    prompt += "\n2.Your SQL command must be executable by python sqlite3."
    prompt += "\n3.If possible, you should use ORDER BY only."
    # prompt += "\n4.If using SELECT COUNT(*), you must use AS to name the new column.\n"
    prompt += f"\n4.{syntax_instr1}"
    prompt += "\n5.If using FROM, the table to be selected must be table_sql."
    prompt += "\n6.You must look at the cell contents in table_sql to avoid problems of exact matchings in SQL."
    
    prompt += "\nSQL is:\n"

    return prompt

def sort_column_func_sql(
    sample, table_info, llm, llm_options=None, debug=False, skip_op=[]
):
    op_name = 'sort_column' 
    table_text = table_info["table_text"]
    statement = sample["statement"]

    # Setup LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt

    prompt = "" + sort_column_demo_sql.rstrip() + "\n\n"
    prompt += sort_column_build_prompt(table_text, statement, num_rows=3)

    # Generate responses
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    # Sort responses by confidence scores (higher to lower)
    responses.sort(key=lambda x: x[1], reverse=True)

    headers = table_text[0]
    rows = table_text[1:]
    table_data = pd.DataFrame(rows, columns=headers)
    is_sql_executable = False
    processed_table = pd.DataFrame()
    
    # print('Sorting col options:', len(responses))

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
                print("SQL execution error sort_column:", e)
                print(f"Attempted SQL command: {sql_command}")
        else:
            print("No SQL command found in the response.")

    # Handling the case where no SQL is executable
    if not is_sql_executable:
        print("Sort_column: Failed to execute any SQL command.")
        sort_param_and_conf_list = [(table_data, 'NOT FOUND: LLM cannot generate any error-free SQL', 1.0)]

    # If any SQL is executed successfully
    else:
        sort_param_and_conf_list = [(processed_table, sql_command, score)]

    operation = {
        "operation_name": "sort_column",
        "parameter_and_conf": sort_param_and_conf_list,
    }

    # Append the operation to the processing chain and return the updated sample
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy, is_sql_executable, op_name



def sort_column_act_sql(
    table_info, operation, strategy="top", filter="Only Numerical", skip_op=[]
):

    table_info["act_chain"].append(f"f_sort_column()")
    return table_info
