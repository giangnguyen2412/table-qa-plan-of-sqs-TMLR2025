# python run_tabfact_pos.py --use_subset True --load_dataset True > A_DEBUG_TABFACT.txt

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
random.seed(110)

# Import from utils and operations
from utils.load_data import *
from utils.llm import ChatGPT
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *

# Define Azure OpenAI Credentials (commented out)
# from azure.identity import AzureCliCredential
# credential = AzureCliCredential()
# openai_token = credential.get_token("https://cognitiveservices.azure.com/.default")
# openai.api_key = openai_token.token
# openai.api_type = "azure_ad"
# openai.api_version = "2024-02-15-preview"

# OpenAI API key (replace with proper security handling in production)
openai.api_key = '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'

targetted_indices = random.sample(range(2024), k=30)


print('Samples tested:', targetted_indices)

def main(
        dataset_path: str = "data/tabfact/test.jsonl",
        raw2clean_path: str = "data/tabfact/raw2clean.jsonl",
        model: str = LLM,
        result_dir: str = "results/tabfact",
        first_n: int = 2024,
        use_subset: bool = False,
        subset_indices: list = targetted_indices,
        n_proc: int = 10,
        chunk_size: int = 10,
        load_dataset: bool = False,
):
    # Set model name and base URL based on selected model
    if model.upper() in ['GPT4-O', 'GPT4O']:
        n_proc, chunk_size, use_subset = 10, 10, True
        model_name = "gpt-4o"
    elif model.upper() in ['GPT-4', 'GPT4']:
        n_proc, chunk_size = 1, 1
        model_name = "gpt-4-turbo"
    else:
        model_name = "gpt-3.5-turbo-0613"

    print(subset_indices, model_name)

    if K_plans > 1:
        n_proc, chunk_size = 3, 3
        print(n_proc, chunk_size)

    # Initialize ChatGPT model
    gpt_llm = ChatGPT(model_name=model_name, key=openai.api_key)

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

    for idx, sample in proc_samples.items():
        if sample['answer'] != sample['groundtruth'] and sample['is_sql_executable']:
            print(idx)

    accuracy = tabfact_compute_accuracy(proc_samples)
    print(f"Accuracy: {accuracy}")


if __name__ == "__main__":
    fire.Fire(main)
