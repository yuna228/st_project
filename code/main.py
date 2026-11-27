import streamlit as st
import pandas as pd
import altair as alt

# 1. 페이지 설정
st.set_page_config(page_title="학원가 인프라와 중학교 학업성취도 상관분석", layout="wide")

st.title("🏫 학원가 수 및 인구 변화에 따른 중학교 학업성취도 변천사 분석")
st.markdown("**팀 질문(Research Question):** *“지역 내 사설학원 수가 증가하면 인근 중학교의 학업성취도(평균 점수 및 A등급 비율)도 비례하여 상승하는가?”*")
st.caption("비교 대상: 안양시 평촌학원가(평촌중학교) vs 평택시 용이동(용이중학교) | 출처: 경기데이터드림 · 학교알리미 · 행정안전부/지자체 인구통계")

# ---------------------------------------------------------
# 2. 원본 데이터 구성 (인구수 반영 + 결측치/이상치 포함) 및 전처리
# ---------------------------------------------------------
pop_detail_df = pd.DataFrame({
    "기준 시점": [
        "2024년 상반기", "2024년 12월", "2025년 상반기(6월)",
        "2025년 12월", "2026년 8월", "2026년 9월", "2026년 10월"
    ],
    "안양시 동안구 평촌동": [
        "13,996명 (4월 기준)", "-", "-",
        "14,872명", "14,715명", "14,688명", "14,670명"
    ],
    "평택시 용이동": [
        "25,895명 (5월 기준)", "25,758명", "25,492명 (6월 기준)",
        "-", "-", "25,407명", "25,453명"
    ],
    "비고": [
        "", "", "평택시 공공데이터 기준",
        "평촌동 전입 등으로 소폭 증가", "평촌동 구축 단지 인구 소폭 감소세", "", "최신 집계 기준"
    ]
})

raw_data = pd.DataFrame({
    "지역": ["안양 평촌", "안양 평촌", "안양 평촌", "평택 용이동", "평택 용이동", "평택 용이동", "평택 용이동(오류행)", "안양 평촌(이상치행)"],
    "학교명": ["평촌중학교", "평촌중학교", "평촌중학교", "용이중학교", "용이중학교", "용이중학교", None, "평촌중학교"],
    "연도": [2024, 2025, 2026, 2024, 2025, 2026, 2025, 2026],
    "인구수(명)": [13996, 14872, 14670, 25758, 25492, 25453, 25492, 14670],
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

# 파생 지표 추가
clean_df["연도_문자"] = clean_df["연도"].astype(str) + "년"
clean_df["인구1만명당_학원수"] = round((clean_df["학원수"] / clean_df["인구수(명)"]) * 10000, 1)

pc_df = clean_df[clean_df["지역"] == "안양 평촌"].sort_values("연도")
yi_df = clean_df[clean_df["지역"] == "평택 용이동"].sort_values("연도")

# ---------------------------------------------------------
# 3. 5개 페이지(탭) 섹션 구성
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣ 평촌중학교 (안양 평촌)",
    "2️⃣ 용이중학교 (평택 용이동)",
    "3️⃣ 학원수·인구 대비 성취도 비교",
    "4️⃣ 데이터 해석 및 질문 연결",
    "5️⃣ 데이터 개요 & 결측·이상치"
])

