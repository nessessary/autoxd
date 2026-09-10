#coding:utf8
"""形态识别蒸馏(route B)
用YOLO模型对当前数据现场推理产生对齐标签, 提取数值特征训练GBDT分类器,
替代 matplotlib画图+YOLO+zmq 的识别链路.

流程(train_all):
 1. 拉取各code的800根five(本地缓存), 按step滑窗画布林图
 2. 调yolov5 detect.py批量推理, 输出每张图的形态框
 3. 只保留框右边缘接近窗口末端的样本(与实盘"当前形态"语义一致),
    对应片段提取数值特征
 4. 二分类训练(u1/u2/u3->up, d1/d2/d3->down), 交叉验证+特征重要性

YOLO类别(data/autoxd-ai.yaml): ['u1','u2','u3','d1','d2','d3']
"""

import os
import re
import sys
import pickle
import subprocess
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from autoxd import agl, stock
from autoxd import warp_pytdx as tdx

g_here = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(g_here, 'cache_hq')
IMG_DIR = os.path.join(g_here, 'distill_img')
MODEL_PATH = os.path.join(g_here, 'shape_model.pkl')
PRESENCE_MODEL_PATH = os.path.join(g_here, 'shape_model_presence.pkl')

YOLO_DIR = r'I:\workc\MyWorkSource\wk\yolo\yolov5'
YOLO_WEIGHTS = os.path.join(YOLO_DIR, 'runs/train/exp8/weights/best.pt')
YOLO_NAME = 'distill_autoxd'

WIN = 100
STEP = 50              # 滑窗步长
MAX_COUNT = 800
CONF = 0.25
# 框右边缘(l+w)超过该值才算"当前形态", 与实盘只关心末端一致
RIGHT_END = 0.8
SEG_LEN = 40           # 特征片段长度(与predict一致)

FEATURE_NAMES = [
    'slope_all', 'slope_40', 'slope_20',
    'boll_poss_last', 'boll_poss_mean',
    'boll_w_last', 'boll_w_slope',
    'adx_last', 'adx_slope',
    'close_pos_in_range', 'total_chg_pct', 'volatility_20',
]
CLASS_NAMES = ['u1', 'u2', 'u3', 'd1', 'd2', 'd3']


def filter_close(h, l, middle):
    """同 get_detect_result.filter_close, 在mid上面用high, 下面用low"""
    middle = agl.arrary_fillna(middle)
    with np.errstate(invalid='ignore'):
        return np.where(h > middle, h, l)


def _slope(y):
    """归一化线性回归斜率, 无效值返回0"""
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 3 or not np.isfinite(y).any():
        return 0.
    y = agl.arrary_fillna(y)
    mean = np.abs(y).mean()
    if mean < 1e-9:
        return 0.
    return float(np.polyfit(np.arange(n), y, 1)[0] / mean)


def get_features(df):
    """df: 40根以上five片段, columns h,l,c
    return: list(float), 顺序同FEATURE_NAMES
    """
    h = df['h'].values.astype(float)
    l = df['l'].values.astype(float)
    c = df['c'].values.astype(float)

    upper, middle, lower = stock.TDX_BOLL(c)
    fc = filter_close(h, l, middle)

    boll_w = (upper - lower) / np.where(np.abs(middle) < 1e-9, 1e-9, middle)
    adx = np.asarray(stock.ADX(h, l, c), dtype=float)
    bp = np.asarray(stock.boll_poss(upper, middle, lower), dtype=float)

    rng = np.nanmax(h) - np.nanmin(l)
    close_pos = float((c[-1] - np.nanmin(l)) / rng) if rng > 1e-9 else 0.5
    chg = np.diff(c) / np.where(np.abs(c[:-1]) < 1e-9, 1e-9, c[:-1])

    feats = [
        _slope(fc),
        _slope(fc[-40:]),
        _slope(fc[-20:]),
        float(np.nan_to_num(bp[-1], nan=0.)),
        float(np.nanmean(np.nan_to_num(bp, nan=0.))),
        float(np.nan_to_num(boll_w[-1], nan=0.)),
        _slope(boll_w[-40:]),
        float(np.nan_to_num(adx[-1], nan=0.)) if len(adx) else 0.,
        _slope(adx[-40:]),
        close_pos,
        float((c[-1] / c[0] - 1) * 100) if c[0] != 0 else 0.,
        float(np.nanstd(chg[-20:])) if len(chg) >= 20 else 0.,
    ]
    return [0. if not np.isfinite(v) else v for v in feats]


