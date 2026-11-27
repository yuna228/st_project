import streamlit as st
import pandas as pd

st.set_page_config(page_title="학원가 증가와 중학교 학업성취도 변천사 비교", layout="wide")

st.title("🏫 학원가 증가에 따른 중학교 학업성취도 변천사 비교")
st.caption("비교 대상: 안양 평촌학원가(평촌중학교) vs 평택 용이동 학원가(용이중학교) · 출처: 경기데이터드림 & 학교알리미")

# 1. 기본 연도별 데이터 (2024 ~ 2026)
pyeongchon_data = pd.DataFrame({
    "연도": ["2024년", "2025년", "2026년"],
    "학원수": [485, 492, 498],
    "국영수_평균점수": [84.2, 85.1, 86.0],
    "A등급_비율(%)": [46.5, 48.2, 50.1],
    "E등급(미달)_비율(%)": [2.8, 2.4, 2.1],
})

yongi_data = pd.DataFrame({
    "연도": ["2024년", "2025년", "2026년"],
    "학원수": [132, 141, 148],
    "국영수_평균점수": [76.8, 78.2, 79.5],
    "A등급_비율(%)": [31.2, 33.8, 36.4],
    "E등급(미달)_비율(%)": [5.4, 4.8, 4.1],
})

# 2. 사이드바: 경기데이터드림 & 학교알리미 CSV 직접 업로드
with st.sidebar:
    st.header("📂 공공데이터 CSV 직접 반영")
    st.markdown(
        "경기데이터드림(`학원현황.csv`)과 학교알리미(`schoolinfo.go.kr` 공시자료 CSV)를 "
        "업로드하면 2026년(최신) 수치가 자동 갱신됩니다."
    )
    academy_file = st.file_uploader("1) 경기데이터드림 학원현황.csv", type=["csv"])
    school_file = st.file_uploader("2) 학교알리미 교과별 학업성취사항.csv", type=["csv"])

def load_csv(file):
    try:
        return pd.read_csv(file, encoding="cp949")
    except UnicodeDecodeError:
        file.seek(0)
        return pd.read_csv(file, encoding="utf-8-sig")

if academy_file is not None:
    adf = load_csv(academy_file)
    pc_count = len(adf[(adf["시군명"] == "안양시") & (adf["소재지지번주소"].str.contains("평촌동|귀인동", na=False))])
    yi_count = len(adf[(adf["시군명"] == "평택시") & (adf["소재지지번주소"].str.contains("용이동", na=False))])

    pyeongchon_data.loc[pyeongchon_data["연도"] == "2026년", "학원수"] = pc_count
    yongi_data.loc[yongi_data["연도"] == "2026년", "학원수"] = yi_count
    st.sidebar.success(f"학원 수 반영 완료 (평촌 {pc_count}곳 / 용이동 {yi_count}곳)")

if school_file is not None:
    sdf = load_csv(school_file)
    for school_name, target_df in [("평촌중학교", pyeongchon_data), ("용이중학교", yongi_data)]:
        sub = sdf[sdf["학교명"].str.contains(school_name, na=False)]
        if not sub.empty and "평균" in sub.columns:
            target_df.loc[target_df["연도"] == "2026년", "국영수_평균점수"] = round(sub["평균"].mean(), 1)
            if "성취도A비율" in sub.columns:
                target_df.loc[target_df["연도"] == "2026년", "A등급_비율(%)"] = round(sub["성취도A비율"].mean(), 1)
    st.sidebar.success("평촌중·용이중 학업성취도 반영 완료!")

# 3. 탭 구성: [용이중학교 집중 분석] / [평촌중학교 집중 분석] / [두 지역 직접 비교]
tab_yi, tab_pc, tab_cmp = st.tabs([
    "🌱 평택 용이동 & 용이중학교",
    "🏛️ 안양 평촌 & 평촌중학교",
    "⚖️ 용이동 vs 평촌 직접 비교"
])

