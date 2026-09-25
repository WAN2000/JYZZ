from zoneinfo import reset_tzpath

import chardet
import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path

SUBDIRS = ("one", "two", "three")

CSV_COLUMNS = [
    "子目录", "文件名", "城市", "年份",
    "字符数", "文件状态"
]

# 空文件阈值
EMPTY_CHARS = 100

# 文件名
NAME_PATTERN = re.compile(r"^(?P<city>.+?)_?(?P<year>(?:19|20)\d{2})$")

CITY_PATTERN = re.compile(r"(?P<city>.+?(?:省|市|自治区|自治州|县|区))")
YEAR_PATTERN = re.compile(r"(?P<year>(?:19|20)\d{2})$")

def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b-\u200f\ufeff\ue000-\uf8ff]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\u3000]+", " ", text)
    return text


def parse_name(stem):
    stem = re.sub(r"\s*\(\d+\)\s*$", "", stem.strip())    # 去掉尾部的 " (2)"（盐城市2025(2)）

    stem_city = CITY_PATTERN.match(stem)
    if stem_city:
        city = stem_city.group("city").strip("_ ")
        rest = stem[stem_city.end():]
    else:
        city = ""
        rest = stem

    stem_year = YEAR_PATTERN.search(rest)
    if not stem_year:
        return city, None

    return city, int(stem_year.group("year"))

#用utf-8读取文件
def read_text(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")

def main():
    root = Path(__file__).resolve().parent.parent      # 项目根目录(JYZZ)
    raw_dir = root / "data" / "Data_raw"
    out_path = root / "data" / "out" / "文件汇总.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # enc_count = Counter()
    # for sub in SUBDIRS:
    #     for p in (raw_dir / sub).iterdir():
    #         if p.suffix.lower() == ".txt":
    #             enc_count[chardet.detect(p.read_bytes()[:20000])["encoding"]] += 1
    #
    # print("=" * 40)
    # print("编码分布")
    # print("=" * 40)
    # enc_total = sum(enc_count.values())
    # for enc, n in enc_count.most_common():
    #     print(f"  {str(enc):<15}{n:>6} 个{n / enc_total * 100:>8.1f}%")
    # print("-" * 40)
    # print(f"  {'合计':<15}{enc_total:>6} 个")

    rows = []
    sum_files = 0
    for sub in SUBDIRS:
        folder = raw_dir / sub
        if not folder.is_dir():
            print(f"[跳过] 没有这个目录：{folder}")
            continue
        files = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".txt")
        print(f"[读取] {sub}：{len(files)} 个文件")
        sum_files += len(files)
        for path in files:
            city, year = parse_name(path.stem)
            text = normalize(read_text(path))
            n = len(text)
            rows.append({
                "子目录": sub,
                "文件名": path.name,
                "城市": city,
                "年份": year if year else "",
                "字符数": n,
                "文件状态": "空文件" if n <= EMPTY_CHARS else "正常"
            })
    print(f"[实际总数] {sum_files}  个文件")
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[写出] {out_path}")
    print(f"文件总数        : {len(rows)}")
    for sub in SUBDIRS:
        print(f"  {sub:<6}        : {sum(1 for r in rows if r['子目录'] == sub)}")
    print(f"空文件      : {sum(1 for r in rows if r['文件状态'] == '空文件')}")
    print(f"城市为空    :{sum(1 for r in rows if r['城市'] == '')}")
    print(f"年份解析失败 : {sum(1 for r in rows if r['年份'] == '')}")

# [读取] one：57 个文件
# [读取] two：6581 个文件
# [读取] three：743 个文件
# [实际总数] 7381  个文件
#
# [写出] H:\PyProject\JYZZ\data\out\文件汇总.csv
# 文件总数        : 7381
#   one           : 57
#   two           : 6581
#   three         : 743
# 空文件      : 592
# 城市为空    :57
# 年份解析失败 : 0


if __name__ == "__main__":
    main()
