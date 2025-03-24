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


import copy
import re
import os
import ast
import logging
import json
import pickle
import shutil
import traceback
import multiprocessing as mp
from tqdm import tqdm
from collections import Counter, defaultdict
from sqlalchemy.sql import text
from utils.helper import table2string
from operations import *
from utils.helper import *
from utils.prompts import *
from utils.plan import *


import json
import fcntl
import time
from filelock import FileLock



#################################################################################################################################################################
#################################################################################################################################################################
#################################################################################################################################################################
# WIKITQ handles

# Doing fallback here
def wikitq_fall_back(fb_table, sample, llm):
    table_info = {}
    table_info["table_text"] = fb_table
    sample_copy = wikitq_simple_query(sample, table_info, llm, debug=False, use_demo=False, llm_options=None)

    fallback_answer = sample_copy["chain"][0]['parameter_and_conf'][0][0].lower().rstrip('.')

    print(type(fallback_answer))
    print('wikitq answer for fall back before:\n', fallback_answer)

    fallback_answer = process_string(fallback_answer)
    print('wikitq answer for fall back after:\n', fallback_answer)

    # if is_list_of_strings(fallback_answer) is True:
    #     print('Wrong post-processing: ', fallback_answer)

    return [fallback_answer]

#
if planning_algorithm == 'static':

    def wikitq_natural_language_chain_exec_one_sample(sample, llm, llm_options=None, strategy="top", debug=False):
        table_name = 'table_sql'
        question = sample['statement']
        table_text = sample['table_text']
        answer = sample['answer']
        sample_id = sample['id']

        logger, log_filename = wikitq_setup_logger(sample_id)


        original_table = copy.deepcopy(table_text)  # Store the original table
        groundtruth = answer
        is_sql_executable = False
        fall_back_llm = True

        try:
            # PLANNING
            plans, plans_generated_successfully = wikitq_generate_natural_language_planning(
                sample, llm=llm, llm_options=llm_options, strategy=strategy, debug=debug
            )

            if not plans or not plans_generated_successfully:
                logger.error('Failed to generate plans or initial executable flag is False!')
                print('ERR2: Failed to generate plans or initial executable flag is False!')

                result_dict = {}
                final_answer = wikitq_fall_back(original_table, sample, llm)
                return sample_id, final_answer, is_sql_executable, groundtruth, result_dict, fall_back_llm

            for plan_idx, plan in enumerate(plans):
                intermediate_table = copy.deepcopy(original_table)  # Reset the table for each plan
                all_operations_successful = True

                logger.info('*' * 120)

                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Query: {sample["statement"]}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Groundtruth: {groundtruth}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: X-Original table pd: \n{table2df(intermediate_table)}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Caption: none')

                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Original table: {intermediate_table}')


                print('DB1: Generated plan:')
                for operation_idx, operation in enumerate(plan):
                    print('DB1: operation:', operation)

                int_tables = []
                int_tables.append(original_table)
                for operation_idx, operation in enumerate(plan):
                    if operation_idx == (len(plan) - 1):  # Last operation
                        question = sample["statement"]
                    else:
                        question = None

                    prompt = wikitq_natural_language_plan_step_to_sql(sample, intermediate_table, operation, table_name, question)
                    logger.info('#' * 120)
                    try:
                        responses = llm.generate_plus_with_score(prompt, options=llm_options, end_str="\n\n")

                        if responses and len(responses) > 0 and len(responses[0]) > 0:
                            sql_command = extract_sql_code(responses[0][0])
                        else:
                            logger.error("No responses or unexpected response format.")
                            print(f'ERR3: No responses or unexpected response format:', responses)
                            continue  # Skip to the next iteration of the loop or handle error as needed

                        previous_ops = plan[0:operation_idx]
                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Operation {operation_idx + 1}: {operation}')

                        if SQL_EXECUTOR == 'SQL_ALCHEMY':
                            sql_command = text(sql_command)
                            intermediate_table, selected_indices = transform_table_with_sqlalchemy(intermediate_table, sql_command, table_name)
                            logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Selected indices: {selected_indices}')

                        else:
                            intermediate_table, selected_indices = transform_table_with_sql(intermediate_table, sql_command, table_name)
                            logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Selected indices: {selected_indices}')

                        int_tables.append(intermediate_table)

                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: X-Table after operation df:\n{table2df(intermediate_table)}')
                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Table after operation: {(intermediate_table)}')

                    except Exception as e:
                        logger.error(f"SQL execution error in operation {operation_idx + 1}: {e}")
                        print(f'ERR4: SQL execution error in operation {operation_idx + 1}: {e}')
                        print(traceback.format_exc())  # Print the detailed traceback information
                        all_operations_successful = False
                        break

            if all_operations_successful is True:
                # Remove the header for the final answer
                final_answer = intermediate_table[1:]

                print('formatted answer:', final_answer)

                if len(final_answer) == 0 or None in final_answer[0]:
                    print('empty final ans:', final_answer)
                    # WIKITQ: Doing fallback here with original table if SQL is executable cannot give answer in the right format

                    final_answer = wikitq_fall_back(original_table, sample, llm)

                    print('DB1: Question:', question)
                    print('DB1: Answer:', answer)
                    print('WIKITQ final answer for fall back 3:\n', final_answer)
                    logger.info(f'Fall-back: TRUE')

                else:
                    logger.info(f'Fall-back: FALSE')
                    fall_back_llm = False
                    is_sql_executable = True

                logger.info(f'Answer from plan {plan_idx + 1}: {final_answer}')
                logger.info(f'Groundtruth: {groundtruth}')

            else:
                logger.error("Intermediate table does not have the expected structure.")
                final_answer = wikitq_fall_back(original_table, sample, llm)


                logger.info(f'Fall-back: TRUE')
                logger.info(f'Answer from plan {plan_idx + 1}: {final_answer}')
                logger.info(f'Groundtruth: {groundtruth}')


                print('DB1: Question:', question)
                print('DB1: Answer:', answer)
                print('WIKITQ final answer for fall back 2:\n', final_answer)

            return sample_id, final_answer, is_sql_executable, groundtruth, {}, fall_back_llm

        except Exception as e:
            print(f'ERR1: Unexpected error occurred: {e}')
            print(traceback.format_exc())  # Print the detailed traceback information

            result_dict = {}
            final_answer = wikitq_fall_back(original_table, sample, llm)
            return sample_id, final_answer, is_sql_executable, groundtruth, result_dict, fall_back_llm

