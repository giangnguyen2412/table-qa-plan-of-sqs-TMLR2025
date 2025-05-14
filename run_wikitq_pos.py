# python run_wikitq_pos.py --load_dataset True --use_subset True > A_DEBUG_WIKITQ.txt

import fire
import os
import random
import json
import collections
import numpy as np

# Set the random seed for reproducibility
random.seed(42)

from utils.load_data import *
from utils.llm import TableQA_LLM
from utils.helper import *
from utils.chain import *
from utils.wikitq_eval import *
import openai

# openai.api_key = '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'

############################################################################################################
# USING LAB APIs in regular mode

import yaml
import os
import json
import argparse
import random
import time
import openai
from bs4 import BeautifulSoup
from tqdm import tqdm
import numpy as np
import dotenv

dotenv.load_dotenv()

# Load the configuration from the YAML file
with open("llm_config.yaml") as f:
    config_yaml = yaml.load(f, Loader=yaml.FullLoader)

# Determine which provider to use
active_provider = config_yaml.get('active_provider', 'azure_openai')

# Check if we're using the new format with "providers" key
if 'providers' in config_yaml:
    # New format with multiple providers
    if active_provider == 'azure_openai':
        # Handle Azure OpenAI
        provider_config = config_yaml['providers']['azure_openai']
        api_key = provider_config['api_key']
        azure_endpoint = provider_config['base_endpoint']
        api_version = provider_config.get('api_version', '2024-08-01-preview')

        # Find active deployment
        deployment_name = None
        for depl in provider_config['deployments']['regular']:
            if depl.get('active', False):
                deployment_name = depl['name']
                break

        # Set up OpenAI client with Azure settings
        openai.api_type = "azure"
        openai.api_key = api_key
        openai.api_base = azure_endpoint
        openai.api_version = api_version

        # Use deployment_name in your subsequent code
        print(f"Using Azure OpenAI deployment: {deployment_name}")
        model_name = deployment_name

    elif active_provider == 'deepseek':
        # Handle DeepSeek
        provider_config = config_yaml['providers']['deepseek']
        api_key = provider_config['api_key']
        base_url = provider_config['base_url']

        # Find active model
        model_name = None
        for model in provider_config['models']:
            if model.get('active', False):
                model_name = model['name']
                break

        # Set up DeepSeek client
        # This would be your DeepSeek client initialization code
        # e.g., deepseek_client = DeepSeekClient(api_key=api_key, base_url=base_url)
        print(f"Using DeepSeek model: {model_name}")

    elif active_provider == 'sambanova':
        # Handle SambaNova
        provider_config = config_yaml['providers']['sambanova']
        api_key = provider_config['api_key']
        base_url = provider_config['base_url']

        # Find active model
        model_name = None
        for model in provider_config['models']:
            if model.get('active', False):
                model_name = model['name']
                break

        # Set up SambaNova client
        # This would be your SambaNova client initialization code
        # e.g., sambanova_client = SambanovaClient(api_key=api_key, base_url=base_url)
        print(f"Using SambaNova model: {model_name}")

else:
    # Handle legacy format (backward compatibility)
    api_key = config_yaml['api_key']
    azure_endpoint = config_yaml['azure_endpoint']
    api_version = config_yaml.get('api_version', '2024-08-01-preview')
    deployment_name = config_yaml.get('deployment_name')

    # Set up OpenAI client with Azure settings
    openai.api_type = "azure"
    openai.api_key = api_key
    openai.api_base = azure_endpoint
    openai.api_version = api_version

    print(f"Using legacy config with deployment: {deployment_name}")
############################################################################################################

# Sample indices for testing
targetted_indices = random.sample(range(4344), k=10)

