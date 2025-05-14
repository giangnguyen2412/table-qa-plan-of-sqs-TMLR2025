import fire
import os
import pandas as pd
import random
from datetime import datetime
import shutil
import openai
import matplotlib.pyplot as plt
from tqdm import tqdm
# Set the random seed for reproducibility
random.seed(42)

# Import from utils and operations
from utils.load_data import *
from utils.llm import TableQA_LLM
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *

############################################################################################################

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

targetted_indices = random.sample(range(2024), k=20)


print('Samples tested:', targetted_indices)

def main(
        dataset_path: str = "data/tabfact/test.jsonl",
        raw2clean_path: str = "data/tabfact/raw2clean.jsonl",
        result_dir: str = "results/tabfact",
        use_subset: bool = False,
        subset_indices: list = targetted_indices,
        n_proc: int = 30,
        chunk_size: int = 30,
        load_dataset: bool = False,
):
    # Set model name and base URL based on selected model
    # if model.upper() in ['GPT4-O', 'GPT4O']:
    #     n_proc, chunk_size, use_subset = 10, 10, True
    #     model_name = "gpt-4o"
    # elif model.upper() in ['GPT-4', 'GPT4']:
    #     n_proc, chunk_size = 1, 1
    #     model_name = "gpt-4-turbo"
    # else:
    #     model_name = "gpt-3.5-turbo-0613"

    print(subset_indices, model_name)

    if K_plans > 1:
        n_proc, chunk_size = 3, 3
        print(n_proc, chunk_size)

    # Initialize TableQA_LLM model
    # gpt_llm = TableQA_LLM(model_name=model_name, key=openai.api_key)
    gpt_llm = TableQA_LLM()

    # Load or process dataset
    if load_dataset:
        print('Loading preprocessed dataset...')
        dataset_raw = load_tabfact_dataset(dataset_path, raw2clean_path, first_n=-1)
        reformatted_dataset_raw = {int(raw_sample['id'].split('-')[1]): raw_sample for raw_sample in dataset_raw}

        dataset = load_dataset_from_pkl('data/tabfact/gpt-3.5-turbo-0613_TabFact_processed_with_tokens.pkl')

        updated_dataset = []
        token_counts = []

        for sample in tqdm(dataset, desc="Counting tokens and updating dataset"):
            token_num = count_table_tokens(sample)
            sample['table_token_count'] = token_num  # Add new field
            token_counts.append(token_num)

            id = int(sample['id'].split('-')[1])
            if 330 < id < 341:
                updated_sample = reformatted_dataset_raw[id]
                updated_sample['table_token_count'] = token_num
                updated_dataset.append(updated_sample)
            else:
                updated_dataset.append(sample)

        # Save the updated dataset
        with open('data/tabfact/gpt-3.5-turbo-0613_TabFact_processed_with_tokens.pkl', 'wb') as f:
            pickle.dump(updated_dataset, f)

        print("Updated dataset saved with token counts.")

        # Plot the distribution
        plt.figure(figsize=(10, 6))
        plt.hist(token_counts, bins=50, edgecolor='black')
        plt.title('Distribution of Token Counts in TabFact Dataset')
        plt.xlabel('Number of Tokens')
        plt.ylabel('Frequency')
        plt.savefig(os.path.join(result_dir, 'token_distribution.png'))
        plt.close()

        # Print some statistics
        print(f"Average token count: {sum(token_counts) / len(token_counts):.2f}")
        print(f"Minimum token count: {min(token_counts)}")
        print(f"Maximum token count: {max(token_counts)}")

        dataset = updated_dataset

    else:
        print('Standardizing dataset...')
        dataset_raw = load_tabfact_dataset(dataset_path, raw2clean_path, first_n=-1)
        dataset = standardize_dates(dataset_raw[:len(dataset_raw)], llm=gpt_llm)
        save_dataset_to_pkl(dataset, f"{model_name}_TabFact_date_processed.pkl")
        return

    # Subset the dataset if needed
    dataset = dataset if not use_subset else [dataset[i] for i in subset_indices]
    dataset = [preprocess_entry(entry) for entry in dataset]

    print(f'Model name: {model_name}')
    print(f'Testing {len(dataset)} samples')
    print(f'Testing on: {test_dataset}')

    os.makedirs(result_dir, exist_ok=True)

    # running POS
    proc_samples, _ = dynamic_chain_exec_with_cache_mp(
        dataset,
        llm=gpt_llm,
        llm_options=gpt_llm.get_model_options(temperature=0.0, per_example_max_decode_steps=200,
                                              per_example_top_p=1.0),
        strategy="top",
        cache_dir=os.path.join(result_dir, "cache"),
        n_proc=n_proc,
        chunk_size=chunk_size,
    )

    # Print out the wrong samples for debugging
    for idx, sample in proc_samples.items():
        if sample['answer'] != sample['groundtruth'] and sample['is_sql_executable']:
            print(idx)

    accuracy = tabfact_compute_accuracy(proc_samples)
    print(f"Accuracy: {accuracy}")


if __name__ == "__main__":
    fire.Fire(main)

# python run_tabfact_pos.py --use_subset True --load_dataset True > A_DEBUG_TABFACT.txt
