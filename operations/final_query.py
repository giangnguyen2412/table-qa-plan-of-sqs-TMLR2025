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
# from utils.helper import table2string
from utils.helper import *

import pandas as pd

def table2df(table_text, num_rows=100):
    header, rows = table_text[0], table_text[1:]

    # if test_dataset == 'WikiTQ':
    #     rows = rows[:num_rows]

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

general_demo = """
/*
table caption : 2008 sidecarcross world championship.
col : position | driver / passenger | equipment | bike no | points
row 1 : 1 | daniël willemsen / reto grütter | ktm - ayr | 1 | 531
row 2 : 2 | kristers sergis / kaspars stupelis | ktm - ayr | 3 | 434
row 3 : 3 | jan hendrickx / tim smeuninx | zabel - vmc | 2 | 421
row 4 : 4 | joris hendrickx / kaspars liepins | zabel - vmc | 8 | 394
row 5 : 5 | marco happich / meinrad schelbert | zabel - mefo | 7 | 317
*/
Statement: bike number 3 is the only one to use equipment ktm - ayr.
The anwser is: NO

/*
table caption : 1957 vfl season.
col : home team | home team score | away team | away team score | venue | crowd | date
row 1 : footscray | 6.6 (42) | north melbourne | 8.13 (61) | western oval | 13325 | 10 august 1957
row 2 : essendon | 10.15 (75) | south melbourne | 7.13 (55) | windy hill | 16000 | 10 august 1957
row 3 : st kilda | 1.5 (11) | melbourne | 6.13 (49) | junction oval | 17100 | 10 august 1957
row 4 : hawthorn | 14.19 (103) | geelong | 8.7 (55) | brunswick street oval | 12000 | 10 august 1957
row 5 : fitzroy | 8.14 (62) | collingwood | 8.13 (61) | glenferrie oval | 22000 | 10 august 1957
*/
Statement: collingwood was the away team playing at the brunswick street oval venue.
The anwser is: NO

/*
table caption : co - operative commonwealth federation (ontario section).
col : year of election | candidates elected | of seats available | of votes | % of popular vote
row 1 : 1934 | 1 | 90 | na | 7.0%
row 2 : 1937 | 0 | 90 | na | 5.6%
row 3 : 1943 | 34 | 90 | na | 31.7%
row 4 : 1945 | 8 | 90 | na | 22.4%
row 5 : 1948 | 21 | 90 | na | 27.0%
*/
Statement: the 1937 election had a % of popular vote that was 1.4% lower than that of the 1959 election.
The anwser is: NO

/*
table caption : 2003 pga championship.
col : place | player | country | score | to par
row 1 : 1 | shaun micheel | united states | 69 + 68 = 137 | - 3
row 2 : t2 | billy andrade | united states | 67 + 72 = 139 | - 1
row 3 : t2 | mike weir | canada | 68 + 71 = 139 | - 1
row 4 : 4 | rod pampling | australia | 66 + 74 = 140 | e
row 5 : t5 | chad campbell | united states | 69 + 72 = 141 | + 1
*/
Statement: phil mickelson was one of five players with + 1 to par , all of which had placed t5.
The anwser is: YES
"""

import pandas as pd

