import csv
import pandas as pd
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import jionlp as jio
import jiojio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from scan_file import read_text, normalize

ROOT = Path(__file__).resolve().parent.parent
rf_csv = ROOT / "data" / "out" / "kw_parsing.csv"
RAW_DIR = ROOT / "data" / "Data_raw"
nlp_kp_csv = ROOT / "data" / "out" / "kw_parsing_nlp.csv"

KEYWORDS_1 = ["城镇新增就业岗位", "城镇居民登记失业率", "城镇新增就业", "城镇登记失业率", "城镇调查失业率", "新增城镇就业", "新增就业岗位", "新增就业", "登记失业率", "调查失业率"]
KEYWORDS_2 = ["就业补贴", "社保补贴", "就业培训", "职业技能培训", "职业培训", "创业担保贷款", "公益性岗位", "就业援助", "就业服务", "就业创业", "灵活就业", "零就业家庭", "就业困难人员"]

SENT_SPLIT = re.compile(r"[。！？；\n]+")

QUERY_1 = " ".join(KEYWORDS_1)
QUERY_2 = " ".join(KEYWORDS_2)

THRESHOLD = 0.15
jiojio.init()

def load_text(row):
    fp = RAW_DIR / row["子目录"] / row["文件名"]
    if not fp.exists():
        return ""
    text = normalize(read_text(fp))
    text = jio.clean_text(text)
    return text

def jiojio_tokenize(text):
    if not text.strip():
        return []
    return [w for w in jiojio.cut(text) if len(w) >= 2]

def split_sentences(text, query, threshold):
    sentences = [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]
    if not sentences:
        return ""

    corpus = sentences + [query]
    vec = TfidfVectorizer(
        tokenizer=jiojio_tokenize,
        token_pattern=None,
        lowercase=False,
    )
    matrix = vec.fit_transform(corpus)
    sims = cosine_similarity(matrix[:-1], matrix[-1]).ravel()

    hits = [s for s, score in zip(sentences, sims) if score >= threshold]
    return " || ".join(hits)

def main():
    df = pd.read_csv(rf_csv, encoding="utf-8-sig")

    kw1_col, kw2_col = [], []
    for i, row in df.iterrows():
        text = load_text(row)
        kw1_col.append(split_sentences(text, QUERY_1, THRESHOLD))
        kw2_col.append(split_sentences(text, QUERY_2, THRESHOLD))
        if (i + 1) % 500 == 0:
            print(f"已处理 {i + 1}/{len(df)}")

    df["就业增长句子"] = kw1_col
    df["就业政策句子"] = kw2_col

    df.to_csv(nlp_kp_csv, index=False, encoding="utf-8-sig")
    print(f"写出 {nlp_kp_csv}")
    print(f"就业增长命中：{(df['就业增长句子'] != '').sum()} 个文件")
    print(f"就业政策命中：{(df['就业政策句子'] != '').sum()} 个文件")

if __name__ == "__main__":
    main()