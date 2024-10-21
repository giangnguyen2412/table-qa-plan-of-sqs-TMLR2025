import wandb
import fire
import os
import pandas as pd
import sys
import argparse
import openai
from azure.identity import AzureCliCredential
import random
from datetime import datetime
import json

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from utils.load_data import load_tabfact_dataset, standardize_dates
from utils.llm import ChatGPT
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *
from utils.prompts import *

# Azure OpenAI Credentials setup
credential = AzureCliCredential()
openai_token = credential.get_token("https://cognitiveservices.azure.com/.default")
openai.api_key = openai_token.token
openai.api_base = "https://llmopenai.jpmchase.net/WS0001037P-exp"
openai.api_type = "azure_ad"
openai.api_version = "2024-02-15-preview"

# Model selection logic
model = LLM  # This should be defined elsewhere in your project

if model == 'GPT4-O':
    n_proc = 1
    chunk_size = 1
    use_subset = True
    model_name = "gpt-4o"
    openai.api_base = "https://llmopenai-02.jpmchase.net/WS0001037P-exp-use2/"
elif model == 'GPT4':
    n_proc = 1
    chunk_size = 1
    model_name = "gpt-4-turbo"
    openai.api_base = "https://llmopenai-02.jpmchase.net/WS0001037P-exp-use2/"
else:
    model_name = "gpt-3.5-turbo-0613"
    openai.api_base = "https://llmopenai.jpmchase.net/WS0001037P-exp"


def compare_reasoning_explanations(file_name, llm, method_a_folder, method_b_folder, llm_options=None):
    # Read the content of the HTML files from method A and method B folders
    with open(os.path.join(method_a_folder, file_name), 'r') as file:
        method_a_content = file.read()

    method_a = os.path.basename(method_a_folder)

    with open(os.path.join(method_b_folder, file_name), 'r') as file:
        method_b_content = file.read()

    method_b = os.path.basename(method_b_folder)

    # Prepare the prompt for the LLM
    prompt = f"""
Your task in this experiment is to evaluate different methods that explain how the TableQA system arrives at its answers (here TRUE). Understanding these explanations helps improve trust and transparency in AI systems.

Attribution explanations highlight specific parts of a table—such as rows, columns, or cells—that are most relevant to the answer provided by a TableQA system. These explanations help you understand which data points the system considered important when generating the answer.

By using different colors for highlighting, the system provides a more nuanced explanation:

- Yellow highlights (rows): Show the rows that are needed to verify the Statement.
- Green highlights (cells): Pinpoint the exact data points that directly answer the question.
- Contextual information: The factual information that has been fact-checked.

You are given two explanations that describe the reasoning process of a Table Question Answering model in HTML format. One explanation is based on the '{method_a}' method, and the other is based on the '{method_b}' method. Please carefully analyze both explanations and determine which one better clarifies the reasoning process behind the Table QA model's decisions.

{method_a} Explanation:
{method_a_content}

{method_b} Explanation:
{method_b_content}

Which explanation provides a clearer and more accurate reasoning process? Answer with '{method_a}' or '{method_b}':
"""
    # Set up LLM options if not provided
    if llm_options is None:
        llm_options = llm.get_model_options()

    # Generate a response from the model
    try:
        response = llm.generate_plus_with_score(prompt, options=llm_options)

        if response == 'Exceed context length':
            return None

        answer = response[0][0].strip()
        return answer

    except Exception as e:
        print(f"Error generating response from the model: {e}")
        return None


def compare_all_explanations(method_a_folder, method_b_folder, llm=None, llm_options=None):
    # Initialize counters and results dictionary
    method_a_preference_count = 0
    method_b_preference_count = 0
    total_comparisons = 0
    results = {}

    random.seed(42)

    all_common_files = []

    # Collect files from all subfolders
    for subfolder in ['TP', 'TN', 'FP', 'FN']:
        method_a_subfolder = os.path.join(method_a_folder, subfolder)
        method_b_subfolder = os.path.join(method_b_folder, subfolder)

        method_a_files = set(os.listdir(method_a_subfolder))
        method_b_files = set(os.listdir(method_b_subfolder))

        # Find common files between method A and method B in this subfolder
        common_files = method_a_files.intersection(method_b_files)

        # Store the full path to the file along with its subfolder for later processing
        all_common_files.extend([(subfolder, file_name) for file_name in common_files])

    # Shuffle the list to mix files from different subfolders
    random.shuffle(all_common_files)

    all_common_files = all_common_files[:500]

    # Process the mixed list of files
    for idx, (subfolder, file_name) in enumerate(all_common_files):
        method_a_subfolder = os.path.join(method_a_folder, subfolder)
        method_b_subfolder = os.path.join(method_b_folder, subfolder)

        # Compare the two explanations using the model
        preference = compare_reasoning_explanations(file_name, llm, method_a_subfolder, method_b_subfolder,
                                                    llm_options=llm_options)

        method_a = os.path.basename(method_a_folder)
        method_b = os.path.basename(method_b_folder)

        # Update counters based on the model's preference
        if preference == method_a:
            method_a_preference_count += 1
        elif preference == method_b:
            method_b_preference_count += 1

        total_comparisons += 1

        # Store the result for this file
        results[file_name] = {
            'subfolder': subfolder,
            'preference': preference
        }

        if idx % 5 == 0:
            print(f'{method_a} preference count:', method_a_preference_count)
            print(f'{method_b} preference count:', method_b_preference_count)
            print('Total comparisons:', total_comparisons)
            print('---------------------------------------')

    # Compute the preference rates
    method_a_preference_rate = 100 * method_a_preference_count / total_comparisons if total_comparisons > 0 else 0
    method_b_preference_rate = 100 * method_b_preference_count / total_comparisons if total_comparisons > 0 else 0

    # Prepare the final results dictionary
    final_results = {
        'preference_rates': {
            f'{method_a} Preference Rate': method_a_preference_rate,
            f'{method_b} Preference Rate': method_b_preference_rate,
            'Total Comparisons': total_comparisons
        },
        'file_results': results
    }

    # Save the results to a JSON file
    with open(f'preference_comparison_results_{LLM}_{method_a}_vs_{method_b}.json', 'w') as f:
        json.dump(final_results, f, indent=4)

    return final_results['preference_rates']


def main():
    parser = argparse.ArgumentParser(description='Compare reasoning explanations using an LLM.')
    parser.add_argument('--method_a', type=str, required=True, help='The first explanation method (e.g., COT).')
    parser.add_argument('--method_b', type=str, required=True, help='The second explanation method (e.g., POS).')

    args = parser.parse_args()

    print(f'Comparing {args.method_a} vs. {args.method_b}...')

    gpt_llm = ChatGPT(
        model_name=model_name,
        key=openai.api_key,
    )

    results = compare_all_explanations(
        method_a_folder=args.method_a,
        method_b_folder=args.method_b,
        llm=gpt_llm
    )
    print(results)


if __name__ == '__main__':
    main()

# Usage: python xai_compare_preference.py --method_a COT --method_b POS