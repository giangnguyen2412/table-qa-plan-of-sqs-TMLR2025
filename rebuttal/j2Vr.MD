> 1. The authors report that 9.8% of samples on TabFact and 27.8% on WikiTQ could not be fully processed using POS and thus defaulted to end-to-end QA methods. Even on relatively simple Table QA datasets like TabFact and WikiTQ, these rates are notably high, raising concerns about POS’s scalability to more complex datasets, such as TabMWP. If the unprocessable rate rises significantly with more complex datasets, it raises the concern that POS may only improve interpretability with a sacrifice of precision provided in pure program-based methods. The authors do not provide enough analysis regarding this matter, such as a comparison of unprocessable rates between POS and other program-based models and the unprocessable rates on more complex table-QA datasets.


Thank you for the constructive feedback! We agree with Reviewer `j2Vr’s` comment that the high rate of unprocessable samples does affect the utility of POS, especially when scaled to more complex datasets.

Encouraged by this feedback, we delved into all cases where samples were unprocessable by POS (9.8% on TabFact and 27.8% on WikiTQ) and identified that **one-time planning** (generating a complete plan of steps at once in the beginning) is the bottleneck. Take this query as an example:

**Query**: True or False? "no games were played in **december**."

Table caption: final games in mlb

| game_id |   game_date  | score | attendance | team_name |
|:-------:|:------------:|:-----:|:----------:|:---------:|
|    1    |  5 nov 2011  |   3   |    2000    |  falcons  |
|    2    |  12 nov 2011 |   4   |    1500    |   hawks   |
|    3    |  21 oct 2111 |   2   |    1800    |   eagles  |
|    4    | 30 sept 2011 |   1   |    2200    |   bears   |
|    5    |  20 nov 2011 |   3   |    2100    |  wildcats |

**One-time** plan of POS:

1. Extract the month from the **date** column then add a new column.
2. Select rows where **month = 12**.
3. Use a **CASE** statement to return **TRUE** if the number of rows is **0**, otherwise **FALSE**.

In the example above, the NL Planner generated Step 2 without seeing the output table of Step 1, which added a column with month names as text (e.g., "dec") instead of numeric values (e.g., "12"). 
Additionally, there is no guarantee that the new column from Step 1 is named "month," potentially causing Step 2 to reference a non-existent column.
We found `198` such cases in TabFact and `1207` in WikiTQ, where the one-time planning approach makes Table QA queries unprocessable.

In one-time planning (generating a complete plan of steps at once in the beginning), the NL Planner assumes that previous transformations have succeeded and produced the expected output. If any step fails (e.g., due to missing columns or data formatting issues), the process halts, leading to an unprocessable sample.

We solved this issue by simply prompting the NL Planner to generate one step at a time (instead of generating a complete plan before transforming the table), with the input of planner being the previous steps and the current intermediate table. 
We call this step-by-step planning. As shown below, this `significantly boosted the accuracy for both TabFact and WikiTQ` and `mitigated the unprocessable problem` that `Reviewer j2Vr` raised.

Table: Table QA accuracy (&uarr;) on TabFact and WikiTQ datasets using step-by-step planning

| Method                    | TabFact         | WikiTQ          |
|---------------------------|-----------------|-----------------|
| End-to-end QA             | 71.17%          | 49.24%          |
| POS one-time planning     | 77.22%          | 48.90%          |
| POS step-by-step planning | 83.45% (+6.23%) | 54.95% (+6.05%) |

Table: Unprocessable rates (&darr;) on TabFact and WikiTQ datasets using step-by-step planning. 

| Method                    | TabFact       | WikiTQ         |
|---------------------------|---------------|----------------|
| POS one-time planning     | 10.56%        | 22.63%         |
| POS step-by-step planning | 3.16% (-7.4%) | 13.58 (-9.05%) |

Using GPT4o-mini as the LLM backbone, we found that POS is able to process the vast majority 
of examples using SQLs only, reaching up to about `97%` on TabFact and `86%` on WikiTQ!
It is important to note that WikiTQ contains considerable data noise [a], thus achieving this processable rate using SQLs alone is non-trivial. 

We appreciate the Reviewer’s insights, which guided us toward a more robust and scalable solution for handling the problem.


