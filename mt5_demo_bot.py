# MT5 Demo Trading Bot - Safe starter
# Works on Windows with MetaTrader 5 desktop terminal.
# IMPORTANT: This file does NOT contain your password.
#
# Install:
#   py -m pip install MetaTrader5
#
# Before running:
#   1) Install XM MetaTrader 5.
#   2) Log in to your DEMO account in MT5.
#   3) Keep MT5 open.
#   4) Run: py mt5_demo_bot.py
#
# The bot starts in READ-ONLY mode. It will NOT place an order until
# you explicitly choose option 6 and confirm.

import time
import getpass
import MetaTrader5 as mt5

DEFAULT_SERVER = "XMGlobal-MT5 6"
DEFAULT_ACCOUNT = "1302109751"
DEFAULT_SYMBOL = "XAUUSD"
DEFAULT_LOT = 0.01

def money(v):
    try:
        return f"{v:,.2f}"
    except Exception:
        return str(v)

def connect():
    print("\nConnecting to MetaTrader 5...")

    # Let MT5 use the password already saved in the desktop terminal.
    # If it is not saved, we ask for it securely without displaying it.
    if not mt5.initialize():
        print("MT5 initialize failed:", mt5.last_error())
        return False

    account = int(input(f"Account [{DEFAULT_ACCOUNT}]: ").strip() or DEFAULT_ACCOUNT)
    server = input(f"Server [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER

    password = getpass.getpass("Password (press Enter if MT5 already saved it): ")

    if password:
        ok = mt5.login(account, password=password, server=server)
    else:
        ok = mt5.login(account, server=server)

    if not ok:
        print("Login failed:", mt5.last_error())
        mt5.shutdown()
        return False

    info = mt5.account_info()
    if info is None:
        print("Could not read account information:", mt5.last_error())
        mt5.shutdown()
        return False

    print("\nCONNECTED")
    print("-" * 50)
    print("Login:       ", info.login)
    print("Server:      ", info.server)
    print("Company:     ", info.company)
    print("Currency:    ", info.currency)
    print("Balance:     ", money(info.balance))
    print("Equity:      ", money(info.equity))
    print("Free margin: ", money(info.margin_free))
    print("Trade allowed:", info.trade_allowed)
    print("-" * 50)
    return True

def show_symbol(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"Symbol '{symbol}' was not found.")
        return False

    if not info.visible:
        if not mt5.symbol_select(symbol, True):
            print("Could not select symbol:", mt5.last_error())
            return False

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print("No live tick for", symbol)
        return False

    print(f"\n{symbol}")
    print("Bid:", tick.bid)
    print("Ask:", tick.ask)
    print("Spread:", tick.ask - tick.bid)
    return True

def show_positions():
    positions = mt5.positions_get()
    if positions is None:
        print("Could not read positions:", mt5.last_error())
        return

    if len(positions) == 0:
        print("\nNo open positions.")
        return

    print("\nOPEN POSITIONS")
    print("-" * 90)
    for p in positions:
        side = "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL"
        print(
            f"Ticket={p.ticket} | {p.symbol} | {side} | "
            f"Lot={p.volume} | Open={p.price_open} | "
            f"Profit={money(p.profit)}"
        )
    print("-" * 90)

def test_buy(symbol, lot):
    # This is a REAL order on the connected MT5 account.
    # It is intended ONLY for the user's DEMO account.
    if not show_symbol(symbol):
        return

    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not tick:
        return

    # Basic volume validation.
    lot = max(info.volume_min, min(lot, info.volume_max))
    step = info.volume_step
    lot = round(round(lot / step) * step, 8)

    print("\nWARNING: This will place a BUY order on the connected account.")
    print("Make absolutely sure the account is DEMO.")
    confirm = input(f"Type TEST BUY to place {lot} lot {symbol}: ").strip()
    if confirm != "TEST BUY":
        print("Cancelled.")
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "deviation": 20,
        "magic": 2601007,
        "comment": "Python MT5 Demo Test",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": info.filling_mode,
    }

    result = mt5.order_send(request)

    if result is None:
        print("order_send returned None:", mt5.last_error())
        return

    print("\nORDER RESULT")
    print("Retcode:", result.retcode)
    print("Comment:", result.comment)
    print("Order:", result.order)
    print("Deal:", result.deal)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("SUCCESS: Demo BUY was executed.")
    else:
        print("Order was NOT confirmed as executed.")

def close_position(ticket):
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        print("Position not found.")
        return

    p = positions[0]
    symbol = p.symbol
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not tick:
        print("Could not read market data.")
        return

    if p.type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": p.volume,
        "type": order_type,
        "position": p.ticket,
        "price": price,
        "deviation": 20,
        "magic": 2601007,
        "comment": "Python MT5 Demo Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": info.filling_mode,
    }

    confirm = input(f"Type CLOSE to close ticket {ticket}: ").strip()
    if confirm != "CLOSE":
        print("Cancelled.")
        return

    result = mt5.order_send(request)
    if result is None:
        print("Close failed:", mt5.last_error())
    else:
        print("Close retcode:", result.retcode)
        print("Comment:", result.comment)

def menu():
    symbol = DEFAULT_SYMBOL
    lot = DEFAULT_LOT

    while True:
        print("\n" + "=" * 55)
        print("          MT5 DEMO PYTHON BOT")
        print("=" * 55)
        print(f"Symbol: {symbol} | Lot: {lot}")
        print("1. Account information")
        print("2. Show current price")
        print("3. Show open positions")
        print("4. Change symbol")
        print("5. Change lot")
        print("6. TEST BUY (DEMO)")
        print("7. Close a position")
        print("8. Continuous price monitor")
        print("0. Exit")
        print("=" * 55)

        choice = input("Choose: ").strip()

        if choice == "1":
            info = mt5.account_info()
            if info:
                print("\nLogin:", info.login)
                print("Server:", info.server)
                print("Balance:", money(info.balance))
                print("Equity:", money(info.equity))
                print("Profit:", money(info.profit))
                print("Free margin:", money(info.margin_free))
                print("Trade allowed:", info.trade_allowed)
        elif choice == "2":
            show_symbol(symbol)
        elif choice == "3":
            show_positions()
        elif choice == "4":
            symbol = input("Symbol (example XAUUSD): ").strip().upper()
        elif choice == "5":
            try:
                lot = float(input("Lot size: ").strip())
            except ValueError:
                print("Invalid lot.")
        elif choice == "6":
            test_buy(symbol, lot)
        elif choice == "7":
            try:
                ticket = int(input("Position ticket: ").strip())
                close_position(ticket)
            except ValueError:
                print("Invalid ticket.")
        elif choice == "8":
            print("Monitoring. Press Ctrl+C to stop.")
            try:
                while True:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        print(
                            f"\r{symbol} | Bid {tick.bid} | Ask {tick.ask}",
                            end="",
                            flush=True,
                        )
                    time.sleep(0.25)
            except KeyboardInterrupt:
                print("\nMonitor stopped.")
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def main():
    print("=" * 55)
    print(" MT5 DEMO BOT - SAFE TEST VERSION")
    print("=" * 55)
    print("This version does not contain or display your password.")
    print("It starts without automatic trading.")
    print()

    if not connect():
        input("\nPress Enter to exit...")
        return

    try:
        menu()
    finally:
        mt5.shutdown()
        print("\nMT5 connection closed.")

if __name__ == "__main__":
    main()
