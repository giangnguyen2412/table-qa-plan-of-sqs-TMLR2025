# Interpretable LLM-based Table Question Answering | [pdf](https://arxiv.org/abs/2412.12386)

## Abstract

> Interpretability for Table Question Answering (Table QA) is critical, particularly in high-stakes industries like finance or healthcare.
Although recent approaches using Large Language Models (LLMs) have significantly improved Table QA performance, their explanations for how the answers are generated are ambiguous.
To fill this gap, we introduce Plan-of-SQLs (\POS), an interpretable approach to Table QA that answers an input query solely with SQL executions.
Through qualitative and quantitative evaluations with human and LLM judges, we show that \POS is most preferred among explanation methods, helps human users understand model decision boundaries, and facilitates model success and error identification.
Furthermore, when evaluated on standard benchmarks (TabFact, WikiTQ, and FetaQA), \POS achieves accuracy that is competitive with or superior to existing methods, while also offering greater efficiency—requiring significantly fewer LLM calls and database queries—and robust performance on large tables.
Finally, we observe high agreement between LLM judges and human users when making decisions based on the same explanations, suggesting that LLMs could serve as effective proxies for humans in evaluating AI explanations.

## Setup Environment

```shell
# 1. Create a new conda environment with Python 3.10.13
conda create -n tabular-llms-openai python=3.10.13 -y

# 2. Activate the environment
conda activate tabular-llms-openai

# 3. Install required packages
pip install openai==0.27.4
pip install azure-identity==1.12.0
pip install azure-cli==2.41.0
pip install azure-mgmt-cognitiveservices

# 4. Authenticate Azure (you need to sign in)
az login

# 5. Install any project-specific dependencies
python install.py
```

## Running Interpretable Table QA yourself

[interactive interface](https://huggingface.co/spaces/luulinh90s/Interactive-Tabular-XAI)

## TabFact

Step 1: Extract data
```shell
unzip data.zip
```

Step 2: Run evaluation script

```
python run_tabfact_pos.py --use_subset True --load_dataset True

```

## WikiTQ

Step 1: Clone Dater repo. Dater has the official evaluation script and data for WikiTQ.

```
git clone https://github.com/AlibabaResearch/DAMO-ConvAI.git
cd dater/
```

Step 2: Download preprocessed data with this [guidelines](https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/dater#download) to get `dater_data.tar.gz`

Step 3: Run script

```
cd dater/
mv saved/ code/
python run_wikitq_pos.py --load_dataset True --use_subset True
```

# Improved Planning Algorithm
> We notice that many errors in POS are due to the planning stage rather than Step-to-SQL process.
The Planner often misses condition checks in atomic steps.
An interesting (and inherently unavoidable) error due to the exact-matching nature of SQL can also be found in our paper.
> Based on this observation, we implement an improved planning algorithm in which **only one step is generated at a time**, rather than generating all steps upfront. 
This approach encourages the LLM to think one step at a time and reduces the complexity of the planning task.
The input of NL Planner is the previous steps and the current intermediate table.

You can try both methods by modifying the `self.planning_algorithm` in helper.py.
We have seen `dynamic` (aka. planning one step at a time) consistently improves POS accuracy on datasets with different LLM backbone models.

# Performance vs. Table Size Analysis

Run the scripts run_table_size_analysis.py and run_table_size_analysis_wikitq.py to get the performance of the models with different table sizes.

```shell
python run_table_size_analysis.py
```

the input of this script is a json file containing the result of the model on the test set.
An example entry looks like:

```json
"test-1385": {
        "test-1385": {
            "input": {
                "statement": "all of the constituency has 2nd snp 's place 2003",
                "label": 1,
                "table_caption": "scottish parliament general election , 2007",
                "table_text": [
                    [
                        "rank",
                        "constituency",
                        "winning_party_2003",
                        "swing_to_gain",
                        "snp__s_place_2003",
                        "result"
                    ],
                    [
                        "1",
                        "galloway & upper nithsdale",
                        "conservative",
                        "0.17",
                        "2nd",
                        "con hold"
                    ], ...
             ],
                "table_id": "2-11105214-2.html.csv",
                "id": "test-1385",
                "chain": [],
                "cleaned_statement": "all of the constituency have 2nd snp 's place 2003",
                "table_token_count": 101
            },
            "id": "test-1385",
            "answer": "TRUE",
            "answer_plans": {
                "dynamic": 1
            },
            "groundtruth": "TRUE",
            "fallback_LLM": false,
            "is_sql_executable": true
        }
    },
```

## Visualizing Table QA explanations
This will visualize explanations and the corresponding `json` file that contains the metadata for the explanations

```
cd visualization/script
sh vis_POS.sh
```

## LLM-as-a-Judge for Table QA explanations

**Note**: Make sure you have the Visualizations before going to this evaluation 

Step 1: Extract the similar examples across XAI methods

```
cd xai_study/llm-judge/scripts
sh prepare_samples.sh
```

Experiment 1: Preference - `Which explanation provides a clearer and more accurate reasoning process?`

```
sh 
```

Experiment 2: Forward Simulation - `Given an explanation, what is the model prediction?'`

```
sh 
```

Experiment 3: Decision-making - `Given an explanation, is the model prediction correct? Answer with 'Yes' or 'No'`

```
sh 
```

## Human evaluation for Table QA explanations

**Note**: To update the interface, please change `visualizations` and the `json` files that contain metadata for explanations accordingly.

```
cd xai_study/flask_experiment
python app.py
```


