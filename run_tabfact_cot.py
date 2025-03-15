# python run_tabfact_cot.py --load_dataset False --use_subset True > COTABLE_log_gpt4omini.txt
# TODO: You must set using_sql_for_COT; NATURAL_LANGUAGE_PLANNING and USING_SQL in helper.py to False
import wandb
import fire
import os
import pandas as pd

from utils.load_data import load_tabfact_dataset, standardize_dates
from utils.llm import TableQA_LLM
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *
from utils.prompts import *

#### FREDDY
import openai 
from azure.identity import AzureCliCredential

import os
import shutil
from datetime import datetime

# # Azure OpenAI Credentials
# credential = AzureCliCredential()
# openai_token = credential.get_token("https://cognitiveservices.azure.com/.default")
# openai.api_key = openai_token.token
# ############################################# Uncomment for using GPT3.5
# openai.api_base = "https://llmopenai.jpmchase.net/WS0001037P-exp" #required #alternative https://llm-test-cib-research.openai.azure.com/
# # openai.api_base = "https://llmopenai-02.jpmchase.net/WS0001037P-exp-use2/"
# #############################################
# openai.api_type = "azure_ad" # required
# openai.api_version = "2024-02-15-preview" # to work till: 2024/04/02: "2023-05-15"
# #### FREDDY

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

# # Load the OpenAI API key and Azure endpoint from config
# with open("llm_config.yaml") as f:
#     config_yaml = yaml.load(f, Loader=yaml.FullLoader)
#
# # Extract configuration variables
# api_key = config_yaml['api_key']
# azure_endpoint = config_yaml['azure_endpoint']
# api_version = config_yaml.get('api_version',)  # Default version if not specified
#
# # Set up OpenAI client with Azure settings
# openai.api_type = "azure"
# openai.api_key = api_key
# openai.api_base = azure_endpoint
# openai.api_version = api_version

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

targetted_indices = [i for i in range(0,2)]
# targetted_indices = []
print('Samples tested:', targetted_indices)

POS_DEBUG = False

if POS_DEBUG:
    pos_wrongs = ['test-51', 'test-1652', 'test-255', 'test-161', 'test-1130', 'test-189', 'test-704', 'test-447', 'test-407', 'test-1466', 'test-1330', 'test-1436', 'test-1751', 'test-1774', 'test-919', 'test-1988', 'test-1563', 'test-1409', 'test-1402', 'test-1573', 'test-1300', 'test-1794', 'test-1342', 'test-2006', 'test-1197', 'test-877', 'test-1043', 'test-334', 'test-234', 'test-1812', 'test-1099', 'test-788', 'test-781', 'test-1083', 'test-1133', 'test-1979', 'test-2022', 'test-601', 'test-6', 'test-611', 'test-1915', 'test-1561', 'test-330', 'test-1793', 'test-1560', 'test-217', 'test-1782', 'test-1280', 'test-1963', 'test-629', 'test-1086', 'test-1000', 'test-1557', 'test-1090', 'test-1568', 'test-262', 'test-411', 'test-1460', 'test-1859', 'test-1995', 'test-897', 'test-1205', 'test-1991', 'test-866', 'test-1949', 'test-924', 'test-247', 'test-460', 'test-43', 'test-570', 'test-1756', 'test-1481', 'test-968', 'test-1323', 'test-124', 'test-824', 'test-193', 'test-882', 'test-287', 'test-1719', 'test-4', 'test-119', 'test-1426', 'test-1496', 'test-996', 'test-607', 'test-832', 'test-1196', 'test-322', 'test-1218', 'test-139', 'test-826', 'test-643', 'test-19', 'test-1339', 'test-167', 'test-1860', 'test-1157', 'test-647', 'test-436', 'test-1588', 'test-714', 'test-1035', 'test-431']
    pos_wrongs = ['test-178', 'test-864', 'test-51', 'test-285', 'test-758', 'test-255', 'test-161', 'test-2002', 'test-865', 'test-440', 'test-1563', 'test-1287', 'test-447', 'test-1149', 'test-407', 'test-1466', 'test-1330', 'test-1436', 'test-189', 'test-198', 'test-735', 'test-704', 'test-1236', 'test-1573', 'test-2018', 'test-552', 'test-1300', 'test-1794', 'test-435', 'test-1811', 'test-1763', 'test-1393', 'test-292', 'test-1197', 'test-877', 'test-817', 'test-1901', 'test-1043', 'test-23', 'test-1099', 'test-1221', 'test-788', 'test-781', 'test-1083', 'test-1133', 'test-1793', 'test-2022', 'test-1090', 'test-1568', 'test-1915', 'test-1561', 'test-330', 'test-1104', 'test-1', 'test-663', 'test-1000', 'test-1871', 'test-1242', 'test-866', 'test-1949', 'test-924', 'test-247', 'test-1205', 'test-1995', 'test-570', 'test-270', 'test-968', 'test-1379', 'test-1323', 'test-124', 'test-824', 'test-694', 'test-154', 'test-103', 'test-882', 'test-841', 'test-1719', 'test-1605', 'test-119', 'test-117', 'test-1496', 'test-832', 'test-1717', 'test-322', 'test-164', 'test-643', 'test-583', 'test-1339', 'test-16', 'test-1157', 'test-647', 'test-1272', 'test-204', 'test-1588', 'test-500', 'test-1977', 'test-1035', 'test-1787', 'test-104', 'test-1367']

    pos_wrong = [int(x.split('-')[1]) for x in pos_wrongs]


