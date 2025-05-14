#!/usr/bin/env python3

import json
import sys
import math


def flatten_answer(ans):
    """
    Convert 'answer'/'groundtruth' to a simple lowercased string.
    Handles:
      - direct string ("TRUE", "FALSE", etc.)
      - list of strings (["some", "answer"])
      - nested list ([["some answer"]])
    """
    if isinstance(ans, str):
        return ans.strip().lower()
    if isinstance(ans, list):
        # Flatten any nesting
        flattened = []
        for item in ans:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return " ".join(str(x) for x in flattened).strip().lower()
    # fallback
    return str(ans).strip().lower()


def compute_table_token_count(table_text):
    """
    If 'table_token_count' is not given (as in WikiTQ),
    we approximate by summing character lengths of all cells.
    Adjust if you want an actual token-based count.
    """
    if not table_text or not isinstance(table_text, list):
        return 0
    total_chars = 0
    for row in table_text:
        if isinstance(row, list):
            for cell in row:
                if isinstance(cell, str):
                    total_chars += len(cell.strip())
                else:
                    total_chars += len(str(cell))
        else:
            # If row isn't a list, interpret it as a string
            total_chars += len(str(row))
    return total_chars


def pearson_correlation(x_list, y_list):
    """
    Compute a basic Pearson correlation coefficient between x_list and y_list.
    Both must be numeric lists of the same length.
    If there's insufficient variance or length < 2, we return 0.0 to avoid errors.
    """
    n = len(x_list)
    if n < 2:
        return 0.0

    mean_x = sum(x_list) / n
    mean_y = sum(y_list) / n

    # Calculate numerator & denominator for Pearson r
    num = 0.0
    den_x = 0.0
    den_y = 0.0
    for i in range(n):
        dx = x_list[i] - mean_x
        dy = y_list[i] - mean_y
        num += dx * dy
        den_x += dx * dx
        den_y += dy * dy

    if den_x == 0 or den_y == 0:
        # no variance => correlation is undefined
        return 0.0

    return num / math.sqrt(den_x * den_y)


