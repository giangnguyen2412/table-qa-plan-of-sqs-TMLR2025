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
from tqdm import tqdm
import numpy as np
# from utils.helper import table2string
from collections import defaultdict
import pickle
import os
import traceback


import multiprocessing as mp

from operations import *

from utils.helper import *

    
# Example context
verification_demo = """
You will be given a Table, a statement, and a SQL command.
The SQL command will executed on the Table to extract relevant information to the statement.
Your task is to determine if the SQL command is helpful or not.
Answer YES if the SQL command helps selecting relevant information from the Table to verify the statement. Otherwise, answer NO.

Example 1:
Here is the table and the statement:
/* 
col : rank | lane | player | time
row 1 : 1 | 5 | olga tereshkova (kaz) | 51.86
row 2 : 2 | 6 | manjeet kaur (ind) | 52.17
row 3 : 3 | 3 | asami tanno (jpn) | 53.04
*/
Statement: there are one athlete from japan.

```sql
SELECT *,
       substr(player, instr(player, '(') + 1, instr(player, ')') - instr(player, '(') - 1) AS country_of_athletes
FROM athletes;
-- This SQL query extracts the substring between parentheses in the 'player' column to create a new column 'country_of_athletes'.
```
Does this SQL help verify the statement?
The answer is YES. The current table does not have the nationality column for athletes then it is correct to exract the nationality information from the column player.

Example 2:
Here is the table and the statement:
/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
row 4 : district 2 | chris a. brown | rep | ventnor | 2012
row 5 : district 3 | john j. burzichelli | dem | paulsboro | 2002
*/
Statement: the number of districts that are democratic is 5.

```sql
SELECT residence, COUNT(*) AS num_districts
FROM government_officials
GROUP BY residence;
-- This SQL query groups districts by 'residence'.
```
Does this SQL help verify the statement?
The answer is NO. It is not correct to group districts by residence because the statement is about party.

Example 3:
Here is the table and the statement:
/*
table caption: 1972 vfl season.
col: home team | home team score | away team | away team score | venue | crowd | date
row 1: st kilda | 13.12 (90) | melbourne | 13.11 (89) | moorabbin oval | 18836 | 19 august 1972
row 2: south melbourne | 9.12 (66) | footscray | 11.13 (79) | lake oval | 9154 | 19 august 1972
row 3: richmond | 20.17 (137) | fitzroy | 13.22 (100) | mcg | 27651 | 19 august 1972
*/
Statement: The away team with the highest score is fitzroy.

```sql
SELECT *
FROM vfl_season_1972
WHERE away team = fitzroy;
-- This SQL query sorts the table by the 'home_team_score' column in descending order.
```
Does this SQL help verify the statement?
The answer is NO. It is not correct to select only the row where the away team is fitzroy because we are doing comparison among all rows.

Example 4:
Here is the table and the statement:
/*
col : year | team | games | score
row 1 : 2004 | Hou | 16 | 34
row 2 : 2005 | Hou | 12 | 16
row 3 : 2006 | Hou | 15 | 120
*/
Statement: In 2006 Babin had the best score.

```sql
SELECT *
FROM nfl_scores
ORDER BY score ASC
LIMIT 1;
-- This SQL query sorts the 'score' column in ascending order to find the player with the best score.
```
Does this SQL help verify the statement?
The answer is NO. It is not correct to sort ascendingly and choose the first row because it will return the row for the worse score instead of the best score.

Example 5:
Here is the table and the statement:
/*
table caption: 1972 vfl season.
col: home team | home team score | away team | away team score | venue | crowd | date
row 1: st kilda | 13.12 (90) | melbourne | 13.11 (89) | moorabbin oval | 18836 | 19 august 1972
row 2: south melbourne | 9.12 (66) | footscray | 11.13 (79) | lake oval | 9154 | 19 august 1972
row 3: richmond | 20.17 (137) | fitzroy | 13.22 (100) | mcg | 27651 | 19 august 1972
*/
Statement: The away team with the highest score is fitzroy.

```sql
SELECT *
FROM vfl_season_1972;
-- This SQL query selects all rows from the 'vfl_season_1972' table to allow analysis of all team scores.
```
Does this SQL help verify the statement?
The answer is YES. It is correct to select all rows because we are doing comparison among all rows.

Example 6:
Here is the table and the statement:
/* 
col : rank | lane | player | time
row 1 : 5 | olga tereshkova (kaz) | 51.86
row 2 : 6 | manjeet kaur (ind) | 52.17
row 3 : 3 | asami tanno (jpn) | 53.04
*/
Statement: there are one athlete from japan.

```sql
SELECT *,
       time / 60.0 AS time_in_minutes
FROM athletes;
-- This SQL query adds a new column 'time_in_minutes' that converts the time to minutes.
```
Does this SQL help verify the statement?
The answer is NO. Adding the time_in_minutes column does not help in answering if there are one athlete from japan.

Example 7:
Here is the table and the statement:
/*
table caption: south wales derby
col: competition | total matches | cardiff win | draw | swansea win
row 1: league | 55 | 19 | 16 | 20
row 2: fa cup | 2 | 0 | 27 | 2
row 3: league cup | 5 | 2 | 0 | 3
*/
Statement: There are no cardiff wins that have a draw greater than 27.
Explanation: It is correct to group districts by political party and count them.

```sql
SELECT "cardiff win", "draw"
FROM south_wales_derby;
-- This SQL query selects only the 'cardiff win' and 'draw' columns.
```
Does this SQL help verify the statement?
The answer is YES. It is correct to select the 'cardiff win' and 'draw' columns because the statement mentioned these info.

Example 8:
Here is the table and the statement:
/*
col : year | team | games | score
row 1 : 2004 | Hou | 16 | 34
row 2 : 2005 | Hou | 12 | 16
row 3 : 2006 | Hou | 15 | 120
*/
Statement: In 2006 Babin had the best score.

```sql
SELECT *
FROM nfl_scores
ORDER BY score DESC
LIMIT 1;
-- This SQL query sorts the 'score' column in descending order to find the player with the best score.
```
Does this SQL help verify the statement?
The answer is YES. It is correct to sort descendingly and choose the first row as one containing the best score.

Example 9:
Here is the table and the statement:
/*
table caption: south wales derby
col: competition | total matches | cardiff win | draw | swansea win
row 1: league | 55 | 19 | 16 | 20
row 2: fa cup | 2 | 0 | 27 | 2
row 3: league cup | 5 | 2 | 0 | 3
*/
Statement: There are no cardiff wins that have a draw greater than 27.

```sql
SELECT "cardiff win", "competition"
FROM south_wales_derby
-- This SQL query selects columns 'cardiff win' and 'competition'.
```
Does this SQL help verify the statement?
The answer is NO. It is not correct to selects the 'cardiff win' and 'competition' columns because the competition will not help verify the statement. We should use 'cardiff win' and 'draw' instead.

Example 10:
Here is the table and the statement:
/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
row 4 : district 2 | chris a. brown | rep | ventnor | 2012
row 5 : district 3 | john j. burzichelli | dem | paulsboro | 2002
*/
Statement: the number of districts that are democratic is 5.

```sql
SELECT party, COUNT(*) AS num_districts
FROM government_officials
GROUP BY party;
-- Group districts by political party and count them
```
Does this SQL help verify the statement?
The answer is YES. It is correct to group districts by political party and count.
"""

