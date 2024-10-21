# import os
# import json
# import argparse
# import random
# import time
# import openai
# import re
# from bs4 import BeautifulSoup
# from collections import defaultdict
# from tqdm import tqdm
#
# # OpenAI API Configuration
# openai_token = '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'
# openai.api_key = openai_token
#
# # Set the model
# model_name = "gpt-4o-mini"
#
#
# def get_html_content(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return f.read()
#
#
# def ask_llm(prompt, max_retries=5):
#     for _ in range(max_retries):
#         try:
#             response = openai.ChatCompletion.create(
#                 model=model_name,
#                 messages=[
#                     {"role": "system",
#                      "content": "You are a helpful assistant that ranks explanations based on preference."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 temperature=0,
#                 max_tokens=50
#             )
#             return response.choices[0].message['content'].strip()
#         except openai.error.OpenAIError as e:
#             print(f"Error in LLM API call: {e}")
#             if "This model's maximum context length is" in str(e):
#                 return "Exceed context length"
#             time.sleep(20)  # Wait for 20 seconds before retrying
#     print("Max retries reached. Skipping this prompt.")
#     return None
#
#
# def get_common_files(methods):
#     base_folder = "Preference"
#     common_files = defaultdict(list)
#
#     for subfolder in ['TP', 'TN', 'FP', 'FN']:
#         files_per_method = {}
#         for method in methods:
#             method_folder = f"htmls_{method}" if method != "Text2SQL" else "htmls_Text2SQL_with_preds"
#             folder_path = os.path.join(base_folder, method_folder, subfolder)
#             if os.path.exists(folder_path):
#                 files_per_method[method] = set(os.listdir(folder_path))
#             else:
#                 files_per_method[method] = set()
#
#         common = set.intersection(*files_per_method.values())
#         for file in common:
#             common_files[subfolder].append(file)
#
#     return common_files
#
#
# def parse_ranking(ranking_str, methods):
#     pattern = r'(\d+)\.\s*(\w+)'
#     matches = re.findall(pattern, ranking_str)
#
#     if len(matches) != 4:
#         return None
#
#     ranking = {}
#     for rank, method in matches:
#         if method not in methods:
#             return None
#         ranking[method] = int(rank)
#
#     if set(ranking.keys()) != set(methods) or set(ranking.values()) != set(range(1, 5)):
#         return None
#
#     return ranking
#
#
# def generate_balanced_prompts(explanations, methods):
#     prompts = []
#     for _ in range(3):  # Generate 3 different permutations
#         shuffled_methods = random.sample(methods, len(methods))
#         prompt = f"""
# You are given explanations from four different methods for the same table fact verification task.
# Please rank these explanations based on their clarity, coherence, and helpfulness in understanding the model's reasoning.
# Clarity Definition: How easy is the explanation to understand? Is the language clear and straightforward?
# Coherence Definition: Does the explanation logically flow and make sense as a whole? Are the ideas well-connected?
# Helpfulness in Understanding the Model's Reasoning Definition: How effectively does the explanation help you understand why the model made its decision? Does it reveal the reasoning process?
#
# Provide the ranking from best to worst.
#
# Explanations:
#
# """
#         for method in shuffled_methods:
#             prompt += f"{method}:\n{explanations[method]}\n\n"
#
#         prompt += """
# Please provide the ranking in the format:
# 1. [Method]
# 2. [Method]
# 3. [Method]
# 4. [Method]
# Make sure to use the exact method names (COT, DATER, POS, Text2SQL) and include all four methods in your ranking.
#         """
#         prompts.append(prompt)
#     return prompts
#
#
# def process_explanations(methods, sample_size=None):
#     common_files = get_common_files(methods)
#     total_common_files = sum(len(files) for files in common_files.values())
#     print(f"Total number of common files across all methods: {total_common_files}")
#
#     for subfolder, files in common_files.items():
#         print(f"Common files in {subfolder}: {len(files)}")
#
#     all_files = [(subfolder, filename) for subfolder, files in common_files.items() for filename in files]
#
#     if sample_size is not None:
#         files_to_process = random.sample(all_files, min(sample_size, len(all_files)))
#     else:
#         files_to_process = all_files
#
#     results = {}
#     overall_scores = {method: 0 for method in methods}
#
#     os.makedirs("Preference/results", exist_ok=True)
#     result_file = f"Preference/results/preference_ranking_results_balanced2.json"
#
#     if os.path.exists(result_file):
#         with open(result_file, 'r') as f:
#             existing_data = json.load(f)
#             results = existing_data.get("individual_results", {})
#             overall_scores = existing_data.get("overall_scores", {method: 0 for method in methods})
#
#     pbar = tqdm(total=len(files_to_process), desc="Processing files")
#     pbar.update(len(results))
#
#     for subfolder, filename in files_to_process:
#         file_key = f"{subfolder}/{filename}"
#         if file_key in results:
#             pbar.update(1)
#             continue
#
#         explanations = {}
#         for method in methods:
#             method_folder = f"htmls_{method}" if method != "Text2SQL" else "htmls_Text2SQL_with_preds"
#             file_path = os.path.join("Preference", method_folder, subfolder, filename)
#             html_content = get_html_content(file_path)
#             soup = BeautifulSoup(html_content, 'html.parser')
#             explanations[method] = soup.get_text()
#
#         prompts = generate_balanced_prompts(explanations, methods)
#
#         rankings = []
#         for prompt in prompts:
#             ranking = ask_llm(prompt)
#             if ranking is not None:
#                 parsed_ranking = parse_ranking(ranking, methods)
#                 if parsed_ranking is not None:
#                     rankings.append(parsed_ranking)
#
#         if not rankings:
#             print(f"No valid rankings for {file_key}. Skipping this sample.")
#             pbar.update(1)
#             continue
#
#         # Aggregate rankings
#         aggregated_ranking = {method: sum(ranking[method] for ranking in rankings) / len(rankings) for method in
#                               methods}
#         sorted_ranking = sorted(aggregated_ranking.items(), key=lambda x: x[1])
#
#         results[file_key] = {
#             "individual_rankings": rankings,
#             "aggregated_ranking": aggregated_ranking,
#             "final_ranking": sorted_ranking,
#             "prompts": prompts
#         }
#
#         # Update overall scores
#         for method, rank in aggregated_ranking.items():
#             overall_scores[method] += 5 - rank
#
#         with open(result_file, 'w') as f:
#             json.dump({
#                 "individual_results": results,
#                 "overall_scores": overall_scores,
#             }, f, indent=4)
#
#         current_ranking = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
#         ranking_str = ", ".join([f"{method}: {score:.2f}" for method, score in current_ranking])
#         pbar.set_postfix_str(f"Current ranking: {ranking_str}")
#         pbar.update(1)
#
#     pbar.close()
#
#     overall_ranking = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
#
#     print("\nFinal Overall Ranking:")
#     for rank, (method, score) in enumerate(overall_ranking, 1):
#         print(f"{rank}. {method} (Score: {score:.2f})")
#
#     with open(result_file, 'w') as f:
#         json.dump({
#             "individual_results": results,
#             "overall_scores": overall_scores,
#             "overall_ranking": overall_ranking
#         }, f, indent=4)
#     print(f"Final results saved to {result_file}")
#
#
# def main():
#     parser = argparse.ArgumentParser(description='Rank explanations from different methods based on preference.')
#     parser.add_argument('--samples', type=int, default=None,
#                         help='Number of samples to process. If not specified, processes all common files.')
#
#     args = parser.parse_args()
#     methods = ['COT', 'DATER', 'POS', 'Text2SQL']
#     process_explanations(methods, args.samples)
#
#
# if __name__ == "__main__":
#     main()
#
# # python xai_preference.py --samples 5


