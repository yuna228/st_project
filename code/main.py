import streamlit as st
import pandas as pd
import altair as alt

# 1. 페이지 설정
st.set_page_config(page_title="학원가 인프라와 중학교 학업성취도 상관분석", layout="wide")

st.title("🏫 학원가 수 변화에 따른 중학교 학업성취도 변천사 분석")
st.markdown("**팀 질문(Research Question):** *“지역 내 사설학원 수가 증가하면 인근 중학교의 학업성취도(평균 점수 및 A등급 비율)도 비례하여 상승하는가?”*")
st.caption("비교 대상: 안양시 평촌학원가(평촌중학교) vs 평택시 용이동(용이중학교) | 출처: 경기데이터드림 & 학교알리미")

# ---------------------------------------------------------
# 2. 원본 데이터 구성 (결측치/이상치 포함) 및 전처리
# ---------------------------------------------------------
raw_data = pd.DataFrame({
    "지역": ["안양 평촌", "안양 평촌", "안양 평촌", "평택 용이동", "평택 용이동", "평택 용이동", "평택 용이동(오류행)", "안양 평촌(이상치행)"],
    "학교명": ["평촌중학교", "평촌중학교", "평촌중학교", "용이중학교", "용이중학교", "용이중학교", None, "평촌중학교"],
    "연도": [2024, 2025, 2026, 2024, 2025, 2026, 2025, 2026],
    "학원수": [485, 492, 498, 132, 141, 148, None, 9999],
    "국영수_평균점수": [84.2, 85.1, 86.0, 76.8, 78.2, 79.5, 77.0, 150.0],
    "A등급_비율(%)": [46.5, 48.2, 50.1, 31.2, 33.8, 36.4, None, 52.0],
    "E등급_비율(%)": [2.8, 2.4, 2.1, 5.4, 4.8, 4.1, 4.5, 2.0],
})

# 사이드바: 경기데이터드림 & 학교알리미 CSV 직접 반영
with st.sidebar:
    st.header("📂 공공데이터 CSV 직접 반영")
    st.caption("경기데이터드림(`학원현황.csv`)과 학교알리미(`교과별 학업성취사항.csv`)를 업로드하면 2026년 수치가 자동 갱신됩니다.")
    academy_file = st.file_uploader("1) 경기데이터드림 학원현황.csv", type=["csv"])
    school_file = st.file_uploader("2) 학교알리미 교과별 학업성취사항.csv", type=["csv"])

def load_csv(file):
    try:
        return pd.read_csv(file, encoding="cp949")
    except UnicodeDecodeError:
        file.seek(0)
        return pd.read_csv(file, encoding="utf-8-sig")

if academy_file is not None:
    try:
        adf = load_csv(academy_file)
        if "시군명" in adf.columns and "소재지지번주소" in adf.columns:
            addr_col = adf["소재지지번주소"].fillna("") + " " + adf.get("소재지도로명주소", pd.Series("", index=adf.index)).fillna("")
            pc_cnt = len(adf[(adf["시군명"] == "안양시") & (addr_col.str.contains("평촌동|귀인동", na=False))])
            yi_cnt = len(adf[(adf["시군명"] == "평택시") & (addr_col.str.contains("용이동", na=False))])
            raw_data.loc[(raw_data["지역"] == "안양 평촌") & (raw_data["연도"] == 2026), "학원수"] = pc_cnt
            raw_data.loc[(raw_data["지역"] == "평택 용이동") & (raw_data["연도"] == 2026), "학원수"] = yi_cnt
            st.sidebar.success(f"학원 수 반영 완료 (평촌 {pc_cnt}곳 / 용이동 {yi_cnt}곳)")
        else:
            st.sidebar.error("CSV 파일에 '시군명' 또는 '소재지지번주소' 컬럼이 없습니다.")
    except Exception as e:
        st.sidebar.error(f"파일 처리 오류: {e}")

if school_file is not None:
    try:
        sdf = load_csv(school_file)
        if "학교명" in sdf.columns:
            for school_name in ["평촌중학교", "용이중학교"]:
                sub = sdf[sdf["학교명"].astype(str).str.contains(school_name, na=False)]
                if not sub.empty and "평균" in sub.columns:
                    raw_data.loc[(raw_data["학교명"] == school_name) & (raw_data["연도"] == 2026), "국영수_평균점수"] = round(sub["평균"].mean(), 1)
                    if "성취도A비율" in sub.columns:
                        raw_data.loc[(raw_data["학교명"] == school_name) & (raw_data["연도"] == 2026), "A등급_비율(%)"] = round(sub["성취도A비율"].mean(), 1)
            st.sidebar.success("평촌중·용이중 학업성취도 반영 완료!")
        else:
            st.sidebar.error("CSV 파일에 '학교명' 컬럼이 없습니다.")
    except Exception as e:
        st.sidebar.error(f"파일 처리 오류: {e}")

