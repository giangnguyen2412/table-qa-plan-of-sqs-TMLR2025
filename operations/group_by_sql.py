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


import re
import numpy as np
import copy
from utils.helper import *
import pandas as pd
from utils.verifier import *

group_column_demo_sql = """
### Example 1:
/*
col : rank | lane | athlete | time | country
row 1 : 1 | 6 | Manjeet Kaur (IND) | 52.17 | IND
row 2 : 2 | 5 | Olga Tereshkova (KAZ) | 51.86 | KAZ
row 3 : 3 | 4 | Pinki Pramanik (IND) | 53.06 | IND
row 4 : 4 | 1 | Tang Xiaoyin (CHN) | 53.66 | CHN
row 5 : 5 | 8 | Marina Maslyonko (KAZ) | 53.99 | KAZ
*/
Statement: There is one athlete from Japan.
The existing columns are: rank, lane, athlete, time, country.

SQL is:

```sql
SELECT country, COUNT(*) AS num_athletes
FROM table_sql
GROUP BY country;
-- Group athletes by country and count them
```

Explanation: the statement says the number of athletes from japan is one. Each row is about an athlete. We can group column country to group the athletes from the same country.

### Example 2:
/*
col : district | name | party | residence | first_served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
row 4 : district 2 | chris a. brown | rep | ventnor | 2012
row 5 : district 3 | john j. burzichelli | dem | paulsboro | 2002
*/
Statement: the number of districts that are democratic is 5.
The existing columns are: district, name, party, residence, first_served.

SQL is:

```sql
SELECT party, COUNT(*) AS num_districts
FROM table_sql
GROUP BY party;
-- Group districts by political party and count them
```

Explanation: the statement says the number of districts that are democratic is 5. Each row is about a district. We can group the column party to group the districts from the same party.
"""

def group_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
    table_str = table2string(
        table_text, caption=table_caption, num_rows=num_rows
    ).strip()

    table_name = 'table_sql'
    prompt = f"Given this table '{table_name}':\n"
    prompt += "/*\n" + table_str + "\n*/\n"
    prompt += "Statement: " + statement + "\n"
    
    # print('Table into sorting grouping prompting:', prompt)

    prompt += "\nConstraints for your SQL:"

    prompt += "\n1.The columns used in your SQL must match "

    if len(table_text[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in table_text[0])
    else:
        existing_cols = f"{table_text[0][0]}"
    prompt += f"{existing_cols}"

    # prompt += "\n2.In SELECT COUNT(*), you must use AS to name the new column.\n"
    prompt += f"\n2.{syntax_instr1}"
    prompt += "\n3.Your SQL command must be executable by python sqlite3."
    prompt += "\n4.If using FROM, the table to be selected must be table_sql."
    prompt += "\n5.You must look at the cell contents in table_sql to avoid problems of exact matchings in SQL."

    prompt += "\nSQL is:\n"
    return prompt


def group_column_func_sql(
    sample, table_info, llm, llm_options=None, debug=False, skip_op=[]
):
    op_name = 'group_column'
    table_text = table_info["table_text"]
    table_caption = sample["table_caption"]
    statement = sample["statement"]

    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt

    prompt = "" + group_column_demo_sql.rstrip() + "\n\n"
    prompt += group_column_build_prompt(
        table_text, statement, table_caption=table_caption, num_rows=5
    )
    
    print(prompt)

    # Generate responses
    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    # Sort responses by confidence scores (higher to lower)
    responses.sort(key=lambda x: x[1], reverse=True)

    headers = table_text[0]
    rows = table_text[1:]
    table_data = pd.DataFrame(rows, columns=headers)
    is_sql_executable = False
    processed_table = pd.DataFrame()
    
    # print('Grouping col options:', len(responses))

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
                print(f"SQL execution error group_column: {e}")
                print(f"Attempted SQL command: {sql_command}")
        else:
            print("No SQL command found in the response.")

    # Handling the case where no SQL is executable
    if not is_sql_executable:
        print("GROUP_by: Failed to execute any SQL command.")
        group_param_and_conf_list = [(table_data, 'NOT FOUND: LLM cannot generate any error-free SQL', 1.0)]

    # If any SQL is executed successfully
    else:
        group_param_and_conf_list = [(processed_table, sql_command, score)]

    operation = {
        "operation_name": "group_column",
        "parameter_and_conf": group_param_and_conf_list,
    }

    # Append the operation to the processing chain and return the updated sample
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy, is_sql_executable, op_name


def group_column_act_sql(table_info, operation, strategy="top", skip_op=[]):
    table_info = copy.deepcopy(table_info)

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_group_column()")

    if "group_column" in skip_op:
        return failure_table_info
    if len(operation["parameter_and_conf"]) == 0:
        return failure_table_info
    
    table_info["act_chain"].append(f"f_group_column()")

    return table_info

