import os
from openai import OpenAI

# 1. Initialize the client. 
# It automatically looks for an environment variable named OPENAI_API_KEY
client = OpenAI()

try:
    # 2. Trigger the completion endpoint
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful programming assistant."},
            {"role": "user", "content": "Write a short Python function to calculate Fibonacci numbers."}
        ],
        max_tokens=150, # Guardrail to control costs
        temperature=0.7 # Controls creativity/randomness
    )

    # 3. Extract and use the text generation result
    ai_output = response.choices[0].message.content
    print("AI Response:\n", ai_output)

except Exception as e:
    print(f"An error occurred: {e}")

