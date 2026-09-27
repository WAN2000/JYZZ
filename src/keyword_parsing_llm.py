import csv
import pandas as pd
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

from scan_file import read_text, normalize

from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-dpdmqghciolvcayivsaolojojruynlnuzqzanyibatgjrgay",
    base_url="https://api.siliconflow.cn/v1"
)
MODEL = "Qwen/Qwen3-8B"

path_csv = Path(__file__).resolve().parent.parent/"data"/"out"/"文件汇总.csv"

if not path_csv.exists():
    raise FileNotFoundError(f"找不到文件: {path_csv}")
with open(path_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
df = pd.read_csv(path_csv)
# print(df.head().to_string())


CITIES = [
    "石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市",
    "衡水市", "太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市",
    "吕梁市",
    "呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市",
    "沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市",
    "铁岭市", "朝阳市", "葫芦岛市", "长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市",
    "哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市",
    "牡丹江市", "黑河市", "绥化市", "南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市",
    "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市", "杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市",
    "金华市",
    "衢州市", "舟山市", "台州市", "丽水市", "合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市",
    "安庆市", "黄山市", "阜阳市", "宿州市",
    "滁州市", "六安市", "宣城市", "池州市", "亳州市", "福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市",
    "南平市", "龙岩市", "宁德市",
    "南昌市", "景德镇市", "萍乡市", "九江市", "抚州市", "鹰潭市", "赣州市", "吉安市", "宜春市", "新余市", "上饶市",
    "济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市",
    "临沂市", "德州市", "聊城市", "滨州市", "菏泽市", "郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市",
    "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市",
    "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市", "武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市",
    "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市",
    "随州市", "长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市",
    "永州市",
    "怀化市", "娄底市", "广州市", "深圳市", "珠海市", "汕头市", "佛山市", "韶关市", "湛江市", "肇庆市", "江门市",
    "茂名市", "惠州市",
    "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市",
    "南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市",
    "河池市", "来宾市", "崇左市", "海口市", "三亚市", "三沙市", "儋州市",
    "成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市",
    "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市",
    "贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市",
    "昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市",
    "拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市",
    "西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市",
    "兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市",
    "陇南市", "西宁市", "海东市", "银川市", "石嘴山市", "吴忠市", "固原市", "中卫市", "乌鲁木齐市", "克拉玛依市",
    "吐鲁番市", "哈密市"
]

KEYWORDS_1 = ["城镇新增就业岗位", "城镇居民登记失业率","城镇新增就业", "城镇登记失业率", "城镇调查失业率","新增城镇就业", "新增就业岗位", "新增就业","登记失业率", "调查失业率",]
KEYWORDS_2 = ["就业补贴", "社保补贴", "就业培训", "职业技能培训", "职业培训", "创业担保贷款", "公益性岗位", "就业援助", "就业服务", "就业创业", "灵活就业", "零就业家庭", "就业困难人员"]

def split_chapter(text):
    m_start = re.search(
        r'(?:工作回顾|过去.{0,6}(?:工作|发展|成绩)|回顾.{0,6})',
        text
    )

    if not m_start:
        return text
    rest = text[m_start.end():]
    m_end = re.search(r'\n\s*[二三四五六七八九十]+[、.．]', rest)
    if m_end:
        return rest[:m_end.start()]
    return rest

def extract_hits(text, keywords):
    text = normalize(text)
    text = split_chapter(text)
    sentences = [s.strip() for s in re.split(r"[。！？；\n]+", text) if s.strip()]
    if not sentences:
        return []
    kw_str = "、".join(keywords)
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))
    prompt = f"""你是政府工作报告文本分析助手。请阅读下面编号的句子，以下句子来自政府工作报告的"工作回顾"部分。
                请找出与下列关键词高度相关的句子（含义等价即可，不必原样出现）：
                关键词：{kw_str}
                
                注意：如果个别句子实际是描述"今年计划 / 未来目标"（例如含"将、力争、目标、预期、确保、计划、努力培育"等），请排除，不要保留。
                
                请只输出一个JSON 数组,每个元素必须同时包含id,keywords,sentence三个字段，：
                [{{"sent_id": 12, "keywords": ["命中关键词1"], "sentence": "该句的完整原文"}}, ...]
                要求：
                - sent_id 是句子列表里的编号（从 1 开始）
                - keywords 必须是给定关键词列表中的词
                - sentence 是字符串（原句原文），必须原文照抄，不要做更改
                - 只输出 JSON，不要作任何解释
                - 不要用 markdown
                
                句子列表：
                {numbered}"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是一个有用的助手"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()

        content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.M).strip()
        data = json.loads(content)
        print("data： ",data)
    except Exception as e:
        print(f"[LLM] 调用失败: {e}")
        return []
    hits = []
    for item in data:
        sid = item.get("sent_id")
        kws = [k for k in (item.get("keywords") or []) if k in keywords]
        llm_sent = item.get("sentence", "")

        if not kws:
            continue
        if not isinstance(sid, int) or not (1 <= sid <= len(sentences)):
            continue

        local_sent = sentences[sid - 1]
        hits.append((kws, local_sent))
    return hits

def add_hits(df,keywords,suffix):
    start_time = time.time()
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "Data_raw"

    kw_col = []
    stc_col = []

    for _, row in df.iterrows():
        print(f"处理{row["文件名"]}的关键词")
        fp = raw_dir / row["子目录"] / row["文件名"]
        if not fp.exists():
            kw_col.append("")
            stc_col.append("")
            continue

        hits = extract_hits(read_text(fp), keywords)
        if hits:
            all_kws = sorted({k for ks,_ in hits for k in ks})
            kw_col.append("、 ".join(all_kws))
            stc_col.append("| ".join(h for _,h in hits))
        else:
            kw_col.append("")
            stc_col.append("")


    df[f"命中{suffix}"] = kw_col
    df[f"命中{suffix}整句"] = stc_col
    line_hit = f"命中{suffix}"
    end_time = time.time()
    process_time = end_time - start_time
    print(f"解析关键词 {suffix}")
    print(f"花费时间： {process_time:.2f} s")
    print(f"关键词命中行数: {(df[line_hit]!="").sum()}")
    return df


def build_csv_rf():
    df_cities = df[df["城市"].isin(CITIES)]
    print(f"地级市数量： {len(df_cities)}")
    df_two = df[df["子目录"] == "two"]
    print(f"two文件夹数量： {len(df_two)}")
    df_both = pd.concat([df_cities, df_two])
    # print(len(df_both))
    df_cha = df_both.drop_duplicates(keep=False)
    print(f"差集数量： {len(df_cha)}")
    out_path_cha = Path(__file__).resolve().parent.parent / "data" / "out" / "差值.csv"
    df_cha.to_csv(out_path_cha, index=False, encoding="utf-8-sig")

    out_path = Path(__file__).resolve().parent.parent / "data" / "out" / "粗筛.csv"
    df_intersected = df_cities.merge(df_two, how="inner")
    return df_intersected

def main():
    rf_path = Path(__file__).resolve().parent.parent / "data" / "out" / "粗筛.csv"
    out_path = Path(__file__).resolve().parent.parent / "data" / "out" / "kw_parsing_llm.csv"
    if not rf_path.exists():
        print(f"初筛文件未找到： {rf_path}")
        df_rf = build_csv_rf()
        df_rf.to_csv(rf_path, index=False, encoding="utf-8-sig")

    else:
        print(f"初筛文件找到，进行关键词匹配")
        df = pd.read_csv(rf_path, encoding="utf-8-sig")
        df = add_hits(df,KEYWORDS_1,"就业增长")
        df = add_hits(df,KEYWORDS_2,"就业力度")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")


# 初筛文件找到，进行关键词匹配
# 处理七台河市2003.txt的关键词
# 处理七台河市2004.txt的关键词
# 处理七台河市2005.txt的关键词
# 处理七台河市2006.txt的关键词
# 处理七台河市2007.txt的关键词
# data：  [{'sent_id': 46, 'keywords': ['城镇新增就业', '城镇登记失业率'], 'sentence': '四年实现新就业6.3万人,城镇登记失业率低于省控指标0.9个百分点,受到省和国家的表彰'}]
# 处理七台河市2008.txt的关键词
# data：  [{'sent_id': 68, 'keywords': ['新增就业'], 'sentence': '为下岗失业人员减免税费、发放小额贷款2389 万元,兑现灵活就业人员社保补贴1355 万元,新增就业1.3 万人'}]
# 处理七台河市2009.txt的关键词
# data：  [{'sent_id': 68, 'keywords': ['新增就业'], 'sentence': '为下岗失业人员减免税费、发放小额贷款2389 万元,兑现灵活就业人员社保补贴1355 万元,新增就业1.3 万人'}]
# 处理七台河市2010.txt的关键词
# data：  [{'sent_id': 52, 'keywords': ['城镇登记失业率', '新增就业岗位'], 'sentence': '千方百计扩大就业,实施零就业家庭专项援助和促进返乡农民工就业专项行动,城镇登记失业率低于省控指标1.2个百分点'}]
# 处理七台河市2011.txt的关键词
# data：  [{'sent_id': 123, 'keywords': ['城镇登记失业率'], 'sentence': '开发公益性岗位安置困难群体就业1370人，城镇登记失业率低于省控指标1.2个百分点'}]
# 处理七台河市2012.txt的关键词
# data：  [{'sent_id': 12, 'keywords': ['城镇登记失业率'], 'sentence': '有入住要求的农村五保户和城镇“三无”人员全部实现集中供养,“五险”参保范围进一步扩大,社保标准进一步提高,教育、卫生等社会事业全面进步,高标准完成采煤沉陷区综合治理工程,“两棚一草”改造扎实推进,廉租房、经济适用房、公租房超额完成省政府下达任务'}, {'sent_id': 70, 'keywords': ['城镇居民登记失业率'], 'sentence': '坚持财政资金优先向民生领域倾斜,七项民生工程、20件实事全面落实,城镇居民人均可支配收入实现16500元,增长10%;农民人均纯收入8241元,增长18.5%'}, {'sent_id': 74, 'keywords': ['新增城镇就业'], 'sentence': '新建廉租房2124套、公共租赁房1456套、经济适用住房200套,新增廉租住房租赁补贴家庭2715户'}, {'sent_id': 75, 'keywords': ['新增就业岗位'], 'sentence': '改造农村泥草房7254户、危房409户'}, {'sent_id': 77, 'keywords': ['登记失业率'], 'sentence': '失业保险实现市级统筹,支付标准月提高125元;城乡低保补助标准月提高28元,城乡低保人均财政补助标准月提高20元;廉租住房租赁补贴标准由月均60-100元上调至90-150元;城乡居民医保财政补助水平提高80元,人均基本公共卫生服务经费提高10元,新农合筹资标准提高80元,市内三级定点医保资金实现预付制和住院医保患者即结即报制,城乡医保住院报销比例提高5%'}]
# 处理七台河市2013.txt的关键词
# data：  [{'sent_id': 41, 'keywords': ['新增就业', '城镇登记失业率'], 'sentence': '新增就业1.3 万人,城镇登记失业率低于省控指标'}]
# 处理七台河市2014.txt的关键词
# data：  [{'sent_id': 35, 'keywords': ['新增就业'], 'sentence': '加大就业帮扶力度,新增就业1.2 万人,再就业8509 人'}]
# 处理七台河市2015.txt的关键词
# data：  [{'sent_id': 13, 'keywords': ['城镇新增就业', '城镇登记失业率'], 'sentence': '全年新增就业8965人,城镇登记失业率4.13%'}]
# 处理七台河市2016.txt的关键词
# data：  [{'sent_id': 23, 'keywords': ['新增就业岗位', '新增就业'], 'sentence': '大力推动创业就业,为643人发放小额贷款3215万元,新增就业7400人;积极帮助七矿公司解困发展,落实帮扶资金2.2亿元,已安置和正在落实安置富余人员2348人'}]

# [读取] two：6581 个文件
if __name__ == "__main__":
    main()