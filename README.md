<!-- ----------------------------------------------------------- -->
<!--  Interpretable LLM-based Table Question Answering (POS)     -->
<!-- ----------------------------------------------------------- -->

<h1 align="center">
  Interpretable LLM-based Table Question Answering
  <br/>
  <sub></sub>
</h1>

<div align="center">    
  <p style="font-size: 20px;">by 
    <a href="https://giangnguyen2412.github.io/">Giang Nguyen</a><sup>1</sup>,
    <a href="https://ivanbrugere.github.io/">Ivan Brugere</a><sup>2</sup>, 
              <a href="https://scholar.google.com/citations?user=BoV4KYAAAAAJ&hl=en&oi=ao">Shubham Sharma</a><sup>2</sup>, 
              <a href="https://sanjaykariyappa.github.io/">Sanjay Kariyappa</a><sup>3</sup>, 
    <a href="https://anhnguyen.me/research/">Anh Totti Nguyen</a><sup>2*</sup>
        <a href="https://www-sop.inria.fr/members/Freddy.Lecue/">Freddy Lecue</a><sup>1*</sup>,
  </p>
  <p>
    <sup>*</sup>Equal advising<br>
    <sup>1</sup>Auburn University, <sup>2</sup>J.P.Morgan AI Research, <sup>3</sup>NVIDIA
  </p>
  
  <p style="font-size: 18px; font-weight: bold;">
    Transactions on Machine Learning Research
  </p>

[![arXiv](https://img.shields.io/badge/arXiv-2505.18545-b31b1b.svg)](https://arxiv.org/abs/2412.12386)
[![Interface](https://img.shields.io/badge/🤗%20Hugging%20Face-Demo-yellow)](https://huggingface.co/spaces/luulinh90s/Interactive-Tabular-XAI)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
</div>

---

## 📜 Abstract
>Interpretability in Table Question Answering (Table QA) is critical, especially in high-stakes domains like finance and healthcare. While recent Table QA approaches based on Large Language Models (LLMs) achieve high accuracy, they often produce ambiguous explanations of how answers are derived. We propose Plan-of-SQLs (POS), a new Table QA method that makes the model's decision-making process interpretable. POS decomposes a question into a sequence of atomic steps, each directly translated into an executable SQL command on the table, thereby ensuring that every intermediate result is transparent. Through extensive experiments, we show that: First, POS generates the highest-quality explanations among compared methods, which markedly improves the users' ability to simulate and verify the model’s decisions. Second, when evaluated on standard Table QA benchmarks (TabFact, WikiTQ, and FeTaQA), POS achieves QA accuracy that is competitive to existing methods, while also offering greater efficiency—requiring significantly fewer LLM calls and table database queries (up to 25x fewer)—and more robust performance on large-sized tables. Finally, we observe high agreement (up to 90.59% in forward simulation) between LLMs and human users when making decisions based on the same explanations, suggesting that LLMs could serve as an effective proxy for humans in evaluating Table QA explanations.

---

## 🗺️ Table of Contents
1. [Environment Setup](#environment-setup)
2. [Datasets & Benchmarks](#datasets--benchmarks)
   * [TabFact](#tabfact)
   * [WikiTQ](#wikitq)
3. [Improved Planning Algorithm](#improved-planning-algorithm)
4. [Performance vs. Table Size](#performance-vs-table-size)
5. [Visualization & Evaluation](#visualization--evaluation)
   * [LLM-as-a-Judge](#llm-as-a-judge)
   * [Human Evaluation Interfaces](#human-evaluation-interfaces)
6. [Interactive Demo](#interactive-demo)
7. [Citation](#citation)

---

## Environment Setup

```bash
# 1️⃣  Create and activate Conda env
conda create -n tabular-llms-openai python=3.10.13 -y
conda activate tabular-llms-openai

# 2️⃣  Install core dependencies
pip install openai==0.27.4 azure-identity==1.12.0 azure-cli==2.41.0 azure-mgmt-cognitiveservices

# 3️⃣  Authenticate with Azure (browser sign-in)
az login

# 4️⃣  Project-specific dependencies
python install.py
```

---

## Datasets & Benchmarks

### TabFact
```bash
# 🔍 Step 1: Extract data
unzip data.zip

# ▶️ Step 2: Run evaluation
python run_tabfact_pos.py --use_subset True --load_dataset True
```

### WikiTQ
```bash
# 🔍 Step 1: Clone Dater repo (official evaluation code)
git clone https://github.com/AlibabaResearch/DAMO-ConvAI.git
cd DAMO-ConvAI/dater

# 🔍 Step 2: Download pre-processed data (see repo instructions) to obtain dater_data.tar.gz

# ▶️ Step 3: Run POS on WikiTQ
mv saved/ code/
python run_wikitq_pos.py --load_dataset True --use_subset True
```

---

## Improved Planning Algorithm
<details>
<summary>Why & how (click to expand)</summary>

We observed that many POS errors stem from the **planning stage**.  
The original planner generates *all* steps up‑front, often missing crucial conditions.  
Our **dynamic planner** instead generates **one atomic step at a time**, conditioned on the current intermediate table—leading to consistent accuracy gains across LLM backbones.

**Try it** by toggling `self.planning_algorithm` in `helper.py` between `static` and `dynamic`.
</details>

---

## Performance vs. Table Size
Generate the table-size analysis plots:

```bash
python run_table_size_analysis.py           # TabFact
python run_table_size_analysis_wikitq.py    # WikiTQ
```

*Input*: a JSON results file (see example below).

```jsonc
{
  "test-1385": {
    "input": { ... },
    "answer": "TRUE",
    "answer_plans": { "dynamic": 1 },
    "groundtruth": "TRUE",
    "table_token_count": 101
  },
  ...
}
```

---

## Visualization & Evaluation

### Visualizing Table QA Explanations
```bash
cd visualization/script
sh vis_POS.sh
```

### LLM-as-a-Judge
<details>
<summary>Prepare & run the three automatic XAI studies</summary>

```bash
# 1. Extract similar examples across XAI methods
cd xai_study/llm-judge/scripts
sh prepare_samples.sh

# 2. Experiments
# 2a. Preference (clearer reasoning?)
sh run_preference.sh     

# 2b. Forward Simulation (given explanation, predict model answer)
sh run_forward_sim.sh   

# 2c. Model Prediction Debugging (is prediction correct?)
sh run_debugging.sh      
```
</details>

### Human Evaluation Interfaces
* **Preference Ranking** – <https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Preference-Ranking>  
* **Forward Simulation** – <https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Forward-Simulation>  
* **Model Prediction Debugging** – <https://huggingface.co/spaces/luulinh90s/Tabular-LLM-Study-Debugging>

---

## Interactive Demo
Explore POS explanations live: **[Interactive Tabular XAI](https://huggingface.co/spaces/luulinh90s/Interactive-Tabular-XAI)**.

---

## Citation
```bibtex
@article{nguyen2024interpretable,
  title={Interpretable llm-based table question answering},
  author={Nguyen, Giang and Brugere, Ivan and Sharma, Shubham and Kariyappa, Sanjay and Nguyen, Anh Totti and Lecue, Freddy},
  journal={arXiv preprint arXiv:2412.12386},
  year={2024}
}
```

---

<p align="center">♥  Please reach out to nguyengiangbkhn@gmail.com for any inquiries  ♥</p>
