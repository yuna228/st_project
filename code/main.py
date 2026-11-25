import os
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="용이동 vs 평촌학원가 학원 현황 비교", layout="wide")

st.title("📊 용이동 vs 평촌학원가 학원 현황 비교 (2024 ~ 2026)")
st.caption("평택시 용이동 · 안양시 평촌학원가(평촌동·귀인동)")

# 1. 기본 3개년 데이터 (2024~2026)
data = {
    2024: {"평택시 용이동": 96, "안양시 평촌학원가": 392},
    2025: {"평택시 용이동": 102, "안양시 평촌학원가": 398},
    2026: {"평택시 용이동": 107, "안양시 평촌학원가": 404},
}


def load_csv(file_source):
    try:
        return pd.read_csv(file_source, encoding="cp949")
    except UnicodeDecodeError:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        return pd.read_csv(file_source, encoding="utf-8-sig")


def categorize_subject(val):
    if pd.isna(val):
        return "기타"
    s = str(val)
    if "입시" in s or "보습" in s:
        return "입시·보습"
    if "보통교과" in s:
        return "보통교과"
    if "예능" in s:
        return "예능(음악·미술)"
    if "국제화" in s or "외국어" in s:
        return "국제화·외국어"
    return "독서실·종합·기타"


# 2. 업로드 파일 또는 동일 폴더의 '학원현황 (1).csv' 자동 로드
DEFAULT_CSV = "학원현황 (1).csv"
uploaded_file = st.file_uploader("📂 경기데이터드림 '학원현황.csv' 업로드 (미업로드 시 기본 CSV 자동 적용)", type=["csv"])

df = None
if uploaded_file is not None:
    df = load_csv(uploaded_file)
elif os.path.exists(DEFAULT_CSV):
    df = load_csv(DEFAULT_CSV)

subject_df = pd.DataFrame(
    {
        "평택시 용이동": [46, 7, 29, 16, 9],
        "안양시 평촌학원가": [139, 131, 82, 26, 26],
    },
    index=["입시·보습", "보통교과", "예능(음악·미술)", "국제화·외국어", "독서실·종합·기타"],
)

if df is not None:
    # 지번주소 + 도로명주소 통합 검색 (안양시는 구/읍면동명이 '동안구'로 되어 있어 주소 검색 필수)
    addr_col = (
        df["소재지지번주소"].fillna("")
        + " "
        + df.get("소재지도로명주소", pd.Series("", index=df.index)).fillna("")
    )
    yi = df[(df["시군명"] == "평택시") & (addr_col.str.contains("용이동"))]
    pc = df[(df["시군명"] == "안양시") & (addr_col.str.contains("평촌동|귀인동"))]

    data[2026] = {
        "평택시 용이동": len(yi),
        "안양시 평촌학원가": len(pc),
    }

    # 교습과정명 실제 데이터 집계
    categories = ["입시·보습", "보통교과", "예능(음악·미술)", "국제화·외국어", "독서실·종합·기타"]
    yi_subj = yi["교습과정명"].apply(categorize_subject).value_counts().reindex(categories, fill_value=0)
    pc_subj = pc["교습과정명"].apply(categorize_subject).value_counts().reindex(categories, fill_value=0)

    subject_df = pd.DataFrame(
        {
            "평택시 용이동": yi_subj,
            "안양시 평촌학원가": pc_subj,
        }
    )
    st.success(f"실제 CSV 데이터 반영 완료! (용이동 {len(yi):,}곳 / 평촌학원가 {len(pc):,}곳)")

# 3. 3개년 변화 요약 KPI 카드 (2024 -> 2026 누적 변화)
col1, col2 = st.columns(2)
yi_diff = data[2026]["평택시 용이동"] - data[2024]["평택시 용이동"]
pc_diff = data[2026]["안양시 평촌학원가"] - data[2024]["안양시 평촌학원가"]

col1.metric(
    "평택시 용이동 (2026년 기준)",
    f"{data[2026]['평택시 용이동']:,}곳",
    f"2024년 대비 {yi_diff:+}곳 ({yi_diff / data[2024]['평택시 용이동'] * 100:+.1f}%)",
)
col2.metric(
    "안양시 평촌학원가 (2026년 기준)",
    f"{data[2026]['안양시 평촌학원가']:,}곳",
    f"2024년 대비 {pc_diff:+}곳 ({pc_diff / data[2024]['안양시 평촌학원가'] * 100:+.1f}%)",
)

# 4. 2024 ~ 2026 학원 수 변화 통합 그래프 (그룹 막대 + 수치/증감 라벨)
st.subheader("📈 2024 ~ 2026년 지역별 학원 수 변화 추이")

records = []
for year in sorted(data.keys()):
    for region, count in data[year].items():
        prev_count = data.get(year - 1, {}).get(region)
        diff_str = f" ({count - prev_count:+})" if prev_count is not None else ""
        records.append(
            {
                "연도": f"{year}년",
                "지역": region,
                "학원 수": count,
                "라벨": f"{count:,}곳{diff_str}",
            }
        )
chart_df = pd.DataFrame(records)

base = alt.Chart(chart_df).encode(
    x=alt.X("연도:N", title="연도", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("학원 수:Q", title="학원 수 (곳)", scale=alt.Scale(domain=[0, chart_df["학원 수"].max() * 1.15])),
    xOffset="지역:N",
    color=alt.Color(
        "지역:N",
        scale=alt.Scale(range=["#2E86C1", "#E67E22"]),
        legend=alt.Legend(title="지역", orient="top"),
    ),
    tooltip=["연도", "지역", "라벨"],
)

bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=45)
labels = base.mark_text(dy=-8, fontSize=13, fontWeight="bold").encode(text="라벨:N")

st.altair_chart((bars + labels).properties(height=400), use_container_width=True)

# 5. 과목별 분포 비교 차트 및 상세 표 (CSV 실제 교습과정명 반영)
st.subheader("📚 주요 교습과정 분포 비교 (2026년 CSV 기준)")
st.bar_chart(subject_df, stack=False)

with st.expander("📋 과목별 학원 수 및 비중(%) 상세 보기", expanded=True):
    summary_table = subject_df.copy()
    summary_table["용이동 비중(%)"] = (summary_table["평택시 용이동"] / summary_table["평택시 용이동"].sum() * 100).round(1)
    summary_table["평촌 비중(%)"] = (summary_table["안양시 평촌학원가"] / summary_table["안양시 평촌학원가"].sum() * 100).round(1)
    st.dataframe(summary_table, use_container_width=True)
