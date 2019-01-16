import numpy as np
import os

from builtins import range, print
from builtins import Exception

import datetime

import pandas as pd
from dateutil import relativedelta


class FxDtoEnv:
    def __init__(self):
        # 観測できる足数
        self.visible_bar = 100
        # CSVファイルのパス配列(最低4ヶ月分を昇順で)
        self.csv_file_paths = []
        now = datetime.datetime.now()
        for _ in range(4):
            now = now - relativedelta.relativedelta(months=1)
            filename = 'DAT_MT_EURUSD_M1_{}.csv'.format(now.strftime('%Y%m'))
            if not os.path.exists(filename):
                print('ヒストリーファイルが存在していません。下記からダウンロードしてください。', filename)
                print('http://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/EURUSD/')
                raise Exception('ヒストリーファイルが存在していません。')
            else:
                self.csv_file_paths.append(filename)

        self.data = pd.DataFrame()
        for path in self.csv_file_paths:
            csv = pd.read_csv(path,
                              names=['date', 'time', 'open', 'high', 'low', 'close', 'v'],
                              parse_dates={'datetime': ['date', 'time']},
                              dtype={'datetime': np.long, 'open': np.float32, 'high': np.float32, 'low': np.float32, 'close': np.float32}
                              )
            csv.index = csv['datetime']
            csv['datetime'] = csv['datetime'].astype(np.long)
            csv = csv.drop('datetime', axis=1)
            # ohlcを作る際には必要
            # csv = csv.drop('open', axis=1)
            # histdata.comはvolumeデータが0なのでdrop
            csv = csv.drop('v', axis=1)
            self.data = self.data.append(csv)


period_rsi = 8
period_stoch = 5
period_sk = 3
period_sd = 3

env = FxDtoEnv()
target_5m = env.data['close'].resample('5min').ohlc().dropna()
# DTO(8,5,3,3)
# RSI計算(8)
close = target_5m['close']
diff = close.diff()[1:]
up, down = diff.copy(), diff.copy()
up[up < 0] = 0
down[down > 0] = 0
up_sma = up.rolling(window=8, center=False).mean()
down_sma = down.abs().rolling(window=8, center=False).mean()
rs = up_sma / down_sma
rsi = 100.0 - (100.0 / (1.0 + rs))
# DTOの計算
rolling = rsi.rolling(period_stoch)
llv = rolling.min()
hhv = rolling.max()
sto_rsi = 100 * ((rsi - llv) / (hhv - llv))
sk_5m = sto_rsi.rolling(period_sk).mean()
sd_5m = sk_5m.rolling(period_sd).mean()

signal_index = []
cross_index = []
win_buy = 0
lose_buy = 0
win_sell = 0
lose_sell = 0
for i in range(1, len(target_5m) - 1):
    if sk_5m[i] > sd_5m[i] and sk_5m[i - 1] < sd_5m[i - 1]:
        cross_index.append(i)
        direction = 1
    elif sk_5m[i] < sd_5m[i] and sk_5m[i - 1] > sd_5m[i - 1]:
        cross_index.append(i)
        direction = -1
    if len(cross_index) >= 4:  # TODO
        if direction > 0:
            c = target_5m['low'][cross_index[-1]]
            b = target_5m['high'][cross_index[-2]]
            a = target_5m['low'][cross_index[-3]]
            start = target_5m['high'][cross_index[-4]]
            if c < a < b < start:
                # innerの計算ABCパターン先頭からABCパターンの2倍分
                inner_min = target_5m['close'].rolling((cross_index[-1] - cross_index[-4]) * 2).min().dropna()
                if len(inner_min) < 1:
                    # 十分なデータがない
                    continue
                inner = inner_min[len(inner_min) - 1]
                if inner < c:
                    print(inner, c, a, b, start)
                    open = target_5m['open'][i]
                    # innerをストップロスとし、それの3倍で利確する
                    takeProfit = open + (open - inner) * 3
                    for j in range(i, len(target_5m) - 1):
                        if target_5m['low'][i] < inner:
                            signal_index.append([target_5m[i].index, -1])
                            print("--- ABC Buy pattern lose --- on ", target_5m.index[i])
                            lose_buy += 1
                            break
                        elif target_5m['high'][i] > takeProfit:
                            signal_index.append([target_5m[i].index, 1])
                            print("--- ABC Buy pattern win --- on ", target_5m.index[i])
                            win_buy += 1
                            break
                    print("NOT MOVE on Buy!! ", target_5m.index[i])
        else:
            c = target_5m['high'][cross_index[-1]]
            b = target_5m['low'][cross_index[-2]]
            a = target_5m['high'][cross_index[-3]]
            start = target_5m['low'][cross_index[-4]]
            if not c > a > b > start:
                # innerの計算ABCパターン先頭からABCパターンの2倍分
                inner_max = target_5m['close'].rolling((cross_index[-1] - cross_index[-4]) * 2).max().dropna()
                if len(inner_max) < 1:
                    # 十分なデータがない
                    continue
                inner = inner_max[len(inner_max) - 1]
                if inner > c:
                    print(inner, c, a, b, start)
                    open = target_5m['open'][i]
                    # innerをストップロスとし、それの3倍で利確する
                    takeProfit = open - (inner - open) * 3
                    for j in range(i, len(target_5m) - 1):
                        if target_5m['high'][i] > inner:
                            signal_index.append([target_5m[i].index, -1])
                            print("--- ABC Sell pattern lose --- on ", target_5m.index[i])
                            lose_sell += 1
                            break
                        elif target_5m['low'][i] < takeProfit:
                            signal_index.append([target_5m[i].index, 1])
                            print("--- ABC Sell pattern win --- on ", target_5m.index[i])
                            lose_buy += 1
                            break
                    print("NOT MOVE on Sell!! ", target_5m.index[i])
print(win_buy, " ", win_sell, " ", lose_buy, " ", lose_sell)
print(signal_index)
