# # Copyright 2024 The Chain-of-Table authors
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


import re
import copy
import numpy as np
import pandas as pd
from utils.helper import *
from io import StringIO
from utils.verifier import *


add_column_demo = """To tell the statement is true or false, we can add a new column to the table.

The added columns should have these data types:
1. Numerical: the numerical strings that can be used in sort, sum
2. Datetype: the strings that describe a date, such as year, month, day
3. String: other strings

### Example 1: 
/*
col : week | when | kickoff | opponent | results; final_score | results; team_record | game_site | attendance
row 1 : 1 | saturday, 2024-04-13 | 7:00 p.m. | at rhein fire | w 27–21 | 1–0 | rheinstadion | 32,092
row 2 : 2 | saturday, 2024-04-20 | 7:00 p.m. | london monarchs | w 37–3 | 2–0 | waldstadion | 34,186
row 3 : 3 | sunday, 2024-04-28 | 6:00 p.m. | at barcelona dragons | w 33–29 | 3–0 | estadi olímpic de montjuïc | 17,503
*/

Statement: april 20 is the date of the competition with highest attendance.
The existing columns are: week, when, kickoff, opponent, results; final_score, results; team_record, game_site, attendance.

SQL is: 

```sql
SELECT *,
       CAST(REPLACE(attendance, ',', '') AS INT) AS attendance_number
FROM table_sql;
-- This SQL query will select all columns from the table and create a new column attendance_number where the attendance values are converted from strings to integers for numerical operations.
```

Explanation: To tell this statement is true or false, we need to know the attendance number of each competition. 
We extract the value from column attendance and create a different column attendance_number for each row. The datatype is numerical.
Therefore, the answer is: f_add_column(attendance_number). The value: 32092 | 34186 | 17503

### Example 2: 
/*
col : rank | lane | player | time
row 1 :  | 5 | olga tereshkova (kaz) | 51.86
row 2 :  | 6 | manjeet kaur (ind) | 52.17
row 3 :  | 3 | asami tanno (jpn) | 53.04
*/
Statement: there are one athlete from japan.
The existing columns are: rank, lane, player, time.

SQL is: 

```sql
SELECT *,
       substr(player, instr(player, '(') + 1, instr(player, ')') - instr(player, '(') - 1) AS country_of_athletes
FROM table_sql;
-- This SQL query extracts the substring between parentheses in the 'player' column to create a new column country_of_athletes.
```

Explanation: To tell this statement is true or false, we need to know the country of each athlete. We extract the value from column player and create a different column country_of_athletes for each row. The datatype is string.
The value: kaz | ind | jpn

### Example 3: 
/*
col : year | competition | venue | position | notes
row 1 : 1991 | european junior championships | thessaloniki, greece | 10th | 4.90 m
row 2 : 1992 | world junior championships | seoul, south korea | 1st | 5.45 m
row 3 : 1996 | european indoor championships | stockholm, sweden | 14th (q) | 5.45 m
*/
Statement: laurens place 1st in 1991.
The existing columns are: year, competition, venue, position, notes.

SQL is:

```sql
SELECT *,
       CAST(substr(position, 1, instr(position || ' ', ' ') - 1) AS INT) AS placing_result
FROM table_sql;
-- This SQL query extracts the numerical placement from the position column to create a new column placing_result for sorting or comparison.
```

Explanation: To tell this statement is true or false, we need to know the place of each competition. We extract the value from column position and create a different column placing_result for each row. The datatype is numerical.
The value: 10 | 1 | 14

### Example 4: 
/*
col : iso/iec_standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2008) | 7
*/
Statement: the standards published three times in 2008.
The existing columns are: iso/iec_standard, title, status, description, wg.

SQL is:

```sql
SELECT *,
       CAST(SUBSTR(status, INSTR(status, '(') + 1, 4) AS INT) AS year_of_standard
FROM table_sql;
-- This SQL query extracts the four rightmost characters of the status column as the publication year to create a new year_of_standard column.
```

Explanation: To tell this statement is true or false, we need to know the year of each standard. We extract the value from column status and create a different column year_of_standard for each row. The datatype is datetype.
The value: 2005 | 2008 | 2008

### Example 5: 
/*
table caption : 1984 u.s. open (golf)
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | - 4
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | -- 3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | - 2
*/
Statement: david canipe of united states has 138 score
The existing columns are: place, player, country, score, to_par.

SQL is:

```sql
SELECT *,
       CAST(substr(score, instr(score, '=') + 2) AS INT) AS score_value
FROM table_sql;
-- This SQL query extracts the final score after the '=' sign from the score column to create a new score_value column.
```

Explanation: To tell this statement is true or false, we need to know the score values of each player. We extract the value from column score and create a different column score_value for each row. The datatype is numerical.
The value: 136 | 137 | 138

### Example 6: 
/*
col : code | county | former_province | area_km2 | population | capital
row 1 : 1 | mombasa | coast | 212.5 | 939,370 | mombasa (city)
row 2 : 2 | kwale | coast | 8,270.3 | 649,931 | kwale
row 3 : 3 | kilifi | coast | 12,245.9 | 1,109,735 | kilifi
*/
Statement: kwale has a population in 2009 higher than 500,000.
The existing columns are: code, county, former_province, area_km2, population, capital.

SQL is:

```sql
SELECT *,
       CAST(REPLACE(population, ',', '') AS INT) AS population_count
FROM table_sql;
-- This SQL query removes commas and converts the population column to an integer to create a new population_count column.
```

Explanation: To tell this statement is true or false, we need to know the population of each county. We extract the value from column population and create a different column population_count for each row. The datatype is numerical.
The value: 939370 | 649311 | 1109735
"""


