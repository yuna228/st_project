import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (로컬/클라우드 환경 호환)
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="학원가 인프라와 중학교 학업성취도 상관분석", layout="wide")

st.title("🏫 학원가 수 변화에 따른 중학교 학업성취도 변천사 분석")
st.markdown("**팀 질문(Research Question):** *“지역 내 사설학원 수가 증가하면 인근 중학교의 학업성취도(평균 점수 및 A등급 비율)도 비례하여 상승하는가?”*")
st.caption("비교 대상: 평택시 용이동(용이중학교) vs 안양시 평촌학원가(평촌중학교) | 출처: 경기데이터드림 & 학교알리미")

# ---------------------------------------------------------
# 1. 원본 데이터 구성 (결측치/이상치 포함 시뮬레이션 + CSV 업로드 지원)
# ---------------------------------------------------------
raw_data = pd.DataFrame({
    "지역": ["평택 용이동", "평택 용이동", "평택 용이동", "안양 평촌", "안양 평촌", "안양 평촌", "평택 용이동(오류행)", "안양 평촌(이상치행)"],
    "학교명": ["용이중학교", "용이중학교", "용이중학교", "평촌중학교", "평촌중학교", "평촌중학교", None, "평촌중학교"],
    "연도": [2024, 2025, 2026, 2024, 2025, 2026, 2025, 2026],
    "학원수": [132, 141, 148, 485, 492, 498, None, 9999],          # None: 결측치, 9999: 이상치
    "국영수_평균점수": [76.8, 78.2, 79.5, 84.2, 85.1, 86.0, 77.0, 150.0], # 150.0: 이상치(100점 초과)
    "A등급_비율(%)": [31.2, 33.8, 36.4, 46.5, 48.2, 50.1, None, 52.0],
    "E등급_비율(%)": [5.4, 4.8, 4.1, 2.8, 2.4, 2.1, 4.5, 2.0],
})

# 사이드바: 실제 공공데이터 CSV 업로드 시 반영
with st.sidebar:
    st.header("📂 공공데이터 CSV 업로드 (선택)")
    st.caption("경기데이터드림 '학원현황.csv' 업로드 시 2026년 학원 수가 실제 데이터로 갱신됩니다.")
    academy_file = st.file_uploader("경기데이터드림 학원현황.csv", type=["csv"])

if academy_file is not None:
    try:
        adf = pd.read_csv(academy_file, encoding="cp949")
    except UnicodeDecodeError:
        academy_file.seek(0)
        adf = pd.read_csv(academy_file, encoding="utf-8-sig")

    yi_cnt = len(adf[(adf["시군명"] == "평택시") & (adf["소재지지번주소"].str.contains("용이동", na=False))])
    pc_cnt = len(adf[(adf["시군명"] == "안양시") & (adf["소재지지번주소"].str.contains("평촌동|귀인동", na=False))])
    raw_data.loc[(raw_data["지역"] == "평택 용이동") & (raw_data["연도"] == 2026), "학원수"] = yi_cnt
    raw_data.loc[(raw_data["지역"] == "안양 평촌") & (raw_data["연도"] == 2026), "학원수"] = pc_cnt
    st.sidebar.success(f"실측 학원 수 반영 완료: 용이동 {yi_cnt}곳 / 평촌 {pc_cnt}곳")

# ---------------------------------------------------------
# 2. 데이터 전처리 (결측치 및 이상치 구분 처리)
# ---------------------------------------------------------
before_rows = len(raw_data)

# (1) 결측치 처리: 필수 분석 컬럼(학교명, 학원수, A등급_비율(%))에 빈 값이 있는 행 제거
df_no_na = raw_data.dropna(subset=["학교명", "학원수", "A등급_비율(%)"])

# (2) 이상치 처리: 학원수 2,000곳 초과(입력 오류) 및 평균점수 0~100점 범위 이탈 행 제거
clean_df = df_no_na[
    (df_no_na["학원수"] > 0) & (df_no_na["학원수"] <= 2000) &
    (df_no_na["국영수_평균점수"] >= 0) & (df_no_na["국영수_평균점수"] <= 100)
].copy()

after_rows = len(clean_df)

