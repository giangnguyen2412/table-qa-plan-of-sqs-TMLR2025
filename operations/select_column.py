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

from third_party.select_column_row_prompts.select_column_row_prompts import select_column_demo
import pandas as pd
from _ctypes import PyObj_FromPtr


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

def twoD_list_transpose(arr, keep_num_rows=3):
    arr = arr[: keep_num_rows + 1] if keep_num_rows + 1 <= len(arr) else arr
    return [[arr[i][j] for i in range(len(arr))] for j in range(len(arr[0]))]


def select_column_build_prompt(table_text, statement, table_caption=None, num_rows=100):
    num_rows = 3
    df = table2df(table_text, num_rows=num_rows)
    tmp = df.values.tolist()
    list_table = [list(df.columns)] + tmp
    list_table = twoD_list_transpose(list_table, len(list_table))
    if table_caption is not None:
        dic = {
            "table_caption": table_caption,
            "columns": NoIndent(list(df.columns)),
            "table_column_priority": [NoIndent(i) for i in list_table],
        }
    else:
        dic = {
            "columns": NoIndent(list(df.columns)),
            "table_column_priority": [NoIndent(i) for i in list_table],
        }
    linear_dic = json.dumps(
        dic, cls=MyEncoder, ensure_ascii=False, sort_keys=False, indent=2
    )
    prompt = "/*\ntable = " + linear_dic + "\n*/\n"
    prompt += "statement : " + statement + ".\n"
    prompt += "similar words link to columns :\n"
    return prompt


def select_column_func(sample, table_info, llm, llm_options, debug=False, num_rows=100):
    num_rows = 3
    # table_info = get_table_info(sample)
    table_text = table_info["table_text"]

    table_caption = sample["table_caption"]
    statement = sample["statement"]

    prompt = "" + select_column_demo.rstrip() + "\n\n"
    prompt += select_column_build_prompt(
        table_text, statement, table_caption, num_rows=num_rows
    )

    # print('Prompt to LLMs for select_column_func')
    # print(prompt)

    responses = llm.generate_plus_with_score(prompt, options=llm_options)

    # print('Response from LLMs for select_column_func')
    # print(responses)

    if debug:
        print(prompt)
        print(responses)

    pattern_col = r"f_col\(\[(.*?)\]\)"

    pred_conf_dict = {}
    for res, score in responses:
        try:
            pred = re.findall(pattern_col, res, re.S)[0].strip()
        except Exception:
            continue
        pred = pred.split(", ")
        pred = [i.strip() for i in pred]
        pred = sorted(pred)
        pred = str(pred)
        if pred not in pred_conf_dict:
            pred_conf_dict[pred] = 0
        pred_conf_dict[pred] += np.exp(score)

    select_col_rank = sorted(pred_conf_dict.items(), key=lambda x: x[1], reverse=True)

    operation = {
        "operation_name": "select_column",
        "parameter_and_conf": select_col_rank,
    }

    sample_copy = copy.deepcopy(sample)
    sample_copy["chain"].append(operation)

    return sample_copy


def select_column_act(table_info, operation, union_num=2, skip_op=[]):
    table_info = copy.deepcopy(table_info)

    failure_table_info = copy.deepcopy(table_info)
    failure_table_info["act_chain"].append("skip f_select_column()")

    if "select_column" in skip_op:
        print('Skip select_column')

        return failure_table_info

    def union_lists(to_union):
        return list(set().union(*to_union))

    def twoD_list_transpose(arr):
        return [[arr[i][j] for i in range(len(arr))] for j in range(len(arr[0]))]

    selected_columns_info = operation["parameter_and_conf"]
    selected_columns_info = sorted(
        selected_columns_info, key=lambda x: x[1], reverse=True
    )
    selected_columns_info = selected_columns_info[:union_num]
    selected_columns = [x[0] for x in selected_columns_info]
    selected_columns = [eval(x) for x in selected_columns]
    selected_columns = union_lists(selected_columns)

    real_selected_columns = []

    table_text = table_info["table_text"]
    table = twoD_list_transpose(table_text)
    new_table = []
    for cols in table:
        if cols[0].lower() in selected_columns:
            real_selected_columns.append(cols[0])
            new_table.append(copy.deepcopy(cols))
    if len(new_table) == 0:
        new_table = table
        real_selected_columns = ["*"]
    new_table = twoD_list_transpose(new_table)

    table_info["table_text"] = new_table
    table_info["act_chain"].append(
        f"f_select_column({', '.join(real_selected_columns)})"
    )

    return table_info
