#!/usr/bin/env python3
import argparse

from deck_run_state import find_page, load_jobs, now_iso, read_json, run_dir_from_target, save_jobs, write_json


FAILURE_TYPES = {
    "missing_text",
    "clipped_text",
    "wrong_text_wrapping",
    "missing_asset",
    "bad_asset_split",
    "bad_generated_background",
    "primary_text_left_in_background",
    "bad_generated_picture_asset",
    "bad_art_text_asset",
    "bad_asset_provenance",
    "layout_drift",
    "broken_pptx",
    "notes_mismatch",
    "imagegen_blocked",
    "svg_fallback_used",
    "native_shape_complex_visual",
    "validation_failed",
    "qa_failed",
}


def next_repair_id(queue, page_id):
    return f"repair_{len(queue.get('items', [])) + 1:03d}_{page_id}"


def validation_failed(run_dir, page):
    validation = run_dir / page.get("validation", "")
    if not validation.exists():
        return True
    try:
        return read_json(validation).get("passed") is not True
    except Exception:
        return True


def add_item(queue, page, args, evidence):
    item = {
        "repair_item_id": next_repair_id(queue, page["page_id"]),
        "page_id": page["page_id"],
        "failure_type": args.failure_type,
        "reason": args.reason,
        "evidence": evidence,
        "suggested_scope": args.suggested_scope,
        "required_output": args.required_output,
        "previous_attempt_summary": args.previous_attempt_summary,
        "status": "queued",
        "created_at": now_iso(),
    }
    queue.setdefault("items", []).append(item)
    page.setdefault("repair", []).append(item)
    page["status"] = "repair_needed"
    return item


def main():
    parser = argparse.ArgumentParser(description="Create repair queue items from page validation or explicit QA evidence.")
    parser.add_argument("run", help="Run directory or deck_manifest.json")
    parser.add_argument("--page", action="append", help="page_001 or 1; may be repeated")
    parser.add_argument("--from-validation", action="store_true")
    parser.add_argument("--reason", default="page validation or QA requires repair")
    parser.add_argument("--failure-type", default="validation_failed", choices=sorted(FAILURE_TYPES))
    parser.add_argument("--suggested-scope", default="smallest failing page-local element or generated asset")
    parser.add_argument("--required-output", default="updated manifest, page.pptx, preview, contact sheet, validation, qa_review, page_result")
    parser.add_argument("--previous-attempt-summary", default="See page_result.json, validation.json, qa_review.json, preview.png, and split_assets_contact.png.")
    parser.add_argument("--evidence", action="append", default=[])
    args = parser.parse_args()

    run_dir = run_dir_from_target(args.run)
    jobs = load_jobs(run_dir)
    queue_path = run_dir / "repair_queue.json"
    queue = read_json(queue_path, default={"schema_version": 1, "items": []})
    targets = []
    if args.page:
        targets = [find_page(jobs, page) for page in args.page]
    elif args.from_validation:
        targets = [
            page
            for page in jobs.get("pages", [])
            if page.get("status") == "recorded" and validation_failed(run_dir, page)
        ]
    else:
        raise SystemExit("Use --page or --from-validation")

    created = []
    for page in targets:
        if page.get("status") != "recorded":
            raise SystemExit(f"{page['page_id']} must be recorded before repair queueing; got {page.get('status')}")
        evidence = list(args.evidence)
        if not evidence:
            evidence.append(page.get("validation"))
            evidence.append(page.get("result", {}).get("outputs", {}).get("qa_review") or f"{page.get('page_dir')}/qa_review.json")
        evidence = [item for item in evidence if item]
        created.append(add_item(queue, page, args, evidence))

    queue["updated_at"] = now_iso()
    write_json(queue_path, queue)
    save_jobs(run_dir, jobs)
    print(f"queued={len(created)}")


if __name__ == "__main__":
    main()
