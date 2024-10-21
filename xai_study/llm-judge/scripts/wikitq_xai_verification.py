import os
import json
import argparse
import random
import time
import openai
from bs4 import BeautifulSoup
from tqdm import tqdm
import numpy as np

project_directory = '/home/giang/Downloads/job1/tabular-xai/plan-of-sqls'

# OpenAI API Configuration
openai_token = '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'
openai.api_key = openai_token

# Set the model
model_name = 'gpt-4o-mini'  # Update this to the model you want to use


def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def get_html_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def ask_llm(prompt, max_retries=5):
    for _ in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a judge who determines whether a prediction is correct or not."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=10
            )
            return response.choices[0].message['content'].strip()
        except openai.error.OpenAIError as e:
            print(f"Error in LLM API call: {e}")
            if "This model's maximum context length is" in str(e):
                return "Exceed context length"
            time.sleep(20)  # Wait for 20 seconds before retrying
    print("Max retries reached. Skipping this prompt.")
    return None


import random

def get_method_specific_prompt(method):
    base_prompt = """
The Table Question Answering (Table QA) model is working on the WikiTQ dataset, answering questions based on a given table.

You are given an HTML file containing a Question, Input Table, Prediction, and an Explanation clarifying the Prediction.

Your task is to carefully analyze all the information and determine whether the Prediction is correct or not.

Explanation Method: {method}
{method_specific_info}

HTML content:
{html_content}

Answer with '{option1}' or '{option2}' only.

You MUST ignore the order of the options and answer based on the correctness of the Prediction!
"""

    method_info = {
        "DATER": """
DATER is a method that focuses on selecting relevant information from the input table and providing factually-checked information to support the question answering process.
The explanation contains:
1. Sub-table Selection: DATER selects a sub-table from the original input Table that is relevant to the Question.
2. Factually-checked Information: DATER provides factually-checked information that is fact-checked against the Table.
""",
        "POS": """
POS is a Table QA method that breaks down the question-answering process into a series of natural-language steps. Each step represents a specific operation on the table, leading to the final answer.
The explanation contains:
1. Step Descriptions: Each step is accompanied by a natural-language description of the atomic step performed, providing context for the transformation.
2. Intermediate Tables: We display the intermediate tables resulting from each step, showing the state of the table at each step.
3. Attribution Maps: We highlight the rows, columns, and cells involved in each table transformation over intermediate tables. The highlighted cells in this tables are used to create the next table.
Row and Column Highlighting: Rows and Columns used in the current step are highlighted with background-color:yellow.
Cell Highlighting: Cells that directly match the conditions in the current step are green-highlighted with background-color:#90EE90.
"""
    }

    # Randomly shuffle the order of 'Yes' and 'No'
    options = ['Yes', 'No']
    random.shuffle(options)
    option1, option2 = options

    return base_prompt.format(
        method=method,
        method_specific_info=method_info[method],
        html_content="{html_content}",
        option1=option1,
        option2=option2
    )