def render_school_tab(region_label, dong_label, school_label, df_sub, subject_df, bar_color):
    latest = df_sub.iloc[-1]
    prev = df_sub.iloc[-2]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"{dong_label} 인구 (2026.10)", f"{int(latest['인구수(명)']):,}명", f"{int(latest['인구수(명)'] - prev['인구수(명)']):+,}명")
    c2.metric(f"{region_label} 학원 수", f"{int(latest['학원수'])}곳", f"+{int(latest['학원수'] - prev['학원수'])}곳")
    c3.metric("인구 1만명당 학원 수", f"{latest['인구1만명당_학원수']}곳", f"+{round(latest['인구1만명당_학원수'] - prev['인구1만명당_학원수'], 1)}곳")
    c4.metric(f"{school_label} 국·영·수 평균", f"{latest['국영수_평균점수']}점", f"+{round(latest['국영수_평균점수'] - prev['국영수_평균점수'], 1)}점")
    c5.metric("성취도 A등급 비율", f"{latest['A등급_비율(%)']}%", f"+{round(latest['A등급_비율(%)'] - prev['A등급_비율(%)'], 1)}%p")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        chart_bar = (
            alt.Chart(df_sub)
            .mark_bar(color=bar_color, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=45)
            .encode(
                x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("학원수:Q", title="등록 학원 수 (개소)"),
                tooltip=["지역", "연도_문자", "인구수(명)", "학원수", "인구1만명당_학원수"],
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
    st.dataframe(
        df_sub[["지역", "학교명", "연도_문자", "인구수(명)", "학원수", "인구1만명당_학원수", "국영수_평균점수", "A등급_비율(%)", "E등급_비율(%)"]],
        use_container_width=True,
        hide_index=True
    )

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
    render_school_tab("안양 평촌학원가", "평촌동", "평촌중학교", pc_df, pc_subjects, "#f59e0b")

    st.divider()
    st.subheader("🏛️ 경기 안양시 평촌동: 전통 학군지의 집적 효과와 상권 확장")
    st.markdown("""
    평촌동은 대한민국을 대표하는 3대 학원가 중 하나로 자리 잡은 곳으로, 행정동 인구가 소폭 감소하는 흐름 속에서도 학원가가 꾸준히 유지·확장되는 이유는 다음과 같습니다.
    * **강력한 학원 집적 효과 (클러스터 형성):** 수도권 남부(안양, 과천, 의왕, 군포 등)의 학생들이 모두 모이는 거점 역할을 합니다. 수백 개의 입시·보습·예체능 학원이 밀집해 있어 학생과 학부모 입장에서 선택지가 넓고, 신규 학원 역시 유동 인구를 노려 계속 진입합니다.
    * **우수한 중등 학군과 교육열:** 귀인중, 평촌중, 범계중 등 특목고·자사고 진학 실적이 뛰어난 중학교들이 포진해 있어 초등 고학년부터 중학생 시기의 사교육 수요가 매우 탄탄합니다.
    * **주변 주거 환경과의 시너지:** 평촌 1기 신도시의 재건축·리모델링 추진과 더불어 인접 지역의 대규모 신규 아파트 입주가 이어지면서 젊은 학부모 세대의 유입이 계속되고 있습니다.
    """)

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
    render_school_tab("평택 용이동", "용이동", "용이중학교", yi_df, yi_subjects, "#10b981")

    st.divider()
    st.subheader("🌱 경기 평택시 용이동: 신도시 입주와 학령인구 급증")
    st.markdown("""
    용이동(용죽지구, 현촌지구 등 포함)은 평택시 내에서도 신흥 주거지로 급부상하며 학원가가 빠르게 형성되는 지역입니다.
    * **학령인구의 폭발적 증가:** 전국적으로 학생 수가 줄어드는 추세와 달리, 평택시는 대규모 택지 개발과 산업단지 조성으로 초·중·고 학생 수가 꾸준히 늘어나고 있습니다. 특히 용이동 일대는 30~40대 젊은 부부 비중이 높아 유아 및 초·중등 학원 수요가 급증했습니다.
    * **대단지 아파트와 상업시설의 결합:** e편한세상, 푸르지오 등 수천 세대 규모의 브랜드 아파트 단지가 들어서면서 배후 수요가 확실해졌고, 단지 앞 중심 상가 건물들이 신축되면서 학원이 입점하기 좋은 물리적 환경이 갖춰졌습니다.
    * **대형·프랜차이즈 학원의 선점 전략:** 대치동이나 분당 등 기존 학군지에서 검증된 대형 학원 브랜드들이 신흥 주거지의 교육 시장을 선점하기 위해 용이동과 인접한 소사벌·비전동 일대로 빠르게 분원을 확장하고 있습니다.
    """)

# ---------------------------------------------------------
# 3페이지: 학원 수 및 인구 대비 국·영·수 평균 점수 상관관계
# ---------------------------------------------------------
with tab3:
    st.subheader("📈 학원 수 대비 국·영·수 평균 점수 상관관계 산점도")
    color_scale = alt.Scale(domain=["안양 평촌", "평택 용이동"], range=["#f59e0b", "#10b981"])

    base_scatter = alt.Chart(clean_df).encode(
        x=alt.X("학원수:Q", title="등록 학원 수 (개소)"),
        y=alt.Y("국영수_평균점수:Q", title="국·영·수 평균 점수 (점)", scale=alt.Scale(zero=False)),
        color=alt.Color("지역:N", scale=color_scale, legend=alt.Legend(title="지역/학교", orient="top")),
        tooltip=["지역", "학교명", "연도_문자", "인구수(명)", "학원수", "인구1만명당_학원수", "국영수_평균점수", "A등급_비율(%)"],
    )
    points = base_scatter.mark_circle(size=180)
    labels = base_scatter.mark_text(dy=-14, fontSize=12, fontWeight="bold").encode(text="연도_문자:N")

    scatter_chart = (points + labels).properties(
        title="차트 3. 지역 내 학원 수 vs 인근 중학교 국·영·수 평균 점수 상관분석 (2024~2026)",
        height=380,
    )
    st.altair_chart(scatter_chart, use_container_width=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        compare_line = (
            alt.Chart(clean_df)
            .mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=3)
            .encode(
                x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("A등급_비율(%):Q", title="성취도 A등급 비율 (%)", scale=alt.Scale(zero=False)),
                color=alt.Color("지역:N", scale=color_scale, legend=alt.Legend(title="지역/학교", orient="top")),
                tooltip=["지역", "학교명", "연도_문자", "A등급_비율(%)"],
            )
            .properties(title="차트 4. 평촌중 vs 용이중 A등급 비율 추이 비교", height=320)
        )
        st.altair_chart(compare_line, use_container_width=True)

    with col_c2:
        density_bar = (
            alt.Chart(clean_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("연도_문자:N", title="조사 연도 (Year)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("인구1만명당_학원수:Q", title="인구 1만 명당 학원 수 (개소)"),
                color=alt.Color("지역:N", scale=color_scale, legend=alt.Legend(title="지역", orient="top")),
                xOffset="지역:N",
                tooltip=["지역", "연도_문자", "인구수(명)", "학원수", "인구1만명당_학원수"],
            )
            .properties(title="차트 5. 행정동 인구 1만 명당 학원 밀집도 비교", height=320)
        )
        st.altair_chart(density_bar, use_container_width=True)

    st.divider()
    st.subheader("👥 참고: 안양시 동안구 평촌동 vs 평택시 용이동 시점별 인구수 변화")
    st.dataframe(pop_detail_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 4페이지: 데이터 해석 및 팀 질문 연결
# ---------------------------------------------------------
with tab4:
    st.subheader("1️⃣ 지역별 인구 및 학원가 성장 배경 요약")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("""
        **① 경기도 안양시 동안구 평촌동 (전통 학군지 · 클러스터형)**
        * **전체 인구 추이:** 2025년 12월 **14,872명** → 2026년 8월 **14,715명** → 2026년 10월 **14,670명**
        * **인구 특징:** 1기 신도시 구축 아파트 단지 비중이 높아 전체 인구가 매월 소폭 감소하는 흐름을 보입니다.
        * **학원가 성장 요인:**
          1. **강력한 집적 효과:** 수도권 남부(안양·과천·의왕·군포) 학생이 모이는 광역 거점으로 신규 학원이 지속 진입합니다.
          2. **우수한 중등 학군:** 귀인중·평촌중·범계중 등 특목·자사고 진학 실적이 뛰어난 학군 수요가 탄탄합니다.
          3. **주거 환경 시너지:** 1기 신도시 재건축·리모델링 추진과 인근 신규 아파트 입주로 젊은 학부모 유입이 이어집니다.
        """)
    with col_p2:
        st.markdown("""
        **② 경기도 평택시 용이동 (신흥 주거지 · 인구유입형)**
        * **전체 인구 추이:** 2025년 6월 **25,492명** → 2026년 10월 **25,453명**
        * **인구 특징:** 30~40대 젊은 부부 비중이 높고 약 2만 5천 명대의 큰 인구 규모를 안정적으로 유지하고 있습니다.
        * **학원가 성장 요인:**
          1. **학령인구 증가:** 택지 개발과 산업단지 조성으로 유아 및 초·중등 학원 수요가 급증했습니다.
          2. **대단지·상업시설 결합:** e편한세상·푸르지오 등 대단지 아파트 앞 신축 상가에 학원이 빠르게 입점하고 있습니다.
          3. **프랜차이즈 분원 확장:** 대치·분당 등 검증된 대형 학원 브랜드들이 용이동 및 인접 소사벌·비전동으로 확장 중입니다.
        """)

    st.divider()
    st.subheader("2️⃣ 그래프 인사이트 및 팀 질문 연결")
    st.markdown("""
- **📊 그래프에서 찾아낸 근거 수치:**
  - **평택 용이동(용이중):** 2024년~2026년 사이 인구는 약 2만 5천 명대(**2025년 6월 25,492명 → 2026년 10월 25,453명**)를 유지하며 학원 수가 **132곳 → 148곳(+16곳, +12.1%)**으로 증가했고, 용이중학교의 성취도 A등급 비율은 **31.2% → 36.4%(+5.2%p)**, 국·영·수 평균 점수는 **76.8점 → 79.5점(+2.7점)** 상승했습니다.
  - **안양 평촌(평촌중):** 평촌동은 1기 신도시 구축 단지 특성상 인구가 **14,872명(2025.12) → 14,715명(2026.08) → 14,670명(2026.10)**으로 매월 소폭 감소하는 추세에도 불구하고, 학원 수는 **485곳 → 498곳(+13곳, +2.7%)**으로 늘었고 평촌중학교 A등급 비율은 **46.5% → 50.1%(+3.6%p)**, 평균 점수는 **84.2점 → 86.0점(+1.8점)**을 기록했습니다.
- **🔗 팀 질문과의 연결:**
  - 두 지역 모두 학원 수가 늘어나면서 인근 중학교의 상위권(A등급) 비율과 평균 점수가 동반 상승하는 양(+)의 방향성을 보였습니다. 특히 신흥 학원가인 용이동은 학원 증가율(+12.1%)이 높은 만큼 A등급 비율 상승 폭(+5.2%p)도 평촌(+3.6%p)보다 가팔랐습니다.
- **🤔 예상과 다른 점 & 다음 분석에서 확인할 점:**
  - **예상과 다른 점 (상반된 성장 동력):** 용이동은 **신도시 인구·학령인구 유입**을 바탕으로 학원가가 커진 반면, 평촌동은 **행정동 전체 인구가 소폭 감소함에도 광역 클러스터 효과(과천·의왕·군포 유입)** 덕분에 학원 수가 오히려 증가했습니다. 또한 인구 1만 명당 학원 밀집도는 평촌동(339.5곳)이 용이동(58.1곳)보다 약 5.8배 높지만, 성적(A등급 비율) 격차는 1.38배(50.1% vs 36.4%)로 학원 밀집도 배수만큼 성적 차이가 벌어지지는 않았습니다.
  - **다음 분석에서 확인할 점:** 용이동 학생들의 인접 상권(소사벌·비전동 프랜차이즈 학원) 이용 비율과 평촌학원가의 타 지역 유입 학생 비율을 통제 변수로 추가하여 정확한 학습 효과를 검증할 필요가 있습니다.
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

- **⚠️ 전처리로 생길 수 있는 데이터 치우침(Bias) 및 한계점:**
  1. **행정구역 경계 치우침:** 평촌학원가는 평촌동뿐 아니라 귀인동·호계동 및 수도권 남부(과천·의왕·군포) 학생을 흡수하는 광역 상권이며, 용이동 학생들 역시 인접한 소사벌·비전동 프랜차이즈 학원을 이용하므로 단일 행정동 기준 집계 시 실제 사교육 수요와 괴리가 발생할 수 있습니다.
  2. **폐업·휴원 미반영 치우침:** 경기데이터드림 기준 정상 등록 학원만 집계하고 휴원·소규모 개인과외교습자 데이터를 제외했으므로, 실제 사교육 참여 규모가 과소추정될 가능성이 있습니다.
    """)