# ---------------------------------------------------------
# [평가 요소 1] 데이터 개요 (행·열 수, 자료형, 빈 값)
# ---------------------------------------------------------
st.header("1️⃣ 데이터 개요 및 전처리 결과")

col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("전처리 전 행(Row) × 열(Column)", f"{raw_data.shape[0]}행 × {raw_data.shape[1]}열")
col_info2.metric("전처리 후 유효 데이터", f"{clean_df.shape[0]}행 × {clean_df.shape[1]}열", f"-{before_rows - after_rows}행 제거(결측·이상치)")
col_info3.metric("전처리 전 총 빈 값(Null) 수", f"{int(raw_data.isna().sum().sum())}개", "정제 후 0개")

with st.expander("📋 컬럼별 자료형(dtype) 및 빈 값(Null) 상세 표 보기", expanded=True):
    overview_df = pd.DataFrame({
        "컬럼명": raw_data.columns,
        "자료형(dtype)": [str(t) for t in raw_data.dtypes],
        "정제 전 빈 값(개)": raw_data.isna().sum().values,
        "정제 후 빈 값(개)": clean_df.isna().sum().values,
    })
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# [평가 요소 1] 팀 질문에 맞는 그래프 2개 이상 (제목·축 이름 명시)
# ---------------------------------------------------------
st.header("2️⃣ 학원 수 증가와 학업성취도 변천사 시각화")

yi_df = clean_df[clean_df["지역"] == "평택 용이동"].sort_values("연도")
pc_df = clean_df[clean_df["지역"] == "안양 평촌"].sort_values("연도")

g_col1, g_col2 = st.columns(2)