def parse_json_file(json_path):
    """
    Parse a JSON file (TabFact or WikiTQ style).
    Return a list of (pred_answer, gt_answer, table_count, fallback_llm) for each entry.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    # In both TabFact and WikiTQ, the top-level structure is dict-like:
    # { <id> : { <id> : { ... } }, ... }
    # We'll recursively look for items that have "input" + "answer" + "groundtruth".
    for outer_key, outer_val in data.items():
        if not isinstance(outer_val, dict):
            continue

        for inner_key, content in outer_val.items():
            if not isinstance(content, dict):
                continue

            input_data = content.get("input", {})

            # In TabFact style, we might see:
            #   table_token_count = input_data["table_token_count"]
            #   answer = content["answer"]
            #   groundtruth = content["groundtruth"]
            # In WikiTQ style, we might see:
            #   answer = content["answer"] (could be list-of-lists)
            #   groundtruth = content["groundtruth"]
            #   table_token_count not present => compute from table_text
            raw_answer = content.get("answer", input_data.get("answer", ""))
            raw_groundtruth = content.get("groundtruth", input_data.get("groundtruth", ""))

            # Get fallback_LLM value, default to False if not present
            fallback_llm = content.get("fallback_LLM", False)

            # Flatten them to strings
            norm_answer = flatten_answer(raw_answer)
            norm_groundtruth = flatten_answer(raw_groundtruth)

            # Try to get table_token_count
            if "table_token_count" in input_data:
                table_count = input_data["table_token_count"]
            else:
                # compute
                table_text = input_data.get("table_text", [])
                table_count = compute_table_token_count(table_text)

            records.append((norm_answer, norm_groundtruth, table_count, fallback_llm))

    return records


def main():
    """
    Usage:
      python compute_pos_accuracy_samplebins.py file1.json [file2.json ...]

    This script:
      - Reads one or more JSON files in TabFact / WikiTQ style.
      - Collects (answer, groundtruth, table_token_count).
      - Computes overall accuracy, plus correlation between table length and correctness.
      - Reports wrong samples with fallback_LLM = True and fallback_LLM = False
      - Partitions the data into 3 bins by sample count (lowest 1/3, middle 1/3, highest 1/3).
        * Each bin has ~ the same number of samples.
      - Reports bin ranges, sample counts, and bin-wise accuracy.
    """

    # if len(sys.argv) < 2:
    #     print("Usage: python compute_pos_accuracy_samplebins.py file1.json [file2.json ...]")
    #     sys.exit(1)

    # Collect all (answer, groundtruth, count, fallback_llm) records from each file
    all_records = []
    # for path in sys.argv[1:]:
    # path = '/home/giang/Downloads/table-qa-2025/result_files/GPT4-O_TabFact_results_test_run58.json'
    path = '/home/giang/Downloads/table-qa-2025/result_files/gpt-35-turbo-16k_results_test_run152184Oh.json'
    file_records = parse_json_file(path)
    all_records.extend(file_records)

    # If no records found, exit
    if not all_records:
        print("No valid records found in the provided files.")
        sys.exit(0)

    # Sort by table_token_count (ascending)
    sorted_records = sorted(all_records, key=lambda x: x[2])

    # Basic stats
    N = len(sorted_records)
    min_count = sorted_records[0][2]
    max_count = sorted_records[-1][2]

    print(f"--- Loaded {N} total entries ---")
    print(f"Min table_token_count: {min_count}")
    print(f"Max table_token_count: {max_count}")

    # Overall correctness
    total = 0
    correct = 0

    # For the new fallback_LLM stats
    wrong_with_fallback = 0
    wrong_without_fallback = 0

    # For correlation: x_list = table_length, y_list = 1 if correct else 0
    x_list = []
    y_list = []

    for (norm_answer, norm_gt, count, fallback_llm) in sorted_records:
        total += 1
        is_correct = (norm_answer == norm_gt)
        if is_correct:
            correct += 1
        else:
            # Track wrong samples based on fallback_LLM value
            if fallback_llm:
                wrong_with_fallback += 1
            else:
                wrong_without_fallback += 1

        x_list.append(count)
        y_list.append(1 if is_correct else 0)

    overall_accuracy = correct / total
    print(f"\nOverall Accuracy = {overall_accuracy:.3f} ({correct}/{total})")

    # Display the new fallback_LLM statistics
    print(f"Number of wrong samples when fallback_LLM = false: {wrong_without_fallback}")
    print(f"Number of wrong samples when fallback_LLM = true: {wrong_with_fallback}")

    # Correlation between table length and correctness
    corr = pearson_correlation(x_list, y_list)
    print(f"Correlation(table_length, correctness) = {corr:.3f}")
    if abs(corr) > 0.1:
        if corr > 0:
            print("  (Positive correlation => Accuracy tends to be higher with longer tables.)")
        else:
            print("  (Negative correlation => Accuracy tends to drop as table length increases.)")
    else:
        print("  (Near-zero correlation => Table length has little direct effect on correctness.)")

    # Now we create 3 bins by sample count:
    #   Bin1: lowest 1/3 table_token_count
    #   Bin2: middle 1/3
    #   Bin3: highest 1/3
    if N < 3:
        print("\nNot enough samples to form 3 bins. All data in one bin.")
        bin1_records = sorted_records
        bin2_records = []
        bin3_records = []
    else:
        cutoff1 = N // 3
        cutoff2 = 2 * N // 3

        bin1_records = sorted_records[:cutoff1]
        bin2_records = sorted_records[cutoff1:cutoff2]
        bin3_records = sorted_records[cutoff2:]

    def compute_bin_stats(bin_records, bin_name):
        if not bin_records:
            print(f"{bin_name}: No samples in this bin.")
            return
        # min and max table_token_count in this bin
        b_min = bin_records[0][2]
        b_max = bin_records[-1][2]
        b_total = len(bin_records)
        b_correct = sum(1 for (ans, gt, c, fallback) in bin_records if ans == gt)
        b_acc = b_correct / b_total
        print(
            f"{bin_name}: Range=[{b_min}, {b_max}] | Samples={b_total} | Accuracy={b_acc:.3f} ({b_correct}/{b_total})")

    print("\n--- Bin-wise Accuracy by Sample Count ---")
    compute_bin_stats(bin1_records, "Bin1 (lowest 1/3)")
    compute_bin_stats(bin2_records, "Bin2 (middle 1/3)")
    compute_bin_stats(bin3_records, "Bin3 (highest 1/3)")

    print("\nAnalysis Summary:")
    print("1) We partitioned data into three bins by sample index, not by numeric range,")
    print("   ensuring each bin has ~the same number of samples.")
    print("2) This reveals whether accuracy systematically differs for short vs. long tables.")
    print("3) Check the correlation to see if performance degrades with length (negative r).")
    print("4) The bin stats show accuracy and sample count in each bin.")
    print("5) We additionally display the count of wrong samples by fallback_LLM status.\n")


if __name__ == "__main__":
    main()