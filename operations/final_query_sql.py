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
import numpy as np
from utils.helper import *
import re

general_demo = """
### Demo Example 1 
Given this Statement: cody zeller helpmin went to washington high school , and his hometown is washington , la

Let verify the statement on this original table table_sql:
/*
col : player | height | school | hometown | college
row 1 : khem birch | 6 - 9 | notre dame prep | montreal , qc , canada | pittsburgh / unlv
row 2 : cody zeller helpmin | 6 - 11 | washington high school | washington , la | los angeles
*/

I executed these below intermediate SQL commands to simplify the table table_sql for you to more easily verify the statement.

SQL1: This SQL query selects the row where the player is cody zeller helpmin and the hometown is washington, la from table table_sql.
```sql
SELECT *
FROM table_sql
WHERE player = 'cody zeller helpmin' AND hometown = 'washington , la';
```

SQL1 executed on the original table table_sql and results in this table1:
/*
col : player | height | school | hometown | college
row 1 : cody zeller helpmin | 6 - 11 | washington high school | washington , la | los angeles
*/


SQL2: This SQL query selects the player and hometown columns from the table1 table.
```sql
SELECT player, hometown
FROM table1;
```

SQL2 executed on the intermediate table table1 and results in this table2:

/*
col : player | hometown
row 1 : cody zeller helpmin | washington , la
*/


Now, let verify the Statement: cody zeller helpmin went to washington high school , and his hometown is washington , la

Let's think step-by-step and use the table_sql, SQL1, table1, SQL2, and table2 to write the SQL that correctly verifies the statement.
Your SQL must refer to these existing columns only: player or hometown. Otherwise, your SQL will not be executable!
SQL is:
```sql
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM table2
            WHERE player = 'cody zeller helpmin' AND hometown = 'washington , la'
        ) THEN 'YES'
        ELSE 'NO'
    END AS verification_result;
```

### Demo Example 2
Given this Statement: plymouth argyle played the away team derby county after 18 march 1984

Let verify the statement on this original table table_sql:
/*
col : tie_no | home_team | score | away_team | date
row 1 : 1 | notts county | 1 - 2 | everton | 1984-03-10
row 2 : 3 | plymouth argyle | 0 - 0 | derby county | 1984-03-10
row 3 : replay | derby county | 0 - 1 | plymouth argyle | 1984-03-18
*/

I executed these below intermediate SQL commands to simplify the table table_sql for you to more easily verify the statement.

SQL1: This SQL query selects the rows where plymouth argyle played against derby county as the away team after march 18, 1984 from table table_sql.
```sql
SELECT *
FROM table_sql
WHERE home_team = 'plymouth argyle' AND away_team = 'derby county' AND date > '1984-03-18';
```

SQL1 executed on the original table table_sql and results in this table1:
/*
col : tie_no | home_team | score | away_team | date
*/

Now, let verify the Statement: plymouth argyle played the away team derby county after 18 march 1984

Let's think step-by-step and use the table_sql, SQL1, and table1 to write the SQL that correctly verifies the statement.
Your SQL must refer to these existing columns only: tie_no or home_team or score or away_team or date. Otherwise, your SQL will not be executable!
SQL is:
```sql
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM table1
            WHERE home_team = 'plymouth argyle' AND away_team = 'derby county' AND date > '1984-03-18' 
        ) THEN 'YES'
        ELSE 'NO'
    END AS verification_result;
```

# Demo Example 3
Given this Statement: there was a 150 point difference between the highest score and the lowest score

Let verify the statement on this original table table_sql:
/*
col : rank | name | nation | sp_+_fs | points | places
row 1 : 1 | linda fratianne | united states | 1 | 300 | 11
row 2 : 2 | anett pötzsch | east germany | 3 | 184.36 | 18
row 3 : 3 | gloria mas | spain | 3 | 150 | 279
*/

I executed these below intermediate SQL commands to simplify the table_sql table for you to more easily verify the statement.

SQL1: This SQL query calculates the difference between the highest and lowest scores in the points column and creates a new column point_difference.
```sql
SELECT MAX(points) - MIN(points) AS point_difference
FROM table_sql;
```

SQL1 executed on the original table table_sql and results in this table1:
/*
col : point_difference
row 1 : 150
*/

Now, let verify the Statement: there was a 150 point difference between the highest score and the lowest score

Let's think step-by-step and use table_sql, table1, and SQL1 to write the SQL that correctly verifies the statement.
Your SQL must refer to this existing column only: point_difference. Otherwise, your SQL will not be executable!
SQL is:
```sql
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM table1 WHERE point_difference = 150
        ) THEN 'YES'
        ELSE 'NO'
    END AS verification_result;
```

# Demo Example 4
Given this Statement: iran is the 1st in gdp in the middle east and also ranks tenth among all countries in asia

Let verify the statement on this original table table_sql:
/*
col : rank_mideast | rank_asia | rank_world | country | 2011_gdp_(ppp)_billions_of_usd
row 1 : 1 | 8 | 17 | iran | 930.236
row 2 : 2 | 9 | 23 | saudi arabia | 677.663
row 3 : 3 | 18 | 48 | united arab emirates | 261.189
*/

I executed these below intermediate SQL commands to simplify the table table_sql for you to more easily verify the statement.

SQL1: This SQL query selects the country, rank_mideast, and rank_asia columns from the table table_sql.
```sql
SELECT country, rank_mideast, rank_asia
FROM table_sql
```

SQL1 executed on the original table table_sql and results in this table1:
/*
col : country | rank_mideast | rank_asia
row 1 : iran | 1 | 8
row 2 : saudi arabia | 2 | 9
row 3 : united arab emirates | 3 | 18
*/

SQL2: This SQL query selects the country and its rank in asia where the rank in the middle east is 1.
```sql
SELECT country, rank_asia
FROM table1
WHERE rank_mideast = 1;
```

SQL2 executed on the intermediate table table1 and results in this table2:
/*
col : country | rank_asia
row 1 : iran | 8
*/

Now, let verify the Statement: iran is the 1st in gdp in the middle east and also ranks tenth among all countries in asia

Let's think step-by-step and use the table_sql, SQL1, table1, SQL2, and table2 to write the SQL that correctly verifies the statement.
Your SQL must refer to these existing columns only: country or rank_asia. Otherwise, your SQL will not be executable!
SQL is:
```sql
SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM table2 WHERE country = 'iran' AND rank_asia = 10
        ) THEN 'YES'
        ELSE 'NO'
    END AS verification_result;
```
"""

