> The novelty of the method is limited. Since the step-by-step execution has been already proposed in CoTable, this work seems a simple extension of CoTable with SQL queries and plan generation. And the final performance is even reduced with the added components.

Thank you for your comment!
While POS shares similarities with CoTable in its step-by-step approach, 
we believe our method introduces key innovations beyond CoTable. POS systematically decomposes 
complex queries into atomic, interpretable sub-steps and SQL-compatible transformations, 
providing transparency that CoTable and other existing methods lack. Unlike traditional 
program-based approaches, which often struggle with unexplainable selections or function 
arguments (see Fig. 1), POS allows each transformation to be fully traceable, making 
the entire reasoning process interpretable.

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

|   Dataset   |   TabFact   |        |         |        | WikiTQ |        |
|:-----------:|:-----------:|:------:|:-------:|:------:|:------:|:------:|
|    Method   | Text-to-SQL | DATER  | CoTable |  POS   | DATER  |  POS   |
| GPT-4o-mini |   55.37%    | 55.43% | 61.36%  | **76.74%** | 64.58% | **71.93%** |
|    GPT-4o   |   55.97%    | 70.95% | 67.34%  | **72.85%** | 73.31% | **74.45%** |
|    GPT-4    |   49.93%    | 57.56% | 60.38%  | **72.08%** | **73.5%**  | 72.38% |

Our findings are:
- POS significantly improves model prediction debugging accuracy compared to other Table QA baselines. 
- On the TabFact dataset, POS achieves a debugging accuracy of 76.74% with GPT-4o-mini, 72.85% with GPT-4o, and 72.08% with GPT-4, outperforming other methods by margins of up to 21%. 
- On WikiTQ, POS reaches the highest accuracy of 74.45 with GPT4-o. 

These results again confirm that POS offers a distinctive interpretability advantage and usefulness compared to existing Table QA models.

References:
- [c] The effectiveness of feature attribution methods and its correlation with automatic evaluation scores, NeurIPS

- [d] HIVE: Evaluating the Human Interpretability of Visual Explanations, ECCV.

- [e] What I Cannot Predict, I Do Not Understand: A Human-Centered Evaluation Framework for Explainability Methods, NeurIPS.

- [f] Debugging Tests for Model Explanations, NeurIPS.

- [g] Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation, ICLR.

> What is the motivation to add highlights in the XAI experiments?

Thank you for this great question! 

Highlights (or attribution maps) are widely recognized as a key method for explaining 
AI decisions to humans across all domains, including images[a], text[b], and time series[c]. 
In these domains, highlights effectively draw users’ attention to the most relevant parts of 
the data, helping them understand how the model arrived at its decisions.

- [a] What i cannot predict, i do not understand: A human-centered evaluation framework for explainability methods, NeurIPS
- [b] Evaluating Explainable AI: Which Algorithmic Explanations Help Users Predict Model Behavior?, ACL
- [c] Explainable AI for Time Series Classification, IEEE Access

For Table QA, there has been limited work visualizing model explanations in an interpretable way. 
To address this gap, we adapted the highlight method from other domains for tabular data 
to help users understand how the model utilizes specific parts (features) of the input table 
to arrive at the final answer. By highlighting relevant rows, columns, or cells in the table, 
we aim to provide a clear visual explanation of the model's reasoning process.


> The XAI comparison is not very convincing. The highlight method is preferable for SQL-based methods such as PoS or Text-to-SQL. However, it is not explicit for other baselines without SQL, such as Dater and CoTable.
Did you try to remove them in the experiments and see the results?

We find this comment very thought-provoking, and it indeed aided us in improving our XAI evaluation. 

We understand that the highlight-based interpretability 
method may naturally align better with SQL-based approaches like POS and Text-to-SQL. 
For non-SQL methods, such as Dater and CoTable, we agree that highlight-based interpretability 
may be less advantageous compared to SQL-based methods.

Following Reviewer `VQhj`'s suggestion, we removed highlights to assess which explanations 
perform best without the potential advantage that highlights may give to methods like 
Text-to-SQL or POS.

