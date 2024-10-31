# Copyright 2024 The Chain-of-Table authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import openai
# from openai import OpenAI # OLD FREDDY
import time
import numpy as np
import tiktoken

# import openai 
# from azure.identity import AzureCliCredential

class ChatGPT:
    def __init__(self, model_name, key):
        self.model_name = model_name
        self.key = key

    def get_model_options(
        self,
        temperature=0,
        per_example_max_decode_steps=150,
        per_example_top_p=1,
        n_sample=1,
    ):
        return dict(
            temperature=temperature,
            n=n_sample,
            top_p=per_example_top_p,
            max_tokens=per_example_max_decode_steps,
        )

    # Function to truncate the head of the prompt
    def truncate_prompt_head_exact(prompt, max_tokens):
        tokens = openai.Encoding.encode(prompt)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[-max_tokens:]
        else:
            truncated_tokens = tokens
        return openai.Encoding.decode(truncated_tokens)

    def truncate_prompt(prompt, max_tokens):
        # Truncate the prompt to fit within the maximum token limit
        tokens = prompt.split()
        truncated_tokens = tokens[:max_tokens]
        return ' '.join(truncated_tokens)

    def truncate_prompt_head(prompt, max_tokens):
        # Truncate the head of the prompt to fit within the maximum token limit
        tokens = prompt.split()
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[-max_tokens:]
        else:
            truncated_tokens = tokens
        return ' '.join(truncated_tokens)

    def generate_plus_with_score(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()

        if self.model_name == "gpt-3.5-turbo-0613":
            # the_engine = "gpt-35-turbo-0613"
            # the_engine = "gpt-35-turbo-16k-0613"
            the_engine = "gpt-3.5-turbo-16k"

        elif self.model_name == "gpt-4-turbo":
            the_engine = "gpt-4-turbo-2024-04-09"

        elif self.model_name == "gpt-4o":
            # the_engine = "gpt-4o-2024-05-13"
            the_engine = "gpt-4o-mini"

        else:
            raise ValueError("Invalid model name. Use 'gpt-3.5-turbo' or 'gpt-4-turbo'.")

        print("The LLM engine is:", the_engine)

        deploymnent = 'gpt-4o-mini-high-TPM'

        gpt_responses = None
        retry_num = 0
        retry_limit = 2  # Try two times
        error = None

        while gpt_responses is None:
            try:
                
                ###########
                gpt_responses = openai.ChatCompletion.create( # client.chat.completions.create( # OLD FREDDY
                    messages=[
                        {"role": "system", "content": "I will give you some examples, you need to follow the examples and complete the text, and no other content."},
                        {"role": "user", "content": prompt},
                    ],
                    engine = deploymnent,
                    model=the_engine,
                    stop=end_str,
                    **options
                )
                error = None

            except Exception as e:
                print(str(e), flush=True)
                error = str(e)
                if "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    return "Exceed context length"
                else:  # Rate limit
                    time.sleep(10)
                    retry_num += 1
        if error:
            raise Exception(error)

        results = []
        for i, res in enumerate(gpt_responses.choices):
            text = res.message.content
            # What is fake confidence?
            fake_conf = (len(gpt_responses.choices) - i) / len(gpt_responses.choices)
            results.append((text, np.log(fake_conf)))

        return results

    def generate(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        options["n"] = 1
        result = self.generate_plus_with_score(prompt, options, end_str)[0][0]
        return result