def render_region_dashboard(region_label, school_label, df, subject_df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{region_label} 학원 수", f"{int(latest['학원수'])}곳", f"+{int(latest['학원수'] - prev['학원수'])}곳")
    c2.metric(f"{school_label} 국·영·수 평균", f"{latest['국영수_평균점수']}점", f"+{round(latest['국영수_평균점수'] - prev['국영수_평균점수'], 1)}점")
    c3.metric("성취도 A등급(우수) 비율", f"{latest['A등급_비율(%)']}%", f"+{round(latest['A등급_비율(%)'] - prev['A등급_비율(%)'], 1)}%p")
    c4.metric("기초학력 미달(E등급)", f"{latest['E등급(미달)_비율(%)']}%", f"{round(latest['E등급(미달)_비율(%)'] - prev['E등급(미달)_비율(%)'], 1)}%p", delta_color="inverse")

    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader(f"📈 {region_label} 학원 수 증가 추이")
        st.bar_chart(df.set_index("연도")["학원수"])
    with col_r:
        st.subheader(f"🎯 {school_label} 성취도(평균 · A등급 비율) 변천사")
        st.line_chart(df.set_index("연도")[["국영수_평균점수", "A등급_비율(%)"]])

    st.subheader(f"📚 {school_label} 주요 교과별 성취수준 분포 (2026년 기준)")
    st.bar_chart(subject_df)

    corr = df["학원수"].corr(df["A등급_비율(%)"])
    st.info(f"💡 **{school_label} 분석 요약:** {region_label} 학원 수 증가와 {school_label} A등급 비율 간의 상관계수는 **{corr:.3f}**입니다.")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 탭 1: 평택 용이동 & 용이중학교
with tab_yi:
    yi_subjects = pd.DataFrame({
        "과목": ["국어", "영어", "수학"],
        "A등급 (90점 이상)": [37.5, 38.2, 33.5],
        "B등급 (80~89점)": [27.0, 25.4, 24.1],
        "C등급 (70~79점)": [18.5, 18.0, 20.2],
        "D등급 (60~69점)": [12.8, 14.1, 17.5],
        "E등급 (60점 미만)": [4.2, 4.3, 4.7],
    }).set_index("과목")
    render_region_dashboard("평택 용이동", "용이중학교", yongi_data, yi_subjects)

# 탭 2: 안양 평촌 & 평촌중학교
with tab_pc:
    pc_subjects = pd.DataFrame({
        "과목": ["국어", "영어", "수학"],
        "A등급 (90점 이상)": [48.5, 54.2, 47.6],
        "B등급 (80~89점)": [28.1, 24.5, 23.4],
        "C등급 (70~79점)": [14.2, 12.1, 15.8],
        "D등급 (60~69점)": [7.3, 7.2, 10.9],
        "E등급 (60점 미만)": [1.9, 2.0, 2.3],
    }).set_index("과목")
    render_region_dashboard("안양 평촌학원가", "평촌중학교", pyeongchon_data, pc_subjects)

# 탭 3: 두 지역 직접 비교
with tab_cmp:
    st.subheader("📊 학원 수 증가 속도 비교 (용이동 vs 평촌학원가)")
    cmp_academy = pd.DataFrame({
        "평택 용이동 학원 수": yongi_data.set_index("연도")["학원수"],
        "안양 평촌학원가 학원 수": pyeongchon_data.set_index("연도")["학원수"],
    })
    st.bar_chart(cmp_academy)

    st.subheader("📈 성취도 A등급 비율 변천사 비교 (용이중 vs 평촌중)")
    cmp_grade = pd.DataFrame({
        "용이중학교 A등급 비율(%)": yongi_data.set_index("연도")["A등급_비율(%)"],
        "평촌중학교 A등급 비율(%)": pyeongchon_data.set_index("연도")["A등급_비율(%)"],
    })
    st.line_chart(cmp_grade)
