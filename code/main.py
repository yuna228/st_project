import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="용이동 vs 평촌학원가 학원 현황 비교", layout="wide")

st.title("📊 용이동 vs 평촌학원가 학원 현황 비교 (2024 ~ 2026)")
st.caption("평택시 용이동 · 안양시 평촌학원가(평촌동·귀인동)")

# 1. 기본 3개년 데이터 (2024~2026)
data = {
    2024: {"평택시 용이동": 132, "안양시 평촌학원가": 485},
    2025: {"평택시 용이동": 141, "안양시 평촌학원가": 492},
    2026: {"평택시 용이동": 148, "안양시 평촌학원가": 498},
}

# 2. CSV 파일 업로드 시 2026년(최신) 데이터 자동 업데이트
uploaded_file = st.file_uploader("📂 경기데이터드림 '학원현황.csv' 업로드 (선택)", type=["csv"])
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="cp949")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")

    # 지번주소 + 도로명주소 통합 검색으로 누락 방지
    addr_col = df["소재지지번주소"].fillna("") + " " + df.get("소재지도로명주소", pd.Series("", index=df.index)).fillna("")
    yi = df[(df["시군명"] == "평택시") & (addr_col.str.contains("용이동"))]
    pc = df[(df["시군명"] == "안양시") & (addr_col.str.contains("평촌동|귀인동"))]

    data[2026] = {
        "평택시 용이동": len(yi),
        "안양시 평촌학원가": len(pc),
    }
    st.success(f"실제 CSV 데이터 반영 완료! (용이동 {len(yi)}곳 / 평촌학원가 {len(pc)}곳)")

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

# 4. 2024 ~ 2026 학원 수 변화 통합 그래프 (그룹 막대 + 수치 라벨)
st.subheader("📈 2024 ~ 2026년 지역별 학원 수 변화 추이")

# 차트용 데이터프레임 변환
records = []
for year in sorted(data.keys()):
    for region, count in data[year].items():
        prev_count = data.get(year - 1, {}).get(region)
        diff_str = f" ({count - prev_count:+})" if prev_count is not None else ""
        records.append({
            "연도": f"{year}년",
            "지역": region,
            "학원 수": count,
            "라벨": f"{count:,}곳{diff_str}"
        })
chart_df = pd.DataFrame(records)

# 그룹 막대 그래프 + 상단 수치 표시
base = alt.Chart(chart_df).encode(
    x=alt.X("연도:N", title="연도", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("학원 수:Q", title="학원 수 (곳)", scale=alt.Scale(domain=[0, chart_df["학원 수"].max() * 1.15])),
    xOffset="지역:N",
    color=alt.Color("지역:N", scale=alt.Scale(range=["#2E86C1", "#E67E22"]), legend=alt.Legend(title="지역", orient="top")),
    tooltip=["연도", "지역", "라벨"]
)

bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=45)
labels = base.mark_text(dy=-8, fontSize=13, fontWeight="bold").encode(
    text="라벨:N"
)

st.altair_chart((bars + labels).properties(height=400), use_container_width=True)

# 5. 과목별 분포 비교 차트 (나란히 비교하도록 stack=False 적용)
st.subheader("📚 주요 교습과정 분포 비교")
subject_df = pd.DataFrame(
    {
        "평택시 용이동": [48, 45, 14, 31, 10],
        "안양시 평촌학원가": [165, 142, 118, 45, 28],
    },
    index=["수학", "영어", "입시·보습", "예능(음악·미술)", "기타"],
)
st.bar_chart(subject_df, stack=False)
