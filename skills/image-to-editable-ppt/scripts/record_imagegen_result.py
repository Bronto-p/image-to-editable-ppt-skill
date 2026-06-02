#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path

from deck_run_state import now_iso, read_json, resolve_inside, sha256_file, write_json


def parse_input_roles(values):
    roles = []
    for value in values or []:
        if "=" in value:
            role, path = value.split("=", 1)
            roles.append({"role": role.strip(), "path": path.strip()})
        else:
            roles.append({"role": "reference", "path": value.strip()})
    return roles


def load_metadata(args):
    metadata = {}
    if args.metadata_file:
        metadata.update(json.loads(Path(args.metadata_file).read_text(encoding="utf-8")))
    if args.metadata_json:
        metadata.update(json.loads(args.metadata_json))
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Copy a selected $imagegen output into a page directory and record provenance.")
    parser.add_argument("page_dir")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source-image", required=True)
    parser.add_argument("--dest", required=True, help="Destination path relative to page_dir")
    parser.add_argument("--role", default="asset", help="clean_base, asset_sheet, repair_asset, etc.")
    parser.add_argument("--intended-layer", help="clean-background, picture-asset, art-text-asset, visual-asset, repair")
    parser.add_argument("--source-type", default="imagegen")
    parser.add_argument("--tool")
    parser.add_argument("--model")
    parser.add_argument("--input-role", action="append", default=[], help="Input role as role=/path/to/image or just /path/to/image")
    parser.add_argument("--prompt-file")
    parser.add_argument("--metadata-json")
    parser.add_argument("--metadata-file")
    parser.add_argument("--note")
    args = parser.parse_args()

    page_dir = Path(args.page_dir).resolve()
    if not page_dir.exists():
        raise SystemExit(f"Page dir does not exist: {page_dir}")
    source = Path(args.source_image).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Generated image does not exist: {source}")
    dest = resolve_inside(page_dir, args.dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source != dest:
        shutil.copy2(source, dest)
    prompt_path = None
    prompt_sha256 = None
    if args.prompt_file:
        prompt_path = Path(args.prompt_file).expanduser()
        if not prompt_path.is_absolute():
            prompt_path = page_dir / prompt_path
        prompt_path = prompt_path.resolve()
        if not prompt_path.exists():
            raise SystemExit(f"Prompt file does not exist: {prompt_path}")
        prompt_sha256 = sha256_file(prompt_path)

    jobs_path = page_dir / "imagegen-jobs.json"
    jobs = read_json(jobs_path, default={"schema_version": 1, "jobs": []})
    existing = None
    for item in jobs.get("jobs", []):
        if item.get("job_id") == args.job_id:
            existing = item
            break
    if existing is None:
        existing = {"job_id": args.job_id}
        jobs.setdefault("jobs", []).append(existing)
    existing.update(
        {
            "role": args.role,
            "intended_layer": args.intended_layer or args.role,
            "source_type": args.source_type,
            "tool": args.tool,
            "model": args.model,
            "status": "recorded",
            "source_image": str(source),
            "input_image_roles": parse_input_roles(args.input_role),
            "output": dest.relative_to(page_dir).as_posix(),
            "output_sha256": sha256_file(dest),
            "prompt_file": str(prompt_path) if prompt_path else None,
            "prompt_sha256": prompt_sha256,
            "metadata": load_metadata(args),
            "note": args.note,
            "completed_at": now_iso(),
            "recorded_at": now_iso(),
        }
    )
    jobs["updated_at"] = now_iso()
    write_json(jobs_path, jobs)
    print(dest)


if __name__ == "__main__":
    main()
