import streamlit as st
import pandas as pd

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

    yi = df[(df["시군명"] == "평택시") & (df["소재지지번주소"].str.contains("용이동", na=False))]
    pc = df[(df["시군명"] == "안양시") & (df["소재지지번주소"].str.contains("평촌동|귀인동", na=False))]

    data[2026] = {
        "평택시 용이동": len(yi),
        "안양시 평촌학원가": len(pc),
    }
    st.success(f"실제 CSV 데이터 반영 완료! (용이동 {len(yi)}곳 / 평촌학원가 {len(pc)}곳)")

# 3. 연도 선택 및 KPI 카드 출력
year = st.radio("연도 선택", [2024, 2025, 2026], index=2, horizontal=True)
curr = data[year]
prev = data.get(year - 1)

col1, col2 = st.columns(2)
col1.metric("평택시 용이동", f"{curr['평택시 용이동']:,}곳", f"{curr['평택시 용이동'] - prev['평택시 용이동']:+}곳" if prev else "기준 연도")
col2.metric("안양시 평촌학원가", f"{curr['안양시 평촌학원가']:,}곳", f"{curr['안양시 평촌학원가'] - prev['안양시 평촌학원가']:+}곳" if prev else "기준 연도")

# 4. 3개년 추이 차트 (용이동 vs 평촌학원가)
st.subheader("📈 용이동 vs 평촌학원가 3개년 학원 수 추이")
trend_df = pd.DataFrame(data).T
trend_df.index = [f"{y}년" for y in trend_df.index]
st.line_chart(trend_df)

# 5. 과목별 분포 비교 차트
st.subheader("📚 주요 교습과정 분포 비교")
subject_df = pd.DataFrame(
    {
        "평택시 용이동": [48, 45, 14, 31, 10],
        "안양시 평촌학원가": [165, 142, 118, 45, 28],
    },
    index=["수학", "영어", "입시·보습", "예능(음악·미술)", "기타"],
)
st.bar_chart(subject_df)
