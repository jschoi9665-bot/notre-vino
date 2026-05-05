# claude_helper.py
# Claude AI API 호출 함수 모음

import anthropic
import base64
import json
import os
from dotenv import load_dotenv
from pathlib import Path

_env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=_env_path, override=True)


def get_client():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    return anthropic.Anthropic(api_key=api_key)


def _parse_json(text):
    """Claude 응답에서 JSON 안전하게 파싱"""
    text = text.strip()
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()
    return json.loads(text)


# ──────────────────────────────────────────
# 1. 와인 라벨 이미지 분석
# ──────────────────────────────────────────
def analyze_wine_label(image_bytes):
    client = get_client()
    image_b64 = base64.standard_b64encode(image_bytes).decode('utf-8')

    prompt = """당신은 세계적인 와인 전문가이자 소믈리에입니다.
이 와인 라벨을 분석하고 아래 JSON 형식으로만 응답하세요. JSON 외 텍스트 금지.

{
    "name": "와인 풀네임 (예: Château Margaux Premier Grand Cru Classé)",
    "producer": "생산자/와이너리 정확한 이름",
    "region": "세부 생산지역 (예: Pauillac, Médoc, Bordeaux)",
    "country": "국가 (한국어)",
    "grape_variety": "품종 (블렌딩이면 비율 포함, 예: 카베르네 소비뇽 75%, 메를로 25%)",
    "vintage": 연도숫자_또는_null,
    "color": "레드/화이트/로제/스파클링",
    "alcohol": "알코올 도수 (예: 13.5%)",
    "taste_profile": "맛 프로필 3~4문장. 탄닌·산도·당도·바디감을 쉬운 말로. 어떤 향이 나는지, 어떤 느낌인지 구체적으로.",
    "tannin": 1~5_소수,
    "acidity": 1~5_소수,
    "sweetness": 1~5_소수,
    "body": 1~5_소수,
    "fruitiness": 1~5_소수,
    "vivino_score": "비비노 예상 점수 (3.0~5.0 소수, 학습 데이터 기반 추정)",
    "vivino_score_basis": "점수 근거 한 문장 (예: '보르도 그랑크뤼 등급으로 일반적으로 높은 평가를 받음')",
    "food_pairing": ["음식1", "음식2", "음식3"],
    "similar_wines": [
        {
            "name": "정확한 와인명 (생산자+이름+빈티지 포함, 예: Louis Jadot Gevrey-Chambertin 2019)",
            "producer": "생산자",
            "region": "지역, 국가",
            "grape_variety": "품종",
            "price_range": "한국 예상 가격대",
            "vivino_score": 예상점수_소수,
            "reason": "이 와인과 비슷한 이유 (맛 특성 포함)"
        },
        {...},
        {...}
    ],
    "description": "이 와인 소개 2~3문장. 역사·등급·특징 포함."
}

라벨 인식 불가 시: {"error": "라벨을 인식할 수 없습니다. 더 선명하게 찍어주세요."}
숫자 필드는 반드시 숫자로."""

    message = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    try:
        return _parse_json(message.content[0].text)
    except json.JSONDecodeError:
        return {"error": "분석 결과 처리 중 오류가 발생했습니다. 다시 시도해주세요."}


