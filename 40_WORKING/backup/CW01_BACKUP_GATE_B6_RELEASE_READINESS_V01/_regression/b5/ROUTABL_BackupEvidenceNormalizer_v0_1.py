"""B5 candidate for validating receipt metadata. It accepts bytes, with no I/O."""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

KST = timezone(timedelta(hours=9))
SHA = re.compile(r"[a-f0-9]{64}")
MANIFEST = re.compile(r"asset_manifest_v0\.[0-9]+\.json")
SNAPSHOT = re.compile(r"ASSET_V21_[0-9]{8}_[0-9]{6}_KST_[0-9]+")
ANCHOR = re.compile(r"NAS_MANUAL_ASSET_V21_[A-Za-z0-9_]{1,150}")
NAS_BASE = PurePosixPath("/Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots")
MAX_JSON = 16 * 1024 * 1024

class InvalidEvidence(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise InvalidEvidence(reason)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def unique(pairs):
    data = {}
    for key, value in pairs:
        require(key not in data, "DUPLICATE_JSON_KEY")
        data[key] = value
    return data

def document(raw):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_JSON, "JSON_SIZE_OR_TYPE")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    require(isinstance(data, dict), "JSON_OBJECT_REQUIRED")
    return data

def matched(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None

def positive(value):
    return type(value) is int and value > 0

def timestamp(text):
    dt = datetime.fromisoformat(text)
    require(dt.utcoffset() is not None, "MISSING_TIMEZONE")
    return dt.astimezone(KST)

def path_name(value):
    require(isinstance(value, str) and bool(value) and "\\" not in value
            and all(ord(char) >= 32 for char in value), "UNSAFE_RELATIVE_PATH")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(part not in ("", ".", "..") for part in value.split("/"))
            and path.as_posix() == value, "UNSAFE_RELATIVE_PATH")
    return value

def sized_rows(rows, limit):
    require(isinstance(rows, list) and 0 < len(rows) <= limit, "ROW_COUNT_OUT_OF_RANGE")
    seen = set()
    for row in rows:
        require(isinstance(row, dict), "ROW_TYPE")
        path = path_name(row["relative_path"])
        require(path not in seen and matched(SHA, row["sha256"]) and
                type(row["size"]) is int and row["size"] >= 0, "ROW_INTEGRITY")
        seen.add(path)
        yield row

def receipt_selection(receipt):
    rows = list(sized_rows(receipt["records"], 100000))
    selected = []
    for row in rows:
        require(row["category"] in ("registry", "project", "managed"), "SELECTION_CATEGORY")
        selected.append([row["relative_path"], row["sha256"], row["size"], row["category"]])
    raw = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                  for row in sorted(selected))
    return digest(raw.encode("utf-8")), len(rows), sum(row["size"] for row in rows)

def check_local_receipt(raw, local, recorded):
    require(digest(raw) == local["receipt_sha256"], "LOCAL_RECEIPT_HASH_MISMATCH")
    receipt = document(raw)
    require(receipt["type"] == "ROUTABL_ASSET_V21_AES256_SELECTIVE_SNAPSHOT"
            and receipt["snapshot_name"] == local["snapshot_name"]
            and receipt["all_snapshot_sha256_verified"] is True, "LOCAL_RECEIPT_ID_OR_STATE")
    require(timestamp(receipt["created_at_kst"]).date() == timestamp(local["created_at_kst"]).date()
            and timestamp(receipt["created_at_kst"]) <= timestamp(local["created_at_kst"]),
            "LOCAL_RECEIPT_TIME_ORDER")
    require((receipt["manifest_name"], receipt["manifest_sha256"], receipt["selection_sha256"])
            == recorded[:3], "LOCAL_RECEIPT_REGISTRY_SELECTION")
    require((receipt["source_manifest"], receipt["source_manifest_sha256"]) == recorded[:2],
            "LOCAL_RECEIPT_SOURCE_BINDING")
    require(receipt["file_count"] == recorded[3] and receipt_selection(receipt) == recorded[2:],
            "LOCAL_SELECTION_RECOMPUTE_MISMATCH")
    summary = receipt["summary"]
    require((summary["manifest_name"], summary["manifest_sha256"], summary["selection_sha256"],
             summary["total_files"], summary["total_source_bytes"]) == recorded,
            "LOCAL_RECEIPT_SUMMARY_MISMATCH")

def validate_cas(cas):
    require(cas["type"] == "ROUTABL_CIPHERTEXT_CAS_V01" and cas["completed"] is True,
            "CAS_NOT_COMPLETE")
    count = total = 0
    for row in sized_rows(cas["files"], 10000):
        ref = row["reference"]
        require(isinstance(ref, dict) and ref["type"] in ("anchor", "blob"), "CAS_REFERENCE_TYPE")
        if ref["type"] == "anchor":
            anchor = ref["snapshot"]
            path = PurePosixPath(anchor)
            require(path.parent == NAS_BASE and matched(ANCHOR, path.name)
                    and path.as_posix() == anchor and anchor == cas["anchor_snapshot"], "CAS_ANCHOR_NAME")
            require(path_name(ref["relative_path"]) == row["relative_path"], "CAS_REFERENCE_PATH")
        count += 1
        total += row["size"]
    require(positive(cas["components"]) and positive(cas["total_ciphertext_bytes"]) and
            (count, total) == (cas["components"], cas["total_ciphertext_bytes"]), "CAS_TOTALS_MISMATCH")