elif planning_algorithm == 'dynamic':

    def wikitq_natural_language_chain_exec_one_sample(sample, llm, llm_options=None, strategy="top", debug=False):
        table_name = 'table_sql'
        question = sample['statement']
        table_text = sample['table_text']
        answer = sample['answer']
        sample_id = sample['id']

        logger, log_filename = wikitq_setup_logger(sample_id)
        original_table = copy.deepcopy(table_text)
        groundtruth = answer
        intermediate_table = copy.deepcopy(original_table)
        operation_history = []
        is_sql_executable = False
        fall_back_llm = True

        try:
            while True:
                # print('Operation history:', operation_history)
                if len(operation_history) >= 10:
                    logger.warning("Maximum steps reached, falling back to default approach")
                    print("Maximum steps reached, falling back to default approach")
                    break

                # Get next operation dynamically
                next_operation = wikitq_generate_natural_language_planning(
                    sample,
                    intermediate_table,
                    operation_history,
                    llm=llm,
                    llm_options=llm_options,
                    strategy=strategy,
                    debug=debug
                )

                if not next_operation:
                    logger.error('Failed to generate next operation')
                    print('Failed to generate next operation')
                    break

                # Check if this is the final step
                is_final_step = "Final step:" in next_operation

                # Remove the final step indication from the operation text
                next_operation = next_operation.replace("Final step:", "").strip()

                # Log current state and operation
                logger.info('*' * 120)
                logger.info(f'Sample {sample_id} - Operation {len(operation_history) + 1}: {next_operation}')
                logger.info(f'Current table state: {intermediate_table}')

                # Convert operation to SQL and execute
                prompt = wikitq_natural_language_plan_step_to_sql(
                    sample,
                    intermediate_table,
                    next_operation,
                    table_name,
                    question
                )

                try:
                    responses = llm.generate_plus_with_score(prompt, options=llm_options, end_str="\n\n")
                    if responses and len(responses) > 0 and len(responses[0]) > 0:
                        sql_command = extract_sql_code(responses[0][0])
                    else:
                        logger.error("No SQL generated")
                        print("No SQL generated")
                        break

                    # Execute SQL
                    if SQL_EXECUTOR == 'SQL_ALCHEMY':
                        sql_command = text(sql_command)
                        intermediate_table, selected_indices = transform_table_with_sqlalchemy(
                            intermediate_table, sql_command, table_name
                        )
                    else:
                        intermediate_table, selected_indices = transform_table_with_sql(
                            intermediate_table, sql_command, table_name
                        )

                    logger.info(f'Sample {sample_id} - Table after operation df:\n{table2df(intermediate_table)}')
                    logger.info(f'Sample {sample_id} - Table after operation: {intermediate_table}')

                    operation_history.append(next_operation)

                    # If this was the final step, extract and return the final answer
                    if is_final_step:
                        result_table = intermediate_table[1:]  # Remove header
                        if len(result_table) > 0:
                            is_sql_executable = True
                            fall_back_llm = False
                            return sample_id, result_table, is_sql_executable, groundtruth, {}, fall_back_llm
                        else:
                            logger.error("Final step executed but no result found.")
                            break

                except Exception as e:
                    print(f"SQL execution error: {e}")
                    logger.error(f"SQL execution error: {e}")
                    print(traceback.format_exc())
                    break

            # If we exit the loop without a result, fall back to the original approach
            final_answer = wikitq_fall_back(original_table, sample, llm)
            return sample_id, final_answer, True, groundtruth, {"fallback": 1}, True

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
            final_answer = wikitq_fall_back(original_table, sample, llm)
            return sample_id, final_answer, True, groundtruth, {"error": 1}, True

else:
    raise ValueError(f"Invalid planning algorithm: {planning_algorithm}")


##################################################################################################################
##################################################################################################################
##################################################################################################################
##################################################################################################################
# TabFact functions

def tabfact_fall_back(fb_table, sample, llm):
    table_info = {}
    table_info["table_text"] = fb_table
    sample_copy = simple_query(sample, table_info, llm, debug=False, use_demo=False, llm_options=None)

    # print('answer for fall back:\n', sample_copy)
    
    fallback_answer = sample_copy["chain"][0]['parameter_and_conf'][0][0].upper()

    if fallback_answer == 'YES':
        answer = 'TRUE'
    elif fallback_answer == 'NO':
        answer = 'FALSE'
    else:
        answer = 'N/A'

    return answer

