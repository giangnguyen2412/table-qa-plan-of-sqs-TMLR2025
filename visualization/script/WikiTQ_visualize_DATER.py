import json
from collections import Counter
import os
import re

# Load the predictions data
with open('/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/wikitq_dater_logs/predictions.json', 'r') as file:
    predictions_data = json.load(file)

# Load the sub_tables data from sub_tables.jsonl
sub_tables = []
with open('/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/wikitq_dater_logs/sub_tables.jsonl', 'r') as file:
    for line in file:
        sub_tables.append(json.loads(line))

# Load the sub_tables data from sub_tables.jsonl
sub_questions = []
with open('/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/wikitq_dater_logs/sub_questions.jsonl', 'r') as file:
    for line in file:
        sub_questions.append(json.loads(line))

output_file_path = "/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/wikitq_dater_logs/extracted_predictions_groundtruth_with_sub_tables.json"
# Ensure the output directories exist
output_dir = "/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/visualization/WikiTQ_DATER"
correct_dir = os.path.join(output_dir, "Correct")
wrong_dir = os.path.join(output_dir, "Wrong")
# Create directories if they don't exist
os.makedirs(correct_dir, exist_ok=True)
os.makedirs(wrong_dir, exist_ok=True)

output_json_dir = "/home/giang/Downloads/job1/tabular-xai/plan-of-sqls/visualization/"


# Initialize an empty dictionary to store the extracted data
extracted_data = {}

from collections import Counter


def extract_answer(text):
    split_result = text.lower().split("the answer is :")
    if len(split_result) > 1:
        return split_result[1].strip()
    return None


def process_generations(generations, groundtruth, statement):
    predicted_answers = []
    all_generations = []

    for gen in generations:
        answer = extract_answer(gen[0])
        predicted_answers.append(answer)

        all_generations.append({
            "full_text": gen[0],
            "extracted_answer": answer,
            "log_prob": gen[1],
            "kl_div": gen[2]
        })

    # Filter out any None values before determining the majority vote
    filtered_answers = [answer for answer in predicted_answers if answer is not None]

    if filtered_answers:
        # Determine the majority vote
        majority_vote = Counter(filtered_answers).most_common(1)[0][0]
    else:
        # Handle cases where no valid predictions are found
        majority_vote = None

    return {
        "prediction": majority_vote,
        "groundtruth": groundtruth,
        "statement": statement,
        "all_generations": all_generations
    }

def check_denotation(target_values, predicted_values):
    """Return True if the predicted denotation is correct.

    Args:
        target_values (list[Value])
        predicted_values (list[Value])
    Returns:
        bool
    """
    try:
        # Check size
        if len(target_values) != len(predicted_values):
            return False

        # Check items
        for target in target_values:
            if not any(re.match(target.lower(), pred.lower()) for pred in predicted_values):
                return False

        return True
    except re.error as e:
        print(f"Regular expression error: {e}")
        return None

# Process each entry in the predictions data
for key, value in predictions_data.items():
    # caption = value["data_item"]["table_caption"]
    statement = value["data_item"]["statement"]
    generations = value["generations"]
    groundtruth = value["data_item"]["answer"]

    # Print the current length of the extracted_data dictionary
    print(len(extracted_data))
    # Print the current list of generations
    print(generations)

    predicted_answers = []
    # extracted_data[key] = process_generations(generations, groundtruth, statement)
    for gen in generations:
        split_result = gen[0].split("the answer is :")
        if len(split_result) > 1:
            predicted_answers.append(split_result[1].strip())
        else:
            predicted_answers.append(None)

    # Filter out any None values before determining the majority vote
    filtered_answers = [answer for answer in predicted_answers if answer is not None]

    if filtered_answers:
        # Determine the majority vote
        majority_vote = Counter(filtered_answers).most_common(1)[0][0]
    else:
        # Handle cases where no valid predictions are found
        majority_vote = None

    # Determine the ground truth
    groundtruth = value["data_item"]["answer"]

    # Store the extracted information in the dictionary
    extracted_data[key] = {
        "prediction": majority_vote,
        "groundtruth": groundtruth,
        "statement": statement,
    }


updated_extracted_data = {}
# Add corresponding sub_tables data to extracted_data
for i, (key, value) in enumerate(extracted_data.items()):
    # Assuming sub_tables[i] corresponds to the same order as the extracted_data
    statement = value["statement"]

    for sub_table in sub_tables:
        if sub_table['statement'] in statement:
            value["sub_tables"] = sub_table
            updated_extracted_data[key] = value
            break

    # # Assuming sub_tables[i] corresponds to the same order as the extracted_data
    # value["sub_tables"] = sub_tables[i]
    # updated_extracted_data[key] = value

    for sub_question in sub_questions:
        if sub_question['statement'] in statement:
            value["sub_questions"] = sub_question
            updated_extracted_data[key] = value
            break

# Optionally, save the updated extracted data to a JSON file
with open(output_file_path, 'w') as outfile:
    json.dump(updated_extracted_data, outfile, indent=4)

# Print or return the final extracted_data if needed
print(len(updated_extracted_data))

#######################################


data = updated_extracted_data



import json
import os

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)


import os

# Ensure the output directories exist
# output_dirs = {
#     "TP": os.path.join(output_dir, "TP"),
#     "TN": os.path.join(output_dir, "TN"),
#     "FP": os.path.join(output_dir, "FP"),
#     "FN": os.path.join(output_dir, "FN")
# }
#
# # Create directories if they don't exist
# for dir_path in output_dirs.values():
#     if not os.path.exists(dir_path):
#         os.makedirs(dir_path)

visualization_data = {}