def _normalize(local, oneshot, cas_raw, manifest_name, manifest_bytes, cas_name,
               observed_at, receipt_raw=None, selected_now=None):
    require(matched(MANIFEST, manifest_name) and isinstance(manifest_bytes, bytes)
            and bool(manifest_bytes), "LATEST_REGISTRY_INPUT")
    latest_hash = digest(manifest_bytes)
    require(isinstance(observed_at, datetime) and observed_at.utcoffset() is not None,
            "OBSERVATION_TIMEZONE_REQUIRED")
    now = observed_at.astimezone(KST)
    loc = document(local)
    job = document(oneshot)
    cas = document(cas_raw)
    snapshot, receipt_hash = loc["snapshot_name"], loc["receipt_sha256"]
    require(matched(SNAPSHOT, snapshot) and matched(SHA, receipt_hash), "LOCAL_ID_OR_RECEIPT_HASH")
    created = timestamp(loc["created_at_kst"])
    cas_created = timestamp(cas["created_kst"])
    job_time = timestamp(job["verified_at_kst"])
    require(created <= cas_created <= job_time <= now, "INVALID_CHRONOLOGY")
    require(loc["status"] == "SUCCESS" and loc["locked_after_backup"] is True
            and loc["sha256_verified"] is True, "LOCAL_STATUS_INCOMPLETE")
    recorded = (loc["manifest_name"], loc["manifest_sha256"], loc["selection_sha256"],
                loc["file_count"], loc["source_bytes"])
    require(matched(MANIFEST, recorded[0]) and all(matched(SHA, h) for h in recorded[1:3])
            and all(positive(n) for n in recorded[3:]), "LOCAL_FINGERPRINT_INVALID")
    validate_cas(cas)
    require(cas_name == "CAS_" + snapshot + ".json"
            and job["nas_cas_manifest"] == cas_name and job["local_snapshot"] == snapshot
            and job["status"] == "SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS"
            and job["aes_image_detached"] is True and job["manifest_name"] == recorded[0]
            and job["local_file_count"] == recorded[3] and job["cas_components"] == cas["components"],
            "ONESHOT_LINK_MISMATCH")
    require(cas["local_snapshot_name"] == snapshot
            and all(row["local_receipt_sha256"] == receipt_hash
                    and (row["manifest_sha256"], row["selection_sha256"]) == recorded[1:3]
                    for row in (job, cas)), "CAS_LINEAGE_MISMATCH")
    if receipt_raw is not None:
        check_local_receipt(receipt_raw, loc, recorded)
    if selected_now is not None:
        require(isinstance(selected_now, tuple) and len(selected_now) == 3 and
                matched(SHA, selected_now[0]) and all(positive(n) for n in selected_now[1:]),
                "CURRENT_SELECTION_INPUT")
    registry_current = (manifest_name, latest_hash) == recorded[:2]
    today = created.date() == now.date()
    selection_current = None if selected_now is None else selected_now == recorded[2:]
    return dict(scope="RECEIPT_METADATA_ONLY", observed_at=now.isoformat(), status="PARTIAL",
                chain="METADATA_LINKED", snapshot_id=snapshot, local_created_at=created.isoformat(),
                same_day_kst=today, latest_registry=manifest_name, latest_registry_sha256=latest_hash,
                reported_registry=recorded[0], reported_registry_sha256=recorded[1],
                current_registry_match=registry_current, reported_selection_sha256=recorded[2],
                reported_selected_files=recorded[3], reported_selected_bytes=recorded[4],
                current_selection_match=selection_current, local_receipt_sha256_reported=receipt_hash,
                local_receipt_bytes_verified=receipt_raw is not None,
                selection_recomputed_from_receipt=receipt_raw is not None,
                local_lock_and_integrity="HISTORICAL_STATUS_REPORT_ONLY",
                cas_manifest_sha256=digest(cas_raw), cas_created_at=cas_created.isoformat(),
                cas_completed=True, cas_components=cas["components"], cas_referenced_bytes=cas["total_ciphertext_bytes"],
                cas_manifest_structure="VERIFIED", current_cas_component_sha256="NOT_PERFORMED",
                historical_oneshot="SUCCESS_CLAIM_BOUND_TO_METADATA", actual_backup_verified=False)

def normalize(*args, **kwargs):
    try:
        return _normalize(*args, **kwargs)
    except InvalidEvidence as error:
        return dict(scope="RECEIPT_METADATA_ONLY", status="FAIL", reason=str(error),
                    actual_backup_verified=False)
    except (ValueError, UnicodeError, KeyError, TypeError, OverflowError):
        return dict(scope="RECEIPT_METADATA_ONLY", status="FAIL", reason="MALFORMED_OR_MISSING_FIELD",
                    actual_backup_verified=False)