import os
import json
import argparse
import random
import time
import openai
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from tqdm import tqdm
from azure.identity import AzureCliCredential
import collections as c
import numpy as np

# # TODO: uncomment this for JPMC Azure API
# # Azure OpenAI Credentials
# credential = AzureCliCredential()
# openai_token = credential.get_token("https://cognitiveservices.azure.com/.default")
# openai.api_key = openai_token.token
#
# openai.api_base = "https://llmopenai-02.jpmchase.net/WS0001037P-exp-use2/"
# openai.api_type = "azure_ad"
# openai.api_version = "2024-02-15-preview"
#
# # Set the model
# model_name = "gpt-4o-2024-05-13"


# OpenAI API Configuration
openai_token = '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'
openai.api_key = openai_token

# Set the model
model_name = "gpt-4o-mini"

# model_name="gpt-4-turbo-2024-04-09"
def get_html_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def ask_llm(prompt, max_retries=5):
    for _ in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": "You are a helpful assistant that ranks explanations based on preference."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=40
            )
            # print(response)
            return response.choices[0].message['content']
        except openai.error.OpenAIError as e:
            print(f"Error in LLM API call: {e}")
            if "This model's maximum context length is" in str(e):
                return "Exceed context length"
            time.sleep(2)  # Wait for 20 seconds before retrying
    print("Max retries reached. Skipping this prompt.")
    return None


