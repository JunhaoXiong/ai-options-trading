import os
import openai
import pandas as pd
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load option chain
df = pd.read_csv("synthetic_option_chain.csv")

# Filter for a snapshot
subset = df.query("snapshot_day == 252 & path_id == 0").head(15)
spot_price = subset['spot_price'].iloc[0]
prompt_table = subset[['strike', 'expiry_days', 'option_type', 'price', 'iv']].to_markdown(index=False)

# Create the LLM prompt
llm_prompt = f"""
You are a trading assistant. The current stock price is ${spot_price:.2f}.

Here is the available option chain:

{prompt_table}

Assume the user has $10,000. Recommend 2 options trading strategies (e.g., long call, vertical spread, straddle).
Explain the reasoning using strike, volatility, and expiration. Include pros/cons and estimated payoff range.
"""

# Call GPT-4
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful financial assistant."},
        {"role": "user", "content": llm_prompt}
    ],
    temperature=0.7
)

# Show response
print(response.choices[0].message.content)
