# database.py
# Supabase 데이터베이스 관리 파일

import os
from datetime import datetime

# Supabase 클라이언트 초기화 — st.secrets 또는 환경변수 둘 다 지원
try:
    import streamlit as st
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

from supabase import create_client, Client

_supabase: Client = create_client(url, key)


def init_db():
    """Supabase 연결 확인 (테이블은 Supabase 대시보드에서 이미 생성됨)"""
    try:
        _supabase.table("wines").select("id").limit(1).execute()
    except Exception as e:
        raise RuntimeError(f"Supabase 연결 실패: {e}")


def save_wine(wine_data: dict) -> int:
    """와인 저장 후 생성된 id 반환"""
    row = {
        "user_name": wine_data.get("user_name", "재석"),
        "name": wine_data.get("name", ""),
        "producer": wine_data.get("producer", ""),
        "region": wine_data.get("region", ""),
        "country": wine_data.get("country", ""),
        "grape_variety": wine_data.get("grape_variety", ""),
        "vintage": wine_data.get("vintage"),
        "color": wine_data.get("color", ""),
        "taste_profile": wine_data.get("taste_profile", ""),
        "tannin": wine_data.get("tannin", 3),
        "acidity": wine_data.get("acidity", 3),
        "sweetness": wine_data.get("sweetness", 3),
        "body": wine_data.get("body", 3),
        "fruitiness": wine_data.get("fruitiness", 3),
        "rating": wine_data.get("rating", 3),
        "memo": wine_data.get("memo", ""),
        "drink_date": wine_data.get("drink_date", datetime.now().strftime("%Y-%m-%d")),
        "image_data": wine_data.get("image_data", ""),
        "purchase_location": wine_data.get("purchase_location", ""),
        "purchase_price": wine_data.get("purchase_price"),
        "vivino_score": wine_data.get("vivino_score"),
    }
    res = _supabase.table("wines").insert(row).execute()
    return res.data[0]["id"]


def get_all_wines(user_name=None, sort_by="date",
                  filter_variety=None, filter_region=None) -> list:
    """조건에 맞는 와인 목록 반환"""
    query = _supabase.table("wines").select("*")

    if user_name:
        query = query.eq("user_name", user_name)
    if filter_variety:
        query = query.ilike("grape_variety", f"%{filter_variety}%")
    if filter_region:
        query = query.ilike("region", f"%{filter_region}%")

    sort_map = {
        "date": ("drink_date", False),    # DESC
        "rating": ("rating", False),      # DESC
        "name": ("name", True),           # ASC
        "price": ("purchase_price", True),  # ASC
    }
    col, ascending = sort_map.get(sort_by, ("drink_date", False))
    query = query.order(col, desc=not ascending)

    res = query.execute()
    return res.data or []


def get_high_rated_wines(user_name=None, min_rating=4) -> list:
    """평점 min_rating 이상 와인 반환"""
    query = _supabase.table("wines").select("*").gte("rating", min_rating)
    if user_name:
        query = query.eq("user_name", user_name)
    query = query.order("rating", desc=True)
    res = query.execute()
    return res.data or []


def delete_wine(wine_id: int):
    """와인 삭제"""
    _supabase.table("wines").delete().eq("id", wine_id).execute()


def update_wine_rating(wine_id: int, rating: int, memo: str):
    """평점 및 메모 업데이트"""
    _supabase.table("wines").update({"rating": rating, "memo": memo}).eq("id", wine_id).execute()


def get_taste_stats(user_name=None) -> dict:
    """맛 통계 집계 — 데이터를 Python에서 처리"""
    query = _supabase.table("wines").select(
        "tannin,acidity,sweetness,body,fruitiness,grape_variety,region,country,rating,color"
    )
    if user_name:
        query = query.eq("user_name", user_name)
    res = query.execute()
    rows = res.data or []

    if not rows:
        return {
            "avg_tannin": None, "avg_acidity": None,
            "avg_sweetness": None, "avg_body": None,
            "avg_fruitiness": None, "total_count": 0,
            "favorite_varieties": [], "favorite_regions": [],
            "color_distribution": [],
        }

    total = len(rows)
    stats = {
        "avg_tannin": sum(r["tannin"] or 0 for r in rows) / total,
        "avg_acidity": sum(r["acidity"] or 0 for r in rows) / total,
        "avg_sweetness": sum(r["sweetness"] or 0 for r in rows) / total,
        "avg_body": sum(r["body"] or 0 for r in rows) / total,
        "avg_fruitiness": sum(r["fruitiness"] or 0 for r in rows) / total,
        "total_count": total,
    }

    # 품종별 통계
    variety_map: dict = {}
    for r in rows:
        v = r.get("grape_variety") or ""
        if not v:
            continue
        if v not in variety_map:
            variety_map[v] = {"count": 0, "rating_sum": 0}
        variety_map[v]["count"] += 1
        variety_map[v]["rating_sum"] += r.get("rating") or 0
    stats["favorite_varieties"] = sorted(
        [{"grape_variety": v, "count": d["count"],
          "avg_rating": d["rating_sum"] / d["count"]}
         for v, d in variety_map.items()],
        key=lambda x: (-x["avg_rating"], -x["count"])
    )[:5]

    # 지역별 통계
    region_map: dict = {}
    for r in rows:
        reg = r.get("region") or ""
        if not reg:
            continue
        key = (reg, r.get("country") or "")
        if key not in region_map:
            region_map[key] = {"count": 0, "rating_sum": 0}
        region_map[key]["count"] += 1
        region_map[key]["rating_sum"] += r.get("rating") or 0
    stats["favorite_regions"] = sorted(
        [{"region": k[0], "country": k[1], "count": d["count"],
          "avg_rating": d["rating_sum"] / d["count"]}
         for k, d in region_map.items()],
        key=lambda x: (-x["avg_rating"], -x["count"])
    )[:5]

    # 색상 분포
    color_map: dict = {}
    for r in rows:
        c = r.get("color") or ""
        if not c:
            continue
        color_map[c] = color_map.get(c, 0) + 1
    stats["color_distribution"] = sorted(
        [{"color": c, "count": n} for c, n in color_map.items()],
        key=lambda x: -x["count"]
    )

    return stats


def get_unique_varieties(user_name=None) -> list:
    """고유 포도 품종 목록 반환"""
    query = _supabase.table("wines").select("grape_variety")
    if user_name:
        query = query.eq("user_name", user_name)
    res = query.execute()
    varieties = sorted({
        r["grape_variety"] for r in (res.data or [])
        if r.get("grape_variety")
    })
    return varieties


def get_unique_regions(user_name=None) -> list:
    """고유 지역 목록 반환"""
    query = _supabase.table("wines").select("region")
    if user_name:
        query = query.eq("user_name", user_name)
    res = query.execute()
    regions = sorted({
        r["region"] for r in (res.data or [])
        if r.get("region")
    })
    return regions
