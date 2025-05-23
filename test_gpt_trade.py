from paper_trader import PaperTrader
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from gpt_sell_strategy import evaluate_sell_strategy

# Load API key
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load snapshot of options
df = pd.read_csv("synthetic_option_chain.csv")
snapshot = df.query("snapshot_day == 252 and path_id == 0")
spot_price = snapshot['spot_price'].iloc[0]

# Select subset to prompt GPT
subset = snapshot[['strike', 'expiry_days', 'option_type', 'price', 'iv']].head(10)
prompt_table = subset.to_markdown(index=False)

# GPT prompt
llm_prompt = f"""
You are an options trading assistant. The current stock price is ${spot_price:.2f}.

Here is the current option chain:

{prompt_table}

Recommend 1 trade for a $10,000 portfolio. Prefer liquid contracts near the money.
Respond ONLY in this format:

ACTION: BUY
TYPE: CALL
STRIKE: 100
EXPIRY_DAYS: 30
QUANTITY: 2
"""

# Ask GPT
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful trading assistant."},
        {"role": "user", "content": llm_prompt}
    ],
    temperature=0.5
)

gpt_reply = response.choices[0].message.content
print("📩 GPT Response:\n", gpt_reply)

# 🧠 Parse GPT output
lines = gpt_reply.splitlines()
trade = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in lines if ":" in line}

# Simulate the trade
trader = PaperTrader(initial_balance=10000)

option = snapshot.query(
    f"option_type == '{trade['TYPE'].lower()}' and strike == {trade['STRIKE']} and expiry_days == {trade['EXPIRY_DAYS']}"
)

if not option.empty:
    unit_price = option.iloc[0]['price'] * 100
    max_qty = int(trader.balance // unit_price)
    gpt_qty = int(trade['QUANTITY'])
    final_qty = min(gpt_qty, max_qty)

    if final_qty > 0:
        trader.buy_option(option.iloc[0], quantity=final_qty)
    else:
            print(f"❌ Cannot afford any contracts of {trade['TYPE']} strike {trade['STRIKE']} at ${unit_price:.2f} each.")
else:
        print("❌ Option contract not found in snapshot.")


# Show result
trader.summary(snapshot)

# Simulate market next day
future = df.query("snapshot_day == 253 and path_id == 0")

# Let GPT evaluate sell decision
print("\n🤖 GPT Decides Whether to Sell on Day 253:")
evaluate_sell_strategy(trader, future)



