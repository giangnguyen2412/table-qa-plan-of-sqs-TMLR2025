import ast
import json
import os
import glob
import sys

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.helper import *

def increment_row_indices(indices_list):
    # Iterate through the list
    for sublist in indices_list:
        # Iterate through each 2D index in the sublist
        for index in sublist:
            # Increment the row index (first element of the 2D index)
            index[0] += 1
    return indices_list

def parse_log(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()
    
    statement = ""
    groundtruth = ""
    original_table = []
    prediction = ""
    
    statement_token = 'Plan 1: Statement:'
    groundtruth_token = 'Plan 1: Groundtruth:'
    caption_token = 'Caption:'
    original_table_token = 'Original table:'

    operation_token = 'Operation'
    highlight_token = 'Selected indices:'
    int_table_token = 'Table after operation:'

    final_answer_token = 'Answer from plan 1:'
    
    error_flag = False
    table_caption = ''
    operations = []
    intermediate_tables = []
    highlights = []
    i = 0
    operation_cnt = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skipping examples using fallback
        if 'SQL execution error' in line:
            error_flag = True
            break

        if 'Extract' in line:
            print('Adding col')
            print(log_file)

        if statement_token in line:
            statement = line.split(statement_token)[1].strip()
        
        if groundtruth_token in line:
            groundtruth = line.split(groundtruth_token)[1].strip()
        
        if caption_token in line:
            table_caption = line.split(caption_token)[1].strip()

        if original_table_token in line:
            original_table = line.split(original_table_token)[1].strip()
            original_table = ast.literal_eval(original_table)

        # adding 'Error' check to ignore unexecutable samples
        if operation_token in line and 'Error' not in line:
            operation_cnt += 1
            op_token = f'Operation {operation_cnt}'
            try:
                operation = line.split(op_token)[1].strip()
            except Exception as e:
                print(operation_cnt)
                print(line)
                print('Two log files are being concatenated!!')
                return True, None, None, None, None, None, None, None, None
            operations.append(operation)
        
        if highlight_token in line:
            hls = line.split(highlight_token)[1].strip()
            hls = ast.literal_eval(hls)
            highlights.append(hls)

        if int_table_token in line:
            int_table = line.split(int_table_token)[1].strip()
            print(int_table)
            print(type(int_table))
            int_table = re.sub(r'\bnan\b', 'None', int_table)
            int_table = ast.literal_eval(int_table)
            intermediate_tables.append([int_table, operation, None])

        if final_answer_token in line:
            prediction = line.split(final_answer_token)[1].strip()
        
        i += 1
    return error_flag, original_table, statement, groundtruth, prediction, operations, intermediate_tables, highlights, table_caption

#######################################
def highlight_cells_basic(input_table, indices):
    highlighted_table = [row[:] for row in input_table]
    for i, j in indices:
        highlighted_table[i][j] = f'<span class="highlighted-cell" title="Used in transformation">{highlighted_table[i][j]}</span>'
    return highlighted_table

def visualize_logs(log_parent_dir):
    categories = ['TP', 'FP', 'TN', 'FN']

    if XAI_METHOD == 'NO_XAI':
        parent_dir = f'{project_directory}/visualization/script/htmls_NO_XAI'
    else:
        parent_dir = f'{project_directory}/visualization/script/htmls_POS'
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    for category in categories:
        log_dir = os.path.join(log_parent_dir, category)
        log_files = glob.glob(os.path.join(log_dir, '*.txt'))

        for log_file in log_files:
            unexecutable, original_table, statement, groundtruth, prediction, operations, intermediate_tables, highlights, table_caption = parse_log(log_file)
            # Skip samples that are not executable
            if unexecutable:
                print('Skipping', log_file)
                continue
            intermediate_tables = [[original_table, None, None]] + intermediate_tables
            highlights.append([])
            print(log_file)
            # print(highlights)
            highlights = increment_row_indices(highlights)
            highlighted_tables = []
            for int_idx in range(len(highlights)):
                highlighted_tables.append(highlight_cells_basic(intermediate_tables[int_idx][0], highlights[int_idx]))

            output_dir = os.path.join(parent_dir, category)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            test_id = os.path.basename(log_file).split('log_')[1].strip()
            test_id = test_id.split('.txt')[0].strip()
            output_file = os.path.join(output_dir, f'{test_id}.html')
            print('Writing html file into ', output_file)
            write_html_file(output_file, original_table, statement, groundtruth, prediction, intermediate_tables, highlighted_tables, table_caption, highlights)

# Specify your log parent directory here
log_parent_directory = f'{project_directory}/{planning_log_path}'
visualize_logs(log_parent_directory)
