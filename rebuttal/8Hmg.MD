> Limited Novelty: While the paper addresses an important problem in 
> Table QA, the core ideas, such as breaking down queries into atomic 
> steps and using SQL transformations for interpretability, are established 
> in other domains. This reduces the method's originality, as it largely 
> adapts existing decomposition and programmatic interpretability 
> approaches rather than introducing fundamentally new techniques 
> specific to Table QA.

Thank you for this insightful comment!

Reviewer `8Hmg` said that:
`the core ideas, such as breaking down queries into atomic steps and using SQL transformations for interpretability, are established in other domains.`

While it’s true that step-by-step planning is the main idea of almost all the LLM planning papers [a], 
to the best of our knowledge, there is no such work in literature that do `breaking down queries into atomic 
steps and using SQL transformations explicitly for interpretability`. 
If there are such papers, we would be grateful if the reviewer could point them out so that we can cite and give proper credit.

We also acknowledge that our method leverages concepts from existing decomposition and programmatic interpretability approaches; 
however, we believe that POS introduces a novel application of these principles specifically tailored to Table QA. 

Besides, we would like to emphasize that our goal is not to introduce a new Table QA method that 
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
- [a] Understanding the planning of LLM agents: A survey. 2024.
- [b] Watch Your Steps: Observable and Modular Chains of Thought. 2024
- [c] The effectiveness of feature attribution methods and its correlation with automatic evaluation scores, NeurIPS
- [d] HIVE: Evaluating the Human Interpretability of Visual Explanations, ECCV.
- [e] What I Cannot Predict, I Do Not Understand: A Human-Centered Evaluation Framework for Explainability Methods, NeurIPS.
- [f] Debugging Tests for Model Explanations, NeurIPS.
- [g] Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation, ICLR.

We sincerely thank the Reviewer `8Hmg` once again for the insightful comments and are more than willing to discuss further.

> Limited Effectiveness and Scalability: The performance improvements with 
> POS are incremental, indicating only a modest boost in interpretability 
> and accuracy over baseline methods. 

In this comment, Reviewer `8Hmg` mentioned that:
`The performance improvements with POS are incremental, indicating only a modest boost in interpretability and accuracy over baseline methods.`
However, in the Strength 2nd, the Reviewer mentioned:
`It includes a comprehensive evaluation, using both human and LLM judges to assess interpretability and predictive accuracy, showcasing POS’s advantages in clarity, coherence, and overall effectiveness compared to existing methods.`

We feel that there is mixed feedback on the interpretability of POS.
As demonstrated in all 3 XAI tasks (Forward Simulation, Preference Ranking, and Model Prediction Debugging), POS consistently outperforms existing state-of-the-art Table QA methods in terms of interpretability and effectiveness.
Then, we do not really get the concern about `modest boost in interpretability`.

> Additionally, the approach relies 
> on SQL-based transformations, which may restrict its applicability in 
> more dynamic or complex data environments where SQL alone may be 
> insufficient. As a result, the method lacks clear potential for further 
> application in other QA scenarios or for handling more complex reasoning
> tasks, limiting its scalability and broader impact.

Regarding the scalability concern, we recognize that tables vary significantly in format, 
which can sometimes make SQL-based processing challenging [1]. 
However, by preprocessing tables into a SQL-compatible format (i.e., making them "SQLifiable"), 
we can achieve significantly better interpretable Table QA. 
For instance, the NormTab paper [2] demonstrates effective data cleaning techniques to 
prepare tables for SQL processing, showing that, after cleaning, applying naive methods 
like Text-to-SQL can boost accuracy on datasets like TabFact and WikiTQ by 5-10 points. 
This shows that POS can not only provide great interpretability but also accurate answers.

We agree that there are cases where answers cannot be generated by SQL queries alone, particularly for tasks 
requiring long-form generation, such as text summarization tasks in datasets like QTSumm [3], which often rely on model 
“creativity” to produce answers. For such datasets, relying solely on SQL is not ideal. We argue that combining the structured 
data handling strengths of SQL with the creative reasoning capabilities of LLMs offers a more powerful approach.

Finally, we want to reiterate that our primary focus in this work is on interpretability, which is why we 
emphasize SQL-based methods. For tasks like long-form generation, hybrid explanation methods (e.g., SQL + natural-language 
explanations) may be more suitable, and we leave this exploration for future work. We hope that POS serves as a foundation 
for further interpretability research in Table QA.

References:
- [1] On the potential of lexico-logical alignments for semantic parsing to sql queries.
- [2] NormTab: Improving Symbolic Reasoning in LLMs Through Tabular Data Normalization.
- [3] QTSumm: Query-Focused Summarization over Tabular Data. 