"""고객등록앱 글자 인식 결과 → 고객 필드 변환 규칙 시제품 v0.1
입력: 글자 인식(OCR) 결과 텍스트. 출력: name/phone1/phone2/dong/address/roadAddress/memo + 확인 필요 항목.
나중에 Kotlin으로 옮기고, 아래 샘플을 그대로 단위 테스트로 씀."""
import re

LABELS = ["고객", "부서", "담당", "전화1", "전화2", "출발", "도착", "의뢰", "위치"]
PHONE = re.compile(r"(0\d{1,2})[-. )]?(\d{3,4})[-. ]?(\d{4})")
EMPTY = {"", "*", "※", "**"}
# 업체명 뒤 괄호 메모: (731호X) (층확인) (접수자확인) (**번지확인)
NAME_NOTE = re.compile(r"\s*\(([^()]*)\)\s*$")
TAIL_STAR = re.compile(r"\s*\*\d+\s*$")
PARCEL = re.compile(
    r"^(?:(?P<city>대구|대구광역시|서울|부산|경북|경상북도|경남|경상남도)\s+)?"
    r"(?:(?P<gu>\S+[구군시])\s+)?"
    r"(?:(?P<eup>\S+[읍면])\s+)?"
    r"(?P<dong>\S+?[동리가])\s*(?P<lot>산?\d+(?:-\d+)?)(?:번지)?")
ROAD = re.compile(r"(?:(?P<pre>(?:\S+\s+){0,3}))?(?P<road>\S+(?:로|길)\s*\d+(?:-\d+)?)")

def phone(text):
    m = PHONE.search(text or "")
    return "-".join(m.groups()) if m else ""

NOTE_WORDS = re.compile(r"확인|요금|금지|착불|선입금|주의|기본\d*|입금|현금|카드|오지|불가")

def clean_name(raw):
    """v0.3 (2026-11-11 사용자 합의)
    - 업체명이 아닌 표기는 이름에서 떼어 메모로: (접수자확인)(층확인)(번지확인)(염색공단요금!!) ★트럭기본25★ ★절대착불금지★
    - (NNN호X) 기사 배제 표기와 끝의 ** 는 버림 (메모에도 안 남김)
    - 괄호 안이 다른 상호면 이름에 유지 + 별칭: 금강산업(금강포일)"""
    name = re.sub(r"\s*\(\s*\d+\s*호\s*[Xx×]\s*\)", "", raw.strip())
    name = re.sub(r"\*+\s*$", "", name).strip()
    notes = []
    def take(m):
        inner = m.group(1).strip("*! ")
        if NOTE_WORDS.search(inner):
            notes.append(m.group(0).strip().strip("()"))
            return ""
        return m.group(0)
    name = re.sub(r"\s*\(([^()]*)\)", take, name)
    name = re.sub(r"\s*(★([^★]*)★)", lambda m: (notes.append(m.group(1)), "")[1], name)
    name = re.sub(r"\s*/\s*", "/", name).strip()
    base = re.sub(r"\([^()]*\)|[*!★]", "", name).strip()
    aliases = ([base] if base != name else []) + [x.strip() for x in re.findall(r"\(([^()]*)\)", name)]
    return name, base, aliases, notes

def split_location(text, region_hint=""):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    first_dong = lines[0] if lines and re.fullmatch(r"\S+[동읍면리가]", lines[0]) else ""
    body = " ".join(lines[1:] if first_dong else lines)
    body = TAIL_STAR.sub("", body)
    out = {"dong": first_dong, "address": "", "roadAddress": "", "memo": ""}
    m = PARCEL.match(body)
    rest = body
    if m:
        addr = m.group(0)
        if not m.group("city") and not m.group("gu") and region_hint:
            addr = region_hint + " " + addr
        out["address"] = re.sub(r"번지$", "", addr).strip()
        out["dong"] = out["dong"] or m.group("dong")
        rest = body[m.end():]
        r = re.match(r"\s*\(([^()]*(?:로|길)\s*\d+[^()]*)\)", rest)
        if r:
            road = r.group(1).strip()
            if not re.match(r"(대구|서울|부산|경|충|전|강원|제주|인천|광주|대전|울산|세종)", road):
                road = " ".join(out["address"].split()[:2]) + " " + road if out["address"].startswith(("대구", "서울", "부산", "경")) else road
            out["roadAddress"] = road
            rest = rest[r.end():]
    else:
        r = ROAD.search(body)
        if r:
            out["roadAddress"] = (r.group("pre") or "").strip() + " " + r.group("road")
            out["roadAddress"] = out["roadAddress"].strip()
            rest = body[r.end():]
    out["memo"] = re.sub(r"^[\s.\-/>]+", "", rest).strip()
    return out

def parse_structured(text):
    """인성데이타 '출발지/의뢰지/도착지 상세' 화면"""
    fields, cur = {}, None
    for line in text.splitlines():
        s = line.strip()
        hit = next((l for l in LABELS if s == l or s.startswith(l + " ")), None)
        if hit:
            cur = hit
            fields[cur] = s[len(hit):].strip()
        elif cur:
            fields[cur] = (fields[cur] + "\n" + s).strip()
    name, base, aliases, notes = clean_name(fields.get("고객", ""))
    region = fields.get("출발", "") or fields.get("도착", "") or fields.get("의뢰", "")
    region = region if re.fullmatch(r"\S+\s+\S+[구군시]", region) else "대구 서구"
    loc = split_location(fields.get("위치", ""), region)
    memo = ["주의: " + " ".join(notes)] if notes else []
    who = re.sub(r"마일리지.*", "", fields.get("담당", "")).strip()
    if who not in EMPTY and who != "사업자등록증": memo.append("담당: " + who)
    if loc["memo"]: memo.append("찾아가는 길: " + loc["memo"])
    p2 = fields.get("전화2", "")
    return {"name": name, "base_name": base, "searchAliases": " ".join(aliases), "phone1": phone(fields.get("전화1")), "phone2": "" if p2 in EMPTY else phone(p2),
            "dong": loc["dong"], "address": loc["address"], "roadAddress": loc["roadAddress"],
            "memo": "\n".join(memo), "source": "structured"}

def parse_free(text):
    """카톡 등 비정형: 전화·주소는 자동, 업체명은 후보를 보여주고 사용자가 고름"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ph = next((phone(l) for l in lines if phone(l)), "")
    addr_i = next((i for i, l in enumerate(lines) if re.search(r"(로|길)\s*\d+|[동리]\s*\d+(-\d+)?", l) and not PHONE.search(l)), None)
    addr = lines[addr_i] if addr_i is not None else ""
    if addr_i is not None and addr_i + 1 < len(lines) and re.fullmatch(r"\d+(-\d+)?", lines[addr_i + 1]):
        addr += " " + lines[addr_i + 1]       # 줄바꿈으로 잘린 번지
    loc = split_location(addr) if addr else {"dong": "", "address": "", "roadAddress": "", "memo": ""}
    stop = {i for i, l in enumerate(lines) if PHONE.search(l)} | ({addr_i} if addr_i is not None else set())
    anchor = min(stop) if stop else len(lines)
    candidates = [l for l in lines[:anchor] if len(l) <= 30 and not re.search(r"[.?!]$|습니다|입니다", l)]
    return {"name": candidates[-1] if candidates else "", "name_candidates": candidates[-3:], "phone1": ph, "phone2": "",
            "dong": loc["dong"], "address": loc["address"], "roadAddress": loc["roadAddress"], "memo": "", "source": "free"}
