#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

/* 페이지 여백 */
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}
[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* ✅ Metric 카드: 밝은 배경 + 짙은 글자색 */
[data-testid="stMetric"] {
    background-color: #f8fafc;          /* 밝은 회백색 */
    color: #0f172a;                      /* 짙은 남색 계열 */
    text-align: center;
    padding: 16px 0;
    border: 1px solid #e2e8f0;           /* 얇은 테두리 */
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

/* 라벨/값 색상 정렬 */
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
  color: #334155;                        /* 라벨색 살짝 연하게 */
}
[data-testid="stMetricValue"], .stMetricValue {
  color: #0f172a;                        /* 값은 진하게 */
}

/* 델타 아이콘 위치 (그대로 유지) */
[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}
[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('weather.csv')  # 분석 데이터 넣기

#######################
# Sidebar
with st.sidebar:
    # ─────────────────────────────────────────
    # Sidebar: 앱 타이틀 & 설명
    st.title("Weather Dashboard")
    st.caption("관측지점별 기상 지표를 선택해 비교/분석하세요.")

    # ─────────────────────────────────────────
    # 기본 설정
    STATION_COL = "관측지점별(1)"
    # 지표 카테고리 매핑 (데이터 컬럼명과 맞춰 필요 시 수정)
    METRIC_GROUPS = {
        "기온 (Temperature)": [
            "평균기온 (℃)", "평균최고기온 (℃)", "평균최저기온 (℃)",
            "최고기온 (℃)", "최저기온 (℃)", "평균지면온도 (℃)"
        ],
        "강수/일조 (Precip & Sun)": [
            "합계강수량 (mm)", "합계일조시간 (hr)"
        ],
        "바람 (Wind)": [
            "평균풍속 (m/s)", "최대풍속 (m/s)"
        ],
        "습도/운량 (Humidity/Cloud)": [
            "평균상대습도 (%)", "평균전운량 (할)"
        ],
        "기압 (Pressure)": [
            "평균현지기압 (hPa)", "평균해면기압 (hPa)",
            "최고해면기압 (hPa)", "최저해면기압 (hPa)"
        ],
    }

    # 실제 데이터에 존재하는 컬럼만 필터링
    METRIC_GROUPS = {
        k: [c for c in v if c in df_reshaped.columns]
        for k, v in METRIC_GROUPS.items()
    }

    # ─────────────────────────────────────────
    # 필터: 관측지점
    stations_all = sorted(df_reshaped[STATION_COL].dropna().unique().tolist())
    default_stations = stations_all[:10] if len(stations_all) > 10 else stations_all
    selected_stations = st.multiselect(
        "관측지점 선택",
        options=stations_all,
        default=default_stations,
        help="비교할 관측지점을 선택하세요. (기본: 상위 10개 또는 전체)"
    )

    if not selected_stations:
        st.info("관측지점을 선택하지 않아 전체 지점을 사용합니다.")
        selected_stations = stations_all

    # ─────────────────────────────────────────
    # 필터: 지표 선택
    group = st.radio(
        "지표 카테고리",
        options=list(METRIC_GROUPS.keys()),
        horizontal=False
    )
    metric = st.selectbox(
        "기준 지표",
        options=METRIC_GROUPS.get(group, []),
        help="지도/랭킹/요약에 사용할 기본 지표를 선택하세요."
    )

    # 값 범위 슬라이더 (문자열 → 숫자 변환 후 min/max 산출)
    _series_num = pd.to_numeric(
        df_reshaped[metric].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )
    vmin, vmax = float(_series_num.min()), float(_series_num.max())
    value_range = st.slider(
        "표시 값 범위 (필터)",
        min_value=float(round(vmin, 2)),
        max_value=float(round(vmax, 2)),
        value=(float(round(vmin, 2)), float(round(vmax, 2))),
        step=float(0.1)
    )

    # ─────────────────────────────────────────
    # 스타일 & 옵션
    color_scheme = st.selectbox(
        "색상 테마",
        options=["default", "blues", "greens", "viridis", "plasma", "inferno", "magma"],
        index=1,
        help="지도/차트 색상 스케일"
    )
    normalize = st.checkbox("값 정규화(0~1)로 비교", value=False)
    show_labels = st.checkbox("차트 라벨 표시", value=True)

    # ─────────────────────────────────────────
    # 선택값을 세션에 저장 (다른 섹션에서 사용)
    st.session_state.update({
        "selected_stations": selected_stations,
        "selected_metric_group": group,
        "selected_metric": metric,
        "metric_range": value_range,
        "color_scheme": color_scheme,
        "normalize": normalize,
        "show_labels": show_labels,
        "station_col": STATION_COL,
    })

    st.divider()
    st.markdown("**Tips**: 지표를 바꾸면 지도/랭킹/요약 카드가 함께 업데이트됩니다.")

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# ─────────────────────────────────────────
# 컬럼1: 요약 지표
with col[0]:
    st.markdown("### 📌 요약 지표")

    # 평균기온
    st.metric(
        label="평균기온 (℃)",
        value=f"{df_reshaped['평균기온 (℃)'].mean():.1f}"
    )

    # 최고기온
    max_temp = df_reshaped['최고기온 (℃)'].max()
    max_temp_date = df_reshaped.loc[
        df_reshaped['최고기온 (℃)'].idxmax(), '최고기온일자'
    ]
    st.metric(
        label="최고기온 (℃)",
        value=f"{max_temp:.1f}",
        delta=f"{max_temp_date}"
    )

    # 최저기온
    min_temp = df_reshaped['최저기온 (℃)'].min()
    min_temp_date = df_reshaped.loc[
        df_reshaped['최저기온 (℃)'].idxmin(), '최저기온일자'
    ]
    st.metric(
        label="최저기온 (℃)",
        value=f"{min_temp:.1f}",
        delta=f"{min_temp_date}"
    )

    # ✅ 평균강수량 (기존: 합계강수량)
    avg_precip = pd.to_numeric(
        df_reshaped['합계강수량 (mm)'].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    ).mean()
    st.metric(
        label="평균강수량 (mm)",
        value=f"{avg_precip:.1f}"
    )

    # 평균풍속 (문자열 → 숫자 변환)
    avg_wind = pd.to_numeric(
        df_reshaped['평균풍속 (m/s)'].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    ).mean()
    st.metric(
        label="평균풍속 (m/s)",
        value=f"{avg_wind:.1f}"
    )

# ─────────────────────────────────────────
# 컬럼2: 지도 · 시각화
with col[1]:
    st.markdown("### 🗺️ 지도 · 시각화")

    stations = st.session_state.get("selected_stations", df_reshaped["관측지점별(1)"].unique())
    metric = st.session_state.get("selected_metric", "평균기온 (℃)")
    color_scheme = st.session_state.get("color_scheme", "blues")

    df_filtered = df_reshaped[df_reshaped["관측지점별(1)"].isin(stations)]

    st.info("※ 지도 시각화를 위해 관측지점별 위도/경도가 필요합니다. 현재는 예시 차트로 표시합니다.")

    # 바 차트
    bar_chart = px.bar(
        df_filtered,
        x="관측지점별(1)",
        y=metric,
        color=metric,
        color_continuous_scale=color_scheme,
        title=f"{metric} 비교"
    )
    st.plotly_chart(bar_chart, use_container_width=True)

    # 히트맵
    pivot_cols = [c for c in ["평균기온 (℃)", "최고기온 (℃)", "최저기온 (℃)", "합계강수량 (mm)", "평균풍속 (m/s)"] if c in df_filtered.columns]
    pivot_df = df_filtered.set_index("관측지점별(1)")[pivot_cols]
    heatmap = px.imshow(
        pivot_df,
        color_continuous_scale=color_scheme,
        aspect="auto",
        title="관측지점별 기상 지표 히트맵"
    )
    st.plotly_chart(heatmap, use_container_width=True)

# ─────────────────────────────────────────
# 컬럼3: 상위 지점 & About
with col[2]:
    st.markdown("### 🏆 상위 지점 & About")

    station_col = st.session_state.get("station_col", "관측지점별(1)")
    stations = st.session_state.get("selected_stations", df_reshaped[station_col].unique().tolist())
    metric = st.session_state.get("selected_metric", "평균기온 (℃)")
    value_range = st.session_state.get("metric_range", None)
    color_scheme = st.session_state.get("color_scheme", "blues")
    normalize = st.session_state.get("normalize", False)
    show_labels = st.session_state.get("show_labels", True)

    if metric not in df_reshaped.columns:
        st.warning("선택한 지표가 데이터에 없습니다. 사이드바에서 다른 지표를 선택하세요.")
    else:
        df2 = df_reshaped[df_reshaped[station_col].isin(stations)].copy()
        df2["_metric_value"] = pd.to_numeric(
            df2[metric].astype(str).str.replace(",", "", regex=False), errors="coerce"
        )

        if value_range:
            vmin, vmax = value_range
            df2 = df2[(df2["_metric_value"] >= vmin) & (df2["_metric_value"] <= vmax)]

        if normalize and not df2["_metric_value"].isna().all():
            mmin, mmax = df2["_metric_value"].min(), df2["_metric_value"].max()
            if mmax > mmin:
                df2["_metric_display"] = (df2["_metric_value"] - mmin) / (mmax - mmin)
            else:
                df2["_metric_display"] = 0.0
            value_label = "정규화 값"
        else:
            df2["_metric_display"] = df2["_metric_value"]
            value_label = metric

        tab1, tab2, tab3 = st.tabs(["Top 10", "Bottom 10", "About"])

        with tab1:
            top10 = df2.dropna(subset=["_metric_display"]).nlargest(10, "_metric_display")
            if top10.empty:
                st.info("표시할 데이터가 없습니다. 범위를 조정하거나 다른 지표를 선택하세요.")
            else:
                fig_top = px.bar(
                    top10.sort_values("_metric_display"),
                    x="_metric_display",
                    y=station_col,
                    orientation="h",
                    color="_metric_display",
                    color_continuous_scale=color_scheme,
                    title=f"Top 10 · {value_label}"
                )
                if show_labels:
                    fig_top.update_traces(text=top10["_metric_value"].round(2), textposition="outside")
                fig_top.update_layout(yaxis_title="", xaxis_title=value_label, showlegend=False)
                st.plotly_chart(fig_top, use_container_width=True)
                st.dataframe(top10[[station_col, "_metric_value"]].rename(columns={"_metric_value": metric}), use_container_width=True)

        with tab2:
            bottom10 = df2.dropna(subset=["_metric_display"]).nsmallest(10, "_metric_display")
            if bottom10.empty:
                st.info("표시할 데이터가 없습니다. 범위를 조정하거나 다른 지표를 선택하세요.")
            else:
                fig_bot = px.bar(
                    bottom10.sort_values("_metric_display", ascending=False),
                    x="_metric_display",
                    y=station_col,
                    orientation="h",
                    color="_metric_display",
                    color_continuous_scale=color_scheme,
                    title=f"Bottom 10 · {value_label}"
                )
                if show_labels:
                    fig_bot.update_traces(text=bottom10["_metric_value"].round(2), textposition="outside")
                fig_bot.update_layout(yaxis_title="", xaxis_title=value_label, showlegend=False)
                st.plotly_chart(fig_bot, use_container_width=True)
                st.dataframe(bottom10[[station_col, "_metric_value"]].rename(columns={"_metric_value": metric}), use_container_width=True)

        with tab3:
            st.markdown(
                f"""
                **데이터 설명**
                - 기준 지표: `{metric}`
                - 표시 값: `{value_label}` (정규화 옵션: {'ON' if normalize else 'OFF'})
                - 값 범위 필터: `{value_range}` 적용

                **사용 팁**
                - 사이드바에서 지표/지점/값 범위를 조절하면 Top/Bottom 랭킹이 즉시 업데이트됩니다.
                - 차트 라벨은 *차트 라벨 표시* 옵션으로 온/오프할 수 있습니다.
                """
            )