def get_common_files(methods):
    base_folder = "Preference"
    common_files = defaultdict(list)

    for subfolder in ['TP', 'TN', 'FP', 'FN']:
        files_per_method = {}
        for method in methods:
            method_folder = f"htmls_{method}" if method != "Text2SQL" else "htmls_Text2SQL_with_preds"
            folder_path = os.path.join(base_folder, method_folder, subfolder)
            if os.path.exists(folder_path):
                files_per_method[method] = set(os.listdir(folder_path))
            else:
                files_per_method[method] = set()

        common = set.intersection(*files_per_method.values())
        for file in common:
            common_files[subfolder].append(file)

    return common_files


def parse_ranking(ranking_str, methods):
    pattern = r'(\d+)\.\s*(\w+)'
    matches = re.findall(pattern, ranking_str)

    if len(matches) != 4:
        return None

    ranking = {}
    for rank, method in matches:
        if method not in methods:
            return None
        ranking[method] = int(rank)

    if set(ranking.keys()) != set(methods) or set(ranking.values()) != set(range(1, 5)):
        return None

    return ranking


def generate_balanced_prompts(explanations, methods):
    prompts = []
    num_methods = len(methods)

    # Create a dictionary mapping methods to their descriptions
    method_descriptions = {
        "DATER": """DATER is a method that focuses on selecting relevant information from the input table and providing contextual information to support the statement verification process.
    The explanation contains:
    1. Sub-table Selection: Dater selects a sub-table from the original input Table that is relevant to the Statement.
    2. Contextual Information: Dater provides contextual information that is fact-checked against the Table.""",

        "COT": """COT is a method that breaks down the question-answering process into a series of intermediate tables. Each step in the chain represents a specific operation on the table, leading to the final answer.
    The explanation contains:
    1. Step Descriptions: Each step is accompanied by a function with arguments, providing context for the transformation. 
    2. Intermediate Tables: We display the intermediate tables resulting from each function, showing the state of the data at each step. 
    3. Row and Column Highlighting: Rows and Columns used in the current step are highlighted with background-color:yellow.""",

        "Text2SQL": """Text2SQL is a method that translates the natural language query into a single SQL query. The SQL query itself serves as the explanation for how the system arrives at its answer.
    The explanation contains:
    The generated SQL command that will be directly applied onto the table to generate the final answer.""",

        "POS": """POS is a Table QA method that breaks down the question-answering process into a series of natural-language steps. Each step represents a specific operation on the table, leading to the final answer.
    The explanation contains:
    1. Step Descriptions: Each step is accompanied by a natural-language description of the atomic step performed, providing context for the transformation. 
    2. Intermediate Tables: We display the intermediate tables resulting from each step, showing the state of the data at each step. 
    3. Attribution Maps: We highlight the the rows, columns, and cells involved in each table transformation over intermediate tables. 
    Row and Column Highlighting: Rows and Columns used in the current step are highlighted with background-color:yellow.
    Cell Highlighting: Cells that directly match the conditions in the current step are highlighted with background-color:#90EE90."""
    }

    for i in range(num_methods):
        shuffled_methods = methods[i:] + methods[:i]
        prompt = f"""
You are given explanations from four different methods for the same table fact verification task.
Please rank these explanations based on their clarity, coherence, and helpfulness in understanding the model's reasoning.
Clarity Definition: How easy is the explanation to understand? Is the language clear and straightforward?
Coherence Definition: Does the explanation logically flow and make sense as a whole? Are the ideas well-connected?
Helpfulness in Understanding the Model's Reasoning Definition: How effectively does the explanation help you understand why the model made its decision? Does it reveal the reasoning process?

Provide the ranking from best to worst.

Explanations:

"""
        for method in shuffled_methods:
            prompt += f"{method}:\n{explanations[method]}\n\n"

        prompt += "\nExplanation Descriptions:\n\n"
        for method in shuffled_methods:
            prompt += f"{method}: {method_descriptions[method]}\n\n"

        prompt += """
Please provide the ranking in the format:
1. [Method]
2. [Method]
3. [Method]
4. [Method]
Make sure to use the exact method names and include all four methods in your ranking.
        """
        prompts.append(prompt)

    return prompts


