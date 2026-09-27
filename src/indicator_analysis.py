import csv
import pandas as pd
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

from narwhals import dtypes

ROOT = Path(__file__).resolve().parent.parent
rf_csv = ROOT / "data" / "out" / "kw_parsing.csv"
RAW_DIR = ROOT / "data" / "Data_raw"
nlp_kp_csv = ROOT / "data" / "out" / "kw_parsing_nlp.csv"
out_path = ROOT / "data" / "out" / "employment_increasement.csv"
out_shift_path = ROOT / "data" / "out" / "indicator_shift.csv"
# df = pd.read_csv(rf_csv, encoding="utf-8-sig")
#
# print(f"csv长度： {len(df)}")
#
# texts = df["命中就业增长"].fillna('')
# i = texts.str.split("、 ").explode()
# # print(i)
# i = i.str.strip()
# ind_count = i.value_counts().get("新增就业")
# print(ind_count)
# print(int(ind_count)/int(len(df)))

# text = "就业形势总体稳定,累计新增城镇就业5.24万人、再就业3.8万人,城镇登记失业率控制在4.5%以内| 有效落实就业创业扶持政策,积极开发就业岗位,全市实现新就业8522 人,城镇登记失业率为4.31%| 主要预期目标是:地区生产总值(GDP)增长6.0%—6.5%,一般公共预算收入增长3%左右,固定资产投资增长10%左右,社会消费品零售总额增长6%左右,城镇登记失业率控制在4.5%以内,城乡居民收入增长高于经济增长"
# pattern = r'(?:城镇)?(?:登记)?失业率(?:始终控制在|控制在|为|不超过|低于|约)?\s*(\d.+?%)'
# print(text)
#
# matches = re.findall(pattern, text)
# print(matches)

def extract_employment_increasement(text):
    if not isinstance(text, str) or text.strip() == '':
        return None

    text = text.strip("| ")
    pattern = r'新增(?:城镇)?就业(?:人数|人员)?(?:达到|为|超过|不低于|约)?\s*([\d.]+)\s*(万人|人)'
    matches = re.findall(pattern, text)
    if not matches:
        return None
    num_str, unit = matches[0]
    try:
        num = float(num_str)
    except ValueError:
        return None

    if unit == '万人':
        num *= 10000
    return str(int(num))

def extract_unemployment_rate(text):
    if not isinstance(text, str) or text.strip() == '':
        return None
    pattern = r'(?:城镇)?(?:登记)?失业率(?:始终控制在|控制在|为|不超过|低于|约)?\s*([\d.]+\s*%)'
    matches = re.findall(pattern, text)
    if not matches:
        return None
    num_str = matches[0]
    return num_str
    # try:
    #     num = float(num_str)
    # except ValueError:
    #     return None



def main():
    df = df = pd.read_csv(rf_csv, encoding="utf-8-sig").copy()

    # cols = df["命中就业增长"].fillna("")
    # print(f"总行数：{len(df)},新增就业出现：{cols.str.contains("新增就业").sum()}, 登记失业率出现{cols.str.contains("登记失业率").sum()}，新增就业岗位出现{cols.str.contains("新增就业岗位").sum()}")


    df["新增就业人数"] = df["命中就业增长整句"].apply(extract_employment_increasement)
    df["登记失业率"] = df["命中就业增长整句"].apply(extract_unemployment_rate)
    df["实际年份"] = df["年份"] - 1
    df = df.drop(df[df["年份"] ==2003].index)
    df = df[["城市","文件状态", "实际年份", "新增就业人数", "登记失业率"]]


    base_rows = []
    for city, sub in df.groupby("城市"):
        # print(city,sub)
        sub = sub.sort_values("实际年份")
        havevalue = sub.dropna(subset=["新增就业人数", "登记失业率"])
        if havevalue.empty:
            continue
        first = havevalue.iloc[0]
        # print(first)
        base_rows.append({"城市": city,
                          "基准年": int(first["实际年份"]),
                          "基准就业": first["新增就业人数"],
                          "基准失业率": first["登记失业率"]})
    # print(base_rows)
    base = pd.DataFrame(base_rows)
    df = df.merge(base, on="城市", how="left")
    df["新增就业人数"] = pd.to_numeric(df["新增就业人数"],errors="coerce")
    df["基准就业"] = pd.to_numeric(df["基准就业"],errors="coerce")
    not_empty = df["基准就业"].notna() & df["新增就业人数"].notna()
    df.loc[not_empty,"就业力度"] = (df.loc[not_empty, "新增就业人数"] / df.loc[not_empty, "基准就业"]).round(3)

    df["登记失业率"] = pd.to_numeric(df["登记失业率"].str.rstrip("%"),errors="coerce")
    df["基准失业率"] = pd.to_numeric(df["基准失业率"].str.rstrip("%"),errors="coerce")
    not_empty = df["基准失业率"].notna() & df["登记失业率"].notna()
    df.loc[not_empty,"失业力度"] = (df.loc[not_empty, "登记失业率"] / df.loc[not_empty, "基准失业率"]).round(3)

    # df["就业力度"] = str(int(df["新增就业人数"]) / int(df["基准就业"]))
    df["就业政策力度"] = (df["就业力度"] * 0.5 + df["失业力度"] * 0.5).round(3)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()