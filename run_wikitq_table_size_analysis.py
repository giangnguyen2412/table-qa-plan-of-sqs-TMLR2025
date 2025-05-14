#!/usr/bin/env python3

import os
import json
import sys
import math
import collections

from utils.load_data import *
from utils.llm import TableQA_LLM
from utils.helper import *
from utils.chain import *
from utils.wikitq_eval import *
import openai


########################################
# Assumed imports from your codebase:
# from utils.helper import tsv_unescape_list, to_value_list
# from utils.wikitq_eval import check_denotation
#
# If these are defined elsewhere, import them here.
# Otherwise, paste their definitions in this script.
########################################

def compute_table_token_count(table_text):
    """
    Approximate table length by summing character lengths of all cells.
    Adjust if you prefer an actual token-based count.
    """
    if not isinstance(table_text, list):
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
            total_chars += len(str(row))
    return total_chars


def pearson_correlation(x_list, y_list):
    """
    Compute a basic Pearson correlation coefficient between x_list and y_list.
    Returns 0 if length < 2 or no variance.
    """
    n = len(x_list)
    if n < 2:
        return 0.0

    mean_x = sum(x_list) / n
    mean_y = sum(y_list) / n

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
        return 0.0

    return num / math.sqrt(den_x * den_y)


def main():
    """
    Usage:
      python wikiq_pos_accuracy.py wikitq_inference.json

    This script:
      1) Reads your WikiTQ inference JSON (the 'proc_samples').
      2) Loads target_values_map, st2id, etc. from local data/wikitq files
         to perform denotation-based correctness checking.
      3) For each sample, we:
         - Gather the predicted answers (res_preds)
         - Check correctness via 'check_denotation'
         - Compute table length
      4) Collect (table_length, correctness) across all samples.
      5) Print overall accuracy, correlation, and bin-based accuracy
         (lowest 1/3, middle 1/3, highest 1/3 by sample count).
    """
    # if len(sys.argv) < 2:
    #     print("Usage: python wikiq_pos_accuracy.py wikitq_inference.json")
    #     sys.exit(1)

    # inference_json_path = sys.argv[1]
    inference_json_path = '/home/giang/Downloads/table-qa-2025/GPT4-O_WikiTQ_results_test_run16.json'
    inference_json_path = '/home/giang/Downloads/table-qa-2025/result_files/GPT4-O_WikiTQ_results_test_run57.json'

    # --------------------------------------------------------------------------
    # 1) Load your 'proc_samples' from the WikiTQ JSON
    #    This JSON is typically structured like:
    #    {
    #      "0": {"0": { "input": {...}, "answer": [...], "fallback_LLM": false, ...}},
    #      "1": {"1": { "input": {...}, "answer": [...], "fallback_LLM": false, ...}},
    #      ...
    #    }
    # --------------------------------------------------------------------------
    with open(inference_json_path, 'r', encoding='utf-8') as f:
        proc_samples = json.load(f)

    # We'll sort by key to maintain consistent order
    proc_samples = dict(sorted(proc_samples.items()))

    # --------------------------------------------------------------------------
    # 2) Load official WikiTQ data for denotation checking
    #    (Same as your snippet: target_values_map, st2id, etc.)
    # --------------------------------------------------------------------------
    # If you have these variables defined in another script, import them.
    # Otherwise, replicate that logic here:
    tagged_dataset_path = 'data/wikitq/data'
    target_values_map = {}
    for filename in os.listdir(tagged_dataset_path):
        if filename.startswith('.'):
            continue
        filepath = os.path.join(tagged_dataset_path, filename)
        print('Reading dataset from', filepath)
        with open(filepath, 'r', encoding='utf8') as fin:
            header = fin.readline().rstrip('\n').split('\t')
            for line in fin:
                stuff = dict(zip(header, line.rstrip('\n').split('\t')))
                ex_id = stuff['id']
                original_strings = tsv_unescape_list(stuff['targetValue'])
                canon_strings = tsv_unescape_list(stuff['targetCanon'])
                target_values_map[ex_id] = to_value_list(original_strings, canon_strings)

    st2id = {}
    with open(os.path.join('data/wikitq/test_lower.jsonl'), 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for l in lines:
            dic_l = json.loads(l)
            st = dic_l['statement']
            ids = dic_l['ids']
            st2id[st] = ids

    with open('data/wikitq/gloc_wtq_end2end_wikitq_test.json', 'r', encoding='utf-8') as f:
        gloc_dic = json.load(f)

    # --------------------------------------------------------------------------
    # 3) Evaluate each sample to compute correctness & gather table length
    # --------------------------------------------------------------------------
    deno_acc = 0
    execs = 0

    fb_count = 0
    fall_back_crt = 0

    # For tracking wrong samples based on fallback_LLM status
    wrong_with_fallback = 0
    wrong_without_fallback = 0

    pos_count = 0
    pos_crt = 0

    # We'll store (table_len, correctness) for correlation + bin stats
    length_correct_records = []

    # We might also track how many total samples
    total_samples = len(proc_samples)

    # Loop over all items
    for sample_idx_str, sub_dict in proc_samples.items():
        # sub_dict might be { "0": { ... } } or similar
        # We'll iterate its values
        for _, res in sub_dict.items():
            # 'res' is the main dictionary with keys:
            #   "input", "answer", "fallback_LLM", etc.
            res_table = res['input']['table_text']
            res_st = res['input']['statement']
            res_preds = res['answer']  # list-of-lists typically
            fall_back = res.get('fallback_LLM', False)

            # fallback vs pos counting
            if fall_back:
                fb_count += 1
            else:
                pos_count += 1

            # If no predictions
            if not res_preds or len(res_preds[0]) == 0:
                continue

            execs += 1

            # We mimic your snippet:
            #   1) Search gloc_dic for matching statement
            #   2) Build 'preds' array => pick top prediction => check denotation
            preds = []
            for key in gloc_dic:
                to_union = collections.defaultdict(float)
                it = gloc_dic[key]
                st = it['data_item']['statement']
                if res_st in st:
                    # Build a single 'preds' entry
                    answs = []
                    for ans in res_preds:
                        answs.append(str(ans[0]))
                    answs_joined = ' SEP_TOKEN '.join(answs)
                    # preds might be [ [answs_joined, 0, 0] ]
                    preds.append([answs_joined, 0, 0])
                    break

            # Next, we do the union of log probs, etc.
            to_union = collections.defaultdict(float)
            for pred in preds:
                log_prob_mean = pred[2]
                pred_str = pred[0]
                to_union[pred_str] += math.exp(log_prob_mean)

            d_ordered = sorted(to_union.items(), key=lambda x: x[1], reverse=True)
            try:
                pred_answer_top = d_ordered[0][0].split('\n')[0].strip()
            except Exception:
                pred_answer_top = 'error'

            # 'st' might have changed, so we use the original st from the loop
            # or from the snippet. Let's keep it consistent:
            # We have the local 'st' from gloc_dic, but let's unify with 'res_st'
            # to ensure indexing is correct.
            st_clean = st.split('\n')[0]
            # get target values
            if st_clean not in st2id:
                # If not found in st2id, skip
                continue
            target_values = target_values_map[st2id[st_clean]]

            pred_split = pred_answer_top.split(' SEP_TOKEN ')
            pred_list = to_value_list(pred_split)

            # Check correctness
            flag = check_denotation(target_values, pred_list)
            if flag:
                deno_acc += 1
                # If fallback is correct
                if fall_back:
                    fall_back_crt += 1
                else:
                    pos_crt += 1
            else:
                # Count wrong answers based on fallback_LLM status
                if fall_back:
                    wrong_with_fallback += 1
                else:
                    wrong_without_fallback += 1

            # Compute table length
            table_len = compute_table_token_count(res_table)
            length_correct_records.append((table_len, flag))

    # --------------------------------------------------------------------------
    # 4) Print your existing final stats
    # --------------------------------------------------------------------------
    print(f"\nTotal samples in JSON: {total_samples}")
    print(f"Executability: {execs}/{total_samples}")
    if total_samples > 0:
        print("Executability Rate:", f"{100 * execs / total_samples:.2f}%")
    print('\n')

    if total_samples > 0:
        print('Fall-back Rate:', f"{100 * fb_count / total_samples:.2f}%")
    if fb_count > 0:
        print('Fall-back Accuracy:', f"{100 * fall_back_crt / fb_count:.2f}%")
    print('\n')

    # Display the new statistics about wrong samples
    print(f"Number of wrong samples when fallback_LLM = false: {wrong_without_fallback}")
    print(f"Number of wrong samples when fallback_LLM = true: {wrong_with_fallback}")
    print('\n')

    if total_samples > 0:
        print('PoS Rate:', f"{100 * pos_count / total_samples:.2f}%")
    if pos_count > 0:
        print('PoS Accuracy:', f"{100 * pos_crt / pos_count:.2f}%")
    print('\n')

    print(f'Denotation: {deno_acc}/{total_samples}')
    if total_samples > 0:
        print('Denotation Accuracy:', f"{100 * deno_acc / total_samples:.2f}%")

    # --------------------------------------------------------------------------
    # 5) Bin-based analysis + correlation
    # --------------------------------------------------------------------------
    if not length_correct_records:
        print("\nNo valid records for bin-based stats (none had predictions?).")
        return

    # sort by table_len ascending
    length_correct_records.sort(key=lambda x: x[0])
    N = len(length_correct_records)
    min_len = length_correct_records[0][0]
    max_len = length_correct_records[-1][0]

    # overall correctness (just among executed)
    correct_count = sum(1 for (_, f) in length_correct_records if f)
    overall_acc = correct_count / N

    print("\n=== BIN-BASED ANALYSIS (WikiTQ) ===")
    print(f"Samples with predictions: {N}")
    print(f"Min table length: {min_len}")
    print(f"Max table length: {max_len}")
    print(f"Overall Denotation Accuracy (among executed) = {overall_acc:.3f} ({correct_count}/{N})")

    # correlation
    x_list = [item[0] for item in length_correct_records]
    y_list = [1 if item[1] else 0 for item in length_correct_records]
    corr = pearson_correlation(x_list, y_list)
    print(f"Correlation(table_length, correctness) = {corr:.3f}")
    if abs(corr) > 0.1:
        if corr > 0:
            print("  (Positive correlation => Accuracy tends to be higher with longer tables.)")
        else:
            print("  (Negative correlation => Accuracy tends to drop as table length increases.)")
    else:
        print("  (Near-zero correlation => Table length has little direct effect on correctness.)")

    # 3 bins by sample index
    if N < 3:
        print("\nNot enough samples for 3 bins. All data in one bin.")
        return

    cutoff1 = N // 3
    cutoff2 = 2 * N // 3
    bin1 = length_correct_records[:cutoff1]
    bin2 = length_correct_records[cutoff1:cutoff2]
    bin3 = length_correct_records[cutoff2:]

    def analyze_bin(bin_data, bin_label):
        bN = len(bin_data)
        if bN == 0:
            print(f"{bin_label}: No samples.")
            return
        b_min_len = bin_data[0][0]
        b_max_len = bin_data[-1][0]
        b_correct = sum(1 for (_, c) in bin_data if c)
        b_acc = b_correct / bN
        print(
            f"{bin_label}: Range=[{b_min_len}, {b_max_len}] | "
            f"Samples={bN} | Accuracy={b_acc:.3f} ({b_correct}/{bN})"
        )

    print("\n--- Bin-wise Accuracy by Sample Count ---")
    analyze_bin(bin1, "Bin1 (lowest 1/3)")
    analyze_bin(bin2, "Bin2 (middle 1/3)")
    analyze_bin(bin3, "Bin3 (highest 1/3)")

    print("\nAnalysis Summary:")
    print("1) Computed denotation accuracy for WikiTQ (using 'check_denotation' etc.).")
    print("2) Partitioned data into 3 bins by sample count, from smallest to largest table.")
    print("3) Checked correlation to see if accuracy degrades as table length grows.")
    print("4) Added statistics on wrong answers based on fallback_LLM status.\n")


if __name__ == "__main__":
    main()