# ──────────────────────────────────────────
# 2. 와인 이름으로 검색 + 비비노 예상 점수
# ──────────────────────────────────────────
def search_wine_by_name(wine_name):
    """
    와인 이름으로 검색하여 상세 정보와 비비노 예상 점수를 반환합니다.
    실제 Vivino API가 아닌 Claude 학습 데이터 기반 추정입니다.
    """
    client = get_client()

    prompt = f"""당신은 세계적인 와인 전문가입니다.
아래 와인에 대한 정보를 최대한 자세히 알려주세요.

검색 와인: "{wine_name}"

JSON 형식으로만 응답하세요:
{{
    "found": true_또는_false,
    "name": "정확한 풀네임",
    "producer": "생산자/와이너리",
    "region": "세부 지역",
    "country": "국가 (한국어)",
    "grape_variety": "품종 (블렌딩 비율 포함)",
    "color": "레드/화이트/로제/스파클링",
    "alcohol": "알코올 도수",
    "taste_profile": "맛 설명 3문장. 탄닌·산도·향기·여운 구체적으로.",
    "tannin": 1~5_소수,
    "acidity": 1~5_소수,
    "sweetness": 1~5_소수,
    "body": 1~5_소수,
    "fruitiness": 1~5_소수,
    "vivino_score": 비비노_예상점수_소수_3.0~5.0,
    "vivino_score_basis": "점수 근거. 이 와인의 명성, 등급, 리뷰 트렌드 기반.",
    "price_range_korea": "한국 평균 판매가",
    "where_to_buy_korea": "국내 주요 구매처",
    "food_pairing": ["음식1", "음식2", "음식3"],
    "awards": "주요 수상/평가 (있으면)",
    "description": "와인 소개 2~3문장",
    "best_vintage": "추천 빈티지 (있으면)",
    "not_found_message": "found가 false일 때만: 검색 실패 이유"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return _parse_json(message.content[0].text)
    except json.JSONDecodeError:
        return {"found": False, "not_found_message": "검색 결과를 처리하는 중 오류가 발생했습니다."}


# ──────────────────────────────────────────
# 3. 비슷한 와인 추천 (정교화 버전)
# ──────────────────────────────────────────
def get_similar_wines_korea(wine_name, grape_variety, region, color, rating,
                             tannin=3, acidity=3, sweetness=3, body=3, fruitiness=3):
    """
    평점 4점 이상 와인과 맛 프로필까지 고려해
    국내 구매 가능한 비슷한 와인을 정교하게 추천합니다.
    """
    client = get_client()

    prompt = f"""당신은 한국 와인 시장에 정통한 최고 수준의 소믈리에입니다.

고객이 아래 와인을 {rating}점(5점 만점)으로 매우 만족했습니다:

━━━ 원본 와인 정보 ━━━
• 와인명: {wine_name}
• 품종: {grape_variety}
• 지역: {region}
• 종류: {color}
• 맛 프로필 (1~5 척도):
  - 탄닌: {tannin:.1f}
  - 산도: {acidity:.1f}
  - 당도: {sweetness:.1f}
  - 바디감: {body:.1f}
  - 과일향: {fruitiness:.1f}

━━━ 추천 조건 ━━━
1. 위 맛 프로필과 유사한 수치를 가진 와인
2. 반드시 현재 한국에서 구매 가능한 와인
3. 와인 이름은 "생산자명 + 와인명 + 빈티지(있으면)" 형태로 정확하게
4. 각 구매처는 실제로 취급하는 곳만 명시
5. 가격대가 다양하도록 (저가~고가 믹스)