# 결측치 및 이상치 전처리
before_rows = len(raw_data)
df_no_na = raw_data.dropna(subset=["학교명", "학원수", "A등급_비율(%)"])
clean_df = df_no_na[
    (df_no_na["학원수"] > 0) & (df_no_na["학원수"] <= 2000) &
    (df_no_na["국영수_평균점수"] >= 0) & (df_no_na["국영수_평균점수"] <= 100)
].copy()
after_rows = len(clean_df)

clean_df["연도_문자"] = clean_df["연도"].astype(str) + "년"
pc_df = clean_df[clean_df["지역"] == "안양 평촌"].sort_values("연도")
yi_df = clean_df[clean_df["지역"] == "평택 용이동"].sort_values("연도")

# ---------------------------------------------------------
# 3. 5개 페이지(탭) 섹션 구성
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣ 평촌중학교 (안양 평촌)",
    "2️⃣ 용이중학교 (평택 용이동)",
    "3️⃣ 학원수 대비 국영수 상관관계",
    "4️⃣ 데이터 해석 및 질문 연결",
    "5️⃣ 데이터 개요 & 결측·이상치"
])

def render_school_tab(region_label, school_label, df_sub, subject_df, bar_color):
    latest = df_sub.iloc[-1]
    prev = df_sub.iloc[-2]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{region_label} 학원 수", f"{int(latest['학원수'])}곳", f"+{int(latest['학원수'] - prev['학원수'])}곳")
    c2.metric(f"{school_label} 국·영·수 평균", f"{latest['국영수_평균점수']}점", f"+{round(latest['국영수_평균점수'] - prev['국영수_평균점수'], 1)}점")
    c3.metric("성취도 A등급(우수) 비율", f"{latest['A등급_비율(%)']}%", f"+{round(latest['A등급_비율(%)'] - prev['A등급_비율(%)'], 1)}%p")
    c4.metric("기초학력 미달(E등급)", f"{latest['E등급_비율(%)']}%", f"{round(latest['E등급_비율(%)'] - prev['E등급_비율(%)'], 1)}%p", delta_color="inverse")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        chart_bar = (
            alt.Chart(df_sub)
            .mark_bar(color=bar_color, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=45)
            .encode(
                x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("학원수:Q", title="등록 학원 수 (개소)"),
                tooltip=["지역", "연도_문자", "학원수"],
            )
            .properties(title=f"차트 1. {region_label} 연도별 학원 수 증가 추이", height=320)
        )
        st.altair_chart(chart_bar, use_container_width=True)

    with col_r:
        melted = df_sub.melt(
            id_vars=["연도_문자"],
            value_vars=["국영수_평균점수", "A등급_비율(%)"],
            var_name="지표",
            value_name="수치",
        )
        chart_line = (
            alt.Chart(melted)
            .mark_line(point=alt.OverlayMarkDef(size=70), strokeWidth=3)
            .encode(
                x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("수치:Q", title="점수(점) / 비율(%)", scale=alt.Scale(zero=False)),
                color=alt.Color("지표:N", legend=alt.Legend(title="성취도 지표", orient="top")),
                tooltip=["연도_문자", "지표", "수치"],
            )
            .properties(title=f"차트 2. {school_label} 성취도(평균·A등급 비율) 변천사", height=320)
        )
        st.altair_chart(chart_line, use_container_width=True)

    st.subheader(f"📚 {school_label} 주요 교과별 성취수준 분포 (2026년 기준)")
    st.bar_chart(subject_df)

    corr = df_sub["학원수"].corr(df_sub["A등급_비율(%)"])
    st.info(f"💡 **{school_label} 요약:** {region_label} 학원 수 증가와 {school_label} A등급 비율 간의 상관계수는 **{corr:.3f}**입니다.")
    st.dataframe(df_sub[["지역", "학교명", "연도_문자", "학원수", "국영수_평균점수", "A등급_비율(%)", "E등급_비율(%)"]], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 1페이지: 안양 평촌 & 평촌중학교
# ---------------------------------------------------------
with tab1:
    pc_subjects = pd.DataFrame({
        "과목": ["국어", "영어", "수학"],
        "A등급 (90점 이상)": [48.5, 54.2, 47.6],
        "B등급 (80~89점)": [28.1, 24.5, 23.4],
        "C등급 (70~79점)": [14.2, 12.1, 15.8],
        "D등급 (60~69점)": [7.3, 7.2, 10.9],
        "E등급 (60점 미만)": [1.9, 2.0, 2.3],
    }).set_index("과목")
    render_school_tab("안양 평촌학원가", "평촌중학교", pc_df, pc_subjects, "#f59e0b")

# ---------------------------------------------------------
# 2페이지: 평택 용이동 & 용이중학교
# ---------------------------------------------------------
with tab2:
    yi_subjects = pd.DataFrame({
        "과목": ["국어", "영어", "수학"],
        "A등급 (90점 이상)": [37.5, 38.2, 33.5],
        "B등급 (80~89점)": [27.0, 25.4, 24.1],
        "C등급 (70~79점)": [18.5, 18.0, 20.2],
        "D등급 (60~69점)": [12.8, 14.1, 17.5],
        "E등급 (60점 미만)": [4.2, 4.3, 4.7],
    }).set_index("과목")
    render_school_tab("평택 용이동", "용이중학교", yi_df, yi_subjects, "#10b981")

# ---------------------------------------------------------
# 3페이지: 학원 수 대비 국·영·수 평균 점수 상관관계 산점도
# ---------------------------------------------------------
with tab3:
    st.subheader("📈 학원 수 대비 국·영·수 평균 점수 상관관계 산점도")
    color_scale = alt.Scale(domain=["안양 평촌", "평택 용이동"], range=["#f59e0b", "#10b981"])

    base_scatter = alt.Chart(clean_df).encode(
        x=alt.X("학원수:Q", title="등록 학원 수 (개소)"),
        y=alt.Y("국영수_평균점수:Q", title="국·영·수 평균 점수 (점)", scale=alt.Scale(zero=False)),
        color=alt.Color("지역:N", scale=color_scale, legend=alt.Legend(title="지역/학교", orient="top")),
        tooltip=["지역", "학교명", "연도_문자", "학원수", "국영수_평균점수", "A등급_비율(%)"],
    )
    points = base_scatter.mark_circle(size=180)
    labels = base_scatter.mark_text(dy=-14, fontSize=12, fontWeight="bold").encode(text="연도_문자:N")

    scatter_chart = (points + labels).properties(
        title="차트 3. 지역 내 학원 수 vs 인근 중학교 국·영·수 평균 점수 상관분석 (2024~2026)",
        height=400,
    )
    st.altair_chart(scatter_chart, use_container_width=True)

    st.subheader("🔄 두 지역 연도별 A등급 비율 변천사 직접 비교")
    compare_line = (
        alt.Chart(clean_df)
        .mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=3)
        .encode(
            x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("A등급_비율(%):Q", title="성취도 A등급 비율 (%)", scale=alt.Scale(zero=False)),
            color=alt.Color("지역:N", scale=color_scale, legend=alt.Legend(title="지역/학교", orient="top")),
            tooltip=["지역", "학교명", "연도_문자", "A등급_비율(%)"],
        )
        .properties(title="차트 4. 평촌중학교 vs 용이중학교 A등급(90점 이상) 비율 추이 비교", height=320)
    )
    st.altair_chart(compare_line, use_container_width=True)

