from paper_trader import PaperTrader
import pandas as pd

df = pd.read_csv("synthetic_option_chain.csv")
snapshot = df.query("snapshot_day == 252 and path_id == 0")

trader = PaperTrader(initial_balance=10000)

spot_price = snapshot['spot_price'].iloc[0]
atm_call = snapshot.query("option_type == 'call' and expiry_days == 30") \
                   .iloc[(snapshot['strike'] - spot_price).abs().argsort()[:1]]

# Buy 2 contracts
trader.buy_option(atm_call.iloc[0], quantity=2)
print("✅ After Buying:")
trader.summary(snapshot)

# Sell 1 contract
trader.sell_option(atm_call.iloc[0], quantity=1, current_df=snapshot)
print("\n✅ After Selling:")
trader.summary(snapshot)





