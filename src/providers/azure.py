import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)


def get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )


def call_llm(prompt: str, system_prompt: str = "You are an expert data analyst.") -> str:
    client = get_azure_client()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content
