from random import random

import numpy as np
import os

from builtins import range, print
from builtins import Exception

import datetime

import pandas
from dateutil import relativedelta
import matplotlib.pyplot as plt
import mpl_finance as mpf


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

        self.data = pandas.DataFrame()
        for path in self.csv_file_paths:
            csv = pandas.read_csv(path,
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
            # 最後に読んだCSVのインデックスを開始インデックスとする
            self.read_index = len(self.data) - len(csv)

        self.tickets = []

    def make_obs(self, mode):
        """
        5分足、1時間足の2時系列データをvisible_bar本分作成する
        :return:
        """
        target = self.data.iloc[self.read_index - 60 * env.visible_bar: self.read_index]
        if mode == 'human':
            m5 = np.array(target.resample('5min').agg({'high': 'max',
                                                       'low': 'min',
                                                       'close': 'last'}).dropna().iloc[-1 * self.visible_bar:][target.columns])
            h1 = np.array(target.resample('1H').agg({'high': 'max',
                                                     'low': 'min',
                                                     'close': 'last'}).dropna().iloc[-1 * self.visible_bar:][target.columns])
            return np.array([m5, h1])
        elif mode == 'ohlc_array':
            m5 = np.array(target.resample('5min').agg({'high': 'max',
                                                       'low': 'min',
                                                       'close': 'last'}).dropna().iloc[-1 * self.visible_bar:][target.columns])
            h1 = np.array(target.resample('1H').agg({'high': 'max',
                                                     'low': 'min',
                                                     'close': 'last'}).dropna().iloc[-1 * self.visible_bar:][target.columns])
            return np.array([m5, h1])


period_rsi = 8
period_stoch = 5
period_sk = 3
period_sd = 3


def show(env):
    # ランダムにデータを抽出
    env.read_index = int(random() * len(env.data))
    target = env.data.iloc[env.read_index - 60 * env.visible_bar: env.read_index]

    target_5m = target['close'].resample('5min').ohlc().dropna().iloc[-1 * env.visible_bar:]
    indices_5m = target_5m.index
    dummy_indices_5m = np.linspace(0, len(target_5m), len(target_5m))
    data_5m = pandas.DataFrame({'datetime': dummy_indices_5m,
                                'open': target_5m['open'],
                                'high': target_5m['high'],
                                'low': target_5m['low'],
                                'close': target_5m['close']})

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

    dto_indices_5m = sk_5m.index
    dummy_indices_dto_5m = np.linspace(0, len(dto_indices_5m), len(dto_indices_5m))

    # 1時間足
    target_1h = target['close'].resample('1H').ohlc().dropna().iloc[-1 * env.visible_bar:]
    indices_1h = target_1h.index
    dummy_indices_1h = np.linspace(0, len(target_1h), len(target_1h))
    data_1h = pandas.DataFrame({'datetime': dummy_indices_1h,
                                'open': target_1h['open'],
                                'high': target_1h['high'],
                                'low': target_1h['low'],
                                'close': target_1h['close']})

    # DTO(8,5,3,3)
    # RSI計算(8)
    close = target_1h['close']
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
    sk_1h = sto_rsi.rolling(period_sk).mean()
    sd_1h = sk_1h.rolling(period_sd).mean()

    dto_indices_1h = sk_1h.index
    dummy_indices_dto_1h = np.linspace(0, len(dto_indices_1h), len(dto_indices_1h))

    # シグナル計算
    latest_sk_h1 = sk_1h[len(sk_1h) - 1]
    latest_sd_h1 = sd_1h[len(sd_1h) - 1]
    if latest_sk_h1 > latest_sd_h1:
        if latest_sd_h1 > 75:
            print("sd_h1 is over 75! ", latest_sd_h1)
            return False
    else:
        if latest_sd_h1 < 25:
            print("sd_h1 is under 25! ", latest_sd_h1)
            return False

    sd_5m_1 = round(sd_5m[len(sd_5m) - 2], 2)
    if 25 < sd_5m_1 < 75:
        print("sd_5m is in middle!")
        return False

    direction = 0
    cross_index = []
    for i in reversed(range(2, len(sk_5m) - 1)):
        if sk_5m[i] > sd_5m[i] and sk_5m[i - 1] < sd_5m[i - 1]:
            cross_index.append(i)
            if direction == 0:
                direction = 1
        elif sk_5m[i] < sd_5m[i] and sk_5m[i - 1] > sd_5m[i - 1]:
            cross_index.append(i)
            if direction == 0:
                direction = -1
        if len(cross_index) >= 4:
            break

    if len(cross_index) < 4:
        print("cross_index len is under 4!")
        return False
    else:
        # innerの計算ABCパターン先頭からABCパターンの2倍分
        rolling = data_5m['close'].rolling((cross_index[0] - cross_index[3]) * 2)
        if direction > 0:
            inner = rolling.min()[cross_index[3]]
        else:
            inner = rolling.max()[cross_index[3]]

    # 0: C
    # 1: B
    # 2: A
    # 3: start
    if direction > 0:
        c = data_5m['low'][cross_index[0]]
        b = data_5m['high'][cross_index[1]]
        a = data_5m['low'][cross_index[2]]
        start = data_5m['high'][cross_index[3]]
        print(inner, c, a, b, start)
        if not inner < c < a < b < start:
            print("not ABC pattern!")
            return False
    else:
        c = data_5m['high'][cross_index[0]]
        b = data_5m['low'][cross_index[1]]
        a = data_5m['high'][cross_index[2]]
        start = data_5m['low'][cross_index[3]]
        print(inner, c, a, b, start)
        if not inner > c > a > b > start:
            print("not ABC pattern!")
            return False

    # 表示
    fig = plt.figure(figsize=(10, 4))
    # ローソク足は全横幅の太さが1である。表示する足数で割ってさらにその1/3の太さにする
    width = 1.0 / env.visible_bar / 3
    # 5分足
    ax = plt.subplot(2, 2, 1)
    # y軸のオフセット表示を無効にする。
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    mpf.candlestick_ohlc(ax, data_5m.values, width=width, colorup='g', colordown='r')
    # DTOは1つ減るのでtickを合わせるため1始まり
    x_tick = [i for i in np.array(indices_5m.to_pydatetime())][1::12]
    x_tick_labels_5m = [i.strftime('%H:%M') for i in x_tick]
    ax = plt.subplot(2, 2, 3)
    ax.set(xticks=dummy_indices_5m[1::12], xticklabels=x_tick_labels_5m)
    ax.plot(dummy_indices_dto_5m, sk_5m, label="sk")
    ax.plot(dummy_indices_dto_5m, sd_5m, label="sd")
    x_tick = [i for i in np.array(dto_indices_5m.to_pydatetime())][::12]
    x_tick_labels_dto_5m = [i.strftime('%H:%M') for i in x_tick]
    ax.set(xticks=dummy_indices_dto_5m[::12], xticklabels=x_tick_labels_dto_5m)

    # 1時間足
    ax = plt.subplot(2, 2, 2)
    # y軸のオフセット表示を無効にする。
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    mpf.candlestick_ohlc(ax, data_1h.values, width=width, colorup='g', colordown='r')
    # DTOは1つ減るのでtickを合わせるため1始まり
    x_tick = [i for i in np.array(indices_1h.to_pydatetime())][1::12]
    x_tick_labels_1h = [i.strftime('%H:%M') for i in x_tick]
    ax.set(xticks=dummy_indices_1h[1::12], xticklabels=x_tick_labels_1h)
    ax = plt.subplot(2, 2, 4)
    ax.plot(dummy_indices_dto_1h, sk_1h, label="sk")
    ax.plot(dummy_indices_dto_1h, sd_1h, label="sd")
    x_tick = [i for i in np.array(dto_indices_1h.to_pydatetime())][::12]
    x_tick_labels_dto_1h = [i.strftime('%H:%M') for i in x_tick]
    ax.set(xticks=dummy_indices_dto_1h[::12], xticklabels=x_tick_labels_dto_1h)
    plt.show()
    return True


dtoEnv = FxDtoEnv()
while True:
    try:
        if show(dtoEnv):
            break
    except KeyError as e:
        print(e)