if planning_algorithm == 'static':

    def tabfact_natural_language_chain_exec_one_sample(sample, llm, llm_options=None, strategy="top", debug=False):
        logger, log_filename = setup_logger(sample["id"])
        table_info = get_table_info(sample)
        table_name = 'table_sql'
        sample_id = sample["id"]
        table_caption = sample['table_caption']

        original_table = copy.deepcopy(table_info["table_text"])  # Store the original table
        groundtruth = "TRUE" if sample["label"] == 1 else "FALSE"
        results = []
        is_sql_executable = False

        try:
            # PLANNING
            plans, plans_generated_successfully = tabfact_generate_natural_language_planning(
                sample, llm=llm, llm_options=llm_options, strategy=strategy, debug=debug
            )

            if not plans or not plans_generated_successfully:
                logger.error('Failed to generate plans or initial executable flag is False!')
                print('ERR2:Failed to generate plans or initial executable flag is False!')

                answer = tabfact_fall_back(original_table, sample, llm)
                result_dict = {}

                return sample_id, answer, is_sql_executable, groundtruth, result_dict, None

            for plan_idx, plan in enumerate(plans):

                intermediate_table = copy.deepcopy(original_table)  # Reset the table for each plan
                all_operations_successful = True
                logger.info('*' * 120)

                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Statement: {sample["statement"]}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Groundtruth: {groundtruth}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: X-Original table pd: \n{table2df(intermediate_table)}')
                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Caption: {table_caption}')

                logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Original table: {intermediate_table}')


                for operation_idx, operation in enumerate(plan):
                    if operation_idx == (len(plan) - 1):  # Last operation
                        statement = sample["statement"]
                    else:
                        statement = None

                    prompt = tabfact_natural_language_plan_step_to_sql(sample, intermediate_table, operation, table_name, statement)
                    logger.info('#' * 120)
                    try:
                        # print('prompt in to the model to get SQL:\n', prompt)
                        # PLAN TO SQL
                        responses = llm.generate_plus_with_score(prompt, options=llm_options, end_str="\n\n")

                        # print('response from to the model to get SQL:\n', responses)

                        if responses and len(responses) > 0 and len(responses[0]) > 0:
                            sql_command = extract_sql_code(responses[0][0])
                        else:
                            logger.error("No responses or unexpected response format.")
                            print(f'ERR3: No responses or unexpected response format:', responses)
                            continue  # Skip to the next iteration of the loop or handle error as needed

                        previous_ops = plan[0:operation_idx]
                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Operation {operation_idx + 1}: {operation}')

                        if SQL_EXECUTOR == 'SQL_ALCHEMY':
                            sql_command = text(sql_command)
                            intermediate_table, selected_indices = transform_table_with_sqlalchemy(intermediate_table, sql_command, table_name)
                            logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Selected indices: {selected_indices}')

                        else:
                            intermediate_table, selected_indices = transform_table_with_sql(intermediate_table, sql_command, table_name)
                            logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Selected indices: {selected_indices}')

                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: X-Table after operation df:\n{table2df(intermediate_table)}')
                        logger.info(f'Sample {sample_id} - Plan {plan_idx+1}: Table after operation: {(intermediate_table)}')

                        if len(intermediate_table) == 2 and (intermediate_table[0][0] == 'verification_result' or intermediate_table[0][0] == 'comparison_result'):
                            all_operations_successful = True
                            break
                    except Exception as e:
                        logger.error(f"SQL execution error in operation {operation_idx + 1}: {e}")
                        print(f'Sample {sample_id} - Plan {plan_idx+1}: Operation {operation_idx + 1}: {operation}')
                        print(f'ERR4: SQL execution error in operation {operation_idx + 1}: {e}')
                        break

                fall_back_llm = True
                if all_operations_successful:
                    if len(intermediate_table) > 1 and len(intermediate_table[1]) > 0:
                        answer = intermediate_table[1][0]
                        if answer in ["TRUE", "FALSE"]:
                            logger.info(f'Answer from plan {plan_idx + 1}: {answer}')
                            logger.info(f'Groundtruth: {groundtruth}')
                            fall_back_llm = False
                            logger.info(f'Fall-back: FALSE')

                        else:
                            # Doing fallback here with original table if SQL is executable cannot give answer in the right format
                            answer = tabfact_fall_back(original_table, sample, llm)
                            # print('final answer for fall back 3:\n', answer)
                            logger.info(f'Fall-back: TRUE')

                            logger.info(f'Answer from plan {plan_idx + 1}: {answer}')
                            logger.info(f'Groundtruth: {groundtruth}')

                    else: # Doing fallback here with original table if SQL is executable cannot give answer in the right format
                        # Doing fallback here with original table
                        answer = tabfact_fall_back(original_table, sample, llm)
                        logger.info(f'Fall-back: TRUE')

                        logger.info(f'Answer from plan {plan_idx + 1}: {answer}')
                        logger.info(f'Groundtruth: {groundtruth}')
                        # print('final answer for fall back 2:\n', answer)
                else:
                    # Doing fallback here with original table if SQL is failed
                        answer = tabfact_fall_back(original_table, sample, llm)
                        logger.info(f'Fall-back: TRUE')

                        logger.info(f'Answer from plan {plan_idx + 1}: {answer}')
                        logger.info(f'Groundtruth: {groundtruth}')
                        # print('final answer for fall back 1:\n', answer)

                results.append(answer)

            if results:
                # Majority vote
                result_counter = Counter(results)
                final_answer = result_counter.most_common(1)[0][0]
                is_sql_executable = True
                result_dict = dict(result_counter)
            else:
                final_answer = 'N/A'
                is_sql_executable = False
                print('it comes here')
                result_dict = {}

            # Determine the correctness of the answer
            if final_answer == groundtruth:
                if final_answer == "TRUE":
                    correctness_dir = "TP"
                else:
                    correctness_dir = "TN"
            else:
                if final_answer == "TRUE":
                    correctness_dir = "FP"
                elif final_answer == "FALSE":
                    correctness_dir = "FN"

            # Move the log file to the corresponding directory
            log_directory = os.path.dirname(log_filename)
            target_directory = os.path.join(log_directory, correctness_dir)
            os.makedirs(target_directory, exist_ok=True)
            shutil.move(log_filename, os.path.join(target_directory, os.path.basename(log_filename)))

            return sample_id, final_answer, is_sql_executable, groundtruth, result_dict, fall_back_llm

        except Exception as e:
            logger.error(f"Unexpected error in generating plans: {e}")
            print(f'ERR5: Planning failed!: {e}')

            answer = tabfact_fall_back(original_table, sample, llm)
            result_dict = {}
            is_sql_executable = False
            return sample_id, answer, is_sql_executable, groundtruth, result_dict, None