# Main function
def main(
        model: str = LLM,
        result_dir: str = "results/wikitq",
        first_n: int = 4344,
        use_subset: bool = False,
        subset_indices: list = targetted_indices,
        n_proc: int = 20,
        chunk_size: int = 20,
        load_dataset: bool = False,
):

    print(subset_indices, model_name)

    if K_plans > 1:
        n_proc, chunk_size = 3, 3
        print(n_proc, chunk_size)

    # Initialize TableQA_LLM model
    gpt_llm = TableQA_LLM()

    # Load the dataset
    dataset_raw = []
    with open('data/wikitq/test.jsonl') as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            dic = json.loads(line)
            dic['id'] = idx
            dataset_raw.append(dic)

    # Use a subset if specified
    dataset = dataset_raw[:first_n]
    dataset = [preprocess_entry(entry) for entry in dataset]
    dataset = dataset if not use_subset else [dataset[i] for i in subset_indices]
    print(f'Model name: {model_name}')
    print(f'Number of samples being tested: {len(dataset)}')
    print(f'Testing on: {test_dataset}')

    os.makedirs(result_dir, exist_ok=True)

    # Process samples using dynamic chain execution with caching
    proc_samples, _ = wikitq_dynamic_chain_exec_with_cache_mp(
        dataset,
        llm=gpt_llm,
        llm_options=gpt_llm.get_model_options(
            temperature=0.0, per_example_max_decode_steps=200, per_example_top_p=1.0
        ),
        strategy="top",
        cache_dir=os.path.join(result_dir, "cache"),
        n_proc=n_proc,
        chunk_size=chunk_size,
    )

    ############# From DATER paper

    # ID string --> list[Value]
    target_values_map = {}
    tagged_dataset_path = 'data/wikitq/data'
    for filename in os.listdir(tagged_dataset_path):
        if filename[0] == '.':
            continue
        filename = os.path.join(tagged_dataset_path, filename)
        print('Reading dataset from', filename)
        with open(filename, 'r', 'utf8') as fin:
            header = fin.readline().rstrip('\n').split('\t')
            for line in fin:
                stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                ex_id = stuff['id']
                original_strings = tsv_unescape_list(stuff['targetValue'])
                canon_strings = tsv_unescape_list(stuff['targetCanon'])

                target_values_map[ex_id] = to_value_list(
                    original_strings, canon_strings)

    st2id = {}

    with open(os.path.join('data/wikitq/test_lower.jsonl')) as f:
        lines = f.readlines()
        for l in lines:
            dic = json.loads(l)
            st = dic['statement']
            ids = dic['ids']
            st2id[st] = ids
    with open('data/wikitq/gloc_wtq_end2end_wikitq_test.json', 'r') as f:
        dic = json.load(f)

    deno_acc = 0
    execs = 0

    fall_back_crt = 0
    fb_count = 0

    pos_crt = 0
    pos_count = 0
    ######### col filed################
    # sort the dict by key
    proc_samples = dict(sorted(proc_samples.items()))
    false_log_files = []

    # process samples to get denotation accuracy
    for sample_index, res in proc_samples.items():
        # breakpoint()
        res_table = res['input']['table_text']
        res_st = res['input']['statement']
        res_preds = res['answer']
        fall_back = res['fallback_LLM']

        if fall_back is True:
            fb_count += 1
        else:
            pos_count += 1

        # if res['is_sql_executable'] is False:
        #     continue
        if len(res_preds) == 0:
            continue

        if len(res_preds[0]) == 0:
            continue
        execs += 1

        for key in dic:
            to_union = collections.defaultdict(float)
            it = dic[key]
            table = it['data_item']['table_text']
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

        # preds = it['generations'] #### getting predictions

        for pred in preds:
            log_prob_mean = pred[2]
            pred = pred[0]

            # pred = pred.split('therefore,the answer is :')[-1]

            key = pred
            to_union[key] += np.exp(log_prob_mean)
        d_ordered = sorted(to_union.items(), key=lambda x: x[1], reverse=True)
        try:
            pred_answer = d_ordered[0][0].split('\n')[0].strip()
        except Exception:
            pred_answer = 'error'

        st = st.split('\n')[0]
        target_values = target_values_map[st2id[st]]

        # if sample_index == 48:
        #     breakpoint()

        pred_answer = pred_answer.split(' SEP_TOKEN ')
        pred_answer = to_value_list(pred_answer)

        flag = False
        # breakpoint()
        if check_denotation(target_values, pred_answer):
            deno_acc += 1
            flag = True

        if flag is True and fall_back is True:
            fall_back_crt += 1
        elif flag is True and fall_back is False:
            pos_crt += 1

        if flag is False:
            # if flag is False:
            if fall_back is True:
                # print(f'### FALLBACK - Sample {sample_index}: {flag}, {pred_answer}, {target_values}')
                pass
            else:
                print(f'### POS - Sample {sample_index}: {flag}, {pred_answer}, {target_values}')

        false_log_files.append(f'log_{sample_index}.txt')

    combine_files_from_directory(wikitq_planning_log_path, false_log_files)

    print(f'Executability: {execs}/{len(proc_samples)}')
    print('Executability Rate:', 100 * execs / len(proc_samples))
    print('\n')

    print('Fall-back Rate:', 100 * fb_count / len(proc_samples))
    print('\n')

    if fb_count > 0:
        print('Fall-back Acc:', 100 * fall_back_crt / fb_count)
        print('\n')

    print('PoS Rate:', 100 * pos_count / len(proc_samples))
    print('\n')

    if pos_crt > 0:
        print('PoS Acc:', 100 * pos_crt / pos_count)
        print('\n')

    print(f'Denotation: {deno_acc}/{len(proc_samples)}')
    print('Denotation Accuracy:', 100 * deno_acc / len(proc_samples))

    #############


if __name__ == "__main__":
    fire.Fire(main)

# python run_wikitq_pos.py --use_subset True --load_dataset True