import datetime
import logging
import os
import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from db2 import Database
import pandas as pd
import requests
from secret_folder.keys import api_key, api_secret, bot_token, TELEGRAM_CHAT_ID


# https://binance-docs.github.io/apidocs/futures/en/#new-order-trade - описание параметров

# binance
api_key = api_key
api_secret = api_secret
client = Client(api_key, api_secret, testnet=True)
client.API_URL = 'https://testnet.binancefuture.com'
# telegram
bot_token = bot_token
TELEGRAM_CHAT_ID = TELEGRAM_CHAT_ID

# get summary info from exchange
# info = client.get_exchange_info()
# print(info)

test_coin_list = ['BNBUSDT', 'BTCUSDT',
    'ETHUSDT', 'LTCUSDT', 'TRXUSDT', 'XRPUSDT']

def send_tlg_message(data):
    try:
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + TELEGRAM_CHAT_ID + \
                    '&text=' + data
        response = requests.get(send_text)
        print("TELEGRAM:", data)
        return response.json()
    except Exception as e:
        print("[X] Telegram Error:\n>", e)
        logging.error(f"[X] Telegram Error:{e}")

def get_order_reverse_side(side):
    if side == 'BUY':
        return 'SELL'
    elif side == 'SELL':
        return 'BUY'
    else:
        print(f'Unknown parameter: get_order_reverse_side("{side}"):')
        return None

