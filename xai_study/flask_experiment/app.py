from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import json
import random
import os
import string
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this to a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Directories for visualizations
VISUALIZATION_DIRS_PLAN_OF_SQLS = {
    "TP": "visualizations/TP",
    "TN": "visualizations/TN",
    "FP": "visualizations/FP",
    "FN": "visualizations/FN"
}

VISUALIZATION_DIRS_CHAIN_OF_TABLE = {
    "TP": "htmls_COT/TP",
    "TN": "htmls_COT/TN",
    "FP": "htmls_COT/FP",
    "FN": "htmls_COT/FN"
}


# Load all sample files from the directories based on the selected method
def load_samples(method):
    if method == "Chain-of-Table":
        visualization_dirs = VISUALIZATION_DIRS_CHAIN_OF_TABLE
    else:
        visualization_dirs = VISUALIZATION_DIRS_PLAN_OF_SQLS

    samples = {"TP": [], "TN": [], "FP": [], "FN": []}
    for category, dir_path in visualization_dirs.items():
        for filename in os.listdir(dir_path):
            if filename.endswith(".html"):
                samples[category].append(filename)
    return samples


# Randomly select balanced samples
def select_balanced_samples(samples):
    tp_fp_samples = random.sample(samples["TP"] + samples["FP"], 5)
    tn_fn_samples = random.sample(samples["TN"] + samples["FN"], 5)
    return tp_fp_samples + tn_fn_samples


def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        seed = request.form.get('seed')
        method = request.form.get('method')

        if not username or not seed or not method:
            return "Missing username, seed, or method", 400

        seed = int(seed)
        random.seed(seed)
        all_samples = load_samples(method)
        selected_samples = select_balanced_samples(all_samples)
        random_string = generate_random_string()
        filename = f'{username}_{seed}_{method}_{random_string}.json'  # Append method to filename

        session['selected_samples'] = selected_samples
        session['responses'] = []  # Initialize responses list
        session['method'] = method  # Store the selected method

        return redirect(url_for('experiment', username=username, sample_index=0, seed=seed, filename=filename))
    return render_template('index.html')


@app.route('/experiment/<username>/<sample_index>/<seed>/<filename>', methods=['GET'])
def experiment(username, sample_index, seed, filename):
    sample_index = int(sample_index)
    selected_samples = session.get('selected_samples', [])
    method = session.get('method')  # Retrieve the selected method

    if sample_index >= len(selected_samples):
        return redirect(url_for('completed', filename=filename))

    visualization_file = selected_samples[sample_index]
    visualization_path = None

    # Determine the correct visualization directory based on the method
    if method == "Chain-of-Table":
        visualization_dirs = VISUALIZATION_DIRS_CHAIN_OF_TABLE
    else:
        visualization_dirs = VISUALIZATION_DIRS_PLAN_OF_SQLS

    # Find the correct visualization path
    for category, dir_path in visualization_dirs.items():
        if visualization_file in os.listdir(dir_path):
            visualization_path = f"{category}/{visualization_file}"
            break

    if not visualization_path:
        return "Visualization file not found", 404

    statement = "Please make a decision to Accept/Reject the AI prediction based on the explanation."
    return render_template('experiment.html',
                           sample_id=sample_index,
                           statement=statement,
                           visualization=visualization_path,
                           username=username,
                           seed=seed,
                           sample_index=sample_index,
                           filename=filename)

@app.route('/visualizations/<path:path>')
def send_visualization(path):
    # Determine which visualization folder to use based on the selected method
    method = session.get('method')
    if method == "Chain-of-Table":
        visualization_dir = 'htmls_COT'
    else:  # Default to Plan-of-SQLs
        visualization_dir = 'visualizations'

    # Serve the file from the appropriate directory
    return send_from_directory(visualization_dir, path)


@app.route('/feedback', methods=['POST'])
def feedback():
    sample_id = request.form['sample_id']
    feedback = request.form['feedback']
    username = request.form['username']
    seed = request.form['seed']
    sample_index = int(request.form['sample_index'])
    filename = request.form['filename']

    selected_samples = session.get('selected_samples', [])
    responses = session.get('responses', [])

    # Store the feedback
    responses.append({
        'sample_id': sample_id,
        'feedback': feedback
    })
    session['responses'] = responses

    # Create the result directory if it doesn't exist
    result_dir = 'human_study'
    os.makedirs(result_dir, exist_ok=True)

    # Load existing data if the JSON file exists
    filepath = os.path.join(result_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    # Update data with the current feedback
    data[sample_index] = {
        'Username': username,
        'Seed': seed,
        'Sample ID': sample_id,
        'Task': f"Please make a decision to Accept/Reject the AI prediction based on the explanation.",
        'User Feedback': feedback
    }

    # Save updated data to the file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

    next_sample_index = sample_index + 1
    if next_sample_index >= len(selected_samples):
        return redirect(url_for('completed', filename=filename))

    return redirect(
        url_for('experiment', username=username, sample_index=next_sample_index, seed=seed, filename=filename))

@app.route('/completed/<filename>')
def completed(filename):
    # Load responses from the session
    responses = session.get('responses', [])

    # Determine which JSON file to load based on the method
    method = session.get('method')
    if method == "Chain-of-Table":
        json_file = 'Tabular_LLMs_human_study_vis_6_COT.json'
    else:  # Default to Plan-of-SQLs
        json_file = 'Tabular_LLMs_human_study_vis_6.json'

    # Load the ground truth data from the appropriate JSON file
    with open(json_file, 'r') as f:
        ground_truth = json.load(f)

    # Initialize counters
    correct_responses = 0
    accept_count = 0
    reject_count = 0

    for response in responses:
        sample_id = response['sample_id']
        feedback = response['feedback']
        index = sample_id.split('-')[1].split('.')[0]  # Extract index from filename

        # Count the feedback
        if feedback.upper() == "TRUE":
            accept_count += 1
        elif feedback.upper() == "FALSE":
            reject_count += 1

        # Construct the ground truth key
        if method == "Chain-of-Table":
            ground_truth_key = f"COT_test-{index}.html"  # Adjust this based on your actual key format in the CoTable JSON
        else:
            ground_truth_key = f"POS_test-{index}.html"

        # Check if the key exists in the ground truth data
        if ground_truth_key in ground_truth and ground_truth[ground_truth_key]['answer'].upper() == feedback.upper():
            correct_responses += 1
        else:
            print(f"Missing or mismatched key: {ground_truth_key}")

    # Calculate accuracy
    accuracy = (correct_responses / len(responses)) * 100 if responses else 0
    accuracy = round(accuracy, 2)

    # Calculate percentages
    total_responses = len(responses)
    accept_percentage = (accept_count / total_responses) * 100 if total_responses else 0
    reject_percentage = (reject_count / total_responses) * 100 if total_responses else 0

    # Round percentages
    accept_percentage = round(accept_percentage, 2)
    reject_percentage = round(reject_percentage, 2)

    return render_template('completed.html',
                           accuracy=accuracy,
                           accept_percentage=accept_percentage,
                           reject_percentage=reject_percentage)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
