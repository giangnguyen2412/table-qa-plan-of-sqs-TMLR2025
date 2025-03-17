import openai
import time
import numpy as np
import yaml
import os


class TableQA_LLM:
    def __init__(self, config_path="llm_config.yaml"):
        # Load configuration
        with open(config_path) as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

        # Set provider based on config
        self.provider = self.config.get('active_provider', 'azure_openai')

        # Configure client based on provider
        self._setup_client()

    def _setup_client(self):
        """Configure the appropriate client based on the active provider"""
        if 'providers' in self.config:
            provider_config = self.config['providers'][self.provider]

            if self.provider == 'azure_openai':
                # Set up Azure OpenAI
                self.api_key = provider_config['api_key']
                self.api_base = provider_config['base_endpoint']
                self.api_version = provider_config.get('api_version', '2024-08-01-preview')

                # Find active deployment
                self.deployment_name = None
                for depl in provider_config['deployments']['regular']:
                    if depl.get('active', False):
                        self.deployment_name = depl['name']
                        break

                # Configure Azure OpenAI client
                openai.api_type = "azure"
                openai.api_key = self.api_key
                openai.api_base = self.api_base
                openai.api_version = self.api_version

                print(f"Using Azure OpenAI deployment: {self.deployment_name}")

            elif self.provider == 'deepseek':
                # Configure DeepSeek
                self.api_key = provider_config['api_key']
                self.base_url = provider_config['base_url']

                # Find active model
                self.model_name = None
                for model in provider_config['models']:
                    if model.get('active', False):
                        self.model_name = model['name']
                        break

                # Import and configure DeepSeek client (placeholder for now)
                print(f"Using DeepSeek model: {self.model_name}")

            elif self.provider == 'sambanova':
                # Configure SambaNova
                self.api_key = provider_config['api_key']
                self.base_url = provider_config['base_url']

                # Find active model
                self.model_name = None
                for model in provider_config['models']:
                    if model.get('active', False):
                        self.model_name = model['name']
                        break

                # For SambaNova, we'll initialize the client just before use
                # to avoid any connection timeouts
                print(f"Using SambaNova model: {self.model_name}")

        else:
            # Legacy config
            self.model_name = self.config.get('model_name', 'gpt-4o-mini')
            self.api_key = self.config['api_key']
            self.api_base = self.config['azure_endpoint']
            self.api_version = self.config.get('api_version', '2024-08-01-preview')
            self.deployment_name = self.config.get('deployment_name')

            # Set up OpenAI client with Azure settings
            openai.api_type = "azure"
            openai.api_key = self.api_key
            openai.api_base = self.api_base
            openai.api_version = self.api_version

            print(f"Using legacy config with model: {self.model_name}")

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

    def truncate_prompt_head_exact(self, prompt, max_tokens):
        tokens = openai.Encoding.encode(prompt)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[-max_tokens:]
        else:
            truncated_tokens = tokens
        return openai.Encoding.decode(truncated_tokens)

    def truncate_prompt(self, prompt, max_tokens):
        tokens = prompt.split()
        truncated_tokens = tokens[:max_tokens]
        return ' '.join(truncated_tokens)

    def truncate_prompt_head(self, prompt, max_tokens):
        tokens = prompt.split()
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[-max_tokens:]
        else:
            truncated_tokens = tokens
        return ' '.join(truncated_tokens)

    def generate_plus_with_score(self, prompt, options=None, end_str=None, system_prompt=None):
        if options is None:
            options = self.get_model_options()

        if system_prompt is None:
            system_prompt = "I will give you some examples, you need to follow the examples and complete the text, and no other content."

        results = []
        retry_num = 0
        retry_limit = 2
        error = None

        while not results and retry_num <= retry_limit:
            try:
                if self.provider == 'azure_openai':
                    # Azure OpenAI implementation
                    gpt_responses = openai.ChatCompletion.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        engine=self.deployment_name,
                        stop=end_str,
                        **options
                    )

                    for i, res in enumerate(gpt_responses.choices):
                        try:
                            text = res.message.content
                            fake_conf = (len(gpt_responses.choices) - i) / len(gpt_responses.choices)
                            results.append((text, np.log(fake_conf)))
                        except AttributeError as e:
                            print(f"Error accessing response content: {e}")
                            results.append(("Error accessing response content", 0))

                elif self.provider == 'deepseek':
                    # DeepSeek implementation placeholder
                    # Will need to be filled based on DeepSeek's API documentation
                    pass

                elif self.provider == 'sambanova':
                    # Initialize SambaNova client
                    client = openai.OpenAI(
                        api_key=self.api_key,
                        base_url=self.base_url
                    )

                    sambanova_model = self.model_name

                    # Set system prompt based on model type if not provided
                    if system_prompt is None:
                        system_prompt = "You are a helpful assistant."

                    # Make the API call
                    response = client.chat.completions.create(
                        model=sambanova_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=options.get('temperature', 0),
                        max_tokens=options.get('max_tokens', 150),
                        stop=end_str
                    )

                    # Process results
                    for i, choice in enumerate(response.choices):
                        text = choice.message.content.strip()
                        # For SambaNova, we'll just use a default confidence score
                        fake_conf = 1.0
                        results.append((text, np.log(fake_conf)))

                error = None

            except Exception as e:
                print(str(e), flush=True)
                error = str(e)

                if self.provider == 'sambanova':
                    # Special handling for SambaNova errors
                    if 'Please reduce the length of the message' in str(e):
                        print("[SambaNova] Overflow context length.")
                        return "Exceed context length"

                    # Specific handling for rate limit errors (429)
                    if 'rate limit exceeded' in str(e).lower():
                        # Implement exponential backoff
                        wait_time = 5 * (2 ** retry_num)
                        print(f"[SambaNova] Rate limit exceeded, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        print(f"[SambaNova] Error: {e}, waiting 5s before retry...")
                        time.sleep(5)
                else:
                    # Generic error handling for other providers
                    if "This model's maximum context length is" in str(e):
                        print(e, flush=True)
                        return "Exceed context length"
                    else:  # Rate limit or other error
                        time.sleep(10)

                retry_num += 1

        if error and not results:
            raise Exception(error)

        return results

    def generate(self, prompt, options=None, end_str=None, system_prompt=None):
        if options is None:
            options = self.get_model_options()
        options["n"] = 1

        result = self.generate_plus_with_score(prompt, options, end_str, system_prompt)
        if isinstance(result, str):  # Error message
            return result

        return result[0][0]