def main(
        dataset_path: str = "data/tabfact/test.jsonl",
        raw2clean_path: str = "data/tabfact/raw2clean.jsonl",
        ############################################# Uncomment for using GPT3.5
        # model_name: str = "gpt-3.5-turbo-0613",
        # model_name: str = "gpt-4-turbo",
        model_name: str = "gpt-4o",

        result_dir: str = "results/tabfact",
        first_n: int = -1,  # Can specify a subset or use None for all data 
        use_subset: bool = True,  # Determines whether to use a subset of samples
        subset_indices: list = targetted_indices,  # Indices of the samples to use if use_subset is True; for select_row
        n_proc: int = 10, # 1,
        chunk_size: int = 10, # 1, # Set chunk_size to 1 to better track the logs
        load_dataset: bool = False,
):
    # Load dataset
    dataset_n = load_tabfact_dataset(dataset_path, raw2clean_path, first_n=-1)
    dataset = dataset_n if not use_subset else [dataset_n[i] for i in subset_indices]
    # breakpoint()
    if POS_DEBUG:
        reformatted_dataset_raw = {}
        for raw_sample in dataset:
            id = raw_sample['id']
            id = int(id.split('-')[1])
            reformatted_dataset_raw[id] = raw_sample

        final_dataset = []
        for sample in dataset:
            id = sample['id']
            id = int(id.split('-')[1])
            if id in pos_wrong:
                final_dataset.append(sample)
        
        dataset = final_dataset  
        # dataset = dataset[:20]

        
    gpt_llm = TableQA_LLM()
    
    # Load processed dataset if needed
    if load_dataset is True:
        print('Loading preprocessed dataset...')
        dataset = load_dataset_from_pkl("processed_dataset.pkl")
        # dataset = load_dataset_from_pkl(f"{model_name}_processed_200_random_dataset.pkl")
        # dataset = load_dataset_from_pkl(f"{model_name}_processed_500_random_dataset_seed42.pkl")

        
    if not POS_DEBUG:
        if first_n == -1:
            pass
        else:
            dataset = dataset[:first_n]
        
    print('The number of samples being tested:', len(dataset))
        
    print('Model name:', model_name)
    print('The number of samples being tested:', len(dataset))

    os.makedirs(result_dir, exist_ok=True)
    proc_samples, dynamic_chain_log_list = dynamic_chain_exec_with_cache_mp(
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

    # Build data and chain to feed into the function fixed_chain_exec_mp
    fixed_chain = [
            (
                "simpleQuery_fewshot",
                simple_query,
                dict(use_demo=True),
                dict(
                    temperature=0, per_example_max_decode_steps=200, per_example_top_p=1.0
                ),
            ),
        ]

    final_result, history = fixed_chain_exec_mp(gpt_llm, proc_samples, fixed_chain)

    acc = tabfact_match_func_for_samples(final_result)
    print("Accuracy:", acc)

    print(f'Accuracy: {acc}', file=open(os.path.join(result_dir, f"COTABLE_TabFact_result_jul17_{POS_DEBUG}.txt"), "w"))
    pickle.dump(final_result, open(os.path.join(result_dir, f"COTABLE_TabFact_final_result_jul17_{POS_DEBUG}.pkl"), "wb"))
    pickle.dump(history, open(os.path.join(result_dir, f"COTABLE_TabFact_cotable_log_jul17_{POS_DEBUG}.pkl"), "wb"))

    pickle.dump(dynamic_chain_log_list, open(os.path.join(result_dir, f"COTABLE_TabFact_dynamic_chain_log_list_jul17_{POS_DEBUG}.pkl"), "wb"))


if __name__ == "__main__":
    fire.Fire(main)