# ---------------------------------------------------------
# 4페이지: 데이터 해석 및 팀 질문 연결
# ---------------------------------------------------------
with tab4:
    st.subheader("🔍 그래프 인사이트 및 팀 질문 연결")
    st.markdown("""
    * **📊 그래프에서 찾아낸 근거 수치:**
      * **평택 용이동(용이중):** 2024년~2026년 사이 학원 수가 **132곳 → 148곳(+16곳, +12.1%)**으로 증가하는 동안, 용이중학교의 성취도 A등급 비율은 **31.2% → 36.4%(+5.2%p)**, 국·영·수 평균 점수는 **76.8점 → 79.5점(+2.7점)** 상승했습니다.
      * **안양 평촌(평촌중):** 같은 기간 학원 수가 **485곳 → 498곳(+13곳, +2.7%)**으로 완만하게 증가할 때, 평촌중학교 A등급 비율은 **46.5% → 50.1%(+3.6%p)**, 평균 점수는 **84.2점 → 86.0점(+1.8점)**을 기록했습니다.
    * **🔗 팀 질문과의 연결:**
      * 두 지역 모두 학원 수가 늘어나면서 인근 중학교의 상위권(A등급) 비율과 평균 점수가 동반 상승하는 양(+)의 방향성을 보였습니다. 특히 신흥 학원가인 용이동은 학원 증가율(+12.1%)이 높은 만큼 A등급 비율 상승 폭(+5.2%p)도 평촌(+3.6%p)보다 가팔랐습니다.
    * **🤔 예상과 다른 점 & 다음 분석에서 확인할 점:**
      * **예상과 다른 점:** 평촌학원가의 학원 수(498곳)는 용이동(148곳)의 **약 3.36배**에 달하지만, A등급 비율 격차는 **1.38배(50.1% vs 36.4%)** 수준으로 학원 수 배수만큼 성적 격차가 벌어지지는 않았습니다. 즉, 학원 수가 일정 임계치를 넘어가면 성적 상승폭이 완만해지는 한계효용 체감 현상이 관찰됩니다.
      * **다음 분석에서 확인할 점:** 단순 학원 '개수'가 아니라 **정원 규모(대형 단과학원 vs 소규모 교습소)**, **학부모 소득·교육비 지출 수준**, **학교별 지필평가 난이도 변화**를 통제 변수로 추가하여 인과관계를 검증할 필요가 있습니다.
    """)

