# %%
import yaml
import os
import openai  # Ensure you are using `openai` here
import dotenv

dotenv.load_dotenv()

#  %%
# Load the OpenAI API key and Azure endpoint from config
with open("llm_config.yaml") as f:
    config_yaml = yaml.load(f, Loader=yaml.FullLoader)

# Extract configuration variables
api_key = config_yaml['api_key']
azure_endpoint = config_yaml['azure_endpoint']
deployment_name = config_yaml['deployment_name']
api_version = config_yaml.get('api_version')

# Set up the OpenAI client with Azure settings
openai.api_type = "azure"
openai.api_key = api_key
openai.api_base = azure_endpoint
openai.api_version = api_version

# Define the message
message_text = [{"role": "system", "content": "What is the habitat of the Chipping Sparrow?"}]

# Make the API call using `engine` instead of `model`
response = openai.ChatCompletion.create(
    engine=deployment_name,  # Use 'engine' for Azure deployments
    messages=message_text,
    temperature=0.7,
    max_tokens=800,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0
)

# Print the response
print(response['choices'][0]['message']['content'])