import pandas as pd

def simple_query_sql(sample, table_info, llm, debug=False, use_demo=False, llm_options=None):
    caption = sample["table_caption"]
    statement = sample["statement"]

    # Setup LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    llm_options["n"] = 1  # Request multiple responses for a single prompt to increase chances of getting a valid SQL

    # Construct the initial prompt based on whether to use demo or not
    prompt = ""
    if use_demo:
        prompt += "Here is a list of Demo Examples you can refer to when you work on Actual Example."
        prompt += "\n"
        prompt += general_demo + "\n"
        
        print('ckz 1:', prompt)
        
        contexts  = []
        context_info = ""

        if USING_SQL_HIST_FINAL_QUERY is True and sample['is_sql_executable'] is True:    
            columns = sample['table_text'][0]
            data_rows = sample['table_text'][1:]
            data = pd.DataFrame(data_rows, columns=columns)
            
            prompt += f"### Actual Example\n"
            # prompt += f"Here come to your actual task!!!\n"
            prompt += f"Given this Statement: {statement}\n"
            prompt += f"\nLet verify the statement on this original table table_sql:"

            prompt += "\n/*\n"
            prompt += f"{df_to_formatted_table(data)}"
            prompt += "\n*/\n"

            prompt += f"\nI executed these below intermediate SQL commands to simplify the table for you to more easily verify the statement."
            
            running_idx = 0
            
            for idx, operation in enumerate(sample['chain']):
                if len(operation['parameter_and_conf'][0]) == 0:
                    continue
                sql_command = operation['parameter_and_conf'][0][1]
                # Skip the command if this operation was not executed
                if 'NOT FOUND' in sql_command:
                    continue
                
                sql_explanation_pattern = re.compile(r'--(.*)')
                sql_explanation = sql_explanation_pattern.search(sql_command)

                if sql_explanation:
                    comment = sql_explanation.group(1).strip()
                    print("Extracted Comment:")
                    print(comment)
                else:
                    print("No comment found in:", sql_explanation)
                    comment = ""
                
                split_pattern = re.compile(r'(--.*)', re.DOTALL)
                # Split the SQL block
                split_result = split_pattern.split(sql_command)
                clean_sql_command = split_result[0].strip()

                if idx == 0:
                    prompt += f"\n\nSQL{running_idx+1}: {comment}"

                    prompt += f"\n```sql\n{clean_sql_command}"
                    prompt += f"\n```"
                else:
                    prompt += f"SQL{running_idx+1}: {comment.replace('table_sql', f'table{running_idx+1}')}"

                    prompt += f"\n```sql\n{clean_sql_command.replace('table_sql', f'table{running_idx}')}"
                    prompt += f"\n```"

                
                if idx == 0:
                    prompt += f"\n\nSQL{running_idx+1} executed on the original table table_sql and results in this table{running_idx+1}:\n"
                else:
                    prompt += f"\n\nSQL{running_idx+1} executed on the intermediate table table{running_idx} and results in this table{running_idx+1}:\n"

                result_table = pd.DataFrame(operation['parameter_and_conf'][0][0])

                prompt += "/*\n"
                prompt += df_to_formatted_table(result_table)
                prompt += "\n*/\n\n"

                # prompt += f"\n\n->"
                
                running_idx += 1
                contexts.append(f"SQL{running_idx}")
                contexts.append(f"table{running_idx}")
            
            context_info = ", ".join(contexts)


            # prompt += f"\nResulting table:\n"
            # result_table = pd.DataFrame(operation['parameter_and_conf'][0][0])
            # prompt += df_to_formatted_table(result_table)
            # prompt += f"\n\n->"
                

    print('ckz 2:', prompt)
  
    if len(contexts) > 0:
        table_name = contexts[-1]
    else:
        table_name = 'table_sql'

    # prompt += f"\nThe final Table {table_name} after applying SQLs:\n"
    if len(sample['chain'][-1]['parameter_and_conf']) > 0 and sample['is_sql_executable'] is True:
        table_text = sample['chain'][-1]['parameter_and_conf'][0][0]
        # prompt += df_to_string(table_text)
        # prompt += df_to_formatted_table(table_text)
        columns = table_text.columns.tolist()
    else:
        table_text = table_info["table_text"]
        # prompt += list_to_formatted_string(table_text)
        # prompt += list_to_formatted_table(table_text)
        columns = table_text[0]
        
    if len(sample['chain'][-1]['parameter_and_conf']) > 0:
        table_data = table_text
    else:
        headers = table_text[0]
        rows = table_text[1:]
        table_data = pd.DataFrame(rows, columns=headers)
    # print('ckz 3:', table_data)

    prompt += f"\n\nNow, let verify the Statement: {statement}"
    # prompt += f"\nYour task is to write a SQL command that outputs YES or NO only to verify the Statement"
    # prompt += "\nThe output of your SQL command on the Table must be YES or NO only."
    
    # prompt += "\nPlease write a SQL command that correctly verifies the statement."
    
    print('ckz 4:', prompt)


    prompt += f"\n\nConstraints for your SQL:"

    prompt += "\n1.Your SQL must be executable by python sqlite3."
    if len(columns) > 1:
        existing_cols = " or ".join(f"{item}" for item in columns)
        # prompt += f"\n2.Existing columns are: {existing_cols}"    
        
    else:
        existing_cols = columns[0]
        # prompt += f"\n2.The only existing column:  {existing_cols}"  
        
    prompt += f"\n2.Your SQL command must be simple because the table {table_name} has been simplified."

    # prompt += "\n4.If using WHERE, you must look at the cell contents in the given final_table_sql to write soft matching rather than hard, exact matchings."
    prompt += f"\n3.You must look at the cell contents in {table_name} to avoid problems of exact matchings in SQL."
    prompt += "\n4.Your SQL command must output YES or NO only."
    
    if len(columns) > 1:
        prompt += f"\n\nLet's think step-by-step and use table_sql, {context_info} to write the SQL that correctly verifies the statement. Your SQL must base on columns: {existing_cols} of the {table_name} only. If you refer others, your SQL will not be executable!\nSQL is:\n"
    else:
        prompt += f"\n\nLet's think step-by-step and use the table_sql, {context_info} to write the SQL that correctly verifies the statement. Your SQL must base on column: {existing_cols} of the {table_name} only. If you refer others, your SQL will not be executable!\nSQL is:\n"
    
    is_sql_executable = False
    results = []
    sql_commands = []
    
    try:
        # Generate responses
        responses = llm.generate_plus_with_score(prompt, options=llm_options)
        responses.sort(key=lambda x: x[1], reverse=True)

        # Process responses to find the first valid SQL
        for response, score in responses:
            # sql_match = re.search(r"```sql\n([\s\S]*?)\n```", response)
            sql_command = extract_sql_code(response)
                
            if sql_command is not None:
                # sql_command = sql_match.group(1)
                sql_commands.append(sql_command)  # Store all SQL commands for debugging
                try:
                    processed_table = apply_sql_to_df(table_data, sql_command, table_name)
                    print('comehere 1', processed_table)
                    print('comehere 2', sql_command)
                    print('comehere 3', table_data)
                    
                    
                    if not processed_table.empty:
                        
                        answer = processed_table.iloc[0][0]
                        if answer in ["YES", "NO"]:
                            results.append(answer)
                            if DEBUG:
                                print('------> Succ: Prompt to the model:', prompt)
                                print('------> Succ: Response of the model:', response)
                                print(f"Final query: Executed SQL: {sql_command} returned {answer}")
                        else:
                            print('------> FAILED: Prompt to the model:', prompt)
                            print('------> FAILED: Response of the model:', response)
                            print('SQL answer is:', answer)
                    else:
                        print('------> FAILED: Prompt to the model:', prompt)
                        print('------> FAILED: Response of the model:', response)
                        print('processed_table is empty:', processed_table)
                        
                except Exception as e:
                    print('------> Prompt to the model:', prompt)
                    print(f"------> Final query: SQL execution error: {e}")
            else:
                print('------> Prompt to the model:', prompt)
                print('------> Response of the model:', response)
                print('No formatted SQLs found in: ', sql_match)
                
    except Exception as e:
        print(f"Error when prompting model in final query. Maybe the prompt is too long and exceeds context length!:", prompt)

    # Perform a majority vote on the results
    if results:
        vote_result = max(set(results), key=results.count)
        if DEBUG:
            print(f"Majority vote result: {vote_result} from results: {results}")
        is_sql_executable = True
    else:
        vote_result = "N/A"
        is_sql_executable = False
        if DEBUG:
            print("FINAL_QUERY: No valid SQL execution results were obtained.")

    # Save the operational details
    operation = {
        "operation_name": "simple_query_sql",
        "parameter_and_conf": [(vote_result, 1.0)],
        "Final_prompt": prompt,
        "SQL_command": sql_commands,
        "Final_query_SQL_executable": is_sql_executable,
    }

    # Append the new operation to the sample
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)
    
    print('Final_query_SQL_executable: ', is_sql_executable)
    return sample_copy