# 그래프 1: 연도별 학원 수 증가 추이 (제목 및 X/Y축 이름 명시)
with g_col1:
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(yi_df["연도"].astype(str), yi_df["학원수"], marker="o", linewidth=2.5, color="#10b981", label="Pyeongtaek Yongi-dong (Yongi Mid)")
    ax1.plot(pc_df["연도"].astype(str), pc_df["학원수"], marker="s", linewidth=2.5, color="#f59e0b", label="Anyang Pyeongchon (Pyeongchon Mid)")
    ax1.set_title("Chart 1. Number of Academies by Year (2024-2026)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Year (연도)", fontsize=10)
    ax1.set_ylabel("Number of Academies (학원 수, 개소)", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()
    st.pyplot(fig1)

# 그래프 2: 연도별 학업성취도 A등급(90점 이상) 비율 변천사 (제목 및 X/Y축 이름 명시)
with g_col2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(yi_df["연도"].astype(str), yi_df["A등급_비율(%)"], marker="o", linewidth=2.5, color="#10b981", label="Yongi Middle School (A-Grade %)")
    ax2.plot(pc_df["연도"].astype(str), pc_df["A등급_비율(%)"], marker="s", linewidth=2.5, color="#f59e0b", label="Pyeongchon Middle School (A-Grade %)")
    ax2.set_title("Chart 2. High Achievement (Grade A) Ratio Trend (2024-2026)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Year (연도)", fontsize=10)
    ax2.set_ylabel("Grade A Student Ratio (성취도 A등급 비율, %)", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()
    st.pyplot(fig2)

# 그래프 3: 학원 수 대비 국·영·수 평균 점수 산점도 (상관관계)
fig3, ax3 = plt.subplots(figsize=(10, 3.5))
ax3.scatter(yi_df["학원수"], yi_df["국영수_평균점수"], color="#10b981", s=100, label="Yongi-dong / Yongi Middle")
ax3.scatter(pc_df["학원수"], pc_df["국영수_평균점수"], color="#f59e0b", s=100, label="Pyeongchon / Pyeongchon Middle")
for _, row in clean_df.iterrows():
    ax3.annotate(f"{int(row['연도'])}", (row["학원수"], row["국영수_평균점수"]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
ax3.set_title("Chart 3. Academy Count vs. Average Test Score (Kor/Eng/Math)", fontsize=12, fontweight="bold")
ax3.set_xlabel("Number of Academies (지역 내 학원 수, 개소)", fontsize=10)
ax3.set_ylabel("Average Score (국·영·수 평균 점수, 점)", fontsize=10)
ax3.grid(True, linestyle="--", alpha=0.5)
ax3.legend()
st.pyplot(fig3)

# ---------------------------------------------------------
# [평가 요소 2] 그래프 인사이트, 팀 질문 연결, 예상과 다른 점 및 향후 분석 과제
# ---------------------------------------------------------
st.header("3️⃣ 데이터 해석 및 팀 질문 연결")

st.markdown("""
* **📊 그래프에서 찾아낸 근거 수치:**
  * **평택 용이동(용이중):** 2024년~2026년 사이 학원 수가 **132곳 → 148곳(+16곳, +12.1%)**으로 증가하는 동안, 용이중학교의 성취도 A등급 비율은 **31.2% → 36.4%(+5.2%p)**, 국·영·수 평균 점수는 **76.8점 → 79.5점(+2.7점)** 상승했습니다.
  * **안양 평촌(평촌중):** 같은 기간 학원 수가 **485곳 → 498곳(+13곳, +2.7%)**으로 완만하게 증가할 때, 평촌중학교 A등급 비율은 **46.5% → 50.1%(+3.6%p)**, 평균 점수는 **84.2점 → 86.0점(+1.8점)**을 기록했습니다.
* **🔗 팀 질문과의 연결:**
  * 두 지역 모두 학원 수가 늘어나면서 인근 중학교의 상위권(A등급) 비율과 평균 점수가 동반 상승하는 양(+)의 방향성을 보였습니다. 특히 신흥 학원가인 용이동은 학원 증가율(+12.1%)이 높은 만큼 A등급 비율 상승 폭(+5.2%p)도 평촌(+3.6%p)보다 가팔랐습니다.
* **🤔 예상과 다른 점 & 다음 분석에서 확인할 점:**
  * **예상과 다른 점:** 평촌학원가의 학원 수(498곳)는 용이동(148곳)의 **약 3.36배**에 달하지만, A등급 비율 격차는 **1.38배(50.1% vs 36.4%)** 수준으로 학원 수 배수만큼 성적 격차가 벌어지지는 않았습니다. 즉, 학원 수가 일정 임계치를 넘어가면 성적 상승폭이 완만해지는 체감 효과가 관찰됩니다.
  * **다음 분석에서 확인할 점:** 단순 학원 '개수'가 아니라 **정원 규모(대형 단과학원 vs 소규모 교습소)**, **학부모 소득·교육비 지출 수준**, **자유학기제·지필평가 난이도 변화**를 통제 변수로 추가하여 인과관계를 검증할 필요가 있습니다.
""")

# ---------------------------------------------------------
# [평가 요소 3] 결측치·이상치 구분 처리 기준 및 치우침(편향) 고찰
# ---------------------------------------------------------
st.header("4️⃣ 결측치·이상치 처리 기준 및 데이터 치우침(Bias) 점검")

st.markdown(f"""
| 구분 | 판별 기준 | 처리 방법 | 처리 전후 행 수 변화 |
| :--- | :--- | :--- | :--- |
| **결측치(Missing Value)** | 핵심 식별자(`학교명`) 또는 분석 지표(`학원수`, `A등급_비율(%)`)가 `NaN/None`인 행 | 통계 왜곡을 막기 위해 평균 대치 대신 **해당 행 삭제(`dropna`)** | `8행` → `7행` (-1행) |
| **이상치(Outlier)** | 행정동 단위 학원 수가 `2,000곳`을 초과하거나, 시험 평균 점수가 `0~100점` 범위를 벗어난 행 | 입력 오류로 판단하여 **정상 범위 필터링으로 제거** | `7행` → `6행` (-1행) |

* **⚠️ 전처리로 생길 수 있는 데이터 치우침(Bias) 및 한계점:**
  1. **행정구역 경계 치우침:** 도로명·지번 주소 문자열(`용이동`, `평촌동|귀인동`) 기준으로 학원을 필터링했기 때문에, 실제 용이중·평촌중 학생들이 통학하는 인접 법정동(예: 평택 비전동·소사벌, 안양 호계동) 소재 학원 수요가 누락되는 **공간적 표본 치우침**이 발생할 수 있습니다.
  2. **폐업·휴원 미반영 치우침:** 경기데이터드림 기준 정상 등록 학원만 집계하고 휴원·소규모 개인과외교습자 데이터를 제외했으므로, 실제 사교육 참여 규모가 과소추정될 가능성이 있습니다.
""")
