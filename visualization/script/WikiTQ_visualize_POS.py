import ast
import json
import os
import glob
import sys
import re

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.helper import *
import ast
import re

output_json_dir = "/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/visualization/"

def check_denotation(target_values, predicted_values):
    """Return True if the predicted denotation is correct.

    Args:
        target_values (str): String representation of a list
        predicted_values (str): String representation of a list
    Returns:
        bool
    """
    try:
        # Parse string representations into actual lists
        target_list = ast.literal_eval(target_values)
        predicted_list = ast.literal_eval(predicted_values)

        # Flatten nested lists and convert all elements to lowercase strings
        def flatten_and_lowercase(lst):
            result = []
            for item in lst:
                if isinstance(item, list):
                    result.extend(flatten_and_lowercase(item))
                else:
                    result.append(str(item).lower())
            return result

        target_list = flatten_and_lowercase(target_list)
        predicted_list = flatten_and_lowercase(predicted_list)

        # Check size
        if len(target_list) != len(predicted_list):
            return False

        # Check items
        for target in target_list:
            if not any(re.match(re.escape(target), pred) for pred in predicted_list):
                return False

        return True
    except (ValueError, SyntaxError, re.error) as e:
        print(f"Error: {e}")
        return None

def increment_row_indices(indices_list):
    for sublist in indices_list:
        for index in sublist:
            index[0] += 1
    return indices_list


def parse_wikitq_log(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    question = ""
    groundtruth = ""
    original_table = []
    prediction = ""

    question_token = 'Query:'
    groundtruth_token = 'Groundtruth:'
    caption_token = 'Caption:'
    original_table_token = 'Original table:'

    operation_token = 'Operation'
    highlight_token = 'Selected indices:'
    int_table_token = 'Table after operation:'

    final_answer_token = 'Answer from plan 1:'

    error_flag = False
    fallback_flag = False
    table_caption = ''
    operations = []
    intermediate_tables = []
    highlights = []
    i = 0
    operation_cnt = 0
    while i < len(lines):
        line = lines[i].strip()

        if 'SQL execution error' in line:
            error_flag = True
            break

        if 'Fall-back: TRUE' in line:
            fallback_flag = True

        if question_token in line:
            question = line.split(question_token)[1].strip()

        if groundtruth_token in line:
            groundtruth = line.split(groundtruth_token)[1].strip()

        if caption_token in line:
            table_caption = line.split(caption_token)[1].strip()

        if original_table_token in line:
            original_table = line.split(original_table_token)[1].strip()
            original_table = ast.literal_eval(original_table)

        if operation_token in line and 'Error' not in line:
            operation_cnt += 1
            op_token = f'Operation {operation_cnt}'
            operation = line.split(op_token)[1].strip()
            operations.append(operation)

        if highlight_token in line:
            hls = line.split(highlight_token)[1].strip()
            hls = ast.literal_eval(hls)
            highlights.append(hls)

        if int_table_token in line:
            int_table = line.split(int_table_token)[1].strip()
            int_table = re.sub(r'\bnan\b', 'None', int_table)
            int_table = ast.literal_eval(int_table)
            intermediate_tables.append([int_table, operation, None])

        if final_answer_token in line:
            prediction = line.split(final_answer_token)[1].strip()

        i += 1
    return error_flag, fallback_flag, original_table, question, groundtruth, prediction, operations, intermediate_tables, highlights, table_caption


def highlight_cells_basic(input_table, indices):
    highlighted_table = [row[:] for row in input_table]
    for i, j in indices:
        if i < len(highlighted_table) and j < len(highlighted_table[i]):
            highlighted_table[i][
                j] = f'<span class="highlighted-cell" title="Used in transformation">{highlighted_table[i][j]}</span>'
    return highlighted_table


def visualize_wikitq_logs(log_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Create 'Correct' and 'Wrong' subdirectories
    correct_dir = os.path.join(output_directory, 'Correct')
    wrong_dir = os.path.join(output_directory, 'Wrong')
    os.makedirs(correct_dir, exist_ok=True)
    os.makedirs(wrong_dir, exist_ok=True)

    log_files = glob.glob(os.path.join(log_directory, '*.txt'))
    visualization_data = {}

    for log_file in log_files:
        error_flag, fallback_flag, original_table, question, groundtruth, prediction, operations, intermediate_tables, highlights, table_caption = parse_wikitq_log(
            log_file)

        if error_flag or fallback_flag:
            print(f'Skipping {log_file} - {"Unexecutable" if error_flag else "Fallback"}')
            continue

        intermediate_tables = [[original_table, None, None]] + intermediate_tables
        highlights.append([])
        print(f'Processing {log_file}')
        highlights = increment_row_indices(highlights)
        highlighted_tables = []
        for int_idx in range(len(highlights)):
            highlighted_tables.append(highlight_cells_basic(intermediate_tables[int_idx][0], highlights[int_idx]))

        test_id = os.path.basename(log_file).split('log_')[1].strip()
        test_id = test_id.split('.txt')[0].strip()

        if prediction is None:
            prediction = 'None'
        correctness = check_denotation(prediction, groundtruth)

        if correctness is None:
            continue

        # Determine the appropriate directory based on correctness
        output_subdir = correct_dir if correctness else wrong_dir
        output_file = os.path.join(output_subdir, f'{test_id}.html')

        print('Writing html file into ', output_file)
        wikitq_write_html_file(output_file, original_table, question, groundtruth, prediction, intermediate_tables,
                               highlighted_tables, table_caption, highlights)

        html_filename = f"POS_{test_id}.html"
        # Update the JSON structure with the relevant details
        visualization_data[html_filename] = {
            "filename": f"test-{test_id}.html",
            "statement": question,
            "answer": groundtruth,
            "prediction": prediction,
            "method": "POS",
            "model_correctness": correctness,
        }

    # Write the visualization data to a JSON file
    json_output_path = os.path.join(output_json_dir, "WikiTQ_POS_visualization_data.json")
    with open(json_output_path, 'w') as json_file:
        json.dump(visualization_data, json_file, indent=4)

    print(f"JSON data has been saved to '{json_output_path}'")

# Specify your log and output directories here
log_directory = '/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/WikiTQ_logs/logs'
output_directory = '/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/visualization/WikiTQ_POS/'

visualize_wikitq_logs(log_directory, output_directory)