class PaperTrader:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.positions = []  # list of dicts
        self.transaction_history = []

    def buy_option(self, option_row, quantity):
        """
        Buy an option contract.
        :param option_row: Row of option chain DataFrame
        :param quantity: Number of contracts
        """
        total_cost = option_row['price'] * quantity * 100  # 100 shares per contract
        if self.balance >= total_cost:
            self.balance -= total_cost
            self.positions.append({
                'option': option_row,
                'quantity': quantity,
                'total_cost': total_cost
            })
            self.transaction_history.append({
                'action': 'BUY',
                'option_type': option_row['option_type'],
                'strike': option_row['strike'],
                'expiry_days': option_row['expiry_days'],
                'quantity': quantity,
                'price': option_row['price'],
                'total_cost': total_cost
            })
        else:
            print(f"❌ Insufficient balance to buy {quantity}x {option_row['option_type']} strike {option_row['strike']}.")

    def sell_option(self, option_row, quantity, current_df=None):
        """Sell an option contract from the existing positions.

        :param option_row: Row of option chain DataFrame representing the option to sell.
        :param quantity: Number of contracts to sell.
        :param current_df: Optional snapshot of the option chain. Included for API
            compatibility but not required because ``option_row`` already contains
            the current price.
        """
        for idx, pos in enumerate(self.positions):
            opt = pos['option']
            if (
                opt['strike'] == option_row['strike']
                and opt['expiry_days'] == option_row['expiry_days']
                and opt['option_type'] == option_row['option_type']
            ):
                if quantity > pos['quantity']:
                    print(
                        f"❌ Cannot sell {quantity}x {option_row['option_type']} strike "
                        f"{option_row['strike']}: only {pos['quantity']} owned."
                    )
                    return

                sell_price = option_row['price']
                proceeds = sell_price * quantity * 100
                self.balance += proceeds

                cost_per_contract = pos['total_cost'] / pos['quantity'] if pos['quantity'] else 0
                pos['quantity'] -= quantity
                pos['total_cost'] = max(0, pos['total_cost'] - cost_per_contract * quantity)

                self.transaction_history.append({
                    'action': 'SELL',
                    'option_type': option_row['option_type'],
                    'strike': option_row['strike'],
                    'expiry_days': option_row['expiry_days'],
                    'quantity': quantity,
                    'price': sell_price,
                    'total_cost': proceeds,
                    'realized_pnl': proceeds - cost_per_contract * quantity
                })

                if pos['quantity'] == 0:
                    self.positions.pop(idx)
                return

        print(
            f"❌ No position found to sell {quantity}x {option_row['option_type']} "
            f"strike {option_row['strike']} expiring in {option_row['expiry_days']} days."
        )

    def mark_to_market(self, current_df):
        """
        Calculate total value of all current positions.
        :param current_df: Current snapshot of option chain (DataFrame)
        :return: Total position value
        """
        value = 0
        for pos in self.positions:
            opt = pos['option']
            match = current_df[
                (current_df['strike'] == opt['strike']) &
                (current_df['expiry_days'] == opt['expiry_days']) &
                (current_df['option_type'] == opt['option_type'])
            ]
            if not match.empty:
                current_price = match['price'].values[0]
                value += current_price * pos['quantity'] * 100
        return value

    def summary(self, current_df):
        """
        Print portfolio summary.
        :param current_df: Snapshot to use for mark-to-market
        """
        mtm = self.mark_to_market(current_df)
        total = self.balance + mtm
        print(f"💰 Cash Balance: ${self.balance:.2f}")
        print(f"📈 Position Value: ${mtm:.2f}")
        print(f"📊 Total Equity: ${total:.2f}")
        print("📝 Transaction History:")
        for log in self.transaction_history:
            print(f"  • {log['action']} {log['quantity']} {log['option_type'].upper()} @ strike {log['strike']} for ${log['price']:.2f} (${log['total_cost']:.2f})")