# Loop through each entry in the JSON data
for key, entry in data.items():
    # Initialize the HTML content for this specific entry
    html_content = """
    <html>
    <head>
    <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { text-align: center; }
    .cot-title { color: blue; }
    .pos-title { color: green; }
    h2 { color: black; text-align: left; }
    h3 { color: black; text-align: left; }
    h4 { color: darkslategray; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    table, th, td { border: 1px solid #ddd; padding: 8px; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    .highlight { background-color: #ffffcc; }
    .true { color: green; }
    .false { color: red; }
    .highlighted-text { background-color: yellow; }
    .step-title { background-color: #f1f1f1; color: #444; padding: 10px; margin: 10px 0; font-size: 18px; border-left: 4px solid #888; }
    .step { display: block; }
    .result-label { font-weight: bold; padding: 5px; margin-top: 20px; display: inline-block; }
    .tp { background-color: lightgreen; }
    .tn { background-color: lightblue; }
    .fp { background-color: lightcoral; }
    .fn { background-color: lightgoldenrodyellow; }
    </style>
    </head>
    <body>
    """

    statement = entry["statement"]
    prediction = entry["prediction"]
    groundtruth = entry["groundtruth"]
    sub_tables = entry["sub_tables"]
    # caption = entry["caption"]
    if "sub_questions" in entry:
        sub_questions = entry["sub_questions"]["sub_q"]
        sub_questions = 'AND '.join(sub_questions)
    else:
        sub_questions = 'Not Available!'

    table_text = sub_tables["table_text"]
    rows = sub_tables["rows"]
    cols = sub_tables["cols"]

    # Add the statement and input table title to the HTML content
    html_content += f"<hr><h3><span>Question:</span> {statement.split('in the table')[0].strip()}</h3>"
    html_content += f"<hr><h3><span>Input Table:</span></h3>"

    # Display the Step 1 selection criteria on top of the original table
    html_content += f'<div class="step"><div class="step-title">Step 1: Select Rows (row {", row ".join(rows)}) and Select Columns ({", ".join(cols)})</div>'

    # Display the original table with highlighted text in selected rows and columns
    html_content += '<div id="original-table" class="content"><table><tr>'
    headers = table_text[0]
    selected_indices = [headers.index(col) for col in cols if col in headers]

    for header in headers:
        if header in cols:
            html_content += f"<th><span class='highlighted-text'>{header}</span></th>"
        else:
            html_content += f"<th>{header}</th>"
    html_content += "</tr>"

    for i, row in enumerate(table_text[1:], start=1):
        html_content += "<tr>"
        for j, cell in enumerate(row):
            if str(i) in rows and j in selected_indices:
                html_content += f'<td><span class="highlighted-text">{cell}</span></td>'
            elif str(i) in rows or j in selected_indices:
                html_content += f'<td><span class="highlighted-text">{cell}</span></td>'
            else:
                html_content += f"<td>{cell}</td>"
        html_content += "</tr>"
    html_content += "</table></div></div><hr>"

    # Handle "*" for rows and columns
    if rows == ["*"]:
        rows = [str(i) for i in range(1, len(table_text))]
    if cols == ["*"]:
        cols = headers

    # Sub-table Selection (No highlighting in the intermediate table)
    html_content += f'<div class="step"><div class="step-title">Sub-table Selection</div>'
    html_content += '<div id="sub-table-selection" class="content"><table><tr>'

    # Add selected column headers
    for col in cols:
        if col in headers:
            html_content += f"<th>{col}</th>"
    html_content += "</tr>"

    # Add selected column rows, highlighting selected rows
    for i, row in enumerate(table_text[1:], start=1):
        if str(i) in rows:
            html_content += "<tr>"
            for index in selected_indices:
                html_content += f'<td>{row[index]}</td>'
            html_content += "</tr>"
    html_content += "</table></div></div><hr>"

    # Sub-table Selection for contextual information
    html_content += f'<div class="step"><div class="step-title">Factually-checked information: {sub_questions}</div>'

    # Final Prediction, Groundtruth, and Result Label
    html_content += "<h2>Prompting LLM for the final answer... >>> </h2><hr>"
    # prediction_color = "true" if prediction == "True" else "false"
    # groundtruth_color = "true" if groundtruth == "True" else "false"
    html_content += f'<h3>Prediction: {prediction}</h3>'
    # html_content += f'<h3>Groundtruth: {groundtruth}</h3>'


    if prediction is None:
        prediction = 'None'
    formatted_prediction = prediction if isinstance(prediction, list) else [prediction]
    formatted_groundtruth = groundtruth if isinstance(groundtruth, list) else [groundtruth]
    print(formatted_prediction, formatted_groundtruth)
    correctness = check_denotation(formatted_groundtruth, formatted_prediction)
    if correctness is None:
        continue
    # html_content += result_label


    # Determine the appropriate directory based on correctness
    output_subdir = correct_dir if correctness else wrong_dir

    # Close the HTML content
    html_content += "</body></html>"

    # Save the HTML content to the respective folder based on the correctness
    filename = os.path.join(output_subdir, f"test-{key}.html")
    with open(filename, 'w') as file:
        file.write(html_content)

    print(f"Visualization for key {key} has been saved to '{filename}'")

    html_filename = f"DATER_test-{key}.html"
    # Update the JSON structure with the relevant details
    visualization_data[html_filename] = {
        "filename": f"test-{key}.html",
        "statement": statement,
        "answer": groundtruth,
        "prediction": prediction,
        # "table_caption": caption,
        "method": "DATER",
        "model_correctness": correctness,
    }

# Write the visualization data to a JSON file
json_output_path = os.path.join(output_json_dir, "WikiTQ_DATER_visualization_data.json")
with open(json_output_path, 'w') as json_file:
    json.dump(visualization_data, json_file, indent=4)

print(f"JSON data has been saved to '{json_output_path}'")