JSON 형식으로만 응답:
{{
    "match_summary": "원본 와인의 핵심 특성 요약 (왜 이 와인들을 추천하는지 한 문장)",
    "recommendations": [
        {{
            "name": "정확한 와인명 (예: Domaine Drouhin Oregon Pinot Noir 2021)",
            "producer": "생산자/와이너리 정확한 이름",
            "region": "세부 지역, 국가",
            "grape_variety": "품종 (블렌딩이면 주요 품종 포함)",
            "vintage": "추천 빈티지 또는 NV",
            "color": "종류",
            "tannin": 1~5_소수,
            "acidity": 1~5_소수,
            "sweetness": 1~5_소수,
            "body": 1~5_소수,
            "fruitiness": 1~5_소수,
            "vivino_score": 예상_비비노점수_소수,
            "price_korea": 한국_실제판매가_숫자_원단위,
            "where_to_buy": "구체적인 구매처 (예: 이마트 와인, 와인앤모어 온라인, 마켓컬리)",
            "similarity_score": "원본과의 맛 유사도 (상/중상/중)",
            "similarity_detail": "어떤 면에서 비슷한지 구체적으로 (탄닌 강도, 과일향 종류 등)",
            "taste_description": "맛 설명 2문장. 구체적인 향과 풍미 포함.",
            "food_pairing": "잘 어울리는 음식"
        }},
        {{...}},
        {{...}},
        {{...}}
    ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return _parse_json(message.content[0].text)
    except json.JSONDecodeError:
        return {"error": "유사 와인을 찾는 중 오류가 발생했습니다."}


# ──────────────────────────────────────────
# 4. 취향 기반 맞춤 추천
# ──────────────────────────────────────────
def get_recommendations(taste_stats, wine_history):
    client = get_client()

    favorites_text = ""
    if taste_stats.get('favorite_varieties'):
        varieties = [v['grape_variety'] for v in taste_stats['favorite_varieties'][:3]]
        favorites_text += f"선호 품종: {', '.join(varieties)}\n"
    if taste_stats.get('favorite_regions'):
        regions = [f"{r['region']} ({r['country']})" for r in taste_stats['favorite_regions'][:3]]
        favorites_text += f"선호 지역: {', '.join(regions)}\n"

    recent_names = [w.get('name', '') for w in (wine_history or [])[:5] if w.get('name')]
    recent_text = f"최근 마신 와인: {', '.join(recent_names)}" if recent_names else ""

    prompt = f"""당신은 세계 최고의 소믈리에입니다.
아래 취향 데이터를 분석하고 맞춤 추천을 해주세요.

탄닌: {taste_stats.get('avg_tannin', 3):.1f}/5
산도: {taste_stats.get('avg_acidity', 3):.1f}/5
당도: {taste_stats.get('avg_sweetness', 3):.1f}/5
바디: {taste_stats.get('avg_body', 3):.1f}/5
과일향: {taste_stats.get('avg_fruitiness', 3):.1f}/5
{favorites_text}{recent_text}
총 기록: {taste_stats.get('total_count', 0)}개

JSON으로만 응답:
{{
    "personality": "와인 취향 유형 한 문구",
    "taste_summary": "취향 분석 2~3문장",
    "recommendations": [
        {{
            "name": "정확한 와인명 (생산자+이름+빈티지)",
            "producer": "생산자",
            "region": "지역, 국가",
            "grape_variety": "품종",
            "vivino_score": 예상점수,
            "reason": "추천 이유",
            "price_range": "한국 가격대",
            "food_pairing": "어울리는 음식"
        }},
        {{...}},{{...}},{{...}},{{...}}
    ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return _parse_json(message.content[0].text)
    except json.JSONDecodeError:
        return {"error": "추천 생성 중 오류가 발생했습니다."}


# ──────────────────────────────────────────
# 5. 예산별 추천
# ──────────────────────────────────────────
def get_budget_recommendations(budget_min, budget_max, taste_stats=None):
    client = get_client()

    taste_text = ""
    if taste_stats and taste_stats.get('total_count', 0) > 0:
        taste_text = f"""
고객 취향 반영:
탄닌 {taste_stats.get('avg_tannin',3):.1f} / 산도 {taste_stats.get('avg_acidity',3):.1f} / 당도 {taste_stats.get('avg_sweetness',3):.1f} / 바디 {taste_stats.get('avg_body',3):.1f} / 과일향 {taste_stats.get('avg_fruitiness',3):.1f}"""
        if taste_stats.get('favorite_varieties'):
            varieties = [v['grape_variety'] for v in taste_stats['favorite_varieties'][:3]]
            taste_text += f"\n선호 품종: {', '.join(varieties)}"

    prompt = f"""한국 와인 시장 전문 소믈리에로서,
{budget_min:,}원~{budget_max:,}원 예산에서 한국 구매 가능한 최적 와인 5가지를 추천하세요.
{taste_text}

조건: 이마트·홈플러스·롯데마트·와인앤모어·마켓컬리·GS25 wine25 등 실제 취급 와인만.

JSON만 응답:
{{
    "budget_summary": "이 예산대 기대 품질 한 문장",
    "recommendations": [
        {{
            "name": "정확한 와인명 (생산자+이름+빈티지)",
            "producer": "생산자",
            "region": "지역, 국가",
            "color": "종류",
            "grape_variety": "품종",
            "price": 실제가격_숫자,
            "vivino_score": 예상점수,
            "where_to_buy": "구체적인 구매처",
            "taste_description": "맛 설명 2문장",
            "food_pairing": "어울리는 음식",
            "reason": "이 예산에서 추천하는 이유"
        }},
        {{...}},{{...}},{{...}},{{...}}
    ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return _parse_json(message.content[0].text)
    except json.JSONDecodeError:
        return {"error": "추천 생성 중 오류가 발생했습니다."}