def add_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
    table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)

    table_name = 'table_sql'
    prompt = f"Given this table '{table_name}':\n"
    
    prompt += "/*\n" + table_str + "\n*/\n"
    prompt += "Statement: " + statement + "\n"
    
    # print('Table into adding column prompting:', prompt)
    

    prompt += "\nConstraints for your SQL:"

    prompt += "\n1.The columns used in your SQL must match "

    if len(table_text[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in table_text[0])
    else:
        existing_cols = f"{table_text[0][0]}"    
    prompt += f"{existing_cols}"

    prompt += f"\n2.{syntax_instr1} The new column should be different than {existing_cols}"
    prompt += "\n3.You are allowed to use SELECT COUNT(*) once to create only one column in your SQL."
    # prompt += "\n2.You are NOT allowed to use these operations: COUNT, SUM, AVG, MAX, MIN!\n"
    prompt += "\n4.Your SQL command must be executable by python sqlite3."
    prompt += "\n5.If using FROM, the table to be selected must be table_sql."
    prompt += "\n6.You must look at the cell contents in table_sql to avoid problems of exact matchings in SQL."

    prompt += "\nSQL is:\n"
    return prompt


def add_column_func_sql(
    sample, table_info, llm, llm_options=None, debug=False, skip_op=[], strategy="top"
):
    op_name = 'add_column'
    table_text = table_info["table_text"]
    table_caption = sample["table_caption"]
    cleaned_statement = sample["cleaned_statement"]
    cleaned_statement = re.sub(r"\d+", "_", cleaned_statement)

    prompt = "" + add_column_demo.rstrip() + "\n\n"
    prompt += add_column_build_prompt(
        table_text, cleaned_statement, table_caption=table_caption, num_rows=3
    )
    
    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt

    # print(prompt)
    
    # Generate responses
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    # Sort responses by confidence scores (higher to lower)
    responses.sort(key=lambda x: x[1], reverse=True)

    headers = table_text[0]
    rows = table_text[1:]
    table_data = pd.DataFrame(rows, columns=headers)
    is_sql_executable = False
    processed_table = pd.DataFrame()
    
    # print('Adding col options:', len(responses))

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
                print(f"SQL execution error add_column: {e}")
                print(f"Attempted SQL command: {sql_command}")
        else:
            print("No SQL command found in the response.")

    # Handling the case where no SQL is executable
    if not is_sql_executable:
        print("Add_column: Failed to execute any SQL command.")
        add_column_info = [(table_data, 'NOT FOUND: LLM cannot generate any error-free SQL', 1.0)]

    # If any SQL is executed successfully
    else:
        add_column_info = [(processed_table, sql_command, score)]

    operation = {
        "operation_name": "add_column",
        "parameter_and_conf": add_column_info,
    }

    # Append the operation to the processing chain and return the updated sample
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy, is_sql_executable, op_name



def add_column_act_sql(table_info, operation, skip_op=[], debug=False):
    table_info = copy.deepcopy(table_info)

    # Extract the DataFrame from a string representation
    tba_table = operation["parameter_and_conf"][0][0]

    table_text = table_info["table_text"]
    headers = table_text[0]
    rows = table_text[1:]

    # print("Final tba_table before modification:")
    # print(tba_table)

    # Check the number of columns in the tba_table
    # If the table only have 1 column, we will add this column to the existing table
    if len(tba_table.columns) == 1:
        add_column = tba_table.columns[0]
        add_column_contents = tba_table[add_column].tolist()

        # If the tba_table's single column has fewer elements than the number of rows, extend it
        if len(add_column_contents) < len(rows):
            # last_element = add_column_contents[-1] if add_column_contents else None
            # add_column_contents.extend([last_element] * (len(rows) - len(add_column_contents)))
            print('The return table after adding column operation is just a column with 1 entry!')
            print('Giang added on June 18 because doing this makes more sense and fit more to Chain-of-Verification, please revert this code if you see perf degrades!')
            new_headers = tba_table.columns.tolist()
            new_rows = tba_table.values.tolist()
            new_table_text = [new_headers] + new_rows
            table_info["table_text"] = new_table_text
            table_info["act_chain"].append(f"f_add_column({new_headers[-1]})")
            
            return table_info

        # Prepare to add the column to the existing table
        new_headers = headers + [add_column]
        new_rows = []
        for i, row in enumerate(rows):
            row.append(add_column_contents[i])
            new_rows.append(row)

        new_table_text = [new_headers] + new_rows
        table_info["table_text"] = new_table_text
        table_info["act_chain"].append(f"f_add_column({add_column})")

    # If the tba_table has more than 1 column, we will replace the existing table with the tba_table
    else:
        # Directly replace the table_text with tba_table's content, converted to the same format as table_text
        new_headers = tba_table.columns.tolist()
        new_rows = tba_table.values.tolist()
        new_table_text = [new_headers] + new_rows
        table_info["table_text"] = new_table_text
        table_info["act_chain"].append(f"f_add_column({new_headers[-1]})")

    return table_info

