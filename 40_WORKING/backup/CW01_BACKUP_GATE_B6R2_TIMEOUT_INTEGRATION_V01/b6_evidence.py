"""Candidate evidence contract. Uses the verified B5 normalizer without media I/O."""
from hashlib import sha256
from datetime import datetime
from ROUTABL_BackupEvidenceNormalizer_v0_1 import document, normalize, receipt_selection, timestamp

def selection(items):
    rows = []
    for path, category, raw in items:
        if not isinstance(raw, bytes):
            raise ValueError("SELECTION_BYTES_REQUIRED")
        rows.append(dict(relative_path=path, category=category, size=len(raw),
                         sha256=sha256(raw).hexdigest()))
    return receipt_selection({"records": rows})

def components(manifest_raw, read_component):
    manifest = document(manifest_raw)
    count = total = 0
    for row in manifest["files"]:
        expected_size = row["size"]
        size, digest = 0, sha256()
        for chunk in read_component(row):
            if not isinstance(chunk, bytes) or not chunk:
                raise ValueError("INVALID_COMPONENT_STREAM")
            size += len(chunk)
            if size > expected_size:
                raise ValueError("COMPONENT_SIZE")
            digest.update(chunk)
        if (size, digest.hexdigest()) != (expected_size, row["sha256"]):
            raise ValueError("COMPONENT_DIGEST_OR_SIZE")
        count += 1
        total += size
    if (count, total) != (manifest["components"], manifest["total_ciphertext_bytes"]):
        raise ValueError("COMPONENT_TOTALS")
    return dict(manifest_sha256=sha256(manifest_raw).hexdigest(), verified_count=count,
                verified_bytes=total, all_component_bytes_verified_in_fixture=True)

def evaluate(bundle, child, started, ended):
    """Validate byte inputs from independent fixture collectors and trusted run context."""
    if child["image_residual"] is not False or child["descendants_remaining"] is not False:
        return "BLOCKED_RESIDUAL", {}
    if child["outcome"] in ("TIMEOUT", "ESCAPED"):
        return "FAILED_CHILD", {}
    if (child["outcome"] == "LOCK_HELD" and type(child["exit_code"]) is int
            and child["exit_code"] == 0 and child["performed_work"] is False):
        return "SKIPPED_LOCK_HELD", {}
    if type(child["exit_code"]) is not int or child["exit_code"] != 0:
        return "FAILED_CHILD", {}
    if (child["outcome"], child["performed_work"]) not in (("CREATED", True), ("REUSED", False)) or type(child["performed_work"]) is not bool:
        return "NO_NEW_BACKUP_EVIDENCE", {}
    if not bundle.get("receipt_raw"):
        return "LOCAL_ORIGINAL_MISSING", {}
    selected = selection(bundle["selected_bytes"])
    report = normalize(bundle["local"], bundle["oneshot"], bundle["cas"],
                       bundle["registry_name"], bundle["registry_bytes"], bundle["cas_name"],
                       ended, receipt_raw=bundle["receipt_raw"], selected_now=selected)
    if report["status"] != "PARTIAL":
        return "EVIDENCE_INVALID", report
    if not report["current_registry_match"] or not report["same_day_kst"]:
        return "STALE_REGISTRY_BACKUP", report
    if report["current_selection_match"] is not True:
        return "SELECTION_CHANGED", report
    post_selection = selection(bundle["selected_bytes_after"])
    post_registry = sha256(bundle["registry_bytes_after"]).hexdigest()
    if post_selection != selected or post_registry != report["latest_registry_sha256"] or bundle["registry_name_after"] != report["latest_registry"]:
        return "SELECTION_OR_REGISTRY_CHANGED_DURING_RUN", report
    original_created = timestamp(document(bundle["receipt_raw"])["created_at_kst"])
    status_created = timestamp(report["local_created_at"])
    cas_created = timestamp(report["cas_created_at"])
    if child["outcome"] == "CREATED":
        if (not started <= original_created <= status_created <= cas_created <= ended
                or report["snapshot_id"] == bundle.get("prior_snapshot_id")):
            return "NO_NEW_BACKUP_EVIDENCE", report
    elif (report["snapshot_id"] != bundle.get("prior_snapshot_id")
          or report["local_receipt_sha256_reported"] != bundle.get("prior_receipt_sha256")
          or report["cas_manifest_sha256"] != bundle.get("prior_cas_sha256")
          or not cas_created <= started):
        return "REUSE_NOT_PREEXISTING", report
    reader = bundle.get("read_component")
    if reader is None:
        return "CAS_COMPONENTS_NOT_VERIFIED", report
    try:
        component_report = components(bundle["cas"], reader)
    except (OSError, ValueError, TypeError, KeyError):
        return "CAS_COMPONENTS_NOT_VERIFIED", report
    report["fixture_component_verification"] = component_report
    return ("CANDIDATE_NEW_EVIDENCE" if child["outcome"] == "CREATED" else "CANDIDATE_SAME_DAY_RECHECK"), report