def simple_query(sample, table_info, llm, debug=False, use_demo=True, llm_options=None):
    table_text = table_info["table_text"]

    caption = sample["table_caption"]
    statement = sample["statement"]

    # if USING_SQL_HIST_FINAL_QUERY is True and sample.get('is_sql_executable', False):
    if sample.get('is_sql_executable', False):
        # Initial data loading (first step's input data)
        columns = sample['table_text'][0]
        data_rows = sample['table_text'][1:]
        data = pd.DataFrame(data_rows, columns=columns)

    prompt = ""
    prompt += "Here are the statement about the table and the task is to tell whether the statement is True or False.\n"
    prompt += "If the statement is true, answer YES, and otherwise answer NO.\n"

    if use_demo:
        prompt += "\n"
        prompt += general_demo + "\n\n"

        prompt += "\nHere are the statement about the table and the task is to tell whether the statement is True or False.\n"
        prompt += "If the statement is true, answer YES, and otherwise answer NO.\n"
        prompt += "\n"
    

    prompt += "/*\n"
    prompt += table2string(table_text, caption=caption) + "\n"
    prompt += "*/\n"

    if "group_sub_table" in table_info:
        group_column, group_info = table_info["group_sub_table"]
        prompt += "/*\n"
        prompt += "Group the rows according to column: {}.\n".format(group_column)
        group_headers = ["Group ID", group_column, "Count"]
        group_rows = []
        for i, (v, count) in enumerate(group_info):
            if v.strip() == "":
                v = "[Empty Cell]"
            group_rows.append([f"Group {i+1}", v, str(count)])
        prompt += " | ".join(group_headers) + "\n"
        for row in group_rows:
            prompt += " | ".join(row) + "\n"
        prompt += "*/\n"

    prompt += "Statement: " + statement + "\n"

    # if SUPPORT_INT_TABLE is True:
    #     prompt += "If you do not have enough info to verify the Statement, you can look at the intermediate tables I provided below and pick the one that can help you answer!"
    prompt += "The answer is:"

    responses = llm.generate_plus_with_score(prompt, options=llm_options)
    responses = [(res.strip(), np.exp(score)) for res, score in responses]

    if debug:
        print(prompt)
        print(responses)

    operation = {
        "operation_name": "simple_query",
        "parameter_and_conf": responses,
        "Final_prompt": prompt,
    }
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy

############################################################################################################