def load_df(code, use_cache=True):
    """tdx数据按code缓存到本地, 避免重复拉取"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, '%s.pkl' % code)
    if use_cache and os.path.exists(cache):
        with open(cache, 'rb') as f:
            return pickle.load(f)
    df = tdx.getFive(code, MAX_COUNT)
    if use_cache and len(df) > 0:
        with open(cache, 'wb') as f:
            pickle.dump(df, f)
    return df


def gen_image(win, path):
    """画一张与原数据集一致的布林图"""
    upper, middle, lower = stock.TDX_BOLL(win['c'].values)
    fc = filter_close(win['h'].values, win['l'].values, middle)
    plt.figure(figsize=(6.4, 4.8), dpi=100)
    plt.plot(fc)
    plt.plot(upper)
    plt.plot(middle)
    plt.plot(lower)
    plt.savefig(path)
    plt.close()


def gen_images(codes, img_dir=IMG_DIR):
    """滑窗生成待推理图片, return: 生成的数量"""
    os.makedirs(img_dir, exist_ok=True)
    n = 0
    for code in codes:
        try:
            df = load_df(code)
        except Exception as e:
            print('load %s failed: %s' % (code, e))
            continue
        if len(df) < WIN:
            continue
        for i in range(0, len(df) - WIN + 1, STEP):
            win = df[i:i + WIN]
            if win['c'].iloc[-1] == 0:
                continue
            gen_image(win, os.path.join(img_dir, '%s_%d.png' % (code, i)))
            n += 1
    print('images:', n)
    return n


def run_yolo(img_dir=IMG_DIR):
    """批量推理(用兼容torch1.13的yolo_infer), return: labels目录"""
    import autoxd.live.yolo_infer  # noqa: F401  确认脚本存在
    labels_dir = os.path.join(g_here, 'distill_labels')
    cmd = [sys.executable, os.path.join(g_here, 'yolo_infer.py'),
           '--source', img_dir,
           '--weights', YOLO_WEIGHTS,
           '--out', labels_dir,
           '--conf', str(CONF)]
    print(' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise RuntimeError('yolo infer failed')
    return labels_dir


def parse_yolo_labels(labels_dir):
    """解析推理结果, return: (code, i, label, right, l, w) 列表"""
    pat = re.compile(r'^(\d{6})_(\d+)\.txt$')
    samples = []
    for fname in os.listdir(labels_dir):
        m = pat.match(fname)
        if not m:
            continue
        code, i = m.group(1), int(m.group(2))
        boxes = []
        with open(os.path.join(labels_dir, fname)) as f:
            for line in f:
                parts = line.split()
                if len(parts) < 5:
                    continue
                lab = int(parts[0])
                l_, w_ = float(parts[1]), float(parts[3])
                boxes.append((lab, l_ + w_, l_, w_))
        if not boxes:
            continue
        label, right, l_, w_ = max(boxes, key=lambda b: b[1])
        if right < RIGHT_END:
            continue
        samples.append((code, i, label, right, l_, w_))
    return samples


def build_dataset(samples):
    """特征取窗口末端SEG_LEN根(与predict对齐)
    return: X, y, groups(按code分组防泄漏), dropped"""
    X, y, groups, dropped = [], [], [], 0
    codes = sorted(set(s[0] for s in samples))
    dfs = {}
    for code in codes:
        try:
            dfs[code] = load_df(code)
        except Exception as e:
            print('load %s failed: %s' % (code, e))
    for code, i, label, right, l_, w_ in samples:
        df = dfs.get(code)
        if df is None or len(df) < i + WIN:
            dropped += 1
            continue
        win = df[i:i + WIN]
        if len(win) < WIN or win['c'].iloc[-1] == 0:
            dropped += 1
            continue
        seg = win.iloc[-SEG_LEN:]
        try:
            X.append(get_features(seg))
        except Exception:
            dropped += 1
            continue
        y.append(1 if label in (0, 1, 2) else 0)
        groups.append(code)
    return np.array(X), np.array(y), np.array(groups), dropped


def parse_presence_labels(labels_dir):
    """全部窗口是否存在右端形态框(复刻yolo触发语义: len(rcs)>0)
    return: (code, i, present) 列表"""
    pat = re.compile(r'^(\d{6})_(\d+)\.png$')
    samples = []
    for fname in os.listdir(IMG_DIR):
        m = pat.match(fname)
        if not m:
            continue
        code, i = m.group(1), int(m.group(2))
        present = 0
        fpath = os.path.join(labels_dir, '%s_%s.txt' % (code, i))
        if os.path.exists(fpath):
            with open(fpath) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    if float(parts[1]) + float(parts[3]) >= RIGHT_END:
                        present = 1
                        break
        samples.append((code, i, present))
    return samples


def build_presence_dataset(samples):
    """return: X, y, groups, dropped"""
    X, y, groups, dropped = [], [], [], 0
    codes = sorted(set(s[0] for s in samples))
    dfs = {}
    for code in codes:
        try:
            dfs[code] = load_df(code)
        except Exception as e:
            print('load %s failed: %s' % (code, e))
    for code, i, present in samples:
        df = dfs.get(code)
        if df is None or len(df) < i + WIN:
            dropped += 1
            continue
        win = df[i:i + WIN]
        if len(win) < WIN or win['c'].iloc[-1] == 0:
            dropped += 1
            continue
        seg = win.iloc[-SEG_LEN:]
        try:
            X.append(get_features(seg))
        except Exception:
            dropped += 1
            continue
        y.append(present)
        groups.append(code)
    return np.array(X), np.array(y), np.array(groups), dropped


def train_presence(X, y, groups=None):
    """训练"右端是否存在形态框"分类器, 触发阈值按yolo触发率标定"""
    from sklearn.model_selection import cross_val_score, GroupKFold
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier as Cls
        kwargs = dict(max_iter=200, learning_rate=0.1, max_depth=3,
                      random_state=1)
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier as Cls
        kwargs = dict(n_estimators=200, learning_rate=0.1, max_depth=3,
                      random_state=1)
    clf = Cls(**kwargs)
    if groups is not None:
        cv = GroupKFold(n_splits=5)
        scores = cross_val_score(clf, X, y, cv=cv, groups=groups)
    else:
        scores = cross_val_score(clf, X, y, cv=5)
    print('presence 5-fold accuracy: %.3f +- %.3f (pos_rate=%.3f)' % (
        scores.mean(), scores.std(), y.mean()))
    clf.fit(X, y)
    # 阈值取分位数, 使触发率与yolo的实际触发率一致
    probs = clf.predict_proba(X)[:, 1]
    th = float(np.quantile(probs, 1 - y.mean()))
    print('presence threshold: %.3f' % th)
    with open(PRESENCE_MODEL_PATH, 'wb') as f:
        pickle.dump({'model': clf, 'threshold': th}, f)
    print('presence model saved:', PRESENCE_MODEL_PATH)
    return clf


def train(X, y, groups=None):
    from sklearn.model_selection import cross_val_score, GroupKFold
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier as Cls
        kwargs = dict(max_iter=200, learning_rate=0.1, max_depth=3,
                      random_state=1)
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier as Cls
        kwargs = dict(n_estimators=200, learning_rate=0.1, max_depth=3,
                      random_state=1)
    clf = Cls(**kwargs)
    if groups is not None:
        # 相邻窗口片段重叠且同code数据同源, 必须按code分组防止泄漏
        cv = GroupKFold(n_splits=5)
        scores = cross_val_score(clf, X, y, cv=cv, groups=groups)
    else:
        scores = cross_val_score(clf, X, y, cv=5)
    print('5-fold accuracy: %.3f +- %.3f' % (scores.mean(), scores.std()))
    clf.fit(X, y)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)
    print('model saved:', MODEL_PATH)
    return clf


def eval_feature_importance(clf, X, y, groups=None):
    """permutation importance, 观察哪些特征在支撑判断"""
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import GroupShuffleSplit
    if groups is not None:
        tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2,
                                        random_state=1).split(X, y, groups))
    else:
        from sklearn.model_selection import train_test_split
        tr, te = train_test_split(np.arange(len(X)), test_size=0.2,
                                  random_state=1, stratify=y)
    X_tr, X_te, y_tr, y_te = X[tr], X[te], y[tr], y[te]
    clf.fit(X_tr, y_tr)
    print('holdout accuracy: %.3f' % clf.score(X_te, y_te))
    r = permutation_importance(clf, X_te, y_te, n_repeats=10, random_state=1)
    order = np.argsort(r.importances_mean)[::-1]
    for idx in order:
        print('%-20s %.4f' % (FEATURE_NAMES[idx], r.importances_mean[idx]))


def train_all(codes=None):
    if codes is None:
        codes = sorted(set(f[:6] for f in os.listdir(CACHE_DIR))) \
            if os.path.exists(CACHE_DIR) else []
    if not codes:
        raise RuntimeError('no codes; 传codes或先填充cache_hq')
    gen_images(codes)
    labels_dir = run_yolo()
    samples = parse_yolo_labels(labels_dir)
    print('samples: %d (up=%d, down=%d)' % (
        len(samples),
        sum(1 for s in samples if s[2] in (0, 1, 2)),
        sum(1 for s in samples if s[2] in (3, 4, 5))))
    X, y, groups, dropped = build_dataset(samples)
    print('dataset: %d, dropped: %d' % (len(X), dropped))
    if len(set(y)) < 2:
        print('not enough classes')
        return None
    clf = train(X, y, groups)
    eval_feature_importance(clf, X, y, groups)
    # 触发语义(有无形态)与方向分开训练, 复刻yolo的len(rcs)>0行为
    psamples = parse_presence_labels(os.path.join(g_here, 'distill_labels'))
    PX, py, pgroups, pdropped = build_presence_dataset(psamples)
    print('presence dataset: %d, dropped: %d' % (len(PX), pdropped))
    train_presence(PX, py, pgroups)
    return clf


g_model = None
g_presence = None
def predict(df):
    """复刻yolo触发语义: 右端无形态框返回None, 有则返回方向
    df: 含h,l,c的five(>=SEG_LEN根)
    return: (name, prob_up) 或 None
    """
    global g_model, g_presence
    if g_model is None:
        if not os.path.exists(MODEL_PATH):
            return None
        with open(MODEL_PATH, 'rb') as f:
            g_model = pickle.load(f)
    if g_presence is None and os.path.exists(PRESENCE_MODEL_PATH):
        with open(PRESENCE_MODEL_PATH, 'rb') as f:
            g_presence = pickle.load(f)
    if len(df) < SEG_LEN:
        return None
    x = np.array([get_features(df[-SEG_LEN:])])
    if g_presence is not None:
        # yolo: 右端无框则不触发
        pprob = float(g_presence['model'].predict_proba(x)[0][1])
        if pprob < g_presence['threshold']:
            return None
    prob = float(g_model.predict_proba(x)[0][1])
    return ('up', prob) if prob >= 0.5 else ('down', 1 - prob)


if __name__ == '__main__':
    codes = sys.argv[1:] or None
    train_all(codes)