ff_demo = """
You will be given a Table and a statement.
Your task is to determine if the next step is VERIFY or EDIT
VERIFY means the Table contains refined info to verify the statement.
EDIT means the Table can be further refined to verify the statement.


Example 1:
*/
col : rank | lane | athlete | time
row 1 : 1 | 6 | manjeet kaur (ind) | 52.17
row 2 : 2 | 5 | olga tereshkova (kaz) | 51.86
row 3 : 3 | 4 | pinki pramanik (ind) | 53.06
*/
Statement: There are 10 athletes from India.
What is the next steps?
The next step is EDIT. We need to extract the country info of athletes and then perform the counting over country as well to verify the statement.

Example 2:
col : player_name | team | points | game_date
row 1 : John Doe | Rockets | 30 | 2021-06-01
row 2 : Jane Smith | Rockets | 25 | 2021-06-15
row 3 : Alice Johnson | Jets | 20 | 2021-06-02
*/
Statement: The highest point total was scored by a Rockets player.
What is the next steps?
The next step is EDIT. We need to sort the rows by points first and then select the correct row to verify the statement.

Example 3:
/*
col : product | store | sales
row 1 : Bread | Store A | 100
row 2 : Milk | Store B | 150
row 3 : Bread | Store C | 200
*/
Statement: Bread is sold in at least two different stores.
What is the next steps?
The next step is EDIT. We need to select the rows where the product is Bread and then perform counting to verify the statement.

Example 4:
*/
col : september_game
row 1 : 3
*/
Statement: spurs lost 3 games in september.
What is the next steps?
The next step is VERIFY. We have the optimal info to verify the statement.

Example 5:
/*
col : date | game_count
row 1 : 2022-07-01 | 1
row 2 : 2022-06-09 | 2
*/
Statement: there were three games finished in 2022.
What is the next steps?
The next step is VERIFY.The table is simple and sufficient enough to verify the statement.

Example 6:
*/
col : game_count
row 1 : 2
*/
Statement: there were 2 games played in alian arena.
What is the next steps?
The next step is VERIFY. We have the optimal info to verify the statement.

Example 7:
*/
col : team | date | score
*/
Statement: no teams have more than 3 wins over the tournament.
What is the next steps?
The next step is VERIFY. There are no matched info in the table and we can verify the negative statement as correct.
"""

