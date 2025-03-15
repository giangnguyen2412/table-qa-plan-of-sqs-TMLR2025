# Trustworthy Table LLMs with Plan of SQLs


## Environment

```shell
pip install virtualenv
virtualenv venvTable4LLM/ --python=python3.8
source venvTable4LLM/bin/activate
pip install openai=="0.27.4"
pip install azure-identity=="1.12.0"
pip install azure-cli=="2.41.0"
pip install azure-mgmt-cognitiveservices
az login # To authenticate OpenAI API usage
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

## Visualizations
This will visualize explanations and the corresponding `json` file that contains the metadata for the explanations

```
cd visualization/script
sh vis_COT_POS.sh
```

## LLM-as-a-Judge for XAI

**Note**: Make sure you have the Visualizations before going to this evaluation 

Step 1: Extract the similar examples accross XAI methods

```
cd xai_study/llm-judge/scripts
sh prepare_samples.sh
```

Experiment 1: Preference - `Which explanation provides a clearer and more accurate reasoning process?`

```
sh run_preference_exp.sh
```

Experiment 2: Decision-making - `Given an explanation, is the prediction correct? Answer with 'Yes' or 'No'`

```
sh run_desc_making_exp.sh
```

## Human evaluation for XAI

**Note**: To update the interface, please change `visualizations` and the `json` files that contain metadata for explanations accordingly.

```
cd xai_study/flask_experiment
python app.py
```


