# search/services.py
from django.db.models import Q
from fuzzywuzzy import fuzz

from .utils import normalize_vi, expand_query_with_synonyms


def fuzzy_filter(queryset, field_name, query, threshold=70):
    """
    Fuzzy cho tên món / tên quán.
    Dùng riêng trong view (vd: nếu kết quả quá ít thì gọi fuzzy thêm).
    """
    results = []
    q = (query or "").lower()
    for obj in queryset:
        text = getattr(obj, field_name, "") or ""
        if fuzz.partial_ratio(q, text.lower()) >= threshold:
            results.append(obj)
    return results


def basic_search_dish(Dish, query):
    """
    Tìm món ăn:
      - normalize tiếng Việt
      - mở rộng synonyms
      - match theo name / category / tags (đã normalize)
    """
    expanded_queries = expand_query_with_synonyms(query)
    results = []
    seen_ids = set()

    for d in Dish.objects.all():
        name_norm = normalize_vi(d.name)
        cat_norm  = normalize_vi(d.category)
        tag_norm  = normalize_vi(d.tags)

        for q in expanded_queries:
            if q in name_norm or q in cat_norm or q in tag_norm:
                if d.id not in seen_ids:
                    results.append(d)
                    seen_ids.add(d.id)
                break

    return results


def basic_search_restaurant(Restaurant, query):
    """
    Tìm nhà hàng:
      - normalize tiếng Việt
      - mở rộng synonyms
      - match theo name / address / cuisine_type / description
    """
    expanded_queries = expand_query_with_synonyms(query)
    results = []
    seen_ids = set()

    for r in Restaurant.objects.all():
        name_norm    = normalize_vi(r.name)
        addr_norm    = normalize_vi(r.address)
        cuisine_norm = normalize_vi(r.cuisine_type)
        desc_norm    = normalize_vi(getattr(r, "description", ""))

        for q in expanded_queries:
            if (
                q in name_norm
                or q in addr_norm
                or q in cuisine_norm
                or q in desc_norm
            ):
                if r.id not in seen_ids:
                    results.append(r)
                    seen_ids.add(r.id)
                break

    return results