import re

def extract_answer_and_explanation(response):
    # print('response as:', response)
    try:
        # Regular expression to match "YES" or "NO" and the explanation
        match = re.search(r"The answer is (YES|NO)\. (.+)", response, re.DOTALL)
        # print('match as:', match)

        if match:
            answer = match.group(1)
            explanation = match.group(2).strip()
            return answer, explanation
        else:
            return "NO", "LLM cannot verify!"
    
    except Exception as e:
        return "NO", "LLM cannot verify!"


def verify_intermediate_step_old(sql_command, sample, table_info, llm, llm_options=None, debug=False, num_rows=3):
    """
    Function to verify if the intermediate step is correct.
    """
    try:
        # Extract the necessary information for the prompt
        table_text = table_info["table_text"]
        table_caption = sample["table_caption"]
        cleaned_statement = sample["cleaned_statement"]
        cleaned_statement = re.sub(r"\d+", "_", cleaned_statement)

                                   
        table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)
       
        prompt = f"""
{verification_demo}
######
Now we come to your actual task!
Here is the table and the statement:
/*
{table_str}
*/
Statement: {cleaned_statement}

```sql
{sql_command}
```
Does this SQL help verify the statement?\n"""
        
        # print('verification 1:', prompt)
        
        # Set up LLM options
        if llm_options is None:
            llm_options = llm.get_model_options()
        llm_options["n"] = 1  # Request multiple responses for a single prompt
        
        # Use the model to get the response
        try:
            responses = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
            print('verification 2:', responses)
            
        except Exception as e:
            print(f"Error when prompting model. Maybe the prompt is too long and exceeds context length!")
            return False, prompt
        answer, explanation = extract_answer_and_explanation(responses[0][0])
        print('verification 3:', answer)
        print('verification 3:', explanation)
        
        if "YES" in answer:
            return True, prompt
        else:
            return False, prompt
        
    except Exception as e:
        print(f"Error in verify_intermediate_step: {e}")
        traceback.print_exc()
        return False, prompt
    
    
    
    
