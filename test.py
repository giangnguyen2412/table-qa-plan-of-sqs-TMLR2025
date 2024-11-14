# import os
# import re
#
# # Replace 'path_to_your_folder' with the actual path to your folder containing the txt files
# folder_path = '/home/giang/Downloads/table-qa-2025/logs/GPT4-O_log_WikiTQ_test8_run'
#
# total_steps = 0
# num_files = 0
#
# # List of error messages to check for
# error_messages = [
#     'SQL execution error',
#     'Final step executed but no result found',
#     'Failed to generate next operation',
#     'Maximum steps reached',
#     'No SQL generated'
# ]
#
# for filename in os.listdir(folder_path):
#     if filename.endswith('.txt'):
#         file_path = os.path.join(folder_path, filename)
#         with open(file_path, 'r', encoding='utf-8') as file:
#             content = file.read()
#             # Check if any error message is present in the file
#             if any(error_message in content for error_message in error_messages):
#                 print(f"Skipping file '{filename}' due to presence of error messages.")
#                 continue  # Skip this file and move to the next one
#             # If no error messages, proceed to count the steps
#             steps = len(re.findall(r'Operation\s+\d+', content))
#             total_steps += steps
#             num_files += 1  # Count only files without error messages
#
# if num_files > 0:
#     average_steps = total_steps / num_files
#     print(f'Processed {num_files} valid files.')
#     print(f'Total number of steps: {total_steps}')
#     print(f'Average number of steps per file: {average_steps:.2f}')
# else:
#     print('No valid txt files found in the specified folder.')


import pickle

def load_dataset_from_pkl(filepath):
    """Load dataset from a pickle file."""
    with open(filepath, 'rb') as file:
        dataset = pickle.load(file)
    return dataset

cnt = 0
data = load_dataset_from_pkl('/home/giang/Downloads/tabular-xai/cotable_log/COTABLE_TabFact_dynamic_chain_log_list_jul17_False.pkl')
for dt in data:
    chain = dt[-1]
    act_chain = chain['act_chain']
    for op in act_chain:
        if op in ['skip f_add_column()', 'skip f_group_column()', 'skip f_sort_column()']:
            continue
        else:
            if 'skip' in op:
                cnt += 1
                print(act_chain)
                break
print(cnt)