elif planning_algorithm == 'dynamic':

    def tabfact_natural_language_chain_exec_one_sample(sample, llm, llm_options=None, strategy="top", debug=False):
        logger, log_filename = setup_logger(sample["id"])
        table_info = get_table_info(sample)
        table_name = 'table_sql'
        sample_id = sample["id"]
        table_caption = sample['table_caption']

        original_table = copy.deepcopy(table_info["table_text"])
        groundtruth = "TRUE" if sample["label"] == 1 else "FALSE"
        operation_history = []
        intermediate_table = copy.deepcopy(original_table)
        is_sql_executable = False

        try:
            while True:  # Continue until we reach a verification step or max steps

                # print('operation_history:', operation_history)
                if len(operation_history) >= 10:  # Prevent infinite loops
                    logger.warning("Maximum steps reached, falling back to default approach")
                    print("Maximum steps reached, falling back to default approach")

                    break

                # Get next operation dynamically
                next_operation = tabfact_generate_natural_language_planning(
                    sample,
                    intermediate_table,
                    operation_history,
                    llm=llm,
                    llm_options=llm_options,
                    strategy=strategy,
                    debug=debug
                )

                if not next_operation:
                    logger.error('Failed to generate next operation')
                    print('Failed to generate next operation')

                    break

                # Log current state and operation
                logger.info('*' * 120)
                logger.info(f'Sample {sample_id} - Operation {len(operation_history) + 1}: {next_operation}')
                logger.info(f'Current table state: {intermediate_table}')

                # Convert operation to SQL and execute
                prompt = tabfact_natural_language_plan_step_to_sql(
                    sample,
                    intermediate_table,
                    next_operation,
                    table_name,
                    sample["statement"] if "verification" in next_operation.lower() else None
                )

                try:
                    responses = llm.generate_plus_with_score(prompt, options=llm_options, end_str="\n\n")
                    if responses and len(responses) > 0 and len(responses[0]) > 0:
                        sql_command = extract_sql_code(responses[0][0])
                    else:
                        logger.error("No SQL generated")
                        print("No SQL generated")

                        break

                    # Execute SQL
                    if SQL_EXECUTOR == 'SQL_ALCHEMY':
                        sql_command = text(sql_command)
                        intermediate_table, selected_indices = transform_table_with_sqlalchemy(
                            intermediate_table, sql_command, table_name
                        )
                    else:
                        intermediate_table, selected_indices = transform_table_with_sql(
                            intermediate_table, sql_command, table_name
                        )

                    operation_history.append(next_operation)

                    # Check if we've reached a verification result
                    if (len(intermediate_table) == 2 and
                            (intermediate_table[0][0] == 'verification_result' or
                             intermediate_table[0][0] == 'comparison_result')):
                        is_sql_executable = True
                        answer = intermediate_table[1][0]
                        if answer in ["TRUE", "FALSE"]:
                            return sample_id, answer, is_sql_executable, groundtruth, {"dynamic": 1}, False

                except Exception as e:
                    print(f"SQL execution error 1: {e}")
                    logger.error(f"SQL execution error: {e}")
                    break

            print(f"SQL execution error 3:\n {operation_history}")

            # If we exit the loop without a result, fall back to the original approach
            answer = tabfact_fall_back(original_table, sample, llm)
            return sample_id, answer, True, groundtruth, {"fallback": 1}, True

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"Unexpected error 2: {e}")
            answer = tabfact_fall_back(original_table, sample, llm)
            return sample_id, answer, True, groundtruth, {"error": 1}, True
else:
    raise ValueError(f"Invalid planning algorithm: {planning_algorithm}")

##################################################################################################################
##################################################################################################################
##################################################################################################################
##################################################################################################################


# proc_sample ~= init_samples
def fixed_chain_exec_mp(llm, init_samples, fixed_op_list, n_proc=10, chunk_size=50):
    history = {}
    final_result = None

    chain_header = copy.deepcopy(init_samples)
    chain_key = ""

    if DEBUG:
        print(fixed_op_list)

    for i, (op_name, solver_func, kargs, llm_kargs) in enumerate(fixed_op_list):
        # Here is where the table manipulation is done
        chain_key += f"->{op_name}" if i > 0 else op_name
        if DEBUG:
            print(op_name)
        chain_header = conduct_single_solver_mp(
            llm=llm,
            all_samples=chain_header,
            solver_func=solver_func,
            tqdm_tag=op_name,
            n_proc=n_proc,
            chunk_size=chunk_size,
            llm_options=llm.get_model_options(
                **llm_kargs,
            ),
            **kargs,
        )

        history[f"({i}) {chain_key}"] = chain_header
        if i == len(fixed_op_list) - 1:
            final_result = chain_header

    return final_result, history


def conduct_single_solver(llm, all_samples, solver_func, tqdm_tag=None, **kwargs):
    result_samples = [None for _ in range(len(all_samples))]

    for idx in tqdm(range(len(all_samples)), desc=tqdm_tag):
        try:
            sample = all_samples[idx]
            table_info = get_table_info(
                sample,
                skip_op=kwargs.get("skip_op", []),
                first_n_op=kwargs.get("first_n_op", None),
            )
            proc_sample = solver_func(sample, table_info, llm, **kwargs)
            result_samples[idx] = proc_sample
        except Exception as e:
            print(f"CKPT1: Error in {idx}th sample: {e}")
            continue
    return result_samples


