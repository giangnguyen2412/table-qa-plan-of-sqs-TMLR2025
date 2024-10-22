# Copyright 2024 The Chain-of-Table authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from utils.helper import *

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
    correct_list = []
    for i, sample in enumerate(all_samples):
        try:
            if tabfact_match_func(sample, strategy):
                correct_list.append(1)
            else:
                correct_list.append(0)
                # print(f"Model failed on sample {i}-th")
        except:
            print(f"Error")
            continue
    print('Correct:', sum(correct_list))
    print('Total:', len(correct_list))
    return sum(correct_list) / len(correct_list)


def tabfact_compute_accuracy(results):
    correct_count = 0
    wrong_count = 0
    na_count = 0
    total_count = 0
    sample_count = len(results)

    wrong_ids = []
    wrong_tables = {}

    fall_back_crt = 0
    fb_count = 0

    pos_crt = 0
    pos_count = 0

    for item in results.values():
        # Convert both to strings to handle cases where answers might be integers or booleans
        answer = str(item['answer']).upper()
        ground_truth = str(item['groundtruth']).upper()

        if item['fallback_LLM'] is True:
            fb_count += 1
        else:
            pos_count += 1

        # Only consider the items where SQL is executable
        if item['is_sql_executable'] is True:
            total_count += 1
            if answer == ground_truth:
                correct_count += 1
                # Correct answer, so remove the log file

                if item['fallback_LLM'] is True:
                    fall_back_crt += 1
                else:
                    pos_crt += 1
            else:
                wrong_count += 1
                wrong_ids.append(item['id'])

                orig_sample = item['input']
                table_id = orig_sample['table_id']

                # Analyze the wrong samples, ignoring unexecutable samples
                if table_id in wrong_tables:
                    wrong_tables[table_id]['wrong_cnt'] += 1
                    wrong_tables[table_id]['statement'].append(orig_sample['statement'])
                    wrong_tables[table_id]['ids'].append(orig_sample['id'])

                else:
                    wrong_tables[table_id] = {}
                    wrong_tables[table_id]['wrong_cnt'] = 1

                    wrong_tables[table_id]['statement'] = []
                    wrong_tables[table_id]['statement'].append(orig_sample['statement'])

                    wrong_tables[table_id]['ids'] = []
                    wrong_tables[table_id]['ids'].append(orig_sample['id'])

                    wrong_tables[table_id]['table'] = orig_sample['table_text']

        else:
            na_count += 1
            # if os.path.exists(log_path):
            #     os.remove(log_path)
            # SQL not executable, consider as wrong for log management
            # wrong_ids.append(item['id'])

    # print(wrong_tables)

    # Sorting the dictionary by the nested value 'wrong_cnt'
    sorted_wrong_tables = dict(sorted(wrong_tables.items(), key=lambda item: item[1]['wrong_cnt'], reverse=True))

    # Printing the sorted dictionary
    print(sorted_wrong_tables)

    for key, wrong_table in sorted_wrong_tables.items():
        # print('######')

        # print('wrong count:', wrong_table['wrong_cnt'])
        # print('Statements:')
        # for id in wrong_table['ids']:
        #     print(id)
        # for st in wrong_table['statement']:
        #     print(st)

        for id, st in zip(wrong_table['ids'], wrong_table['statement']):
            print(id)
            print(st)


        # print('Table:')
        # print(table2string(wrong_table['table']))

    print(f'Wrong Samples:\n {wrong_ids}')
    print('\n')

    print(f'Executability: {total_count} / {sample_count}')
    exec_rate = (100 * total_count) / sample_count if sample_count > 0 else 0
    print(f'Executability Rate: {exec_rate}')
    print('\n')

    print('Fall-back Rate:', 100*fb_count/sample_count)
    print('\n')

    if fb_count > 0:
        print('Fall-back Acc:', 100*fall_back_crt/fb_count)
        print('\n')

    print('PoS Rate:', 100*pos_count/sample_count)
    print('\n')

    if pos_count > 0:
        print('PoS Acc:', 100*pos_crt/pos_count)
        print('\n')

    print(f'Correct/Total:{correct_count}/{sample_count}')
    print(f'Wrong/Total:{wrong_count}/{sample_count}')
    print(f'NA/Total:{na_count}/{sample_count}')

    # combine_files_from_directory(config.planning_log_path, None)

    # Calculate accuracy
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    print(f"POS Accuracy: {accuracy:.2f}")

    final_accuracy = (correct_count / sample_count) * 100 if sample_count > 0 else 0
    print(f"Final Accuracy: {final_accuracy:.2f}")

    return accuracy