We tested explanations with no highlights on three XAI tasks: Preference Ranking, Forward Simulation, and [Model Debugging](https://openreview.net/forum?id=mDV36U4d6u&noteId=3PACyF2oBr) 
(an additional, more standard XAI evaluation). 
We repeat the LLM-judge setups as described in our paper for GPT4o-mini 
and report the data below:

Table: Evaluating Table QA explanations with no highlights (attribution maps).

|     Task    | Preference Ranking (↓) | Forward Simulation (↑) | Model Debugging (↑) |
|:-----------:|:----------------------:|:----------------------:|:-------------------:|
| Text-to-SQL |          3.97          |         65.67%         |        55.37%       |
|    DATER    |          2.64          |         73.86%         |        56.32        |
|   CoTable   |          1.76          |         75.94%         |        64.18        |
|  POS (Ours) |          1.62          |         81.81%         |        75.10%       |

Our findings are:
- Without highlights, `POS still performs best` across all three XAI tasks—Preference Ranking, Forward Simulation, and Model Debugging.
- The removal of highlights does not affect the accuracy/ratings for the explanation methods, suggesting that highlight-based explanations may not be important for interpretability in Table QA. This finding aligns with similar results in other domains, which indicate that highlights often add minimal value in explaining AI decisions [a, b]. This insight could guide future developments in XAI methods for Table QA.


- [a] The effectiveness of feature attribution methods and its correlation with automatic evaluation scores, NeurIPS
- [b] What i cannot predict, i do not understand: A human-centered evaluation framework for explainability methods, NeurIPS

> Since this is an in-context learning method, the performance is greatly influenced by the choice of LLM backbones. The paper only uses gpt-3.5-turbo-16k-0613 which has already been deprecated by OpenAI. I recommend the authors choose more variety of models and use newer models. This would make the results more reliable and reproducible.

Thank you for the suggestion to test POS on the newer LLM backbones! 
The reason we picked gpt-3.5-turbo-16k-0613 is because this LLM has 
been widely used by a long line of works (CoTable, Binder, DATER, 
TableSQLify) in Table QA. Using gpt-3.5-turbo-16k-0613 makes sure 
we have a fair comparison between POS and baselines.
Given the deprecation of GPT3-5, we tested POS on GPT4o-mini and 
report the numbers below:

Table: Table QA accuracy of POS on TabFact and WikiTQ with GPT3-5 and GPT4o-mini

|            |    TabFact    |        |     WikiTQ    |        |
|:----------:|:-------------:|:------:|:-------------:|:------:|
|   Method   | End-to-end QA |   POS  | End-to-end QA |   POS  |
|   GPT3-5   |     70.45%    | 78.31% |     51.84%    | 54.80% |
| GPT4o-mini |     71.17%    | 83.45% |     49.24%    | 54.95% |

We plan to add GPT4o and GPT4-turbo in the next version of the paper.

> The authors argue that it is better for interpretability to merely depend on SQL to process the table and answer the question. However, the necessity of this constraint is still questionable for the table qa in practical scenarios. The tables are of various formats, and the answer usually cannot be produced by a SQL query. Such limitation may explain the lower performance of PoS compared with many other baselines.
Are there any cases where the answer cannot be generated by SQL queries?

Thank you for this great comment!

Yes, there are cases where the answer cannot be generated by SQL queries alone, particularly those involving long-form generation—such as text summarization tasks in datasets like QTSumm [a]—often relying on model “creativity” to produce answers. For such datasets, relying solely on SQL is not optimal. We argue that combining the strengths of SQL for structured data handling with the creative reasoning capabilities of LLMs offer a more powerful approach. 

We recognize that tables vary significantly in format, which can sometimes make SQL-based processing challenging [b]. However, by preprocessing samples into a SQL-compatible format (i.e., making them "SQLifiable"), we can achieve a significantly better interpretable decision-making process. For instance, the NormTab paper [c] demonstrates effective data cleaning techniques to prepare tables for structured processing, showing that, after cleaning, applying naive methods like Text-to-SQL can boost accuracy on datasets like TabFact and WikiTQ by 5-10 points. This shows that POS can not only provide great interpretability but also accurate answers.

We also want to note that our primary focus in this work is on interpretability, which is why we emphasize SQL-based methods. However, for long-form generation, hybrid explanation methods (e.g. SQL + natural-language explanations) is more promising and we leave this exploration for future work. We hope POS lays the groundwork for interpretability research in Table QA.

- [a] QTSumm: Query-Focused Summarization over Tabular Data, EMNLP
- [b] On the potential of lexico-logical alignments for semantic parsing to sql queries, EMNLP
- [c] NormTab: Improving Symbolic Reasoning in LLMs Through Tabular Data Normalization, EMNLP

> The paper's presentation requires improvement, as some tables extend beyond the page margins