def _conduct_single_solver_mp_core(arg):
    idx, sample, llm, solver_func, kwargs = arg
    try:
        table_info = get_table_info(
            sample,
            skip_op=kwargs.get("skip_op", []),
            first_n_op=kwargs.get("first_n_op", None),
        )
        proc_sample = solver_func(sample, table_info, llm, **kwargs)
        return idx, proc_sample
    except Exception as e:
        traceback.print_exc()
        print(f"CKPT: Error in {idx}-th sample: {e}")
        return idx, None


def conduct_single_solver_mp(
    llm, all_samples, solver_func, tqdm_tag=None, n_proc=10, chunk_size=50, **kwargs
):
    result_samples = [None for _ in range(len(all_samples))]

    args = [
        (idx, sample, llm, solver_func, kwargs)
        for idx, sample in enumerate(all_samples)
    ]
    
    with mp.Pool(n_proc) as p:
        for idx, proc_sample in tqdm(
            p.imap_unordered(_conduct_single_solver_mp_core, args, chunksize=chunk_size),
            total=len(all_samples),
            desc=tqdm_tag,
        ):
            result_samples[idx] = proc_sample
            print(result_samples[idx])
            print(all_samples[idx]['is_sql_executable'])
            result_samples[idx]['is_sql_executable'] = all_samples[idx]['is_sql_executable']

    return result_samples

def generate_prompt_for_next_step(
    sample,
    debug=False,
    llm=None,
    llm_options=None,
    strategy="top",
):
    table_info = get_table_info(sample)
    act_chain = table_info["act_chain"]

    if debug:
        print("Act Chain: ", act_chain, flush=True)

    kept_act_chain = [x for x in act_chain if not x.startswith("skip")]
    kept_act_chain_str = " -> ".join(kept_act_chain)
    if kept_act_chain_str:
        kept_act_chain_str += " ->"

    skip_act_chain = [x for x in act_chain if x.startswith("skip")]
    skip_act_chain_op_names = []
    for op in skip_act_chain:
        op = op[len("skip ") :]
        op_name = get_operation_name(op)
        skip_act_chain_op_names.append(op_name)

    if debug:
        print("Kept Act Chain: ", kept_act_chain, flush=True)
        print("Skip Act Chain: ", skip_act_chain, flush=True)

    if USING_SQL is True:
        # Set the first operation to 'select_column' if the act_chain is empty
        if not kept_act_chain:
            log = {
                "act_chain": act_chain,
                "last_operation": "<init>",
                "possible_next_operations": ["select_column"],
                "prompt": None,
                "response": None,
                "generate_operations": None,
                "next_operation": "select_column",
            }
            return "select_column", log

    last_operation = (
        "<init>" if not kept_act_chain else get_operation_name(kept_act_chain[-1])
    )
    possible_next_operations = possible_next_operation_dict[last_operation]
    possible_next_operations = [
        x for x in possible_next_operations if x not in skip_act_chain_op_names
    ]

    # Remove f_sort_column() if only one row in the table
    table_text = table_info["table_text"]
    if DEBUG:
        print('Table text:')
        print(table_text)
        print('Possible next operations:')
        print(possible_next_operations)
    
    if USING_SQL is True:
        if len(table_text) <= 2:  # Check if there's only one data row besides the header
            print('before:', possible_next_operations)
            print('One-row table! Skipping operations')
            possible_next_operations = [op for op in possible_next_operations if op != "sort_column" and op != "select_row" and op!= "group_column"]
            print('after:', possible_next_operations)

    if DEBUG:
        print("Last Operation: ", last_operation, flush=True)
        print("Final Possible Next Operations: ", possible_next_operations, flush=True)

    if len(possible_next_operations) == 1:
        log = {
            "act_chain": act_chain,
            "last_operation": last_operation,
            "possible_next_operations": possible_next_operations,
            "prompt": None,
            "response": None,
            "generate_operations": None,
            "next_operation": possible_next_operations[0],
        }
        return possible_next_operations[0], log

    prompt = ""
    for operation in possible_next_operations:
        if operation == "<END>":
            continue
        if USING_SQL is True:
            prompt += eval(f"plan_{operation}_demo_sql") + "\n\n"
        else:
            prompt += eval(f"plan_{operation}_demo") + "\n\n"

    prompt += plan_full_demo_simple + "\n\n"
    
    if USING_SQL:
        prompt += "########\nHere is your actual task.\n"
        # prompt += "\nPlease always try to use select_row function for the first operation in the chain. For example, Function Chain: f_select_column() -> f_select_row() -> f_select_column() -> f_group_column() -> <END>\n"

    prompt += "/*\n" + table2string(table_info["table_text"]) + "\n*/\n"
    prompt += "Statement: " + sample["statement"] + "\n"

    _possible_next_operations_str = " or ".join(
        [f"f_{op}()" if op != "<END>" else op for op in possible_next_operations]
    )

    if len(possible_next_operations) > 1:
        prompt += (
            f"The next operation must be one of {_possible_next_operations_str}.\n"
        )
    else:
        prompt += f"The next operation must be {_possible_next_operations_str}.\n"

    prompt += "Function Chain: " + kept_act_chain_str
    if DEBUG:
        print('Before prompting to get operation')
        print(prompt)
    
    if USING_SQL is True:
        try:
            responses = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
        except Exception as e:
            print(f"Error when prompting model in generating next operation. Maybe the prompt is too long and exceeds context length!")
            log = {
            "act_chain": act_chain,
            "last_operation": last_operation,
            "possible_next_operations": possible_next_operations,
            "prompt": None,
            "response": None,
            "generate_operations": None,
            "next_operation": possible_next_operations[0],
            }
            return possible_next_operations[0], log
    else:
        responses = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
        
    if DEBUG:
        print('Model response:')
        print(responses)
        print('*'*100)

    # choose the first suggested operation
    if strategy == "top":
        response = responses[0][0]
        # print(responses)
        generate_operations = get_all_operation_names(response)
        if DEBUG:
            print('Prompt:', prompt.split("\n\n")[-1])
            print('Response:', response)
            print("Generated Operations: ", generate_operations)
        next_operation = "<END>"
        for operation in generate_operations:
            if operation in possible_next_operations:
                next_operation = operation
                # print('Next operation:', next_operation)

                break
    elif strategy == "voting":
        next_operation_conf_dict = defaultdict(float)
        for response, score in responses:
            generate_operations = get_all_operation_names(response)
            next_operation = None
            for operation in generate_operations:
                if operation in possible_next_operations:
                    next_operation = operation
                    break
            if next_operation:
                next_operation_conf_dict[next_operation] += np.exp(score)
        if len(next_operation_conf_dict) != 0:
            next_operation_conf_pairs = sorted(
                next_operation_conf_dict.items(), key=lambda x: x[1], reverse=True
            )
            next_operation = next_operation_conf_pairs[0][0]
        else:
            next_operation = "<END>"

    log = {
        "act_chain": act_chain,
        "last_operation": last_operation,
        "possible_next_operations": possible_next_operations,
        "prompt": prompt,
        "response": response,
        "generate_operations": generate_operations,
        "next_operation": next_operation,
    }
    return next_operation, log