def main():

    # main cycle
    while True:
        try:
            # check status of all active orders
            # request to DATABASE
            with Database() as db:
                # db.create_tables()
                new_orders = db.get_data(f"SELECT * from orders")

                df_orders = pd.DataFrame(new_orders, columns=['id',
                                                              'signal_id',
                                                              'transact_time',
                                                              'symbol',
                                                              'price',
                                                              'origQty',
                                                              'side',
                                                              'state',
                                                              'tp',
                                                              'sl',
                                                              'tp_id',
                                                              'sl_id'])



                error_orders = df_orders[df_orders['state'].isin(['ERROR'])]
                for idx, row in error_orders.iterrows():
                    symbol = row['symbol']
                    order_id = row['id']
                    side = get_order_reverse_side(row['side'])
                    qty = row['origQty']
                    try:
                        order_state = client.get_order(
                            symbol=symbol,
                            orderId=order_id)
                    except BinanceAPIException as e:
                        if 'Order does not exist' in e.message:
                            db.execute(f"""UPDATE orders SET state='CANCELED' where id={order_id}""")
                            continue
                        else:
                            print(e)
                        continue
                    if order_state['status'] == 'CANCELED':
                        # if order was canceled - mark in DB new order state
                        db.execute(
                            f"""UPDATE orders SET state='CANCELED' where id={order_id}""")
                    elif order_state['status'] == 'FILLED':
                        # отменяем ошибочный ордер
                        try:
                            client.create_test_order(symbol=symbol, side=side, type='MARKET', quantity=qty,
                                                reduceOnly='true')
                            client.create_order(symbol=symbol, side=side, type='MARKET', quantity=qty, reduceOnly='true')
                            db.execute(f"""UPDATE orders SET state='CANCELED' where id={order_id}""")

                        except Exception as e:
                            print(e)
                            logging.error(f"Cancel order error (id={order_id}):", e)
                            send_tlg_message(f"Cancel order error (id={order_id}): {e}.")
                            continue
                        try:
                            if cancel['status'] == 'CANCELED':
                                db.execute(f"""UPDATE orders SET state='CANCELED BY TIME' where id={order_id}""")
                                logging.info(f"Order canceled by time expiration (id={order_id}).")
                                send_tlg_message(f"Order canceled by time expiration (id={order_id}).")
                        except Exception as e:
                            print(e)
                            logging.error(f"Update BD error (id={order_id}):", e)
                            continue


                new_orders = df_orders[df_orders['state'].isin(['NEW'])]

                for idx, row in new_orders.iterrows():
                    print(idx, row['id'], row['symbol'])
                    symbol = row['symbol']
                    order_id = row['id']
                    order_state = client.get_order(
                        symbol=symbol,
                        orderId=order_id)
                    print(order_state)
                    if order_state['status'] == 'CANCELED':
                        # ордер был отменен - помечаем в БД новое сосотояние ордера
                        db.execute(
                            f"""UPDATE orders SET state='CANCELED' where id={order_id}""")
                        send_tlg_message(f"UPDATE orders SET state='CANCELED' where id={order_id}")
                    elif order_state['status'] == 'FILLED':
                        # ордер был исполнен => выставляем tp and sl
                        # в БД прописываем статус заявки 'FILLED'
                        # выставляем тейк-профит
                        print('take profit=', row['tp'])
                        print('row["origQty"]', row['origQty'])
                        print('row["origQty"]', row['origQty'])
                        print("row['side']", row['side'])
                        print("get_order_reverse_side(row['side'])", get_order_reverse_side(row['side']))

                        try:
                            tp_order = client.create_order(
                                symbol=symbol,
                                side=get_order_reverse_side(row['side']),
                                type='TAKE_PROFIT_LIMIT',
                                quantity=row['origQty'],
                                price=row['tp'],
                                stopPrice=row['tp'],
                                timeInForce='GTC'
                            )
                            logging.info(f"TP is placed(id={order_id}, {symbol},"
                                         f" {get_order_reverse_side(row['side'])}, {row['tp']}):")
                            send_tlg_message(f"TP is placed(id={order_id}, {symbol},"
                                             f"{get_order_reverse_side(row['side'])}, {row['tp']}):")
                        except Exception as e:
                            logging.error(f"Take profit setup error (id={order_id}):", e)
                            send_tlg_message(f"Take profit setup error (id={order_id}):{e}")
                            db.execute(f"""UPDATE orders SET state='{e}' where id={order_id}""")
                            continue
                        try:
                            db.execute(f"""UPDATE orders SET state='TP placed' where id={order_id}""")
                            logging.info(f"""TP placed. id={order_id}""")
                            send_tlg_message(f"""TP placed. id={order_id}""")
                        except Exception as e:
                            print(e)
                            logging.error(f"Update BD error (id={order_id}):", e)
                            send_tlg_message(f"Update BD error (id={order_id}):{e}")
                            continue

                        # выставляем стоп-лосс
                        try:
                            sl_order = client.create_order(
                                symbol=symbol,
                                side=get_order_reverse_side(row['side']),
                                type='STOP_LOSS_LIMIT',
                                quantity=row['origQty'],
                                price=row['tp'],
                                stopPrice=row['tp'],
                                timeInForce='GTC'
                            )
                            logging.info(f"SL is placed(id={order_id}, {symbol},"
                                         f" {get_order_reverse_side(row['side'])}, {row['tp']}):", e)
                            send_tlg_message(f"SL is placed(id={order_id}, {symbol},"
                                         f" {get_order_reverse_side(row['side'])}, {row['tp']}):", e)
                        except Exception as e:
                            logging.error(f"Stoploss setup error (id={order_id}):", e)
                            db.execute(f"""UPDATE orders SET state='{e}' where id={order_id}""")
                            send_tlg_message(f"Stoploss setup error (id={order_id}): {e}")
                            continue

                        try:
                            db.execute(f"""UPDATE orders SET state='SL placed' where id={order_id}""")
                            logging.info(f"""SL placed. id={order_id}""")
                        except Exception as e:
                            print(e)
                            logging.error(f"Update BD error (id={order_id}):", e)
                            continue
                    else:
                        # проверка на срок жизни ордера и его отмена , если он уже не актуален (20 сут.)
                        if time.mktime((datetime.datetime.now() - datetime.timedelta(minutes=10)).timetuple()) * 1000 > \
                                order_state['time']:
                            print(f"Order live time expired. Orders [id={order_id}] must be cancelled")
                            try:
                                cancel = client.cancel_order(symbol=order_state['symbol'],
                                                             orderId=order_state['orderId'])
                            except Exception as e:
                                print(e)
                                logging.error(f"Cancel order error (id={order_id}):", e)
                                send_tlg_message(f"Cancel order error (id={order_id}): {e}.")
                                continue
                            try:
                                if cancel['status'] == 'CANCELED':
                                    db.execute(f"""UPDATE orders SET state='CANCELED BY TIME' where id={order_id}""")
                                    logging.info(f"Order canceled by time expiration (id={order_id}).")
                                    send_tlg_message(f"Order canceled by time expiration (id={order_id}).")
                            except Exception as e:
                                print(e)
                                logging.error(f"Update BD error (id={order_id}):", e)
                                continue

                # break
                print('Pause 2 sec...')
                print('*' * 30)
                time.sleep(2)
        except Exception as e:
            print("Exception:", e)
            break

if __name__ == "__main__":
    main()
    exit(0)
