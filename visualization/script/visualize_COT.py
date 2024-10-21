import pickle
import pandas as pd

import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


from utils.load_data import load_tabfact_dataset
from utils.llm import ChatGPT
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *

# Path to your pickle files
final_result_path = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/results/tabfact/COTABLE_TabFact_final_result_jul17_False.pkl'
dynamic_chain_log_path = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/results/tabfact/COTABLE_TabFact_dynamic_chain_log_list_jul17_False.pkl'
history_result_path = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/results/tabfact/COTABLE_TabFact_cotable_log_jul17_False.pkl'

def tabfact_match_func(sample, strategy="top"):
    results = sample["chain"][-1]["parameter_and_conf"]

    if strategy == "top":
        res = results[0][0]
    elif strategy == "weighted":
        res_conf_dict = {}
        for res, conf in results:
            if res not in res_conf_dict:
                res_conf_dict[res] = 0
            res_conf_dict[res] += conf
        res_conf_rank = sorted(res_conf_dict.items(), key=lambda x: x[1], reverse=True)
        res = res_conf_rank[0][0]
    else:
        raise NotImplementedError

    res = res.lower()
    if res == "true":
        res = "yes"
    if res == "false":
        res = "no"
    if res == "yes" and sample["label"] == 1:
        return True
    elif res == "no" and sample["label"] == 0:
        return True
    else:
        return False

def tabfact_match_func_for_samples(all_samples, strategy="top"):
    results = []
    for sample in all_samples:
        if sample == None:
            print(sample)
        else:
            try:
                if tabfact_match_func(sample, strategy):
                    results.append((sample, True))
                else:
                    results.append((sample, False))
            except:
                print(f"Error processing sample {sample['id']}")
                continue
    return results


# Load the final result pickle file
with open(final_result_path, 'rb') as file:
    final_data = pickle.load(file)

# Load the dynamic chain log list pickle file
with open(dynamic_chain_log_path, 'rb') as file:
    dynamic_chain_log_list = pickle.load(file)

# Check the type of the loaded data and convert it to a DataFrame if possible
if isinstance(final_data, list):
    results = tabfact_match_func_for_samples(final_data)
    final_df = pd.DataFrame({
        'id': [sample['id'] for sample, result in results],
        'statement': [sample['statement'] for sample, result in results],
        'label': [sample['label'] for sample, result in results],
        'result': [result for sample, result in results],
        'table_caption': [sample['table_caption'] for sample, result in results],
        'table_text': [sample['table_text'] for sample, result in results],
        'table_id': [sample['table_id'] for sample, result in results],
        'cleaned_statement': [sample['cleaned_statement'] for sample, result in results],
    })
else:
    raise ValueError("Unexpected data format")

# Filter out the samples where the model failed
failed_df = final_df[final_df['result'] == False]

# Analyze the failed samples
failure_analysis = failed_df.copy()
failure_analysis['error_type'] = failure_analysis.apply(
    lambda row: 'False Positive' if row['label'] == 0 else 'False Negative', axis=1
)

# Associate the failed samples with the dynamic chain log list
failed_logs = []
for index, row in failure_analysis.iterrows():
    sample_id = row['id']
    sample_index = int(sample_id.split('-')[-1])  # Assuming the ID is in the format 'test-0', 'test-1', etc.
    # print(sample_index)
    # print(len(dynamic_chain_log_list))
    # print(dynamic_chain_log_list)
    failed_logs.append({
        'id': sample_id,
        'statement': row['statement'],
        'label': row['label'],
        'error_type': row['error_type'],
        'dynamic_chain_log': dynamic_chain_log_list[index]
    })

# Convert the failed logs to a DataFrame for easier analysis
failed_logs_df = pd.DataFrame(failed_logs)