def verify_intermediate_step(sql_command, sample, table_info, llm, llm_options=None, debug=False, num_rows=3):
    """
    Function to verify if the intermediate step is correct.
    """
    try:
        # Extract the necessary information for the prompt
        table_text = table_info["table_text"]
        table_caption = sample["table_caption"]
        cleaned_statement = sample["cleaned_statement"]
        cleaned_statement = re.sub(r"\d+", "_", cleaned_statement)

                                   
        table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)
        
        previous_SQL = ""
        if len (sample['chain']) > 0:
            for operation in sample['chain']:
                operation_name = operation['operation_name']
                result_table = pd.DataFrame(operation['parameter_and_conf'][0][0])
                sql_command = operation['parameter_and_conf'][0][1]
                if 'NOT FOUND' in sql_command:
                    continue

                previous_SQL += f"\n{sql_command}"
                previous_SQL += "Resulting Table:\n"
                previous_SQL += df_to_formatted_table(result_table)

            print('prev sql:\n', previous_SQL)
            print('samplechain', sample)
            print('table_info', table_info)
        else:
           previous_SQL = 'N/A'
        
        current_table = ""
        table_text = table_info["table_text"]
        table_caption = sample["table_caption"]
        
        table_str = table2string(table_text, caption=table_caption)

        current_table += "/*\n" + table_str + "\n*/\n"
                  
       
        prompt = f"""
{verification_demo_2}
######
Now we come to your actual task!
Here is the original table:
/*
{table_str}
*/
Statement: {cleaned_statement}

List of SQL:
{previous_SQL}

New SQL command:
```sql
{sql_command}
Resulting Table:
{current_table}
```
Does this SQL help verify the statement?\n"""
        
        print('verification 1:', prompt)
        
        # Set up LLM options
        if llm_options is None:
            llm_options = llm.get_model_options()
        llm_options["n"] = 1  # Request multiple responses for a single prompt
        
        # Use the model to get the response
        try:
            responses = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
            print('verification 2:', responses)
            
        except Exception as e:
            print(f"Error when prompting model. Maybe the prompt is too long and exceeds context length!")
            return False, prompt
        answer, explanation = extract_answer_and_explanation(responses[0][0])
        # print('verification 3:', answer)
        # print('verification 3:', explanation)
        
        if "YES" in answer:
            return True, prompt
        else:
            return False, prompt
        
    except Exception as e:
        print(f"Error in verify_intermediate_step: {e}")
        traceback.print_exc()
        return False, prompt

    
def fast_forward_operation(sample, table_info, llm, llm_options=None, debug=False):
    """
    Determine if the current table is enough for the final query?
    """
    try:
        # Extract the necessary information for the prompt
        table_text = table_info["table_text"]
        table_caption = sample["table_caption"]
        cleaned_statement = sample["cleaned_statement"]
        cleaned_statement = re.sub(r"\d+", "_", cleaned_statement)

                                   
        table_str = table2string(table_text, caption=table_caption, num_rows=num_rows)
       
        prompt = f"""
{ff_demo}
######
Now we come to your actual task!
/*
{table_str}
*/
Statement: {cleaned_statement}
What is the next steps?\n"""
        
        # Set up LLM options
        if llm_options is None:
            llm_options = llm.get_model_options()
        llm_options["n"] = 1  # Request multiple responses for a single prompt
        
        # Use the model to get the response
        try:
            responses = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
            
        except Exception as e:
            print(f"Error when prompting model. Maybe the prompt is too long and exceeds context length!")
            return False, prompt
        answer, explanation = extract_answer_and_explanation(responses[0][0])
        
        if "VERIFY" in answer:
            return True, prompt
        elif "EDIT" in answer:
            return False, prompt
        else:
            return True, prompt
        
    except Exception as e:
        print(f"Error in verify_intermediate_step: {e}")
        traceback.print_exc()
        return False, prompt
