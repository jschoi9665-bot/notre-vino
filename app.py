# app.py — 나의 와인 다이어리

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from PIL import Image
import io
import base64

import database
import claude_helper

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Notre Vino",
    page_icon="🍷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&display=swap');

    html, body { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp {
        background-color: #0f0005;
        color: #f5e6e8;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* 텍스트 전용 요소만 타겟 — 아이콘 요소 제외 */
    .stMarkdown p, .stMarkdown li,
    .stTextInput input, .stTextArea textarea,
    .stNumberInput input, .stSelectbox select,
    .stButton > button,
    .stTabs [data-baseweb="tab"],
    .stCaption, .stAlert,
    label, .stMetric {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    /* Material Icons 보호 */
    .material-icons, [data-baseweb="icon"] {
        font-family: 'Material Icons' !important;
    }
    .main .block-container { padding: 0.8rem 0.8rem 2rem; max-width: 500px; margin: 0 auto; }

    /* 타이틀(h1)만 세리프, 나머지는 Pretendard */
    h1 {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        letter-spacing: 0.02em;
        font-weight: 600 !important;
    }
    h2, h3, h4 {
        font-family: 'Pretendard', -apple-system, sans-serif !important;
        letter-spacing: -0.01em;
        font-weight: 600 !important;
    }

    .stButton > button {
        width: 100%; border-radius: 25px;
        font-size: 14px; font-weight: 500;
        font-family: 'Pretendard', -apple-system, sans-serif;
        padding: 0.55rem 1rem;
        letter-spacing: 0.01em;
        background-color: #1a0508 !important;
        color: #e8c8c8 !important;
        border: 1px solid #5d2020 !important;
    }
    .stButton > button:hover {
        background-color: #2d0d10 !important;
        border-color: #8b0000 !important;
        color: #f5e6e8 !important;
    }
    /* Primary 버튼은 레드 유지 */
    [data-testid="baseButton-primary"] {
        background-color: #8b0000 !important;
        color: #ffffff !important;
        border: none !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background-color: #a00000 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; background-color: #1a0508; border-radius: 22px; padding: 5px 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 18px; color: #c9a0a0; font-weight: 500;
        font-family: 'Pretendard', -apple-system, sans-serif;
        letter-spacing: 0.01em; font-size: 0.8rem;
        padding: 0.35rem 0.9rem !important;
    }
    .stTabs [aria-selected="true"] { background-color: #8b0000 !important; color: white !important; }
    .chip { display:inline-block; background:#8b0000; color:#ffe4e4;
            border-radius:20px; padding:3px 12px; margin:3px; font-size:0.82rem;
            font-family: 'Pretendard', sans-serif; }
    .price-tag { display:inline-block; background:#1a4d1a; color:#a8f0a8;
                 border-radius:20px; padding:3px 12px; margin:3px; font-size:0.82rem;
                 font-weight: 600; font-family: 'Pretendard', sans-serif; }
    .location-tag { display:inline-block; background:#1a2d4d; color:#a8c8f0;
                    border-radius:20px; padding:3px 12px; margin:3px; font-size:0.82rem;
                    font-family: 'Pretendard', sans-serif; }
    .vivino-badge { display:inline-block; background:#750000; color:#ffd0d0;
                    border-radius:20px; padding:4px 14px; margin:3px; font-size:0.9rem;
                    font-weight: 600; font-family: 'Pretendard', sans-serif; }
    .user-banner {
        border-radius: 16px; padding: 0.8rem 1.2rem;
        margin-bottom: 0.8rem; text-align: center;
        font-weight: 600; font-size: 1.05rem;
        font-family: 'Pretendard', sans-serif;
        letter-spacing: 0.01em;
    }
    .user-jaeseok { background: linear-gradient(135deg, #3d1515, #8b0000); color: #ffd0d0; }
    .user-hyunji  { background: linear-gradient(135deg, #4d1535, #b0006a); color: #ffd0ef; }
    hr { border-color: #3d1515; }
    [data-testid="stMetric"] {
        background: #1a0508; border-radius: 12px; padding: 0.5rem; border: 1px solid #3d1515;
    }
    /* 이미지 크기 제한 — 라벨 사진 & 셀러 사진 */
    [data-testid="stImage"] img {
        max-height: 200px !important;
        width: auto !important;
        max-width: 100%;
        display: block;
        margin: 0 auto;
        border-radius: 10px;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 세션 초기화
# ──────────────────────────────────────────
database.init_db()

defaults = {
    'current_user': '재석',
    'analyzed_wine': None,
    'search_result': None,
    'recommendations': {'재석': None, '현지': None},
    'rec_avail': {'재석': None, '현지': None},    # 취향 추천 판매처 확인 결과
    'budget_recs': None,
    'budget_avail': None,                          # 예산 추천 판매처 확인 결과
    'budget_min': 20000,
    'budget_max': 50000,
    'selected_wine_id': None,  # My Cellar 선택된 와인
    'similar_cache': {},
    'wine_detail': {},  # {detail_{wid}: dict} AI 상세 설명 캐시
    'delete_confirm': {},
    'share_wine': {},   # {wine_id: True/False} 공유 폼 표시 여부
    'edit_wine': {},    # {wine_id: True/False} 평점 수정 폼 표시 여부
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────
# 공통 함수
# ──────────────────────────────────────────
def radar_chart(values, height=300):
    cats = ['탄닌', '산도', '당도', '바디감', '과일향']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=cats + [cats[0]],
        fill='toself', fillcolor='rgba(139,0,0,0.35)',
        line=dict(color='#cc2020', width=2.5),
        marker=dict(size=6, color='#cc2020'),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(26,5,8,0.8)',
            radialaxis=dict(visible=True, range=[0,5],
                            tickfont=dict(color='#c9a0a0', size=10), gridcolor='#3d1515'),
            angularaxis=dict(tickfont=dict(color='#f5e6e8', size=12), gridcolor='#3d1515'),
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, height=height, margin=dict(l=40,r=40,t=30,b=30)
    )
    return fig

def color_dot(c):
    """색상별 작은 원형 마커 (HTML 전용)"""
    colors = {'레드':'#cc2020','화이트':'#e8d8a0','로제':'#e87090','스파클링':'#a0c8e8'}
    hex_c = colors.get(c or '', '#888')
    return f"<span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:{hex_c};margin-right:5px;vertical-align:middle;'></span>"

def stars(r):
    return '⭐' * int(r or 0)

def vivino_badge(score):
    if not score: return ""
    return f"<span class='vivino-badge'>Vivino {score:.1f} <small style='opacity:0.7;'>예상</small></span>"


# ──────────────────────────────────────────
# 상단 사용자 선택
# ──────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center;color:#cc2020;font-size:2rem;margin-bottom:0.3rem;"
    "font-family:\"Playfair Display\",Georgia,serif;letter-spacing:0.08em;'>"
    "Notre Vino</h1>",
    unsafe_allow_html=True
)

_, col_js, col_hj, _ = st.columns([1, 2, 2, 1], gap="small")
with col_js:
    if st.button(
        f"{'· ' if st.session_state.current_user == '재석' else ''}재석",
        type="primary" if st.session_state.current_user == '재석' else "secondary",
        use_container_width=True,
    ):
        st.session_state.current_user = '재석'
        st.rerun()

with col_hj:
    if st.button(
        f"{'· ' if st.session_state.current_user == '현지' else ''}현지",
        type="primary" if st.session_state.current_user == '현지' else "secondary",
        use_container_width=True,
    ):
        st.session_state.current_user = '현지'
        st.rerun()

USER = st.session_state.current_user
banner_class = 'user-jaeseok' if USER == '재석' else 'user-hyunji'
st.markdown(
    f"<div class='user-banner {banner_class}'>{USER}의 와인 기록</div>",
    unsafe_allow_html=True
)

# ──────────────────────────────────────────
# 4개 탭
# ──────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Scan Label", "My Cellar", "My Taste", "Budget"])


# ══════════════════════════════════════════
# TAB 1: 와인 인식 & 검색
# ══════════════════════════════════════════
with tab1:

    # ── 와인 이름 검색 (비비노 예상 점수 포함) ──
    st.markdown("### 와인 이름으로 검색")
    st.caption("와인 이름을 입력하면 정보 + 비비노 예상 점수를 알려드려요")

    search_col, btn_col = st.columns([3, 1])
    with search_col:
        wine_query = st.text_input(
            "와인 검색", placeholder="예: Opus One, 샤또 마고, 몬테스 알파",
            label_visibility="collapsed"
        )
    with btn_col:
        search_btn = st.button("검색", type="primary")

    if search_btn and wine_query.strip():
        with st.spinner(f"'{wine_query}' 검색 중..."):
            try:
                result = claude_helper.search_wine_by_name(wine_query.strip())
                st.session_state.search_result = result
            except Exception as e:
                st.error(str(e))

    # 검색 결과 표시
    if st.session_state.search_result:
        sr = st.session_state.search_result

        if not sr.get('found', True):
            st.warning(sr.get('not_found_message','검색 결과가 없습니다.'))
        else:
            st.markdown("---")
            st.markdown(
                f"<h3 style='color:#f5e6e8;margin-bottom:0;'>"
                f"{color_dot(sr.get('color'))}{sr.get('name','')}</h3>",
                unsafe_allow_html=True
            )

            # 비비노 예상 점수 강조
            if sr.get('vivino_score'):
                score_color = '#ff6b6b' if sr['vivino_score'] >= 4.2 else '#ffa07a' if sr['vivino_score'] >= 3.8 else '#c9a0a0'
                st.markdown(
                    f"<div style='background:#1a0508;border:1px solid #8b0000;border-radius:12px;"
                    f"padding:0.8rem;margin:0.5rem 0;text-align:center;'>"
                    f"<p style='color:#c9a0a0;font-size:0.8rem;margin:0;font-family:Inter,sans-serif;'>Vivino 예상 점수 (참고용)</p>"
                    f"<p style='color:{score_color};font-size:2.2rem;font-weight:700;margin:0.2rem 0;"
                    f"font-family:\"Playfair Display\",serif;'>"
                    f"{sr['vivino_score']:.1f}</p>"
                    f"<p style='color:#999;font-size:0.75rem;margin:0;font-family:Inter,sans-serif;'>{sr.get('vivino_score_basis','')}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            col1, col2 = st.columns(2)
            with col1:
                if sr.get('producer'):      st.markdown(f"**생산자** · {sr['producer']}")
                if sr.get('grape_variety'): st.markdown(f"**품종** · {sr['grape_variety']}")
                if sr.get('color'):         st.markdown(f"**종류** · {sr['color']}")
                if sr.get('alcohol'):       st.markdown(f"**도수** · {sr['alcohol']}")
            with col2:
                if sr.get('region') or sr.get('country'):
                    st.markdown(f"**지역** · {sr.get('region','')} {sr.get('country','')}")
                if sr.get('price_range_korea'): st.markdown(f"**한국 가격** · {sr['price_range_korea']}")
                if sr.get('best_vintage'):      st.markdown(f"**추천 빈티지** · {sr['best_vintage']}")
                if sr.get('where_to_buy_korea'):
                    st.markdown(
                        f"<span class='location-tag'>{sr['where_to_buy_korea']}</span>",
                        unsafe_allow_html=True
                    )

            if sr.get('taste_profile'):
                st.info(sr['taste_profile'])

            # 맛 차트
            t_vals = [sr.get('tannin') or 3, sr.get('acidity') or 3,
                      sr.get('sweetness') or 3, sr.get('body') or 3, sr.get('fruitiness') or 3]
            st.plotly_chart(radar_chart(t_vals, height=280), use_container_width=True)

            if sr.get('food_pairing'):
                chips = " ".join([f"<span class='chip'>{f}</span>" for f in sr['food_pairing']])
                st.markdown(chips, unsafe_allow_html=True)

            if sr.get('awards'):
                st.caption(sr['awards'])

            if st.button("검색 결과 닫기"):
                st.session_state.search_result = None
                st.rerun()

    st.markdown("---")

    # ── 라벨 사진 분석 ──
    st.markdown("### 라벨 사진으로 분석")
    st.caption("라벨을 찍으면 AI가 정보 + 비비노 예상 점수를 읽어드려요")

    method = st.radio("", ["갤러리", "카메라"], horizontal=True, label_visibility="collapsed")
    uploaded = None
    if method == "갤러리":
        uploaded = st.file_uploader("사진 선택", type=['jpg','jpeg','png','webp','heic'],
                                    label_visibility="collapsed")
    else:
        cam = st.camera_input("촬영", label_visibility="collapsed")
        if cam: uploaded = cam

    if uploaded:
        image = Image.open(uploaded)
        st.image(image, use_container_width=True)

        if st.button("AI 분석하기", type="primary"):
            with st.spinner("분석 중... (10~20초)"):
                try:
                    if image.mode in ('RGBA','LA','P'): image = image.convert('RGB')
                    buf = io.BytesIO()
                    image.save(buf, format='JPEG', quality=85)
                    img_bytes = buf.getvalue()

                    wine_info = claude_helper.analyze_wine_label(img_bytes)

                    if 'error' in wine_info:
                        st.error(wine_info['error'])
                    else:
                        wine_info['image_data'] = base64.b64encode(img_bytes).decode()
                        st.session_state.analyzed_wine = wine_info
                        st.success("분석 완료!")
                except Exception as e:
                    st.error(str(e))

    # 분석 결과
    if st.session_state.analyzed_wine:
        wine = st.session_state.analyzed_wine
        st.markdown("---")
        st.markdown("## 분석 결과")

        st.markdown(
            f"<h2 style='color:#f5e6e8;margin-bottom:0;'>"
            f"{color_dot(wine.get('color'))}{wine.get('name','알 수 없음')}</h2>",
            unsafe_allow_html=True
        )

        # 비비노 예상 점수
        if wine.get('vivino_score'):
            sc = wine['vivino_score']
            score_color = '#ff6b6b' if sc >= 4.2 else '#ffa07a' if sc >= 3.8 else '#c9a0a0'
            st.markdown(
                f"<div style='background:#1a0508;border:1px solid #8b0000;border-radius:12px;"
                f"padding:0.8rem;margin:0.5rem 0;text-align:center;'>"
                f"<p style='color:#c9a0a0;font-size:0.8rem;margin:0;font-family:Inter,sans-serif;'>Vivino 예상 점수 (참고용)</p>"
                f"<p style='color:{score_color};font-size:2.2rem;font-weight:700;margin:0.2rem 0;"
                f"font-family:\"Playfair Display\",serif;'>{sc:.1f}</p>"
                f"<p style='color:#999;font-size:0.75rem;margin:0;font-family:Inter,sans-serif;'>{wine.get('vivino_score_basis','')}</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        col1, col2 = st.columns(2)
        with col1:
            if wine.get('producer'):      st.markdown(f"**생산자** · {wine['producer']}")
            if wine.get('grape_variety'): st.markdown(f"**품종** · {wine['grape_variety']}")
            if wine.get('alcohol'):       st.markdown(f"**도수** · {wine['alcohol']}")
        with col2:
            if wine.get('region') or wine.get('country'):
                st.markdown(f"**지역** · {wine.get('region','')} {wine.get('country','')}")
            if wine.get('vintage'):       st.markdown(f"**빈티지** · {wine['vintage']}년")

        if wine.get('taste_profile'):
            st.markdown("### 맛 프로필")
            st.info(wine['taste_profile'])

        vals = [wine.get('tannin') or 3, wine.get('acidity') or 3,
                wine.get('sweetness') or 3, wine.get('body') or 3, wine.get('fruitiness') or 3]
        st.plotly_chart(radar_chart(vals), use_container_width=True)

        c1,c2,c3,c4,c5 = st.columns(5)
        for col, lbl, v in zip([c1,c2,c3,c4,c5], ['탄닌','산도','당도','바디','과일향'], vals):
            with col: st.metric(lbl, f"{v:.0f}/5")

        if wine.get('food_pairing'):
            st.markdown("### 어울리는 음식")
            chips = " ".join([f"<span class='chip'>{f}</span>" for f in wine['food_pairing']])
            st.markdown(chips, unsafe_allow_html=True)

        if wine.get('similar_wines'):
            st.markdown("### 비슷한 스타일")
            for s in wine['similar_wines']:
                badge = vivino_badge(s.get('vivino_score'))
                with st.expander(f"{s.get('name','')}  —  {s.get('price_range','')}"):
                    if badge: st.markdown(badge, unsafe_allow_html=True)
                    if s.get('region'): st.markdown(f"**지역** · {s['region']}")
                    if s.get('grape_variety'): st.markdown(f"**품종** · {s['grape_variety']}")
                    if s.get('reason'): st.write(s['reason'])

        if wine.get('description'):
            st.markdown("### 소개")
            st.write(wine['description'])

        # 저장 폼
        st.markdown("---")
        st.markdown("### 기록 저장")

        # 누가 마셨는지 선택
        drink_mode = st.radio(
            "오늘 누가 마셨나요?",
            ["재석만", "현지만", "재석 & 현지 함께"],
            horizontal=True,
            index=2  # 기본값: 함께
        )

        with st.form("save_form", clear_on_submit=True):
            drink_date = st.date_input("마신 날짜", value=datetime.now())

            col1, col2 = st.columns(2)
            with col1:
                purchase_location = st.text_input("구매처", placeholder="이마트, 와인앤모어 등")
            with col2:
                purchase_price = st.number_input("가격 (원)", min_value=0, step=1000, value=0)

            st.markdown("---")

            # 재석 & 현지 함께인 경우: 두 칸 나란히
            if drink_mode == "재석 & 현지 함께":
                col_js, col_hj = st.columns(2)

                with col_js:
                    st.markdown("**재석**")
                    rating_js = st.select_slider(
                        "재석 별점", options=[1,2,3,4,5], value=3,
                        format_func=lambda x: "⭐"*x, key="rating_js"
                    )
                    memo_js = st.text_area(
                        "재석 메모", placeholder="재석의 한 마디",
                        height=80, key="memo_js"
                    )

                with col_hj:
                    st.markdown("**현지**")
                    rating_hj = st.select_slider(
                        "현지 별점", options=[1,2,3,4,5], value=3,
                        format_func=lambda x: "⭐"*x, key="rating_hj"
                    )
                    memo_hj = st.text_area(
                        "현지 메모", placeholder="현지의 한 마디",
                        height=80, key="memo_hj"
                    )

            elif drink_mode == "재석만":
                st.markdown("**재석**")
                rating_js = st.select_slider(
                    "별점", options=[1,2,3,4,5], value=3,
                    format_func=lambda x: "⭐"*x
                )
                memo_js = st.text_area("메모", placeholder="오늘 느낀 점", height=80)
                rating_hj, memo_hj = None, None

            else:  # 현지만
                st.markdown("**현지**")
                rating_hj = st.select_slider(
                    "별점", options=[1,2,3,4,5], value=3,
                    format_func=lambda x: "⭐"*x
                )
                memo_hj = st.text_area("메모", placeholder="오늘 느낀 점", height=80)
                rating_js, memo_js = None, None

            if st.form_submit_button("저장하기", type="primary"):
                saved_users = []
                base = wine.copy()
                base.update({
                    'drink_date': str(drink_date),
                    'purchase_location': purchase_location,
                    'purchase_price': purchase_price if purchase_price > 0 else None,
                })

                # 재석 저장
                if rating_js is not None:
                    save_js = base.copy()
                    save_js.update({'user_name': '재석', 'rating': rating_js, 'memo': memo_js or ''})
                    database.save_wine(save_js)
                    saved_users.append('재석')

                # 현지 저장
                if rating_hj is not None:
                    save_hj = base.copy()
                    save_hj.update({'user_name': '현지', 'rating': rating_hj, 'memo': memo_hj or ''})
                    database.save_wine(save_hj)
                    saved_users.append('현지')

                if len(saved_users) == 2:
                    st.success("재석 & 현지 기록 모두 저장됐어요!")
                else:
                    st.success(f"{saved_users[0]}의 기록에 저장됐어요!")

                st.session_state.analyzed_wine = None
                st.balloons()

        if st.button("다른 와인 분석하기"):
            st.session_state.analyzed_wine = None
            st.rerun()


# ══════════════════════════════════════════
# TAB 2: 내 기록
# ══════════════════════════════════════════
with tab2:
    st.markdown(f"### {USER}의 와인 기록")

    with st.expander("필터 & 정렬"):
        sort_opts = {'최신순':'date','별점순':'rating','이름순':'name','가격순':'price'}
        sort_by = sort_opts[st.selectbox("정렬", list(sort_opts.keys()))]

        varieties = database.get_unique_varieties(USER)
        fv = None
        if varieties:
            sel = st.selectbox("품종", ['전체'] + varieties)
            if sel != '전체': fv = sel

        regions = database.get_unique_regions(USER)
        fr = None
        if regions:
            sel = st.selectbox("지역", ['전체'] + regions)
            if sel != '전체': fr = sel

    wines = database.get_all_wines(USER, sort_by=sort_by, filter_variety=fv, filter_region=fr)

    if not wines:
        st.markdown(f"""
        <div style='text-align:center;padding:3rem 1rem;color:#c9a0a0;font-family:Inter,sans-serif;'>
            <p style='font-size:1.1rem;'>{USER}의 와인 기록이 아직 없어요</p>
            <p style='font-size:0.9rem;opacity:0.7;'>Scan Label 탭에서 라벨을 찍어보세요</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.caption(f"총 {len(wines)}개")

        # ── 별점별 탭 ──
        r5, r4, r3, r2, r1 = st.tabs(["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"])

        for rtab, r in [(r5,5),(r4,4),(r3,3),(r2,2),(r1,1)]:
            with rtab:
                group = [w for w in wines if (w.get('rating') or 0) == r]
                if not group:
                    st.markdown(
                        "<div style='text-align:center;padding:1.5rem;color:#c9a0a0;"
                        "font-size:0.9rem;'>해당 별점의 와인이 없어요</div>",
                        unsafe_allow_html=True
                    )
                    continue

                # ── 와인 이름 목록 ──
                for wine in group:
                    wid = wine['id']
                    is_sel = st.session_state.selected_wine_id == wid
                    sub_parts = []
                    if wine.get('grape_variety'): sub_parts.append(wine['grape_variety'])
                    if wine.get('drink_date'):    sub_parts.append(str(wine['drink_date']))
                    sub = "  ·  " + "  ·  ".join(sub_parts) if sub_parts else ""
                    arrow = "▼" if is_sel else "▶"
                    if st.button(
                        f"{arrow}  {wine.get('name','?')}{sub}",
                        key=f"sel_{wid}",
                        use_container_width=True
                    ):
                        st.session_state.selected_wine_id = None if is_sel else wid
                        st.session_state.edit_wine = {}
                        st.session_state.delete_confirm = {}
                        st.rerun()

                # ── 선택된 와인 상세 카드 ──
                sel_id = st.session_state.selected_wine_id
                sel_wine = next((w for w in group if w['id'] == sel_id), None)

                if sel_wine:
                    wid = sel_wine['id']
                    is_high = r >= 4
                    color_label = sel_wine.get('color', '')

                    st.markdown("---")
                    st.markdown(
                        f"<h3 style='color:#f5e6e8;margin-bottom:0.2rem;'>"
                        f"{color_dot(color_label)}{sel_wine.get('name','')}</h3>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"{'⭐' * r}", unsafe_allow_html=False)

                    # 사진
                    if sel_wine.get('image_data'):
                        try:
                            img_bytes = base64.b64decode(sel_wine['image_data'])
                            st.image(img_bytes, use_container_width=True)
                        except Exception:
                            pass

                    # 기본 정보 + 레이더
                    ci, cc = st.columns([3,2])
                    with ci:
                        if sel_wine.get('producer'):      st.markdown(f"**생산자** · {sel_wine['producer']}")
                        if sel_wine.get('grape_variety'): st.markdown(f"**품종** · {sel_wine['grape_variety']}")
                        if sel_wine.get('region'):
                            st.markdown(f"**지역** · {sel_wine['region']}"
                                        f"{', '+sel_wine['country'] if sel_wine.get('country') else ''}")
                        if sel_wine.get('vintage'):    st.markdown(f"**빈티지** · {sel_wine['vintage']}년")
                        if sel_wine.get('drink_date'): st.markdown(f"**마신 날짜** · {sel_wine['drink_date']}")
                        if sel_wine.get('vivino_score'):
                            st.markdown(vivino_badge(sel_wine['vivino_score']), unsafe_allow_html=True)
                        if sel_wine.get('purchase_location'):
                            st.markdown(f"<span class='location-tag'>{sel_wine['purchase_location']}</span>",
                                        unsafe_allow_html=True)
                        if sel_wine.get('purchase_price'):
                            st.markdown(f"<span class='price-tag'>{sel_wine['purchase_price']:,}원</span>",
                                        unsafe_allow_html=True)
                        if sel_wine.get('memo'): st.markdown(f"**메모** · {sel_wine['memo']}")
                    with cc:
                        has_t = all(sel_wine.get(k) is not None
                                    for k in ['tannin','acidity','sweetness','body','fruitiness'])
                        if has_t:
                            st.plotly_chart(
                                radar_chart([sel_wine['tannin'], sel_wine['acidity'], sel_wine['sweetness'],
                                             sel_wine['body'], sel_wine['fruitiness']], height=190),
                                use_container_width=True
                            )

                    # 저장된 맛 프로필 (라벨 스캔 때 저장된 것)
                    if sel_wine.get('taste_profile'):
                        st.markdown("**맛 프로필**")
                        st.info(sel_wine['taste_profile'])

                    # ── 액션 버튼 (작게, 옆에) ──
                    st.markdown("---")
                    detail_key = f"detail_{wid}"
                    det_loaded = detail_key in st.session_state.wine_detail
                    ckey = f"sim_{wid}"
                    sim_loaded = ckey in st.session_state.similar_cache

                    if is_high:
                        ab1, ab2, ab3, ab4 = st.columns(4)
                        action_edit = ab3
                        action_del  = ab4
                    else:
                        ab1, ab2, ab3 = st.columns(3)
                        action_edit = ab2
                        action_del  = ab3

                    with ab1:
                        det_label = "📖 노트 닫기" if det_loaded else "📖 소믈리에 노트"
                        if st.button(det_label, key=f"detail_btn_{wid}"):
                            if det_loaded:
                                del st.session_state.wine_detail[detail_key]
                                st.rerun()
                            else:
                                with st.spinner("소믈리에 노트 불러오는 중..."):
                                    try:
                                        d = claude_helper.get_sommelier_notes(
                                            wine_name=sel_wine.get('name',''),
                                            producer=sel_wine.get('producer',''),
                                            region=sel_wine.get('region',''),
                                            vintage=sel_wine.get('vintage'),
                                            grape_variety=sel_wine.get('grape_variety',''),
                                        )
                                        st.session_state.wine_detail[detail_key] = d
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))

                    if is_high:
                        with ab2:
                            sim_label = "🔍 비슷한 와인 ✓" if sim_loaded else "🔍 비슷한 와인"
                            if st.button(sim_label, key=f"sim_btn_{wid}"):
                                if not sim_loaded:
                                    with st.spinner("분석 중..."):
                                        result = claude_helper.get_similar_wines_korea(
                                            wine_name=sel_wine.get('name',''),
                                            grape_variety=sel_wine.get('grape_variety',''),
                                            region=sel_wine.get('region',''),
                                            color=sel_wine.get('color',''),
                                            rating=sel_wine.get('rating',4),
                                            tannin=sel_wine.get('tannin',3),
                                            acidity=sel_wine.get('acidity',3),
                                            sweetness=sel_wine.get('sweetness',3),
                                            body=sel_wine.get('body',3),
                                            fruitiness=sel_wine.get('fruitiness',3),
                                        )
                                        st.session_state.similar_cache[ckey] = result
                                        st.rerun()

                    with action_edit:
                        edit_label = "✏️ 수정 닫기" if st.session_state.edit_wine.get(wid) else "✏️ 수정"
                        if st.button(edit_label, key=f"edit_toggle_{wid}"):
                            st.session_state.edit_wine[wid] = not st.session_state.edit_wine.get(wid, False)
                            st.rerun()

                    with action_del:
                        del_label = "🗑️ 취소" if st.session_state.delete_confirm.get(wid) else "🗑️ 삭제"
                        if st.button(del_label, key=f"del_toggle_{wid}"):
                            st.session_state.delete_confirm[wid] = not st.session_state.delete_confirm.get(wid, False)
                            st.rerun()

                    # ── 소믈리에 노트 ──
                    if det_loaded:
                        notes = st.session_state.wine_detail[detail_key]
                        st.markdown("---")
                        st.markdown("### 📖 소믈리에 노트")

                        if 'error' in notes:
                            st.error(notes['error'])
                        else:
                            # 🌹 향 노트
                            an = notes.get('aroma_notes', {})
                            if an:
                                st.markdown("**🌹 향 노트**")
                                if an.get('primary'):
                                    st.caption("과일향")
                                    st.markdown(" ".join(
                                        f"<span class='chip'>{a}</span>" for a in an['primary']
                                    ), unsafe_allow_html=True)
                                if an.get('secondary'):
                                    st.caption("발효향")
                                    st.markdown(" ".join(
                                        f"<span class='chip'>{a}</span>" for a in an['secondary']
                                    ), unsafe_allow_html=True)
                                if an.get('tertiary'):
                                    st.caption("숙성향")
                                    st.markdown(" ".join(
                                        f"<span class='chip'>{a}</span>" for a in an['tertiary']
                                    ), unsafe_allow_html=True)

                            # 🌡️ 서빙 가이드
                            sv = notes.get('serving', {})
                            if sv:
                                st.markdown("**🌡️ 서빙 가이드**")
                                if sv.get('temperature'): st.markdown(f"· **온도** {sv['temperature']}")
                                if sv.get('decanting'):   st.markdown(f"· **디캔팅** {sv['decanting']}")
                                if sv.get('glass'):       st.markdown(f"· **글라스** {sv['glass']}")

                            # 🕰️ 음용 적기
                            dw = notes.get('drinking_window', {})
                            if dw:
                                st.markdown("**🕰️ 음용 적기**")
                                peak = f"{dw.get('peak_start','')} ~ {dw.get('peak_end','')}년"
                                if dw.get('now', True):
                                    st.success(f"✅ 지금 마시기 좋아요  ·  최적기 {peak}")
                                else:
                                    st.info(f"⏳ 조금 더 기다리면 좋아요  ·  최적기 {peak}")
                                if dw.get('aging_note'):
                                    st.caption(dw['aging_note'])

                            # 📖 와이너리 스토리
                            if notes.get('winery_story'):
                                st.markdown("**📖 와이너리 스토리**")
                                st.write(notes['winery_story'])

                    # ── 비슷한 와인 ──
                    if is_high and sim_loaded:
                        cached = st.session_state.similar_cache[ckey]
                        st.markdown("---")
                        st.markdown("### 비슷한 와인 (국내 구매 가능)")
                        if 'error' in cached:
                            st.error(cached['error'])
                        else:
                            if cached.get('match_summary'):
                                st.caption(cached['match_summary'])
                            for i, rec in enumerate(cached.get('recommendations', []), 1):
                                badge = vivino_badge(rec.get('vivino_score'))
                                rec_title = f"#{i} {rec.get('name','')}"
                                if rec.get('price_korea'):
                                    rec_title += f"  ·  {rec['price_korea']:,}원"
                                with st.expander(rec_title):
                                    if badge: st.markdown(badge, unsafe_allow_html=True)
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        if rec.get('producer'):      st.markdown(f"**생산자** · {rec['producer']}")
                                        if rec.get('grape_variety'): st.markdown(f"**품종** · {rec['grape_variety']}")
                                        if rec.get('region'):        st.markdown(f"**지역** · {rec['region']}")
                                    with col_b:
                                        if rec.get('price_korea'):
                                            st.markdown(f"<span class='price-tag'>{rec['price_korea']:,}원</span>",
                                                        unsafe_allow_html=True)
                                        if rec.get('where_to_buy'):
                                            st.markdown(f"<span class='location-tag'>{rec['where_to_buy']}</span>",
                                                        unsafe_allow_html=True)
                                    if rec.get('similarity_detail'):
                                        st.markdown(f"**유사도** · {rec['similarity_detail']}")
                                    if rec.get('taste_description'):
                                        st.caption(rec['taste_description'])
                                    if rec.get('food_pairing'):
                                        st.markdown(rec['food_pairing'])

                    # ── 다른 사람 기록에 추가 ──
                    other_user = '현지' if USER == '재석' else '재석'
                    other_wines = database.get_all_wines(other_user)
                    already_has = any(w.get('name','') == sel_wine.get('name','') for w in other_wines)

                    if not already_has:
                        st.markdown("---")
                        if st.session_state.share_wine.get(wid):
                            st.markdown(f"**{other_user} 기록에 추가**")
                            with st.form(f"share_form_{wid}"):
                                share_rating = st.select_slider(
                                    f"{other_user}의 별점", options=[1,2,3,4,5], value=3,
                                    format_func=lambda x: "⭐"*x, key=f"sr_{wid}"
                                )
                                share_memo = st.text_area(
                                    f"{other_user}의 메모",
                                    placeholder=f"{other_user}이/가 마셨을 때 어땠나요?",
                                    height=70, key=f"sm_{wid}"
                                )
                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    if st.form_submit_button("추가하기", type="primary"):
                                        new_record = sel_wine.copy()
                                        new_record.update({
                                            'user_name': other_user,
                                            'rating': share_rating,
                                            'memo': share_memo,
                                        })
                                        new_record.pop('id', None)
                                        database.save_wine(new_record)
                                        st.session_state.share_wine[wid] = False
                                        st.success(f"{other_user}의 기록에 추가됐어요!")
                                        st.rerun()
                                with sc2:
                                    if st.form_submit_button("취소"):
                                        st.session_state.share_wine[wid] = False
                                        st.rerun()
                        else:
                            if st.button(f"{other_user} 기록에도 추가하기", key=f"share_{wid}"):
                                st.session_state.share_wine[wid] = True
                                st.rerun()
                    else:
                        st.caption(f"{other_user}도 이미 이 와인을 기록했어요")

                    # ── 평점 수정 폼 ──
                    if st.session_state.edit_wine.get(wid):
                        st.markdown("---")
                        st.markdown("**별점 · 메모 수정**")
                        with st.form(f"edit_form_{wid}"):
                            cur_rating = sel_wine.get('rating') or 3
                            cur_memo   = sel_wine.get('memo') or ''
                            new_rating = st.select_slider(
                                "별점", options=[1,2,3,4,5], value=cur_rating,
                                format_func=lambda x: "⭐"*x, key=f"er_{wid}"
                            )
                            new_memo = st.text_area("메모", value=cur_memo, height=80, key=f"em_{wid}")
                            e1, e2 = st.columns(2)
                            with e1:
                                if st.form_submit_button("저장", type="primary"):
                                    database.update_wine_rating(wid, new_rating, new_memo)
                                    st.session_state.edit_wine[wid] = False
                                    st.success("수정됐어요!")
                                    st.rerun()
                            with e2:
                                if st.form_submit_button("취소"):
                                    st.session_state.edit_wine[wid] = False
                                    st.rerun()

                    # ── 삭제 확인 ──
                    if st.session_state.delete_confirm.get(wid):
                        st.markdown("---")
                        st.warning("정말 삭제할까요?")
                        dy, dn = st.columns(2)
                        with dy:
                            if st.button("삭제 확인", key=f"yes_{wid}"):
                                database.delete_wine(wid)
                                st.session_state.similar_cache.pop(f"sim_{wid}", None)
                                st.session_state.wine_detail.pop(f"detail_{wid}", None)
                                st.session_state.delete_confirm[wid] = False
                                st.session_state.selected_wine_id = None
                                st.rerun()
                        with dn:
                            if st.button("취소", key=f"no_{wid}"):
                                st.session_state.delete_confirm[wid] = False
                                st.rerun()


# ══════════════════════════════════════════
# TAB 3: 취향 분석
# ══════════════════════════════════════════
with tab3:
    st.markdown(f"### {USER}의 취향 분석")

    all_wines = database.get_all_wines(USER)
    cnt = len(all_wines)

    if cnt < 3:
        st.markdown(f"""
        <div style='text-align:center;padding:3rem 1rem;color:#c9a0a0;font-family:Inter,sans-serif;'>
            <p style='font-size:1.1rem;'>{USER}의 와인을 {3-cnt}개 더 기록하면 분석이 시작돼요</p>
            <p>현재 <strong>{cnt}</strong>개 기록됨</p>
        </div>""", unsafe_allow_html=True)
    else:
        ts = database.get_taste_stats(USER)
        avg_vals = [ts.get('avg_tannin') or 3, ts.get('avg_acidity') or 3,
                    ts.get('avg_sweetness') or 3, ts.get('avg_body') or 3,
                    ts.get('avg_fruitiness') or 3]

        st.markdown("### 맛 취향 프로필")
        st.plotly_chart(radar_chart(avg_vals, height=340), use_container_width=True)

        c1,c2,c3,c4,c5 = st.columns(5)
        for col,lbl,v in zip([c1,c2,c3,c4,c5],['탄닌','산도','당도','바디','과일향'],avg_vals):
            with col: st.metric(lbl, f"{v:.1f}")

        col1, col2 = st.columns(2)
        with col1:
            if ts.get('favorite_varieties'):
                st.markdown("### 선호 품종")
                for i,v in enumerate(ts['favorite_varieties'][:3],1):
                    st.markdown(f"{i}. **{v['grape_variety']}** {'⭐'*round(v['avg_rating'] or 0)}")
        with col2:
            if ts.get('favorite_regions'):
                st.markdown("### 선호 지역")
                for i,r in enumerate(ts['favorite_regions'][:3],1):
                    st.markdown(f"{i}. **{r['region']}** ({r.get('country','')}) {'⭐'*round(r['avg_rating'] or 0)}")

        if ts.get('color_distribution'):
            st.markdown("### 와인 종류")
            total = sum(c['count'] for c in ts['color_distribution'])
            for c in ts['color_distribution']:
                st.markdown(
                    f"<span>{color_dot(c['color'])}</span>"
                    f"**{c['color']}** — {c['count']}병 ({c['count']/total*100:.0f}%)",
                    unsafe_allow_html=True
                )

        wines_priced = [w for w in all_wines if w.get('purchase_price')]
        if wines_priced:
            st.markdown("### 구매 통계")
            prices = [w['purchase_price'] for w in wines_priced]
            p1,p2,p3 = st.columns(3)
            with p1: st.metric("평균", f"{int(sum(prices)/len(prices)):,}원")
            with p2: st.metric("최저", f"{min(prices):,}원")
            with p3: st.metric("최고", f"{max(prices):,}원")

        st.markdown("---")
        m1,m2,m3 = st.columns(3)
        with m1: st.metric("총 기록", f"{cnt}개")
        with m2:
            rts = [w.get('rating') for w in all_wines if w.get('rating')]
            if rts: st.metric("평균 별점", f"{sum(rts)/len(rts):.1f}⭐")
        with m3:
            high = len([w for w in all_wines if (w.get('rating') or 0) >= 4])
            st.metric("4점↑ 와인", f"{high}개")

        st.markdown("---")
        st.markdown("### AI 맞춤 추천")
        if st.button("추천받기", type="primary"):
            with st.spinner("분석 중..."):
                try:
                    st.session_state.recommendations[USER] = claude_helper.get_recommendations(ts, all_wines)
                    st.session_state.rec_avail[USER] = None  # 새 추천 시 판매처 확인 초기화
                except Exception as e:
                    st.error(str(e))

        recs = st.session_state.recommendations.get(USER)
        if recs:
            if 'error' in recs:
                st.error(recs['error'])
            else:
                if recs.get('personality'):
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#8b0000,#3d1515);"
                        f"border-radius:16px;padding:1.2rem;text-align:center;margin:0.5rem 0;'>"
                        f"<p style='color:#c9a0a0;font-size:0.8rem;margin:0;font-family:Inter,sans-serif;'>나의 와인 취향 유형</p>"
                        f"<p style='color:#f5e6e8;font-size:1.3rem;font-weight:600;margin:0.2rem 0 0;"
                        f"font-family:\"Playfair Display\",serif;'>"
                        f"{recs['personality']}</p></div>",
                        unsafe_allow_html=True
                    )
                if recs.get('taste_summary'): st.info(recs['taste_summary'])

                # ── 한국 판매처 실시간 확인 버튼 ──
                rec_avail = st.session_state.rec_avail.get(USER)
                if not rec_avail:
                    if st.button("🔍 한국 판매처 실시간 확인", key="rec_avail_btn"):
                        wine_names = [r.get('name','') for r in recs.get('recommendations',[]) if r.get('name')]
                        with st.spinner("한국 온라인 판매처 검색 중... (20~40초)"):
                            try:
                                avail = claude_helper.check_wines_availability_korea(wine_names)
                                st.session_state.rec_avail[USER] = avail
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                else:
                    ok = sum(1 for v in rec_avail.values() if v.get('available'))
                    total = len(rec_avail)
                    st.caption(f"✅ 판매처 확인 완료 — {total}개 중 {ok}개 국내 온라인 판매 확인")

                st.markdown("### 추천 와인")
                for i, rec in enumerate(recs.get('recommendations',[]), 1):
                    badge = vivino_badge(rec.get('vivino_score'))
                    with st.expander(f"#{i} {rec.get('name','')}  ·  {rec.get('price_range','')}"):
                        if badge: st.markdown(badge, unsafe_allow_html=True)

                        # 판매처 배지
                        rec_avail = st.session_state.rec_avail.get(USER) or {}
                        avail_info = rec_avail.get(rec.get('name', ''))
                        if avail_info:
                            if avail_info.get('available'):
                                stores = avail_info.get('stores', '')
                                st.success(f"✅ 한국 판매 확인{' · ' + stores if stores else ''}")
                            else:
                                st.error(f"❌ 국내 온라인 판매처 미확인")
                            if avail_info.get('note'):
                                st.caption(avail_info['note'])

                        if rec.get('producer'):     st.markdown(f"**생산자** · {rec['producer']}")
                        if rec.get('region'):       st.markdown(f"**지역** · {rec['region']}")
                        if rec.get('grape_variety'):st.markdown(f"**품종** · {rec['grape_variety']}")
                        if rec.get('reason'):       st.markdown(f"**추천 이유** · {rec['reason']}")
                        if rec.get('food_pairing'): st.markdown(rec['food_pairing'])

                if st.button("다시 추천"):
                    st.session_state.recommendations[USER] = None
                    st.session_state.rec_avail[USER] = None
                    st.rerun()


# ══════════════════════════════════════════
# TAB 4: 예산 추천
# ══════════════════════════════════════════
with tab4:
    st.markdown("### 예산별 와인 추천")
    st.caption("예산 입력 → 국내 구매 가능한 최적 와인 추천")

    st.markdown("**빠른 선택**")
    p1,p2,p3,p4 = st.columns(4)
    presets = [("~2만원",0,20000),("2~5만원",20000,50000),("5~10만원",50000,100000),("10만원+",100000,300000)]
    for col,(lbl,bmin,bmax) in zip([p1,p2,p3,p4], presets):
        with col:
            if st.button(lbl, key=f"p_{bmin}"):
                st.session_state.budget_min = bmin
                st.session_state.budget_max = bmax
                st.session_state.budget_recs = None

    col1, col2 = st.columns(2)
    with col1:
        bmin = st.number_input("최소 (원)", min_value=0, max_value=1000000,
                               step=5000, value=st.session_state.budget_min)
    with col2:
        bmax = st.number_input("최대 (원)", min_value=0, max_value=1000000,
                               step=5000, value=st.session_state.budget_max)

    aw = database.get_all_wines(USER)
    use_taste = False
    if len(aw) >= 3:
        use_taste = st.checkbox("내 취향 반영", value=True)

    if bmin >= bmax:
        st.warning("최대 예산이 최소보다 커야 합니다.")
    else:
        if st.button(f"{bmin:,}원~{bmax:,}원 와인 추천", type="primary"):
            with st.spinner("국내 구매 가능 와인 탐색 중..."):
                try:
                    td = database.get_taste_stats(USER) if use_taste and len(aw) >= 3 else None
                    st.session_state.budget_recs = claude_helper.get_budget_recommendations(bmin, bmax, td)
                    st.session_state.budget_avail = None  # 새 추천 시 판매처 확인 초기화
                    st.session_state.budget_min = bmin
                    st.session_state.budget_max = bmax
                except Exception as e:
                    st.error(str(e))

    if st.session_state.budget_recs:
        br = st.session_state.budget_recs
        if 'error' in br:
            st.error(br['error'])
        else:
            st.markdown("---")
            bmin_s, bmax_s = st.session_state.budget_min, st.session_state.budget_max
            st.markdown(
                f"<div style='background:linear-gradient(135deg,#1a3d1a,#0d260d);"
                f"border-radius:14px;padding:0.8rem;text-align:center;'>"
                f"<p style='color:#a8f0a8;font-weight:600;margin:0;"
                f"font-family:\"Playfair Display\",serif;'>{bmin_s:,}원 ~ {bmax_s:,}원</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            if br.get('budget_summary'): st.info(br['budget_summary'])

            # ── 한국 판매처 실시간 확인 버튼 ──
            budget_avail = st.session_state.budget_avail
            if not budget_avail:
                if st.button("🔍 한국 판매처 실시간 확인", key="budget_avail_btn"):
                    wine_names = [r.get('name','') for r in br.get('recommendations',[]) if r.get('name')]
                    with st.spinner("한국 온라인 판매처 검색 중... (20~40초)"):
                        try:
                            avail = claude_helper.check_wines_availability_korea(wine_names)
                            st.session_state.budget_avail = avail
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            else:
                ok = sum(1 for v in budget_avail.values() if v.get('available'))
                total = len(budget_avail)
                st.caption(f"✅ 판매처 확인 완료 — {total}개 중 {ok}개 국내 온라인 판매 확인")

            for i, rec in enumerate(br.get('recommendations',[]), 1):
                badge = vivino_badge(rec.get('vivino_score'))
                price_str = f" · {rec['price']:,}원" if rec.get('price') else ""
                with st.expander(f"#{i} {rec.get('name','')}{price_str}"):
                    if badge: st.markdown(badge, unsafe_allow_html=True)

                    # 판매처 배지
                    budget_avail = st.session_state.budget_avail or {}
                    avail_info = budget_avail.get(rec.get('name', ''))
                    if avail_info:
                        if avail_info.get('available'):
                            stores = avail_info.get('stores', '')
                            st.success(f"✅ 한국 판매 확인{' · ' + stores if stores else ''}")
                        else:
                            st.error(f"❌ 국내 온라인 판매처 미확인")
                        if avail_info.get('note'):
                            st.caption(avail_info['note'])

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if rec.get('producer'):     st.markdown(f"**생산자** · {rec['producer']}")
                        if rec.get('region'):       st.markdown(f"**지역** · {rec['region']}")
                        if rec.get('grape_variety'):st.markdown(f"**품종** · {rec['grape_variety']}")
                        if rec.get('color'):
                            st.markdown(
                                f"<span style='font-size:0.9rem;'>{color_dot(rec['color'])}{rec['color']}</span>",
                                unsafe_allow_html=True
                            )
                    with col_b:
                        if rec.get('price'):
                            st.markdown(f"<span class='price-tag'>{rec['price']:,}원</span>",
                                        unsafe_allow_html=True)
                        if rec.get('where_to_buy'):
                            st.markdown(f"<span class='location-tag'>{rec['where_to_buy']}</span>",
                                        unsafe_allow_html=True)
                    if rec.get('taste_description'): st.markdown(rec['taste_description'])
                    if rec.get('food_pairing'):      st.markdown(f"**어울리는 음식** · {rec['food_pairing']}")
                    if rec.get('reason'):            st.caption(rec['reason'])

        if st.button("다시 추천"):
            st.session_state.budget_recs = None
            st.session_state.budget_avail = None
            st.rerun()

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#555;font-size:0.8rem;"
    "font-family:Inter,sans-serif;letter-spacing:0.05em;'>"
    "Notre Vino · Powered by Claude AI</div>",
    unsafe_allow_html=True
)