def dynamic_chain_exec_one_sample(
    sample,
    llm,
    llm_options=None,
    strategy="top",
    debug=False,
    operation_parameter_dict=None,
):      
    dynamic_chain_log = []

    # breakpoint()

    current_sample = copy.deepcopy(sample)
    # If none if the operations can be done by SQL, return False
    sql_executable = False
    is_sql_executable = False
        
    while True:
        # generate next operation
        next_operation, log = generate_prompt_for_next_step(
            current_sample,
            llm=llm,
            llm_options=llm_options,
            strategy=strategy,
            debug=debug,
        )
        dynamic_chain_log.append(log)
        if DEBUG:
            print('Expanding the chain...')
            print(next_operation)
        #     print('Chain:')
        #     print(dynamic_chain_log)

        if debug:
            print(next_operation)

        if next_operation == "<END>":
            break

        # Get solver_func to process the Table
        # TODO: Change the table here by using LLMs
        param = operation_parameter_dict[next_operation]

        # Get the solver function that will generate the arguments for the given operation
        op_name, solver_func, kargs, op_llm_options = param
        if DEBUG:
            print('op_name:')
            print(op_name)
            print('Table info BEFORE table manipulation operation:')

        # Then perform the modification on the existing table here.
        # check if using SQL failed --> change the act function

        table_info = get_table_info(current_sample)

        if DEBUG:
            print('Table info AFTER table manipulation operation:')
            print(table_info)


        if current_sample['using_sql'] is True:
            current_sample, is_sql_executable, op_name = solver_func(
                current_sample, table_info, llm=llm, llm_options=op_llm_options, **kargs
        )
        else:
            current_sample = solver_func(
                current_sample, table_info, llm=llm, llm_options=op_llm_options, **kargs
            )

        if is_sql_executable is True:
            sql_executable = True

            
    return current_sample, dynamic_chain_log, sql_executable


def dynamic_chain_exec_with_cache_for_loop(
    all_samples,
    llm,
    llm_options=None,
    strategy="voting",
    cache_dir="./cache/debug",
):
    os.makedirs(cache_dir, exist_ok=True)
    result_samples = [None for _ in range(len(all_samples))]
    dynamic_chain_log_list = [None for _ in range(len(all_samples))]

    cache_filename = "case-{}.pkl"

    def _func(idx):
        sample = all_samples[idx]
        sample_id = sample["id"]
        cache_path = os.path.join(cache_dir, cache_filename.format(sample_id))
        if os.path.exists(cache_path):
            _, proc_sample, log = pickle.load(open(cache_path, "rb"))
        else:
            proc_sample, log = dynamic_chain_exec_one_sample(
                sample, llm=llm, llm_options=llm_options, strategy=strategy
            )
            pickle.dump((sample, proc_sample, log), open(cache_path, "wb"))
        result_samples[idx] = proc_sample
        dynamic_chain_log_list[idx] = log

    for idx in tqdm(range(len(all_samples)), total=len(all_samples)):
        try:
            _func(idx)
        except Exception as e:
            print(f"IDX={idx}: {e}", flush=True)

    return result_samples, dynamic_chain_log_list