Regarding the scalability of POS to more complex datasets like TabMWP [b]. After looking at the dataset, we acknowledge that TabMWP indeed presents additional challenges due to its complexity and the diversity of reasoning requirements. 
We will ensure that our paper includes a discussion on the potential and limitations of scaling POS to handle more complex problems, such as TabMWP.

- [a] On the potential of lexico-logical alignments for semantic parsing to sql queries, EMNLP2020.

- [b] Dynamic Prompt Learning via Policy Gradient for Semi-structured Mathematical Reasoning, ICLR2023.

> 2. The technical contribution of POS is limited, since the whole framework primarily involves prompt engineering. Essentially, compared to traditional program-based methods, POS simply adds an additional layer of prompts to generate natural language “plans” that function as pseudo-comments for SQL statements. This does not introduce substantial technical contribution beyond traditional program-based methods.

Thank you for your feedback! While POS does indeed utilize prompt engineering, its design 
extends beyond simple prompt layering. The key innovation lies in its systematic decomposition 
of complex queries into atomic, **interpretable** sub-steps and table transformations—a feature not found in 
existing approaches. Unlike traditional program-based methods, which often struggle with unexplainable selections or function arguments (Fig. 1), 
POS offers a fully transparent, step-by-step transformation process.

We would like to emphasize that our goal is not to introduce a new Table QA method that 
maximizes accuracy but rather to address critical interpretability gaps in current Table QA 
methods. Interpretability in this domain has been largely overlooked, and POS aims 
to fill that gap.

To further support the interpretability frontier of POS, we conducted an additional evaluation where 
explanation methods (Text-to-SQL, DATER, CoTable, and POS) help us identify whether the Table QA model 
is correct (model prediction debugging[c,d,e,f]). Model prediction debugging is the mainstream and established task in XAI and has 
many real-world applications (e.g. healthcare[g]).

Using both the TabFact and WikiTQ datasets, we evaluated the following question: 
Given the explanations, can users identify if the Table QA model is correct or wrong? 
We leverage LLM-as-a-Judge as we did in Forward Simulation and Preference Ranking for this setup.

Here is our prompt to the LLM judges:
```
The Table Question Answering (Table QA) model is working on a tabular dataset, answering questions based on a given table.

You are given an HTML file containing a Question, Input Table, Prediction, and an Explanation clarifying the Prediction.

Your task is to carefully analyze the explanation and determine whether the Prediction is correct or not.

Explanation Method: [Text2SQL/DATER/CoTable/POS]
Answer with ‘Correct’ or ‘Wrong’ only.

You MUST ignore the order of the options and answer based on the correctness of the Prediction!
```

We report the result of the evaluation below:

Table: Model prediction debugging accuracy (&uarr;) on TabFact and WikiTQ with LLM judges using different Table QA explanations. 

<table style="text-align: center; width: 100%;">
  <tr>
    <th rowspan="2">Dataset</th>
    <th colspan="4">TabFact</th>
    <th colspan="2">WikiTQ</th>
  </tr>
  <tr>
    <th>Text-to-SQL</th>
    <th>DATER</th>
    <th>CoTable</th>
    <th>POS</th>
    <th>DATER</th>
    <th>POS</th>
  </tr>
  <tr>
    <td>GPT-4o-mini</td>
    <td>55.37%</td>
    <td>55.43%</td>
    <td>61.36%</td>
    <td><b>76.74%</b></td>
    <td>64.58%</td>
    <td><b>71.93%</b></td>
  </tr>
  <tr>
    <td>GPT-4o</td>
    <td>55.97%</td>
    <td>70.95%</td>
    <td>67.34%</td>
    <td><b>72.85%</b></td>
    <td>73.31%</td>
    <td><b>74.45%</b></td>
  </tr>
  <tr>
    <td>GPT-4</td>
    <td>49.93%</td>
    <td>57.56%</td>
    <td>60.38%</td>
    <td><b>72.08%</b></td>
    <td><b>73.5%</b></td>
    <td>72.38%</td>
  </tr>
</table>

We find that POS significantly improves model prediction debugging accuracy compared to other Table QA baselines. 
For example, on the TabFact dataset, POS achieves a debugging accuracy of 76.74% with GPT-4o-mini, 72.85% with GPT-4o, and 72.08% with GPT-4, outperforming other methods by margins of up to 21%. 
Similarly, on WikiTQ, POS reaches the highest accuracy of 74.45 with GPT4-o. These results again confirm that POS offers a distinctive interpretability advantage and usefulness compared to existing Table QA models.

