import os
import json
import argparse
import random
import time
import openai
from bs4 import BeautifulSoup
from tqdm import tqdm

# TODO: uncomment this for JPMC Azure API
# Azure OpenAI Credentials
# credential = AzureCliCredential()
# openai_token = credential.get_token("https://cognitiveservices.azure.com/.default")
# openai.api_key = openai_token.token
#
# openai.api_base = "https://llmopenai.jpmchase.net/WS0001037P-exp"
# openai.api_type = "azure_ad"
# openai.api_version = "2024-02-15-preview"

# Set the model
# model_name = "gpt-3.5-turbo-16k-0613"
model_name = "gpt-4o-mini"

# gpt-4-turbo-2024-04-09

# TODO: uncomment this for personal API
openai_token = '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'
openai.api_key = openai_token

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
                    {"role": "system", "content": "You are a helpful assistant that predicts model outputs."},
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

def process_method(method, sample_size=None):
    if method == 'NO_XAI':
        base_folder = "Forward_Sim/htmls_No_XAI_mod"
    elif method == 'DATER':
        base_folder = "Forward_Sim/htmls_DATER_mod2"
    elif method == 'COT':
        base_folder = "Forward_Sim/htmls_COT_mod"
    elif method == 'POS':
        base_folder = "Forward_Sim/htmls_POS_mod2"
    elif method == 'Text2SQL':
        base_folder = "Forward_Sim/htmls_Text2SQL"
    else:
        return None

    json_file = f"Forward_Sim/jsons/Tabular_LLMs_human_study_vis_6_{method}.json"

    metadata = load_json_file(json_file)
    correct_predictions = 0
    total_predictions = 0
    results = {}

    all_files = []
    for subfolder in ['TP', 'TN', 'FP', 'FN']:
        folder_path = os.path.join(base_folder, subfolder)
        if os.path.exists(folder_path):
            all_files.extend([os.path.join(subfolder, f) for f in os.listdir(folder_path) if f.endswith('.html')])

    if sample_size is not None:
        files_to_process = random.sample(all_files, min(sample_size, len(all_files)))
    else:
        files_to_process = all_files

    # Create results directory and file
    os.makedirs("Forward_Sim/results", exist_ok=True)
    result_file = f"Forward_Sim/results/{method}_results.json"

    # Progress bar
    pbar = tqdm(total=len(files_to_process), desc=f"Processing {method}")

    for file_path in files_to_process:
        subfolder, filename = os.path.split(file_path)
        full_path = os.path.join(base_folder, file_path)

        html_content = get_html_content(full_path)
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        prompt = f"""
        Given an input statement, an Artificial Intelligence (AI) model will output either TRUE or FALSE. 
        Your job in this Simulation task is to use the AI's explanation to guess the machine response. 
        Specifically, please choose which response (TRUE/FALSE) model would output regardless of whether you think that response is correct or not.

        Explanation:
        {text_content}

        Based on this explanation, guess what the model will predict on the Statement based on the provided explanation.
        Answer with only 'TRUE' or 'FALSE':
        """

        llm_prediction = ask_llm(prompt)

        if llm_prediction is None:
            pbar.update(1)
            continue

        metadata_key = f"{method}_{filename}"
        if metadata_key in metadata:
            actual_prediction = metadata[metadata_key]['prediction']
            if llm_prediction.lower() == actual_prediction.lower():
                correct_predictions += 1
            total_predictions += 1

            # Save results for this sample
            results[file_path] = {
                "method": method,
                "LLM_guess": llm_prediction,
                "Actual_Prediction": actual_prediction,
                "prompt_to_LLM": prompt
            }

            # Save results to JSON file after each sample
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=4)

            # Calculate and display current accuracy
            current_accuracy = (correct_predictions / total_predictions) * 100
            pbar.set_postfix({"Accuracy": f"{current_accuracy:.2f}%"})
        else:
            print(f"Metadata not found for {metadata_key}")

        pbar.update(1)

    pbar.close()

    final_accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    print(f"\nMethod: {method}")
    print(f"Final Accuracy: {final_accuracy:.2f}%")
    print(f"Correct predictions: {correct_predictions}")
    print(f"Total predictions: {total_predictions}")

    print(f"Results saved to {result_file}")

    return final_accuracy, correct_predictions, total_predictions

def main():
    parser = argparse.ArgumentParser(description='Process explanations and predict model outputs.')
    parser.add_argument('--method', type=str, required=True, choices=['COT', 'DATER', 'POS', 'Text2SQL', 'NO_XAI'],
                        help='The explanation method to process.')
    parser.add_argument('--samples', type=int, default=None,
                        help='Number of samples to process. If not specified, processes all files.')

    args = parser.parse_args()
    process_method(args.method, args.samples)

if __name__ == "__main__":
    main()

# python xai_forward_simulation.py --method COT --samples 5