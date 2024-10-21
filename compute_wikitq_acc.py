import fire
import os
import pandas as pd
import random
# Set the random seed for reproducibility
random.seed(42)
import json
import collections
import numpy as np

from utils.load_data import *
from utils.llm import ChatGPT
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from utils.wikitq_eval import *
from operations import *

#### FREDDY
import openai 
from azure.identity import AzureCliCredential

import os
import shutil
from datetime import datetime

################################################################################

def load_metadata(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def load_target_values_map(tagged_dataset_path):
    target_values_map = {}
    for filename in os.listdir(tagged_dataset_path):
        if filename[0] == '.':
            continue
        filepath = os.path.join(tagged_dataset_path, filename)
        print('Reading dataset from', filepath)
        with open(filepath, 'r', encoding='utf8') as fin:
            header = fin.readline().rstrip('\n').split('\t')
            for line in fin:
                stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                ex_id = stuff['id']
                original_strings = tsv_unescape_list(stuff['targetValue'])
                canon_strings = tsv_unescape_list(stuff['targetCanon'])
                target_values_map[ex_id] = to_value_list(original_strings, canon_strings)
    return target_values_map

def compute_wikitq_accuracy(metadata_file, tagged_dataset_path, st2id_path, results_file):
    # Load the metadata
    results = load_metadata(metadata_file)
    
    # Load the target values map
    target_values_map = load_target_values_map(tagged_dataset_path)

    # Load statement to ID mapping
    st2id = {}
    with open(st2id_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            dic = json.loads(line)
            st = dic['statement']
            ids = dic['ids']
            st2id[st] = ids
    
    # Load results dictionary
    with open(results_file, 'r') as f:
        dic = json.load(f)
    
    deno_acc = 0
    execs = 0
    fall_back_crt = 0
    fb_count = 0
    pos_crt = 0
    pos_count = 0
    false_log_files = []

    for sample_index, res in results.items():
        res = res[sample_index]
        res_table = res['input']['table_text']
        res_st = res['input']['statement']
        res_preds = res['answer']
        fall_back = res['fallback_LLM']

        if fall_back:
            fb_count += 1
        else:
            pos_count += 1

        if not res['is_sql_executable']:
            continue
        if len(res_preds) == 0 or len(res_preds[0]) == 0:
            continue

        execs += 1

        for key in dic:
            to_union = collections.defaultdict(float)
            it = dic[key]
            st = it['data_item']['statement']

            if res_st in st:
                preds = []
                answs = []
                for ans in res_preds:
                    answs.append(str(ans[0]))
                answs = ' SEP_TOKEN '.join(answs)
                preds.append(answs)
                preds.append(0)
                preds.append(0)

                preds = [preds]
                break
        
        for pred in preds:
            log_prob_mean = pred[2]
            pred = pred[0]

            key = pred
            to_union[key] += np.exp(log_prob_mean)
        d_ordered = sorted(to_union.items(), key=lambda x: x[1], reverse=True)
        try:
            pred_answer = d_ordered[0][0].split('\n')[0].strip()
        except Exception:
            pred_answer = 'error'

        st = st.split('\n')[0]
        target_values = target_values_map[st2id[st]]

        pred_answer = pred_answer.split(' SEP_TOKEN ')
        pred_answer = to_value_list(pred_answer)

        flag = False
        if check_denotation(target_values, pred_answer):
            deno_acc += 1
            flag = True

        if flag and fall_back:
            fall_back_crt += 1
        elif flag and not fall_back:
            pos_crt += 1

        if not flag:
            if fall_back:
                pass
            else:
                print(f'### POS - Sample {sample_index}: {flag}, {pred_answer}, {target_values}')

        false_log_files.append(f'log_{sample_index}.txt')

    print(f'Executability: {execs}/{len(results)}')
    print('Executability Rate:', 100 * execs / len(results))
    print('\n')
    print('Fall-back Rate:', 100 * fb_count / len(results))
    print('\n')
    print('Fall-back Acc:', 100 * fall_back_crt / fb_count)
    print('\n')
    print('PoS Rate:', 100 * pos_count / len(results))
    print('\n')
    print('PoS Acc:', 100 * pos_crt / pos_count)
    print('\n')
    print(f'Denotation: {deno_acc}/{len(results)}')
    print('Denotation Accuracy:', 100 * deno_acc / len(results))

# Example usage:
metadata_file = result_file_name
tagged_dataset_path = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/data/wikitq/data'
st2id_path = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/data/wikitq/test_lower.jsonl'
results_file = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/data/wikitq/gloc_wtq_end2end_wikitq_test.json'

compute_wikitq_accuracy(metadata_file, tagged_dataset_path, st2id_path, results_file)
