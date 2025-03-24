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

if planning_algorithm == 'static':

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

        # prompt += general_natural_language_plan_demo + "\n"
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

elif planning_algorithm == 'dynamic':

    def wikitq_generate_natural_language_planning(
            sample,
            current_table,
            operation_history=None,
            debug=False,
            llm=None,
            llm_options=None,
            strategy="top"
    ):
        """
        Generate the next operation dynamically based on current state and history.
        :param sample:
        :param current_table:
        :param operation_history:
        :param debug:
        :param llm:
        :param llm_options:
        :param strategy:
        :return:
        """
        if operation_history is None:
            operation_history = []

        # Set up LLM options
        if llm_options is None:
            llm_options = llm.get_model_options()
        llm_options["n"] = 1  # We only need one next step at a time

        statement = sample['statement']
        num_rows = len(current_table) - 1

        if not operation_history:
            prompt = ""
            prompt += wikitq_natural_language_plan_demo + "\n"
            # prompt += general_natural_language_plan_demo + "\n"
            prompt += f"""
################## Here comes your task!

Input Table:
{table2string(current_table)}

This Table has {num_rows} rows.
Question: {statement}

Let's write the first step in the plan to transform the Input Table.
You MUST carefully analyze and understand the Question before writing the first step!

Your step should be very atomic and straightforward, ensuring it can be easily executed or converted into SQL.

For comparative or superlative questions involving "highest", "lowest", "earliest", "latest", "better", "faster", "earlier", etc.,
you should order the table accordingly before selecting rows. This ensures that the desired comparative or superlative data is correctly retrieved.

Remember to always add the step number **1.** before step. If this step provides the final answer to the question, please indicate so by adding "Final step:".

The first step is:
            """
        else:
            # For subsequent steps, use the history-aware prompt
            history = ""
            for i, op in enumerate(operation_history, 1):
                history += f"{i}. {op}\n"

            prompt = ""
            prompt += wikitq_natural_language_plan_demo + "\n"
            # prompt += general_natural_language_plan_demo + "\n"
            prompt += f"""
################## Here comes your task!

Based on the current intermediate table and previous steps, write the next step in the plan to transform the current intermediate table.

Your next step should be atomic and straightforward, ensuring it can be easily executed or converted into SQL.
Remember to always add the step number **{i+1}**. before step. If this step provides the final answer to the question, please indicate so by adding "Final step:"

Current intermediate table:
{table2string(current_table)}

Question to answer: {statement}

Original table had {num_rows} rows.

Previous executed steps:
{history}
The next step is:
            """

        # print("Prompt to the model: ", prompt)

        try:
            response = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
            next_step = plan_to_step_list(response[0][0])[0] if response else None
            return next_step
        except Exception as e:
            print('ERR: Cannot generate next step:', str(e))
            return None

else:
    raise ValueError(f"Invalid planning algorithm: {planning_algorithm}")


############################################################################################################
############################################################################################################
############################################################################################################

def tabfact_natural_language_plan_step_to_sql(sample, intermediate_table, action, table_name, statement):
    if len(intermediate_table[0]) > 1:
        existing_cols = " or ".join(f"{item}" for item in intermediate_table[0])
    else:
        existing_cols = f"{intermediate_table[0][0]}"

    prompt = ""
    prompt += tabfact_natural_language_step_to_sql_demo
    prompt += "\n#### Here come to your task!!!\n"

    prompt += f"Given this table:\n"
    prompt += "/*\n" + table2string(intermediate_table) + "\n*/\n"

    data_type = table2df(intermediate_table).dtypes

    prompt += f"\nWrite a SQL command that: {action}\n"

    prompt += "\n### Extra information: \nData types of columns:\n"
    for col, dtype in data_type.items():
        dtype_str = "string" if dtype == "object" else str(dtype)
        prompt += f"- {col}: {dtype_str}\n"

    table_info = get_table_info(sample)
    num_rows = len(table_info["table_text"]) - 1
    prompt += f"The original table has {num_rows} rows.\n"

    prompt += f"\n\n###Constraints for your SQL:\n"

    prompt += f"\n1.{syntax_instr1} If adding new columns, they should be different than columns {existing_cols}"

    prompt += f"\n2. Your SQL command MUST be compatible and executable by python sqlite3 and pandas."
    prompt += f"\n3. If using FROM, the table to be selected MUST be {table_name}."
    prompt += "\n\nSQL is:\n"
    return prompt

