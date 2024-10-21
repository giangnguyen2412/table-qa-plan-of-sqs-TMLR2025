from utils.helper import table2string
from operations import *
from utils.helper import *
from utils.prompts import *


def plan_to_step_list(plan):
    # Split the string by newline characters to get individual steps
    steps_list = plan.split('\n')
    # Remove the step numbers
    steps_list = [step.split('. ', 1)[1] if '. ' in step else step for step in steps_list]

    return steps_list

def wikitq_natural_language_plan_step_to_sql(sample, intermediate_table, action, table_name, statement):
    table_name = 'table_sql'
    question = sample['statement']
    table_text = sample['table_text']
    answer = sample['answer']

    if len(intermediate_table[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in intermediate_table[0])
    else:
        existing_cols = f"{intermediate_table[0][0]}"

    prompt = ""
    prompt += wikitq_natural_language_step_to_sql_demo
    prompt += "\n####\n"

    prompt += f"Given this table:\n"
    prompt += "/*\n" + table2string(intermediate_table) + "\n*/\n"

    data_type = table2df(intermediate_table).dtypes

    prompt += "\nData types of columns:\n"
    for col, dtype in data_type.items():
        dtype_str = "string" if dtype == "object" else str(dtype)
        prompt += f"- {col}: {dtype_str}\n"

    prompt += f"\nWrite a SQL command that: {action}\n"

    num_rows = len(table_text) - 1

    prompt += f"\n\nConstraints for your SQL:\n"

    prompt += "\n1.The columns used in your SQL MUST be: "
    prompt += f"{existing_cols}."
    prompt += "\n Otherwise, you will be PENALIZED!"

    prompt += f"\n2.{syntax_instr1} If adding new columns, they MUST be different than existing columns {existing_cols}"

    prompt += f"\n3.Your SQL command MUST be compatible and executable by python sqlite3."
    prompt += f"\n4.If using FROM, the table to be selected MUST be {table_name}."
    prompt += f"\n5.You MUST look at the cell contents in {table_name} and consider data format to avoid problems of exact matchings in SQL. Sometimes, data in the action and Table are not in the same format."
    prompt += f"\n6.If there are conflicting data types between the table and the natural language action, you should convert them into the same data type. Note: 'object' data type corresponds to 'string' data type."

    prompt += "\n####\n"
    return prompt


def wikitq_generate_natural_language_planning(sample, debug=False, llm=None, llm_options=None, strategy="top"):
    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    # llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt
    llm_options["n"] = K_plans  # Request multiple responses for a single prompt

    if llm_options["n"] > 1:
        llm_options["temperature"] = 0.8
        llm_options["top_p"] = 1.0

    statement = sample['statement']
    table_text = sample['table_text']
    answer = sample['answer']

    is_sql_executable = False
    num_rows = len(table_text) - 1

    prompt = ""

    prompt += wikitq_natural_language_plan_demo + "\n"

    prompt += "\n### Here come to your task!\n"
    # We dont have table caption in WikiTQ
    prompt += "/*\n" + table2string(table_text) + "\n*/\n"
    prompt += f"This Table has {num_rows} rows.\n"
    prompt += "Question: " + statement + "\n"

    prompt += """
    Let's develop a precise and detailed step-by-step plan to answer the given Question based on the provided Table.

    Your steps will later be converted to SQL commands to transform the Table into the final answer for the question. 
    You MUST thoroughly analyze and understand the Question before writing the plan.

    Plan Steps:
    1. Each step in your plan should be atomic and straightforward, ensuring they can be easily executed or converted into SQL.
    2. You MUST closely examine the Question and ensure all conditions are checked accurately.

    Step Order:
    1. The order of steps is crucial! Ensure the steps logically support the correct answering.
    2. Each step will be executed sequentially, with the next step operating on the output table of the previous step. 
    The first step will be executed on the given Table.

    Final Step:
    Ensure the last step involves selecting the relevant cells or calculating the values that correctly answer the Question.

    Plan:\n
    """

    # if True:
    #     print('Model prompt for plan:\n')
    #     print(prompt)
    #     print('X'*100)

    try:
        responses = llm.generate_plus_with_score(
            prompt, options=llm_options, end_str="\n\n"
        )
        is_sql_executable = True

    except Exception as e:
        print('ERR1: Cannot generate plans:', (e))
        return None, is_sql_executable

    # Extract the plan
    responses.sort(key=lambda x: x[1], reverse=True)
    plans = []
    for response, score in responses:
        plans.append(plan_to_step_list(response))

    # print('generated plans:\n', plans)
    return plans, is_sql_executable


def tabfact_natural_language_plan_step_to_sql(sample, intermediate_table, action, table_name, statement):
    if len(intermediate_table[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in intermediate_table[0])
    else:
        existing_cols = f"{intermediate_table[0][0]}"

    prompt = ""
    prompt += tabfact_natural_language_step_to_sql_demo
    prompt += "\n####\n"

    prompt += f"Given this table:\n"
    prompt += "/*\n" + table2string(intermediate_table) + "\n*/\n"

    data_type = table2df(intermediate_table).dtypes
    # print(intermediate_table)
    # print(data_type)

    prompt += "\nData types of columns:\n"
    for col, dtype in data_type.items():
        dtype_str = "string" if dtype == "object" else str(dtype)
        prompt += f"- {col}: {dtype_str}\n"

    prompt += f"\nWrite a SQL command that: {action}\n"

    table_info = get_table_info(sample)
    num_rows = len(table_info["table_text"]) - 1
    prompt += f"The original table has {num_rows} rows.\n"

    prompt += f"\n\nConstraints for your SQL:\n"

    prompt += f"\n1.{syntax_instr1} If adding new columns, they should be different than columns {existing_cols}"

    prompt += f"\n2. Your SQL command MUST be compatible and executable by python sqlite3 and pandas."
    prompt += f"\n3. If using FROM, the table to be selected MUST be {table_name}."
    prompt += "\n####\n"
    return prompt


def tabfact_generate_natural_language_planning(
        sample,
        debug=False,
        llm=None,
        llm_options=None,
        strategy="top",
):
    # Set up LLM options
    if llm_options is None:
        llm_options = llm.get_model_options()
    # llm_options["n"] = OPERATION_NUMS  # Request multiple responses for a single prompt
    llm_options["n"] = K_plans  # Request multiple responses for a single prompt

    if llm_options["n"] > 1:
        llm_options["temperature"] = 0.8
        llm_options["top_p"] = 1.0

    table_info = get_table_info(sample)
    act_chain = table_info["act_chain"]
    caption = sample["table_caption"]
    is_sql_executable = False
    num_rows = len(table_info["table_text"]) - 1

    prompt = ""

    prompt += tabfact_natural_language_plan_demo + "\n"

    prompt += "\n### Here come to your task!\n"
    prompt += f"table caption: {caption}\n"
    prompt += "/*\n" + table2string(table_info["table_text"]) + "\n*/\n"
    prompt += f"This Table has {num_rows} rows.\n"
    prompt += "Statement: " + sample["statement"] + "\n"

    prompt += """
    Let's develop a step-by-step plan to verify if the given Statement is TRUE or FALSE on the given Table!
    You MUST think carefully analyze the Statement and comprehend it before writing the plan!

    Plan Steps: Each step in your plan should be very atomic and straightforward, ensuring they can be easily executed or converted into SQL.
    You MUST make sure all conditions (except those mentioned in the table caption) are checked properly in the steps.

    Step order: The order of steps is crucial! You must ensure the orders support the correct information retrieval and verification!
    The next step will be executed on the output table of the previous step. The first step will be executed on the given Table.
    For comparative or superlative Statement involving "highest", "lowest", "earliest", "latest", "better", "faster", "earlier", etc., 
    you should order the table accordingly before selecting rows. This ensures that the desired comparative or superlative data is correctly retrieved.

    Plan:\n
    """

    # if True:
    #     print('Model prompt for plan:\n')
    #     print(prompt)
    #     print('X'*100)

    try:
        responses = llm.generate_plus_with_score(
            prompt, options=llm_options, end_str="\n\n"
        )
        is_sql_executable = True

    except Exception as e:
        print('ERR1: Cannot generate plans:', (e))
        return None, is_sql_executable

    # if True:
    #     print('Model response for plan:\n')
    #     print(responses)
    #     print('X'*100)

    # Extract the plan
    responses.sort(key=lambda x: x[1], reverse=True)
    plans = []
    for response, score in responses:
        plans.append(plan_to_step_list(response))

    # print('generated plans:\n', plans)
    return plans, is_sql_executable

