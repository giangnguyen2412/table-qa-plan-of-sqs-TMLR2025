import json
from operations import *
from utils.helper import *
from utils.prompts import *


def load_metadata(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)


def compute_accuracy(metadata_file):
    # Load the metadata
    results = load_metadata(metadata_file)

    correct_count = 0
    total_count = 0

    for d in results.values():
        for item in d.values():
            # Convert both to strings to handle cases where answers might be integers or booleans
            answer = str(item['answer']).upper()
            ground_truth = str(item['groundtruth']).upper()

            total_count += 1
            if answer == ground_truth:
                correct_count += 1

    accuracy = correct_count / total_count if total_count > 0 else 0

    print(f"Total samples: {total_count}")
    print(f"Correct count: {correct_count}")
    print(f"Accuracy: {accuracy:.4f}")

    return accuracy


# Example usage:
compute_accuracy(f'results-20240906/{result_file_name}')