if planning_algorithm == 'static':

    def tabfact_generate_natural_language_planning(
            sample,
            debug=False,
            llm=None,
            llm_options=None,
            strategy="top",
    ):
        """
        Generate a natural language plan for the given sample.
        :param sample:
        :param debug:
        :param llm:
        :param llm_options:
        :param strategy:
        :return:
        """
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

        # prompt += general_natural_language_plan_demo + "\n"
        prompt += tabfact_natural_language_plan_demo + "\n"

        prompt += "\n### Here come to your task!\n"
        prompt += f"table caption: {caption}\n"
        prompt += "/*\n" + table2string(table_info["table_text"]) + "\n*/\n"
        prompt += f"This Table has {num_rows} rows.\n"
        prompt += "Statement: " + sample["statement"] + "\n"

        prompt += """
        Let's develop a step-by-step plan to verify if the given Statement is TRUE or FALSE on the given Table!
        You MUST carefully analyze the Statement and comprehend it before writing the plan!
    
        Plan Steps: Each step in your plan should be very atomic and straightforward, ensuring they can be easily executed or converted into SQL.
        You MUST make sure all information (except those mentioned in the table caption) are checked properly in the steps.
    
        Step order: The order of steps is crucial! You must ensure the orders support the correct information retrieval and verification!
        The next step will be executed on the output table of the previous step. The first step will be executed on the given Table.
    
        For comparative or superlative Statement involving "highest", "lowest", "earliest", "latest", "better", "faster", "earlier", etc.,
        you should order the table accordingly before selecting rows. This ensures that the desired comparative or superlative data is correctly retrieved.
    
        Plan:\n
        """

    #     The last step MUST use a CASE statement to return TRUE or FALSE based on the count of rows of the table input to the last step. The count should be devised from the Statement.

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

elif planning_algorithm == 'dynamic':
    def tabfact_generate_natural_language_planning(
            sample,
            current_table,
            operation_history=None,
            debug=False,
            llm=None,
            llm_options=None,
            strategy="top"
    ):
        """
        Generate the next operation dynamically based on current state and history.

        Args:
            sample: The original sample containing statement and table info
            current_table: The current state of the table after previous operations
            operation_history: List of previous operations that were executed
            debug, llm, llm_options, strategy: Same as original function
        """
        if operation_history is None:
            operation_history = []

        # Set up LLM options
        if llm_options is None:
            llm_options = llm.get_model_options()
        llm_options["n"] = 1  # We only need one next step at a time

        table_info = get_table_info(sample)
        caption = sample["table_caption"]
        num_rows = len(table_info["table_text"]) - 1

        # If operation_history is None or empty, generate first step
        if not operation_history:
            prompt = ""
            prompt += tabfact_natural_language_plan_demo + "\n"
            # prompt += general_natural_language_plan_demo + "\n"
            prompt += f"""
################## Here come to your task!

Table caption: {caption}

Table:
/*\n{table2string(current_table)}\n*/

This Table has {num_rows} rows.
Statement: {sample["statement"]}

Let's write the first step to verify if the given Statement is TRUE or FALSE on the given Table!
You MUST carefully analyze the Statement and comprehend it before writing the first step!
You do not need to check the information already mentioned in the table caption.

Your step should be very atomic and straightforward, ensuring it can be easily executed or converted into SQL.

For comparative or superlative Statement involving "highest", "lowest", "earliest", "latest", "better", "faster", "earlier", etc.,
you should order the table accordingly before selecting rows. This ensures that the desired comparative or superlative data is correctly retrieved.

The first step is:\n
                """
        else:
            # For subsequent steps, use the history-aware prompt
            history = ""
            for i, op in enumerate(operation_history, 1):
                history += f"{i}. {op}\n"

            prompt = ""
            prompt += tabfact_natural_language_plan_demo + "\n"
            # prompt += general_natural_language_plan_demo + "\n"
            prompt += f"""
################## Here come to your task!

Based on the below current intermediate table and previous steps, write the next step to be applied to the current 
intermediate table to verify if the Statement is TRUE or FALSE.

You do not need to check the information mentioned in the table caption.

The next step should be atomic and straightforward, ensuring it can be easily executed or converted into SQL.
If the current intermediate table and previous steps are sufficient to make a final verification, write a step using a CASE statement 
to return TRUE or FALSE based on the count of rows in the current table.

Table caption: {caption}
Current intermediate table:
/*\n{table2string(current_table)}\n*/

Statement to verify: {sample["statement"]}

Original table had {num_rows} rows.

Previous executed steps:
{history}

The next step is:\n
                """

        # print("prompt to the model: ", prompt)

        try:
            response = llm.generate_plus_with_score(
                prompt, options=llm_options, end_str="\n\n"
            )
            next_step = plan_to_step_list(response[0][0])[0] if response else None
            return next_step
        except Exception as e:
            print('ERR: Cannot generate next step:', str(e))
            return None
else:
    raise ValueError(f"Invalid planning algorithm: {planning_algorithm}")