def process_explanations(methods, sample_size=None):
    common_files = get_common_files(methods)
    total_common_files = sum(len(files) for files in common_files.values())
    print(f"Total number of common files across all methods: {total_common_files}")

    for subfolder, files in common_files.items():
        print(f"Common files in {subfolder}: {len(files)}")

    all_files = [(subfolder, filename) for subfolder, files in common_files.items() for filename in files]

    if sample_size is not None:
        files_to_process = random.sample(all_files, min(sample_size, len(all_files)))
    else:
        files_to_process = all_files

    results = {}
    overall_scores = {method: 0 for method in methods}

    os.makedirs("Preference/results", exist_ok=True)
    result_file = f"Preference/results/preference_ranking_results_balanced_add_desc.json"

    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            existing_data = json.load(f)
            results = existing_data.get("individual_results", {})
            overall_scores = existing_data.get("overall_scores", {method: 0 for method in methods})

    pbar = tqdm(total=len(files_to_process), desc="Processing files")
    pbar.update(len(results))
    full_ranking = c.defaultdict(list)
    for subfolder, filename in files_to_process:
        file_key = f"{subfolder}/{filename}"
        if file_key in results:
            pbar.update(1)
            continue

        explanations = {}
        for method in methods:
            method_folder = f"htmls_{method}" if method != "Text2SQL" else "htmls_Text2SQL_with_preds"
            file_path = os.path.join("Preference", method_folder, subfolder, filename)
            html_content = get_html_content(file_path)
            # soup = BeautifulSoup(html_content, 'html.parser')
            # explanations[method] = soup.get_text()
            explanations[method] = html_content
            # breakpoint()

        prompts = generate_balanced_prompts(explanations, methods)

        rankings = []
        for prompt in prompts:
            llm_response = ask_llm(prompt)
            # print(ranking)
            if llm_response is not None:
                parsed_ranking = parse_ranking(llm_response, methods)
                if parsed_ranking is not None:
                    rankings.append(parsed_ranking)

        if not rankings:
            print(f"No valid rankings for {file_key}. Skipping this sample.")
            pbar.update(1)
            continue

        # Aggregate rankings
        for method in methods:
            for ranking in rankings:
                # print(ranking)
                full_ranking[method].append(ranking[method])
        # aggregated_ranking = {method: sum(ranking[method] for ranking in rankings) / len(rankings) for method in
        #                       methods}
        aggregated_ranking = {k: np.mean(v) for k, v in full_ranking.items()}

        results[file_key] = {
            "individual_rankings": rankings,
            "aggregated_ranking": aggregated_ranking,
            "final_ranking": aggregated_ranking,
            "prompts": prompts,
            "llm_response": llm_response,
        }

        # # Update overall scores
        # for method, rank in aggregated_ranking.items():
        #     overall_scores[method] += 5 - rank

        with open(result_file, 'w') as f:
            json.dump({
                "individual_results": results,
                "overall_scores": aggregated_ranking,
            }, f, indent=4)

        current_ranking = sorted(aggregated_ranking.items(), key=lambda x: x[1])
        ranking_str = ", ".join([f"{method}: {score:.2f}" for method, score in current_ranking])
        pbar.set_postfix_str(f"Current ranking: {ranking_str}")
        pbar.update(1)

    pbar.close()

    overall_ranking = sorted(aggregated_ranking.items(), key=lambda x: x[1])

    print("\nFinal Overall Ranking:")
    for rank, (method, score) in enumerate(overall_ranking, 1):
        print(f"{rank}. {method} (Score: {score:.2f})")

    with open(result_file, 'w') as f:
        json.dump({
            "individual_results": results,
            "overall_scores": overall_scores,
            "overall_ranking": overall_ranking
        }, f, indent=4)
    print(f"Final results saved to {result_file}")


def main():
    parser = argparse.ArgumentParser(description='Rank explanations from different methods based on preference.')
    parser.add_argument('--samples', type=int, default=None,
                        help='Number of samples to process. If not specified, processes all common files.')

    args = parser.parse_args()
    methods = ['COT', 'DATER', 'POS', 'Text2SQL']
    process_explanations(methods, args.samples)


if __name__ == "__main__":
    main()

# python xai_preference.py --samples 5