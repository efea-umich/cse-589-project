from openai import OpenAI
# openai.api_key = "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"
client = OpenAI()
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Write a haiku about recursion in programming."
        }
    ]
)

print(completion.choices[0].message)