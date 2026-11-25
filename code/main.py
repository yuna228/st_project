
import os
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="용이동 vs 평촌학원가 학원·학교 상관관계 분석", layout="wide")

st.title("📊 학원 현황 × 학교알리미 공시자료 상관관계 분석")
st.caption("경기데이터드림 학원현황 + 학교알리미(schoolinfo.go.kr) 공시데이터 결합 분석")


def load_csv(file_source):
    for enc in ("cp949", "utf-8-sig", "euc-kr"):
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            return pd.read_csv(file_source, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 인코딩을 읽을 수 없습니다.")


# 1. 데이터 파일 업로드 영역
col_u1, col_u2 = st.columns(2)
with col_u1:
    academy_file = st.file_uploader(
        "1️⃣ 경기데이터드림 '학원현황.csv' 업로드", type=["csv"], key="academy"
    )
with col_u2:
    school_file = st.file_uploader(
        "2️⃣ 학교알리미 '공시자료.csv' 업로드 (예: 학생현황, 졸업생 진로현황)", type=["csv"], key="school"
    )

# 기본 학원현황 파일 로드
DEFAULT_CSV = "학원현황 (1).csv"
if academy_file is not None:
    df_academy = load_csv(academy_file)
elif os.path.exists(DEFAULT_CSV):
    df_academy = load_csv(DEFAULT_CSV)
else:
    st.warning("경기데이터드림 '학원현황.csv' 파일을 먼저 업로드해 주세요.")
    st.stop()

# 2. 학원 데이터 시군구·행정동별 집계
# 시군명 + 구/읍면동명(또는 주소에서 추출한 법정동) 기준 학원 수 집계
df_academy["법정동"] = (
    df_academy["소재지지번주소"]
    .fillna("")
    .str.extract(r"([가-힣0-9]+(?:동|읍|면))")[0]
    .fillna(df_academy["구/읍면동명"].fillna("미상"))
)
df_academy["지역키"] = df_academy["시군명"].fillna("") + " " + df_academy["법정동"]

academy_counts = (
    df_academy.groupby(["시군명", "법정동", "지역키"], as_index=False)
    .size()
    .rename(columns={"size": "학원수"})
)

st.subheader("1. 지역별 학원 수 집계 미리보기 (상위 10개 지역)")
st.dataframe(academy_counts.sort_values("학원수", ascending=False).head(10), use_container_width=True)

# 3. 학교알리미 공시자료와 결합하여 상관관계 분석
st.subheader("2. 학교알리미 공시지표와의 상관관계 분석")

if school_file is None:
    st.info(
        "학교알리미(schoolinfo.go.kr → 공시자료 다운로드)에서 내려받은 CSV 파일을 위 **2️⃣번 업로더**에 올리면 "
        "지역별 학원 수와 학교 지표(학생 수, 학급당 학생 수, 특목고 진학률 등) 간의 상관계수와 산점도가 자동 생성됩니다."
    )
else:
    df_school = load_csv(school_file)

    # 학교알리미 데이터에서 주소/지역 컬럼과 수치형 지표 컬럼 자동 탐지
    addr_candidates = [c for c in df_school.columns if any(k in c for k in ["주소", "소재지", "시군", "지역"])]
    num_cols = df_school.select_dtypes(include="number").columns.tolist()

    if not addr_candidates or not num_cols:
        st.error("학교알리미 CSV에서 주소 컬럼 또는 수치형 지표 컬럼을 찾지 못했습니다.")
        st.write("감지된 컬럼 목록:", df_school.columns.tolist())
        st.stop()

    sel_col1, sel_col2, sel_col3 = st.columns(3)
    with sel_col1:
        addr_col_name = st.selectbox("학교 주소 컬럼 선택", addr_candidates)
    with sel_col2:
        metric_col = st.selectbox("비교할 학교알리미 수치 지표 선택", num_cols)
    with sel_col3:
        agg_method = st.selectbox("동별 집계 방식", ["합계 (예: 총 학생 수)", "평균 (예: 학급당 학생 수·비율)"])

    # 학교 주소에서 '시군 + 동/읍/면' 추출하여 지역키 생성
    s_city = df_school[addr_col_name].fillna("").str.extract(r"([가-힣]+(?:시|군))")[0].fillna("")
    s_dong = df_school[addr_col_name].fillna("").str.extract(r"([가-힣0-9]+(?:동|읍|면))")[0].fillna("")
    df_school["지역키"] = (s_city + " " + s_dong).str.strip()

    if agg_method.startswith("합계"):
        school_grouped = df_school.groupby("지역키", as_index=False)[metric_col].sum()
    else:
        school_grouped = df_school.groupby("지역키", as_index=False)[metric_col].mean()

    # 학원 수 데이터와 학교알리미 데이터 병합
    merged = pd.merge(academy_counts, school_grouped, on="지역키", how="inner").dropna()

    # 특정 시군 필터 옵션 (전체 경기도 vs 평택시·안양시 비교)
    city_filter = st.multiselect(
        "분석 대상 시군 필터 (비워두면 경기도 전체 동 기준 분석)",
        options=sorted(merged["시군명"].unique()),
        default=[c for c in ["평택시", "안양시"] if c in merged["시군명"].unique()],
    )
    if city_filter:
        merged = merged[merged["시군명"].isin(city_filter)]

    if len(merged) < 3:
        st.warning("상관관계 계산을 위해 최소 3개 이상의 매칭된 지역(동) 데이터가 필요합니다. 시군 필터를 넓혀보세요.")
    else:
        # 피어슨 상관계수 계산
        corr = merged["학원수"].corr(merged[metric_col])

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("분석 대상 행정동 수", f"{len(merged):,}개 지역")
        m_col2.metric(f"피어슨 상관계수 (r)", f"{corr:.3f}")

        if abs(corr) >= 0.7:
            strength = "강한 상관관계"
        elif abs(corr) >= 0.4:
            strength = "뚜렷한 양/음의 상관관계"
        elif abs(corr) >= 0.2:
            strength = "약한 상관관계"
        else:
            strength = "상관관계 거의 없음"
        m_col3.metric("해석", strength)

        # 산점도 + 회귀 추세선 시각화
        scatter = (
            alt.Chart(merged)
            .mark_circle(size=85, opacity=0.8)
            .encode(
                x=alt.X(f"{metric_col}:Q", title=metric_col),
                y=alt.Y("학원수:Q", title="학원 수 (곳)"),
                color=alt.Color("시군명:N", legend=alt.Legend(title="시군명")),
                tooltip=["지역키", "학원수", alt.Tooltip(f"{metric_col}:Q", format=",.2f")],
            )
        )
        reg_line = scatter.transform_regression(metric_col, "학원수").mark_line(color="#E74C3C", strokeDash=[5, 5])

        st.altair_chart((scatter + reg_line).properties(height=420), use_container_width=True)

        with st.expander("📋 지역별 병합 원본 데이터 확인"):
            st.dataframe(merged.sort_values("학원수", ascending=False), use_container_width=True)