# ---------------------------------------------------------
# 5페이지: 데이터 개요 및 결측치·이상치 처리 기준
# ---------------------------------------------------------
with tab5:
    st.subheader("1️⃣ 데이터 개요 (행·열 수, 자료형, 빈 값)")
    c_info1, c_info2, c_info3 = st.columns(3)
    c_info1.metric("전처리 전 행(Row) × 열(Column)", f"{raw_data.shape[0]}행 × {raw_data.shape[1]}열")
    c_info2.metric("전처리 후 유효 데이터", f"{clean_df.shape[0]}행 × {clean_df.shape[1]}열", f"-{before_rows - after_rows}행 제거(결측·이상치)")
    c_info3.metric("전처리 전 총 빈 값(Null) 수", f"{int(raw_data.isna().sum().sum())}개", "정제 후 0개")

    overview_df = pd.DataFrame({
        "컬럼명": raw_data.columns,
        "자료형(dtype)": [str(t) for t in raw_data.dtypes],
        "정제 전 빈 값(개)": raw_data.isna().sum().values,
        "정제 후 빈 값(개)": clean_df[raw_data.columns].isna().sum().values,
    })
    st.dataframe(overview_df, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("2️⃣ 결측치·이상치 구분 처리 기준 및 데이터 치우침(Bias) 점검")
    st.markdown("""
    | 구분 | 판별 기준 | 처리 방법 | 처리 전후 행 수 변화 |
    | :--- | :--- | :--- | :--- |
    | **결측치(Missing Value)** | 핵심 식별자(`학교명`) 또는 분석 지표(`학원수`, `A등급_비율(%)`)가 `NaN/None`인 행 | 통계 왜곡을 막기 위해 평균 대치 대신 **해당 행 삭제(`dropna`)** | `8행` → `7행` (-1행) |
    | **이상치(Outlier)** | 행정동 단위 학원 수가 `2,000곳`을 초과하거나, 시험 평균 점수가 `0~100점` 범위를 벗어난 행 | 입력 오류로 판단하여 **정상 범위 필터링으로 제거** | `7행` → `6행` (-1행) |

    * **⚠️ 전처리로 생길 수 있는 데이터 치우침(Bias) 및 한계점:**
      1. **행정구역 경계 치우침:** 도로명·지번 주소 문자열(`용이동`, `평촌동|귀인동`) 기준으로 학원을 필터링했기 때문에, 실제 용이중·평촌중 학생들이 통학하는 인접 법정동(예: 평택 비전동·소사벌, 안양 호계동) 소재 학원 수요가 누락되는 **공간적 표본 치우침**이 발생할 수 있습니다.
      2. **폐업·휴원 미반영 치우침:** 경기데이터드림 기준 정상 등록 학원만 집계하고 휴원·소규모 개인과외교습자 데이터를 제외했으므로, 실제 사교육 참여 규모가 과소추정될 가능성이 있습니다.
    """)
