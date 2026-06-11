#!/usr/bin/env python3
"""네이버 플레이스 방문자 리뷰 수집 → data/reviews.json (안경369 흥덕지구점)"""
import re, json, sys, datetime, urllib.request

PLACE_ID = "1435026950"
URL = f"https://pcmap.place.naver.com/place/{PLACE_ID}/review/visitor"
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
KST = datetime.timezone(datetime.timedelta(hours=9))


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Referer": URL})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    m = (re.search(r'__APOLLO_STATE__\s*=\s*({.*?})\s*;</script>', html, re.S)
         or re.search(r'__APOLLO_STATE__\s*=\s*({.*?});', html, re.S))
    if not m:
        raise RuntimeError("APOLLO_STATE 파싱 실패 (페이지 구조 변경 가능성)")
    data = json.loads(m.group(1))

    total = None
    for v in data.values():
        if isinstance(v, dict) and v.get("visitorReviewsTotal"):
            total = v["visitorReviewsTotal"]
            break

    def nick(ref):
        if isinstance(ref, dict) and "__ref" in ref:
            a = data.get(ref["__ref"], {})
            return a.get("nickname") or a.get("name") or "익명"
        return "익명"

    reviews = []
    for k, v in data.items():
        if k.startswith("VisitorReview:") and isinstance(v, dict) and v.get("body"):
            reviews.append({"nick": nick(v.get("author")),
                            "created": v.get("created") or "",
                            "body": v.get("body", "").strip()[:300]})
    return total, reviews[:5]


def main():
    total, reviews = fetch()
    if not total or not reviews:
        raise RuntimeError(f"데이터 비정상: total={total}, reviews={len(reviews)}")
    out = {
        "place_id": PLACE_ID,
        "fetched_at_kst": datetime.datetime.now(KST).isoformat(timespec="seconds"),
        "total": total,
        "reviews": reviews,
    }
    with open("data/reviews.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"OK total={total} reviews={len(reviews)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
