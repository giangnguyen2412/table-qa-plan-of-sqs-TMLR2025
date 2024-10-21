import os
import json
import argparse


# Function to compute accuracy and other statistics
def compute_stats_from_json(file_path):
    # Load the JSON data from the file
    with open(file_path, 'r') as file:
        data = json.load(file)

    total_entries = len(data)
    correct_predictions = 0

    # Counters for analysis
    llm_yes_count = 0
    llm_no_count = 0
    correct_yes = 0
    correct_no = 0
    TP, TN, FP, FN = 0, 0, 0, 0

    # Iterate through each entry to compute required stats
    for entry in data.values():
        # Convert comparison strings to uppercase for case-insensitive comparison
        llm_analysis = entry["LLM_analysis"].upper()
        actual_correctness = entry["Actual_Correctness"].upper()
        model_prediction = entry["Model_Prediction"].upper()
        actual_answer = entry["Actual_Answer"].upper()

        # Count Yes/No answers from LLM
        if llm_analysis == "YES":
            llm_yes_count += 1
            if llm_analysis == actual_correctness:
                correct_yes += 1
        elif llm_analysis == "NO":
            llm_no_count += 1
            if llm_analysis == actual_correctness:
                correct_no += 1

        # Check if LLM analysis matches actual correctness
        if llm_analysis == actual_correctness:
            correct_predictions += 1

        # Compute TP, TN, FP, FN based on Model_Prediction and Actual_Answer
        if model_prediction == "TRUE" and actual_answer == "TRUE":
            TP += 1
        elif model_prediction == "FALSE" and actual_answer == "FALSE":
            TN += 1
        elif model_prediction == "TRUE" and actual_answer == "FALSE":
            FP += 1
        elif model_prediction == "FALSE" and actual_answer == "TRUE":
            FN += 1

    # Calculate overall accuracy
    accuracy = (correct_predictions / total_entries) * 100 if total_entries > 0 else 0

    # Calculate accuracy when LLM says Yes and when it says No
    accuracy_yes = (correct_yes / llm_yes_count) * 100 if llm_yes_count > 0 else 0
    accuracy_no = (correct_no / llm_no_count) * 100 if llm_no_count > 0 else 0

    # Ratios for Yes and No
    llm_yes_ratio = (llm_yes_count / total_entries) * 100 if total_entries > 0 else 0
    llm_no_ratio = (llm_no_count / total_entries) * 100 if total_entries > 0 else 0

    return accuracy, llm_yes_ratio, llm_no_ratio, accuracy_yes, accuracy_no, TP, TN, FP, FN


# Function to process all JSON files in a folder
def process_folder(folder_path):
    # Iterate through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            accuracy, llm_yes_ratio, llm_no_ratio, accuracy_yes, accuracy_no, TP, TN, FP, FN = compute_stats_from_json(
                file_path)
            print(f"{filename}:")
            print(f"  Overall Accuracy: {accuracy:.2f}%")
            print(f"  LLM Yes Ratio: {llm_yes_ratio:.2f}%")
            print(f"  LLM No Ratio: {llm_no_ratio:.2f}%")
            print(f"  Accuracy when LLM says Yes: {accuracy_yes:.2f}%")
            print(f"  Accuracy when LLM says No: {accuracy_no:.2f}%")
            print(f"  TP: {TP}, TN: {TN}, FP: {FP}, FN: {FN}\n")


# Set up argument parsing
def main():
    parser = argparse.ArgumentParser(
        description='Compute accuracy and other statistics from all JSON files in a folder.')
    parser.add_argument('folder', type=str, help='Path to the folder containing JSON files')

    # Parse arguments
    args = parser.parse_args()

    # Process each JSON file in the provided folder
    process_folder(args.folder)


if __name__ == '__main__':
    main()

# python analyze_result.py result