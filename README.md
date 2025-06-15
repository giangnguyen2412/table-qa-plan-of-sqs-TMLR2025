# Interpretable LLM-based Table Question Answering | [pdf](https://arxiv.org/abs/2412.12386)

## Accepted at Transactions on Machine Learning Research 2025; [Review](https://openreview.net/forum?id=2eTsZBoU2W)

## Abstract

> Interpretability in Table Question Answering (Table QA) is critical, especially in high-stakes domains like finance and healthcare. While recent Table QA approaches based on Large Language Models (LLMs) achieve high accuracy, they often produce ambiguous explanations of how answers are derived. We propose Plan-of-SQLs (POS), a new Table QA method that makes the model's decision-making process interpretable. POS decomposes a question into a sequence of atomic steps, each directly translated into an executable SQL command on the table, thereby ensuring that every intermediate result is transparent. Through extensive experiments, we show that: First, POS generates the highest-quality explanations among compared methods, which markedly improves the users' ability to simulate and verify the model’s decisions. Second, when evaluated on standard Table QA benchmarks (TabFact, WikiTQ, and FeTaQA), POS achieves QA accuracy that is competitive to existing methods, while also offering greater efficiency—requiring significantly fewer LLM calls and table database queries (up to 25x fewer)—and more robust performance on large-sized tables. Finally, we observe high agreement (up to 90.59% in forward simulation) between LLMs and human users when making decisions based on the same explanations, suggesting that LLMs could serve as an effective proxy for humans in evaluating Table QA explanations.

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

Experiment 3: Model Prediction Debugging - `Given an explanation, is the model prediction correct? Answer with 'Yes' or 'No'`

```
sh 
```

## Human evaluation for Table QA explanations

We developed three interactive interfaces corresponding to the three XAI tasks explored in our paper:

- **Preference Ranking**: [Tabular-LLM-Study-Preference-Ranking](https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Preference-Ranking)
- **Forward Simulation**: [Tabular-LLM-Study-Forward-Simulation](https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Forward-Simulation)
- **Model Prediction Debugging**: [Tabular-LLM-Study-Debugging](https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Debugging)

## An interactive interface for Table QA explanations

We developed an interactive interface to visualize explanations for Table Question Answering (Table QA).

[Interactive Tabular XAI](https://huggingface.co/spaces/luulinh90s/Interactive-Tabular-XAI)

## Consider citing our work

```
@article{nguyen2024interpretable,
  title={Interpretable llm-based table question answering},
  author={Nguyen, Giang and Brugere, Ivan and Sharma, Shubham and Kariyappa, Sanjay and Nguyen, Anh Totti and Lecue, Freddy},
  journal={arXiv preprint arXiv:2412.12386},
  year={2024}
}
```

