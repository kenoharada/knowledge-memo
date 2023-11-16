import webvtt
from openai import OpenAI
import os
MODEL_NAME = 'gpt-4-1106-preview'


client = OpenAI()
response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": 'こんにちは',
            }
        ],
        model=MODEL_NAME,
        )
print(response.choices[0].message.content)