# Extract and analyze the dynamic_chain_log column for the first few failed samples
# for index, row in failed_logs_df.head(3).iterrows():  # Analyze the first 3 samples
for index, row in failed_logs_df.iterrows():  # Analyze the first 3 samples
    sample_id = row['id']
    statement = row['statement']
    label = row['label']
    error_type = row['error_type']
    dynamic_chain_log = row['dynamic_chain_log']  # Converting string representation of list to actual list

#TODO: visualzie the wrong cases in the failed_logs_df to see why the model failed

# Columns of failure_analysis DataFrame:
# ['id', 'statement', 'label', 'error_type', 'dynamic_chain_log']
# Display the columns of the failure_analysis DataFrame
# print("Columns of failure_analysis DataFrame:", failure_analysis.columns.tolist())

# Display the failed logs DataFrame
# print(failed_logs_df)

# Save the failed logs DataFrame to a CSV file for further analysis if needed
# failed_logs_df.to_csv('failed_samples_with_logs_analysis.csv', index=False)


############################################################################################################

import pickle
import pandas as pd
from jinja2 import Template


# Function to generate HTML content for a sample
def generate_html(sample_id, statement, label, error_type, dynamic_chain_log):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Analysis - {{ sample_id }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .step { margin-bottom: 20px; }
            .step h3 { margin: 0; }
            .step pre { background: #f4f4f4; padding: 10px; border: 1px solid #ddd; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            table, th, td { border: 1px solid #ddd; }
            th, td { padding: 8px; text-align: left; }
        </style>
    </head>
    <body>
        <h1>Sample ID: {{ sample_id }}</h1>
        <p><strong>Statement:</strong> {{ statement }}</p>
        <p><strong>Label:</strong> {{ label }}</p>
        <p><strong>Error Type:</strong> {{ error_type }}</p>
        <h2>Dynamic Chain Log:</h2>
        {% for step in dynamic_chain_log %}
        <div class="step">
            <h3>Step {{ loop.index }}</h3>
            <p><strong>Last Operation:</strong> {{ step['last_operation'] }}</p>
            <p><strong>Possible Next Operations:</strong></p>
            <pre>{{ step['possible_next_operations'] }}</pre>
            <p><strong>Prompt:</strong></p>
            <pre>{{ step['prompt'] }}</pre>
            <p><strong>Response:</strong></p>
            <pre>{{ step['response'] }}</pre>
            <p><strong>Generated Operations:</strong></p>
            <pre>{{ step['generate_operations'] }}</pre>
            <p><strong>Next Operation:</strong></p>
            <pre>{{ step['next_operation'] }}</pre>
        </div>
        <hr>
        {% endfor %}
    </body>
    </html>
    """
    template = Template(html_template)
    html_content = template.render(
        sample_id=sample_id,
        statement=statement,
        label=label,
        error_type=error_type,
        dynamic_chain_log=dynamic_chain_log
    )
    return html_content


# Load the final result pickle file
with open(final_result_path, 'rb') as file:
    final_data = pickle.load(file)

# Load the dynamic chain log list pickle file
with open(dynamic_chain_log_path, 'rb') as file:
    dynamic_chain_log_list = pickle.load(file)

# Check the type of the loaded data and convert it to a DataFrame if possible
if isinstance(final_data, list):
    results = tabfact_match_func_for_samples(final_data)
    final_df = pd.DataFrame({
        'id': [sample['id'] for sample, result in results],
        'statement': [sample['statement'] for sample, result in results],
        'label': [sample['label'] for sample, result in results],
        'result': [result for sample, result in results],
        'table_caption': [sample['table_caption'] for sample, result in results],
        'table_text': [sample['table_text'] for sample, result in results],
        'table_id': [sample['table_id'] for sample, result in results],
        'cleaned_statement': [sample['cleaned_statement'] for sample, result in results],
    })
else:
    raise ValueError("Unexpected data format")

# Filter out the samples where the model failed
failed_df = final_df[final_df['result'] == False]

# failed_df = final_df

# Analyze the failed samples
failure_analysis = failed_df.copy()
failure_analysis['error_type'] = failure_analysis.apply(
    lambda row: 'False Positive' if row['label'] == 0 else 'False Negative', axis=1
)

# Associate the failed samples with the dynamic chain log list
failed_logs = []
for index, row in failure_analysis.iterrows():
    sample_id = row['id']
    sample_index = int(sample_id.split('-')[-1])  # Assuming the ID is in the format 'test-0', 'test-1', etc.
    failed_logs.append({
        'id': sample_id,
        'statement': row['statement'],
        'label': row['label'],
        'error_type': row['error_type'],
        'dynamic_chain_log': dynamic_chain_log_list[index]
    })

# Convert the failed logs to a DataFrame for easier analysis
failed_logs_df = pd.DataFrame(failed_logs)

# Generate HTML files for the first few failed samples
for index, row in failed_logs_df.iterrows():  # Analyze the first 3 samples
    sample_id = row['id']
    statement = row['statement']
    label = row['label']
    error_type = row['error_type']
    dynamic_chain_log = row['dynamic_chain_log']  # List of dictionaries representing the chain steps

    html_content = generate_html(sample_id, statement, label, error_type, dynamic_chain_log)

    # Save the HTML content to a file
    # with open(f'{sample_id}_analysis.html', 'w') as f:
    #     f.write(html_content)

# print("HTML files for the first few failed samples have been generated.")

def highlight_cells_basic(input_table, indices):
    highlighted_table = [row[:] for row in input_table]
    for i, j in indices:
        highlighted_table[i][j] = f'<span class="highlighted-cell" title="Used in transformation">{highlighted_table[i][j]}</span>'
    return highlighted_table

def process_and_visualize_pickles(history_result_path):
    with open(history_result_path, 'rb') as file:
        history = pickle.load(file)

    output = history['(0) simpleQuery_fewshot']
    # breakpoint()
    for sample, output_sample in enumerate(output):
        cotable_log = get_table_log(output_sample)
        test_sample_id = output_sample['id']
        table_caption =  output_sample['table_caption']

        answer = 'True' if output_sample['label'] == 1 else 'False'
        statement = output_sample["statement"]
        table_text = output_sample["table_text"]

        log_entries = [{"input_table": table_text}]

        for table_info in cotable_log:
            if table_info["act_chain"]:
                table_text = table_info["table_text"]
                table_action = table_info["act_chain"][-1]
                if "skip" in table_action:
                    continue
                if "query" in table_action:
                    result = table_info["cotable_result"]
                    log_entries.append({
                        "table_text": table_text,
                        "act_chain": table_info["act_chain"],
                        "cotable_result": result
                    })
                else:
                    log_entry = {
                        "table_text": table_text,
                        "act_chain": table_info["act_chain"]
                    }
                    if 'group_sub_table' in table_info:
                        log_entry["group_sub_table"] = table_info["group_sub_table"]
                    log_entries.append(log_entry)

        prediction = log_entries[-1]['cotable_result']
        result_table, result_indices, intermediate_tables, relevant_indices = process_COT_log(log_entries)
        # breakpoint()
        original_table = log_entries[0]['input_table']
        highlights = relevant_indices

        highlighted_tables = [highlight_cells_basic(intermediate_tables[int_idx][0], highlights[int_idx]) for int_idx in range(len(highlights))]
        # breakpoint()
        if prediction == 'YES':
            prediction = 'True'
        elif prediction == 'NO':
            prediction = 'False'

        if prediction == answer:
            correctness_dir = "TP" if prediction == "True" else "TN"
        else:
            correctness_dir = "FP" if prediction == "True" else "FN"

        output_dir = os.path.join('/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/plan-of-sqls/visualization/htmls_COT', correctness_dir)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'{test_sample_id}.html')
        write_html_file(output_file, original_table, statement, answer, prediction, intermediate_tables, highlighted_tables, table_caption, highlights)
        # print(f"HTML file '{output_file}' has been created.")
        # print('#' * 50)

# Example usage
process_and_visualize_pickles(history_result_path)