def bytes_to_serializable(obj):
    """Convert bytes objects to Base64 encoded strings for JSON serialization."""
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')  # Try to decode as text
    elif isinstance(obj, dict):
        return {k: bytes_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [bytes_to_serializable(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(bytes_to_serializable(i) for i in obj)
    else:
        return obj

def save_processed_samples_safe(result_file_path, new_sample_data):
    """Thread-safe function to save processed samples"""
    lock_path = f"{result_file_path}.lock"
    with FileLock(lock_path):
        # Read current data
        try:
            with open(result_file_path, 'r') as f:
                try:
                    current_data = json.load(f)
                except json.JSONDecodeError:
                    current_data = {}
        except FileNotFoundError:
            current_data = {}

        # Update with new data, making sure it's JSON serializable
        current_data.update(bytes_to_serializable(new_sample_data))

        # Write back
        with open(result_file_path, 'w') as f:
            json.dump(current_data, f, indent=4)

# def save_processed_samples_safe(result_file_path, new_sample_data):
#     """Thread-safe function to save processed samples"""
#     lock_path = f"{result_file_path}.lock"
#     with FileLock(lock_path):
#         # Read current data
#         try:
#             with open(result_file_path, 'r') as f:
#                 try:
#                     current_data = json.load(f)
#                 except json.JSONDecodeError:
#                     current_data = {}
#         except FileNotFoundError:
#             current_data = {}
#
#         # Update with new data
#         current_data.update(new_sample_data)
#
#         # Write back
#         with open(result_file_path, 'w') as f:
#             json.dump(current_data, f, indent=4)


def _wikitq_natural_language_chain_exec_with_cache_mp_core(arg):
    idx, sample, llm, llm_options, strategy, cache_dir = arg

    sample_id = sample["id"]

    # Load existing processed results - this is safe to do in parallel
    try:
        with open(result_file_name, 'r') as f:
            processed_samples = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_samples = {}

    # Check if already processed
    if str(sample_id) in processed_samples:
        print(f"Skipping already processed sample {sample_id}")
        cached_data = processed_samples[str(sample_id)][str(sample_id)]
        return (sample, sample_id,
                cached_data['answer'],
                cached_data['is_sql_executable'],
                cached_data['groundtruth'],
                cached_data['answer_plans'],
                None,
                cached_data['fallback_LLM'])

    # Process new sample
    sample_id, answer, is_sql_executable, groundtruth, result_dict, fall_back_llm = \
        wikitq_natural_language_chain_exec_one_sample(
            sample, llm=llm, llm_options=llm_options, strategy=strategy)

    # Prepare new sample data
    new_sample_data = {
        str(sample_id): {
            str(sample_id): {
                'input': sample,
                'id': sample_id,
                'answer': answer,
                'answer_plans': result_dict,
                'groundtruth': groundtruth,
                'fallback_LLM': fall_back_llm,
                'is_sql_executable': is_sql_executable
            }
        }
    }

    # Save with thread-safe function
    save_processed_samples_safe(result_file_name, new_sample_data)

    return sample, sample_id, answer, is_sql_executable, groundtruth, result_dict, None, fall_back_llm


def _natural_language_chain_exec_with_cache_mp_core(arg):
    idx, sample, llm, llm_options, strategy, cache_dir = arg

    sample_id = sample["id"]

    # Load existing processed results - this is safe to do in parallel
    try:
        with open(result_file_name, 'r') as f:
            processed_samples = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_samples = {}

    # Check if already processed
    if str(sample_id) in processed_samples:
        unprocessed = False
        print(f"Skipping already processed sample {sample_id}")
        cached_data = processed_samples[str(sample_id)][str(sample_id)]
        return (unprocessed, sample, sample_id,
                cached_data['answer'],
                cached_data['is_sql_executable'],
                cached_data['groundtruth'],
                cached_data['answer_plans'],
                None,
                cached_data['fallback_LLM'])

    # Process new sample
    sample_id, answer, is_sql_executable, groundtruth, result_dict, fb_llm = \
        tabfact_natural_language_chain_exec_one_sample(
            sample, llm=llm, llm_options=llm_options, strategy=strategy)

    # Prepare new sample data
    new_sample_data = {
        str(sample_id): {
            str(sample_id): {
                'input': sample,
                'id': sample_id,
                'answer': answer,
                'answer_plans': result_dict,
                'groundtruth': groundtruth,
                'fallback_LLM': fb_llm,
                'is_sql_executable': is_sql_executable
            }
        }
    }

    # Save with thread-safe function
    save_processed_samples_safe(result_file_name, new_sample_data)

    return True, sample, sample_id, answer, is_sql_executable, groundtruth, result_dict, None, fb_llm

def _dynamic_chain_exec_with_cache_mp_core(arg):
    idx, sample, llm, llm_options, strategy, cache_dir = arg

    cache_filename = "case-{}.pkl"

    done_by_SQL = 0
    is_sql_executable = False
    if True:
        sample_id = sample["id"]
        cache_path = os.path.join(cache_dir, cache_filename.format(idx))

        if True:

            operation_parameters_dict = {}
            operation_parameters_dict['SQL'] = {
                "add_column": (
                    "addColumn",
                    add_column_func_sql,
                    {},
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
                "select_row": (
                    "selectRow",
                    select_row_func_sql,
                    {},
                    llm.get_model_options(
                        temperature=0.5,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                        n_sample=8,
                    ),
                ),
                "select_column": (
                    "selectColumn",
                    select_column_func_sql,
                    {},
                    llm.get_model_options(
                        temperature=0.5,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                        n_sample=8,
                    ),
                ),
                "group_column": (
                    "groupColumn",
                    group_column_func_sql,
                    dict(skip_op=[]),
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
                "sort_column": (
                    "sortColumn",
                    sort_column_func_sql,
                    dict(skip_op=[]),
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
            }
            #######################################################################################################################################
            operation_parameters_dict['No_SQL'] = {
                "add_column": (
                    "addColumn",
                    add_column_func,
                    {},
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
                "select_row": (
                    "selectRow",
                    select_row_func,
                    {},
                    llm.get_model_options(
                        temperature=0.5,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                        n_sample=8,
                    ),
                ),
                "select_column": (
                    "selectColumn",
                    select_column_func,
                    {},
                    llm.get_model_options(
                        temperature=0.5,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                        n_sample=8,
                    ),
                ),
                "group_column": (
                    "groupColumn",
                    group_column_func,
                    dict(skip_op=[]),
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
                "sort_column": (
                    "sortColumn",
                    sort_column_func,
                    dict(skip_op=[]),
                    llm.get_model_options(
                        temperature=0.0,
                        per_example_max_decode_steps=150,
                        per_example_top_p=1.0,
                    ),
                ),
            }

            is_sql_executable = False
            if USING_SQL is True:
                try:
                    sample['using_sql'] = True
                    proc_sample, log, is_sql_executable = dynamic_chain_exec_one_sample(
                        sample, llm=llm, llm_options=llm_options, strategy=strategy,
                        operation_parameter_dict = operation_parameters_dict['SQL']
                    )

                    if not is_sql_executable:
                        sample['using_sql'] = False
                        # Attempt the second method if SQL is not executable
                        print("SQL execution failed, trying alternative method...")
                        # print('Processed samples by using_sql:\n', proc_sample)

                        proc_sample, log, _ = dynamic_chain_exec_one_sample(
                            sample, llm=llm, llm_options=llm_options, strategy=strategy,
                            operation_parameter_dict = operation_parameters_dict['No_SQL']
                        )
                    else:
                        done_by_SQL += 1
                except Exception as e:
                    # Handle the exception and proceed with alternative method
                    print(f"Error during SQL execution: {e}, trying alternative method...")
                    is_sql_executable = False
                    sample['using_sql'] = False
                    proc_sample, log, _ = dynamic_chain_exec_one_sample(
                        sample, llm=llm, llm_options=llm_options, strategy=strategy,
                        operation_parameter_dict = operation_parameters_dict['No_SQL']
                    )
            else:
                is_sql_executable = False
                sample['using_sql'] = False
                proc_sample, log, _ = dynamic_chain_exec_one_sample(
                    sample, llm=llm, llm_options=llm_options, strategy=strategy,
                    operation_parameter_dict = operation_parameters_dict['No_SQL']
                )

            with open(cache_path, "wb") as f:
                pickle.dump((sample, proc_sample, log), f)
        
        print('Done by SQL:', done_by_SQL)
    return idx, proc_sample, log, is_sql_executable

def dynamic_chain_exec_with_cache_mp(
    all_samples,
    llm,
    llm_options=None,
    strategy="voting",
    cache_dir="./results/debug",
    n_proc=10,
    chunk_size=50,
):
    os.makedirs(cache_dir, exist_ok=True)
    result_samples = [None for _ in range(len(all_samples))]
    dynamic_chain_log_list = [None for _ in range(len(all_samples))]
    result_dict = {}

    args = [
        (idx, sample, llm, llm_options, strategy, cache_dir)
        for idx, sample in enumerate(all_samples)
    ]

    sql_cnt = 0

    if NATURAL_LANGUAGE_PLANNING is True:
        result_samples = {}
        with mp.Pool(n_proc) as p:
            for unprocessed, sample, sample_id, answer, is_sql_executable, groundtruth, result_dict, subs, fb_llm in tqdm(
                p.imap_unordered(
                    _natural_language_chain_exec_with_cache_mp_core, args, chunksize=chunk_size
                ),
                total=len(all_samples),
            ):

                result_samples[f'{sample_id}'] = {}
                result_samples[f'{sample_id}']['input'] = sample
                result_samples[f'{sample_id}']['input']['sub_statements'] = subs
                result_samples[f'{sample_id}']['id'] = sample_id
                result_samples[f'{sample_id}']['answer'] = answer
                result_samples[f'{sample_id}']['answer_plans'] = result_dict
                result_samples[f'{sample_id}']['groundtruth'] = groundtruth
                result_samples[f'{sample_id}']['fallback_LLM'] = fb_llm
                result_samples[f'{sample_id}']['is_sql_executable'] = is_sql_executable

                dynamic_chain_log_list = None

    elif OTG_PLANNING is True:
        with mp.Pool(n_proc) as p:
            for idx, proc_sample, log, is_sql_executable in tqdm(
                p.imap_unordered(
                    _dynamic_chain_exec_with_cache_mp_core, args, chunksize=chunk_size
                ),
                total=len(all_samples),
            ):
                if is_sql_executable is True:
                    sql_cnt += 1
                result_samples[idx] = proc_sample
                result_samples[idx]['is_sql_executable'] = is_sql_executable
                dynamic_chain_log_list[idx] = log
    
        print('Number of samples that have tables (record 1) edited by SQLs:', sql_cnt)

    print('Number of total samples tested:', len(all_samples))

    return result_samples, dynamic_chain_log_list


def wikitq_dynamic_chain_exec_with_cache_mp(
    all_samples,
    llm,
    llm_options=None,
    strategy="voting",
    cache_dir="./results/debug",
    n_proc=10,
    chunk_size=50,
):
    os.makedirs(cache_dir, exist_ok=True)
    result_samples = [None for _ in range(len(all_samples))]
    dynamic_chain_log_list = [None for _ in range(len(all_samples))]
    result_dict = {}

    args = [
        (idx, sample, llm, llm_options, strategy, cache_dir)
        for idx, sample in enumerate(all_samples)
    ]

    sql_cnt = 0

    if NATURAL_LANGUAGE_PLANNING is True:
        result_samples = {}
        with mp.Pool(n_proc) as p:
            for sample, sample_id, answer, is_sql_executable, groundtruth, result_dict, subs, fb_llm in tqdm(
                p.imap_unordered(
                    _wikitq_natural_language_chain_exec_with_cache_mp_core, args, chunksize=chunk_size
                ),
                total=len(all_samples),
            ):

                result_samples[sample_id] = {}
                result_samples[sample_id]['input'] = sample
                result_samples[sample_id]['input']['sub_statements'] = subs
                result_samples[sample_id]['id'] = sample_id
                result_samples[sample_id]['answer'] = answer
                result_samples[sample_id]['answer_plans'] = result_dict
                result_samples[sample_id]['groundtruth'] = groundtruth
                result_samples[sample_id]['fallback_LLM'] = fb_llm
                result_samples[sample_id]['is_sql_executable'] = is_sql_executable

                dynamic_chain_log_list = None

    return result_samples, dynamic_chain_log_list