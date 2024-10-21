import os
import json
import argparse
import random
import time
import openai
from bs4 import BeautifulSoup
from tqdm import tqdm
import numpy as np

# OpenAI API Configuration
# openai_token = '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'
openai_token = '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'
openai.api_key = openai_token

# Set the model
model_name = 'gpt-4o-mini'
seed = 1000


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
                    {"role": "system", "content": "You are a judge who determines whether a prediction is correct or not."},
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
    # Your task is to carefully analyze all the information and determine whether the Prediction is correct or not.

def get_method_specific_prompt(method):
    base_prompt = """
    The Table Fact Verification (TabFact) model is working on verifying if a given Statement is TRUE or FALSE based on a given input Table.
    
    You are given an HTML file containing a Statement, Input Table, Prediction, and an Explanation clarifying the Prediction.
    
    Your task is to carefully analyze the Explanation and determine whether the Prediction is correct or not.
    
    Explanation Method: {method}
    {method_specific_info}
    
    HTML content:
    {html_content}
    
    Answer with '{option1}' or '{option2}' only.
    
    You MUST ignore the order of the options and answer based on the correctness of the Prediction!
    """

    method_info = {
        "COT": """
        COT is a method that breaks down the verification process into a series of intermediate steps. Each step in the chain represents a specific operation on the table, leading to the final prediction.
        The explanation contains:
        1. Step Descriptions: Each step is accompanied by a function with arguments, providing context for the transformation. 
        2. Intermediate Tables: We display the intermediate tables resulting from each function, showing the state of the table at each step. 
        3. Row and Column Highlighting: Rows and Columns used in the current step are highlighted with background-color:yellow.
        """,
        "DATER": """
        DATER is a method that focuses on selecting relevant information from the input table and providing factually-checked information to support the question answering process.
        The explanation contains:
        1. Sub-table Selection: DATER selects a sub-table from the original input Table that is relevant to the Question.
        2. Contextual Information: DATER provides factually-checked information that is fact-checked against the Table.
        """,
        "POS": """
        POS is a Table QA method that breaks down the question-answering process into a series of natural-language steps. Each step represents a specific operation on the table, leading to the final answer.
        The explanation contains:
        1. Step Descriptions: Each step is accompanied by a natural-language description of the atomic step performed, providing context for the transformation.
        2. Intermediate Tables: We display the intermediate tables resulting from each step, showing the state of the table at each step.
        3. Attribution Maps: We highlight the rows, columns, and cells involved in each table transformation over intermediate tables. The highlighted cells in this tables are used to create the next table.
        Row and Column Highlighting: Rows and Columns used in the current step are highlighted with background-color:yellow.
        Cell Highlighting: Cells that directly match the conditions in the current step are green-highlighted with background-color:#90EE90.
        """,
        "Text2SQL": """
        Text-to-SQL is a method that translates the statement into a single SQL query. The SQL query itself serves as the explanation for how the system arrives at its prediction.
        The explanation contains:
        The generated SQL command that will be directly applied to the table to generate the final prediction.
        """,
        "NO_XAI": """
        The NO_XAI method provides a prediction without any explicit explanation. In this case, you should focus solely on the final prediction and any information provided about how it relates to the input table and statement.
        """
    }

    # Randomly shuffle the order of 'Yes' and 'No'
    options = ['Yes', 'No']
    random.seed(seed)
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
    base_folder = f"TabFact_Verification/htmls_{method}"
    if method == "Text2SQL":
        base_folder += "_with_preds"

    json_file = f"TabFact_Verification/jsons/Tabular_LLMs_human_study_vis_6_{method}.json"

    metadata = load_json_file(json_file)
    correct_analyses = 0
    total_analyses = 0
    results = {}

    all_files = []
    for subfolder in ['TP', 'TN', 'FP', 'FN']:
        subfolder_path = os.path.join(base_folder, subfolder)
        if os.path.exists(subfolder_path):
            all_files.extend([(subfolder, f) for f in os.listdir(subfolder_path) if f.endswith('.html')])

    # Add random shuffle
    random.shuffle(all_files)

    if sample_size is not None:
        files_to_process = random.sample(all_files, min(sample_size, len(all_files)))
    else:
        files_to_process = all_files

    # Create results directory and file
    os.makedirs("TabFact_Verification/results", exist_ok=True)
    result_file = f"TabFact_Verification/results/{method}_analysis_results_after_iclr_seed-{seed}.json"

    # Load existing results if any
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            results = json.load(f)
        correct_analyses = sum(1 for result in results.values() if
                               result['LLM_analysis'].lower().startswith(result['Actual_Correctness'].lower()))
        total_analyses = len(results)

    # Progress bar
    pbar = tqdm(total=len(files_to_process), miniters=int(50), desc=f"Processing {method}")
    pbar.update(total_analyses)
    baseline_analyses = 0

    for subfolder, filename in files_to_process:
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
            is_correct = actual_prediction.lower() == actual_answer.lower()
            r = np.random.choice(['yes', 'no'])
            if (llm_analysis.lower().startswith('yes') and is_correct) or (
                    llm_analysis.lower().startswith('no') and not is_correct):
                correct_analyses += 1
            if (r.lower().startswith('yes') and is_correct) or (r.lower().startswith('no') and not is_correct):
                baseline_analyses += 1
            total_analyses += 1

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

            # Calculate and display current accuracy
            current_accuracy = (correct_analyses / total_analyses) * 100
            r_accuracy = (baseline_analyses / total_analyses) * 100
            pbar.set_postfix({"Accuracy": f"{current_accuracy:.2f}%", "Random": f"{r_accuracy:.2f}%"})
        else:
            print(f"Metadata not found for {metadata_key}")

        pbar.update(1)

    pbar.close()

    final_accuracy = (correct_analyses / total_analyses) * 100 if total_analyses > 0 else 0
    print(f"\nMethod: {method}")
    print(f"Final Accuracy of LLM Analysis: {final_accuracy:.2f}%")
    print(f"Correct analyses: {correct_analyses}")
    print(f"Total analyses: {total_analyses}")

    print(f"Results saved to {result_file}")

    return final_accuracy, correct_analyses, total_analyses

def main():
    parser = argparse.ArgumentParser(description='Analyze model explanations and determine correctness for TabFact.')
    parser.add_argument('--method', type=str, required=True, choices=['COT', 'DATER', 'NO_XAI', 'POS', 'Text2SQL'],
                        help='The explanation method to process.')
    parser.add_argument('--samples', type=int, default=None,
                        help='Number of samples to process. If not specified, processes all files.')

    args = parser.parse_args()
    process_method(args.method, args.samples)

if __name__ == "__main__":
    main()

# sample command: python tabfact_xai_verification.py --method POS --samples 10