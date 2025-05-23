import openai
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_sell_prompt(trader, snapshot_df):
    positions = []
    for pos in trader.positions:
        opt = pos['option']
        match = snapshot_df[
            (snapshot_df['strike'] == opt['strike']) &
            (snapshot_df['expiry_days'] == opt['expiry_days']) &
            (snapshot_df['option_type'] == opt['option_type'])
        ]
        if not match.empty:
            current_price = match['price'].values[0]
            positions.append({
                "TYPE": opt["option_type"].upper(),
                "STRIKE": opt["strike"],
                "EXPIRY_DAYS": opt["expiry_days"],
                "BUY_PRICE": round(pos["buy_price"], 2),
                "CURRENT_PRICE": round(current_price, 2),
                "QUANTITY": pos["quantity"]
            })

    if not positions:
        return "You have no open positions. Respond with: DECISION: NO"

    df = pd.DataFrame(positions)
    table = df.to_markdown(index=False)

    return f"""
You are an options trading assistant. Based on the portfolio below, decide whether to sell any contracts today.

Here is the current portfolio:

{table}

Respond only in this format:

DECISION: [YES/NO]
IF YES:
  SELL: [CALL/PUT]
  STRIKE: [e.g. 100]
  EXPIRY_DAYS: [e.g. 30]
  QUANTITY: [e.g. 1]
REASON: [why]
"""

def evaluate_sell_strategy(trader, snapshot_df):
    prompt = create_sell_prompt(trader, snapshot_df)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful trading assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    gpt_reply = response.choices[0].message.content
    print("📩 GPT Sell Decision:\n", gpt_reply)

    lines = gpt_reply.splitlines()
    decision = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in lines if ":" in line}

    if decision.get("DECISION", "NO").upper() == "YES":
        option_to_sell = snapshot_df.query(
            f"option_type == '{decision['SELL'].lower()}' and "
            f"strike == {decision['STRIKE']} and "
            f"expiry_days == {decision['EXPIRY_DAYS']}"
        )
        if not option_to_sell.empty:
            trader.sell_option(option_to_sell.iloc[0], quantity=int(decision['QUANTITY']), current_df=snapshot_df)
        else:
            print("❌ GPT recommended option not found.")