def process_method(method, sample_size=None):
    base_folder = f"{project_directory}/xai_study/llm-judge/scripts/WikiTQ_Verification/WikiTQ_{method}"
    json_file = f"{project_directory}/xai_study/llm-judge/scripts/WikiTQ_Verification/jsons/WikiTQ_{method}_visualization_data.json"

    metadata = load_json_file(json_file)
    results = {}

    all_files = []
    for subfolder in ['Correct', 'Wrong']:
        subfolder_path = os.path.join(base_folder, subfolder)
        if os.path.exists(subfolder_path):
            all_files.extend([(subfolder, f) for f in os.listdir(subfolder_path) if f.endswith('.html')])

    random.seed(1000)
    random.shuffle(all_files)
    sample_size = 100

    if sample_size is not None:
        all_files = all_files[:sample_size]

    # Create results directory and file
    os.makedirs(f"{project_directory}/xai_study/llm-judge/scripts/WikiTQ_Verification/results", exist_ok=True)
    result_file = f"{project_directory}/xai_study/llm-judge/scripts/WikiTQ_Verification/results/{method}_analysis_results.json"

    # Load existing results if any
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            results = json.load(f)

    # Initialize counters
    correct_analyses = {'Correct': 0, 'Wrong': 0, 'Total': 0}
    total_analyses = {'Correct': 0, 'Wrong': 0, 'Total': 0}
    baseline_analyses = {'Correct': 0, 'Wrong': 0, 'Total': 0}

    # Progress bar
    pbar = tqdm(total=len(all_files), desc=f"Processing {method}", position=0)

    for subfolder, filename in all_files:
        file_key = f"{subfolder}/{filename}"
        if file_key in results:
            pbar.update(1)
            continue

        file_path = os.path.join(base_folder, subfolder, filename)
        html_content = get_html_content(file_path)
        prompt = get_method_specific_prompt(method).format(html_content=html_content)
        llm_analysis = ask_llm(prompt)

        if llm_analysis is None:
            pbar.update(1)
            continue

        metadata_key = f"{method}_{filename}"
        if metadata_key in metadata:
            actual_prediction = metadata[metadata_key]['prediction']
            actual_answer = metadata[metadata_key]['answer']
            is_correct = metadata[metadata_key]['model_correctness']
            r = np.random.choice(['yes', 'no'])

            if (llm_analysis.lower() == 'yes' and is_correct) or (llm_analysis.lower() == 'no' and not is_correct):
                correct_analyses[subfolder] += 1
                correct_analyses['Total'] += 1
            if (r.lower() == 'yes' and is_correct) or (r.lower() == 'no' and not is_correct):
                baseline_analyses[subfolder] += 1
                baseline_analyses['Total'] += 1
            total_analyses[subfolder] += 1
            total_analyses['Total'] += 1

            # Save results for this sample
            results[file_key] = {
                "method": method,
                "subfolder": subfolder,
                "LLM_analysis": llm_analysis,
                "Actual_Correctness": "Yes" if is_correct else "No",
                "Model_Prediction": actual_prediction,
                "Actual_Answer": actual_answer,
                "prompt_to_LLM": prompt
            }

            # Save results to JSON file after each sample
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=4)

            # Calculate and display current accuracies
            acc_correct = (correct_analyses['Correct'] / total_analyses['Correct']) * 100 if total_analyses[
                                                                                                 'Correct'] > 0 else 0
            acc_wrong = (correct_analyses['Wrong'] / total_analyses['Wrong']) * 100 if total_analyses[
                                                                                           'Wrong'] > 0 else 0
            acc_total = (correct_analyses['Total'] / total_analyses['Total']) * 100 if total_analyses[
                                                                                           'Total'] > 0 else 0
            acc_random = (baseline_analyses['Total'] / total_analyses['Total']) * 100 if total_analyses[
                                                                                             'Total'] > 0 else 0

            pbar.set_postfix({
                "Acc(Total)": f"{acc_total:.2f}%",
                "Acc(Correct)": f"{acc_correct:.2f}%",
                "Acc(Wrong)": f"{acc_wrong:.2f}%",
                "Random": f"{acc_random:.2f}%"
            })
            pbar.update(1)
        else:
            print(f"Metadata not found for {metadata_key}")

    pbar.close()

    # Calculate final accuracies
    final_accuracy_correct = (correct_analyses['Correct'] / total_analyses['Correct']) * 100 if total_analyses[
                                                                                                    'Correct'] > 0 else 0
    final_accuracy_wrong = (correct_analyses['Wrong'] / total_analyses['Wrong']) * 100 if total_analyses[
                                                                                              'Wrong'] > 0 else 0
    final_accuracy_total = (correct_analyses['Total'] / total_analyses['Total']) * 100 if total_analyses[
                                                                                              'Total'] > 0 else 0
    final_accuracy_random = (baseline_analyses['Total'] / total_analyses['Total']) * 100 if total_analyses[
                                                                                                'Total'] > 0 else 0

    print(f"\nMethod: {method}")
    print(f"Final Accuracy on Correct samples: {final_accuracy_correct:.2f}%")
    print(f"Final Accuracy on Wrong samples: {final_accuracy_wrong:.2f}%")
    print(f"Overall Accuracy: {final_accuracy_total:.2f}%")
    print(f"Random Baseline Accuracy: {final_accuracy_random:.2f}%")
    print(f"Correct analyses: {correct_analyses['Total']}")
    print(f"Total analyses: {total_analyses['Total']}")

    print(f"Results saved to {result_file}")

    return final_accuracy_total, correct_analyses, total_analyses


def main():
    parser = argparse.ArgumentParser(description='Analyze model explanations and determine correctness.')
    parser.add_argument('--method', type=str, required=True, choices=['DATER', 'POS'],
                        help='The explanation method to process.')
    parser.add_argument('--samples', type=int, default=None,
                        help='Total number of samples to process. If not specified, processes all files.')

    args = parser.parse_args()
    process_method(args.method, args.samples)


if __name__ == "__main__":
    main()