wikitq_demo = """
/*
col : position | driver / passenger | equipment | bike no | points
row 1 : 1 | daniël willemsen / reto grütter | ktm - ayr | 1 | 531
row 2 : 2 | kristers sergis / kaspars stupelis | ktm - ayr | 3 | 434
row 3 : 3 | jan hendrickx / tim smeuninx | zabel - vmc | 2 | 421
row 4 : 4 | joris hendrickx / kaspars liepins | zabel - vmc | 8 | 394
row 5 : 5 | marco happich / meinrad schelbert | zabel - mefo | 7 | 317
*/
Question: Which bike number uses equipment zabel - vmc?
The answer is: ['2', '8']

/*
col : home team | home team score | away team | away team score | venue | crowd | date
row 1 : footscray | 6.6 (42) | north melbourne | 8.13 (61) | western oval | 13325 | 10 august 1957
row 2 : essendon | 10.15 (75) | south melbourne | 7.13 (55) | windy hill | 16000 | 10 august 1957
row 3 : st kilda | 1.5 (11) | melbourne | 6.13 (49) | junction oval | 17100 | 10 august 1957
row 4 : hawthorn | 14.19 (103) | geelong | 8.7 (55) | brunswick street oval | 12000 | 10 august 1957
row 5 : fitzroy | 8.14 (62) | collingwood | 8.13 (61) | glenferrie oval | 22000 | 10 august 1957
*/
Question: Did collingwood play at glenferrie oval?
The answer is: ['Yes']

/*
col : year of election | candidates elected | of seats available | of votes | % of popular vote
row 1 : 1934 | 1 | 90 | na | 7.0%
row 2 : 1937 | 0 | 90 | na | 5.6%
row 3 : 1943 | 34 | 90 | na | 31.7%
row 4 : 1945 | 8 | 90 | na | 22.4%
row 5 : 1948 | 21 | 90 | na | 27.0%
*/
Question: What percentage of the popular vote did the 1948 election have?
The answer is: ['27.0']

/*
col : place | player | country | score | to par
row 1 : 1 | shaun micheel | united states | 69 + 68 = 137 | - 3
row 2 : t2 | billy andrade | united states | 67 + 72 = 139 | - 1
row 3 : t2 | mike weir | canada | 68 + 71 = 139 | - 1
row 4 : 4 | rod pampling | australia | 66 + 74 = 140 | e
row 5 : t5 | chad campbell | united states | 69 + 72 = 141 | + 1
*/
Question: Which players had a to par score of -1?
The answer is: ['billy andrade', 'mike weir']

/*
col : name | age | country | medals
row 1 : michael phelps | 23 | usa | 8
row 2 : ian thorpe | 26 | australia | 5
row 3 : mark spitz | 22 | usa | 7
row 4 : natalie coughlin | 25 | usa | 6
row 5 : katie ledecky | 21 | usa | 5
*/
Question: Who is the youngest swimmer?
The answer is: ['katie ledecky']

/*
col : product | category | price | stock
row 1 : laptop | electronics | 1200 | 50
row 2 : smartphone | electronics | 800 | 150
row 3 : washing machine | appliances | 500 | 30
row 4 : refrigerator | appliances | 700 | 20
row 5 : microwave | appliances | 100 | 80
*/
Question: How many products are in the appliances category?
The answer is: ['3']

/*
col : city | population | country | continent
row 1 : new york | 8000000 | usa | north america
row 2 : london | 9000000 | uk | europe
row 3 : paris | 2200000 | france | europe
row 4 : sydney | 5000000 | australia | australia
row 5 : tokyo | 37000000 | japan | asia
*/
Question: Does sydney have a larger population than paris?
The answer is: ['Yes']

/*
col : name | position | department | years of service
row 1 : alice | manager | hr | 5
row 2 : bob | engineer | it | 3
row 3 : charlie | director | finance | 10
row 4 : diana | engineer | it | 4
row 5 : elena | manager | marketing | 2
*/
Question: Are there more engineers than managers?
The answer is: ['No']

/*
col : match | date | team1 | team2 | score1 | score2
row 1 : match1 | 2023-06-01 | team a | team b | 2 | 1
row 2 : match2 | 2023-06-02 | team c | team d | 3 | 3
row 3 : match3 | 2023-06-03 | team e | team f | 1 | 0
row 4 : match4 | 2023-06-04 | team g | team h | 2 | 2
row 5 : match5 | 2023-06-05 | team i | team j | 4 | 3
*/
Question: When did match3 take place?
The answer is: ['2023-06-03']

/*
col : landmark | location | height | visitors per year
row 1 : eiffel tower | paris | 324 | 7000000
row 2 : statue of liberty | new york | 93 | 4000000
row 3 : big ben | london | 96 | 3000000
row 4 : sydney opera house | sydney | 65 | 8500000
row 5 : tokyo tower | tokyo | 333 | 3000000
*/
Question: Where is the sydney opera house located?
The answer is: ['sydney']
"""


def wikitq_simple_query(sample, table_info, llm, debug=False, use_demo=True, llm_options=None):
    table_text = table_info["table_text"]
    question = sample["statement"]

    prompt = ""
    prompt += "Here is the question about the table, and the task is to answer the question based on the table. " \
              "Look at the above examples, your answer must be a list with each element is a string. " \
              "Otherwise, you will be penalized!\n"

    if use_demo:
        prompt += "\n"
        prompt += wikitq_demo + "\n\n"
        prompt += "Here is the question about the table, and the task is to answer the question based on the table. " \
                  "Look at the above examples, your answer must be a list.  " \
                  "Otherwise, you will be penalized!\n"
        prompt += "\n"
    
    prompt += "/*\n"
    prompt += table2string(table_text) + "\n"
    prompt += "*/\n"

    prompt += "Question: " + question + "\n"
    prompt += "You answer MUST be short and if possible, exactly match the info from the Table. The answer is:"

    # Generate responses from the language model
    responses = llm.generate_plus_with_score(prompt, options=llm_options)
    responses = [(res.strip(), np.exp(score)) for res, score in responses]

    if debug:
        print(prompt)
        print(responses)

    operation = {
        "operation_name": "simple_query_wikitq",
        "parameter_and_conf": responses,
        "Final_prompt": prompt,
    }
    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"] = []
    sample_copy["chain"].append(operation)

    return sample_copy