- [c] The effectiveness of feature attribution methods and its correlation with automatic evaluation scores, NeurIPS

- [d] HIVE: Evaluating the Human Interpretability of Visual Explanations, ECCV.

- [e] What I Cannot Predict, I Do Not Understand: A Human-Centered Evaluation Framework for Explainability Methods, NeurIPS.

- [f] Debugging Tests for Model Explanations, NeurIPS.

- [g] Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation, ICLR.

> 3. The NL Atomic Planner in POS depends on in-context planning examples that are specifically tailored to each dataset. This raises questions about its adaptability to a variety of reasoning types and Table QA problems. It remains unclear whether the current prompting schema can generalize effectively across different Table QA tasks.

Thank you for the great comment! 

Our in-context planning examples were specifically crafted to each dataset, 
and it would be insightful to study the generalizability of the current prompting 
schema. To shed light on this question, we modify our in-context planning 
examples so that it does not contain any dataset-specific information. 
Rather, the in-context examples are rewritten `to be general` in the format of general Table QA problems (e.g. input to NL Planner is Query/Table and output is Plan).

The general in-context planning examples now look like this:

```markdown
We are working with a tabular dataset.
Your task is to develop a step-by-step plan to verify if a given statement is TRUE or FALSE or to find the correct answer based on a given table.

### Table: 
/* 
col : id | name | score 
row 1 : 1 | alice | 85 
row 2 : 2 | bob | 90 
row 3 : 3 | charlie | 75 
*/ 
Query: what is the score of alice? 
Plan: 
1. Select rows where the 'name' is 'alice'. 
2. Select the 'score' column.
```

We run POS again using these `general` in-context examples and use them for both datasets.
We find that using general in-context examples `only slightly decreased the accuracy` on both datasets 
compared to using tailored/specific examples. See Table below:

Table: Table QA accuracy (&uarr;) on TabFact and WikiTQ datasets using general in-context examples for planning.

|                             Method                              | TabFact | WikiTQ |
|:---------------------------------------------------------------:|:-------:|:------:|
|                          End-to-end QA                          |  71.17% | 49.24% |
|         POS with 5 general in-context planning examples         |  81.08% | 50.92% |
|       POS 30 (full) general in-context planning examples        |  81.92% | 52.00% |
|   POS 30 (full) dataset-specific in-context planning examples   |  83.45% | 54.95% |

Yet, the accuracy of POS remains competitive, and it shows the minimal necessity of dataset-specific in-context examples.
We also observe that the general in-context examples yield very low unprocessable rates. 
Here the rate on TabFact goes from 3.16% → 3.06% and on WikiTQ goes from 13.58% → 14.48%.

Finally, it is also worth noting that reliance on tailored, dataset-specific examples is common across other methods, such as CoTable. 
Typically, general prompts (e.g., Meta-prompting[1]) yield slightly lower accuracy than dataset-specific prompts but improve generalizability, as confirmed in our Table above as well.

- [1] Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding

> 4. Further experimentation across a broader range of datasets (ideally 5–6) would be needed to demonstrate POS’s generalizability and robustness.

Thank you for this suggestion! We would like to note that in existing works, including our main baselines (CoTable, Binder, Dater, and TableSQLify), TabFact and WikiTQ are also the primary datasets for evaluation. These datasets provide a comprehensive test of Table QA interpretability and accuracy.

Due to limited time and API credit budget, we are currently unable to extend POS testing to additional datasets as requested. We kindly ask the reviewer for understanding and consideration of our evaluation on TabFact and WikiTQ.

The cost of running POS is particularly high due to the nature of these datasets. Since TabFact and WikiTQ involve large input tables and require in-context examples within the prompt, each request consumes a significant number of tokens.
For example, testing TabFact and WikiTQ with step-by-step planning in Question 1 cost over $600, due to the extensive context window requirements of these datasets. In comparison, datasets like GSM8K[2] incur much lower costs, as they require fewer tokens per prompt. Given these considerations, we prioritized TabFact and WikiTQ to provide a robust and feasible evaluation within our resource constraints.

- [2] Training Verifiers to Solve Math Word Problems