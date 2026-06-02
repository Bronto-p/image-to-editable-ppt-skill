#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPT_DIR = Path(__file__).resolve().parent


def run(command, cwd):
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_source(path):
    image = Image.new("RGB", (960, 540), "#f7f7f2")
    draw = ImageDraw.Draw(image)
    draw.rectangle([80, 80, 880, 460], outline="#222222", width=4)
    draw.text((130, 130), "Sample title", fill="#111111")
    image.save(path)


def make_page_artifacts(run_dir):
    page_dir = run_dir / "pages" / "page_001"
    generated = page_dir / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    background = generated / "clean_background.png"
    Image.new("RGB", (960, 540), "#f7f7f2").save(background)
    manifest = {
        "schema_version": 1,
        "slide": {"width": 13.333, "height": 7.5, "background": "#ffffff"},
        "source": {"path": "source.png", "width_px": 960, "height_px": 540},
        "visual_layer_plan": {
            "strategy": "imagegen-first-layered-reconstruction",
            "primary_text_to_rebuild": [{"id": "title", "text": "Sample title", "native_text_box": "tb_title"}],
            "generated_background": {
                "asset_id": "bg_clean",
                "path": "generated/clean_background.png",
                "source_type": "imagegen-clean-background",
                "remove": ["Sample title"],
                "preserve": ["border and blank canvas"],
            },
            "generated_picture_assets": [],
            "art_text_assets": [],
            "generated_visual_assets": [],
            "native_text_boxes": ["tb_title"],
            "minimal_native_shapes": [],
            "background_decorative_text_policy": "No decorative text is preserved.",
        },
        "text_inventory": ["Sample title"],
        "visual_inventory": [],
        "background_strategy": {
            "mode": "imagegen-full-clean-background",
            "source_consistency_contract": "Preserve blank canvas and border.",
            "removed_primary_text": ["Sample title"],
            "preserved_decorative_text": [],
            "comparison_note": "Smoke fixture background is intentionally blank.",
        },
        "quality_checks": {
            "font_size_calibrated": True,
            "visual_inventory_matched": True,
            "background_strategy_checked": True,
            "shape_corner_geometry_checked": True,
            "imagegen_visual_layers_recorded": True,
            "generated_background_checked": True,
            "primary_text_removed_from_background": True,
        },
        "text_boxes": [
            {
                "id": "tb_title",
                "text": "Sample title",
                "box_px": [130, 120, 500, 80],
                "font_size": 28,
                "color": "#111111",
                "z_index": 40,
            }
        ],
        "shapes": [],
        "images": [
            {
                "path": "generated/clean_background.png",
                "box_px": [0, 0, 960, 540],
                "z_index": 0,
                "alt": "imagegen clean background without primary text",
            }
        ],
        "asset_provenance": [
            {
                "path": "generated/clean_background.png",
                "source": "source.png",
                "source_type": "imagegen-clean-background",
                "provenance_note": "Smoke test synthetic clean background.",
                "imagegen_job_id": "smoke_bg",
            }
        ],
        "known_limits": [],
    }
    write_json(page_dir / "manifest.json", manifest)
    qa_review = {
        "schema_version": 1,
        "page_id": "page_001",
        "reviewed_assets": ["preview.png", "split_assets_contact.png"],
        "checks": {
            "visual_layer_matches_source": True,
            "primary_text_not_duplicated": True,
            "editable_text_present": True,
            "generated_assets_accounted_for": True,
            "background_identity_preserved": True,
        },
        "failures": [],
        "qa_note": "Smoke fixture preview and contact sheet generated.",
    }
    write_json(page_dir / "qa_review.json", qa_review)
    run([sys.executable, SCRIPT_DIR / "build_pptx_from_manifest.py", page_dir / "manifest.json", "--out", page_dir / "page.pptx", "--preview", page_dir / "preview.png"], SCRIPT_DIR.parent)
    run([sys.executable, SCRIPT_DIR / "make_page_contact_sheet.py", page_dir], SCRIPT_DIR.parent)
    run([sys.executable, SCRIPT_DIR / "validate_pptx.py", page_dir / "page.pptx", "--manifest", page_dir / "manifest.json", "--report", page_dir / "validation.json"], SCRIPT_DIR.parent)
    page_result = {
        "page_manifest": "manifest.json",
        "imagegen_jobs": "imagegen-jobs.json",
        "page_pptx": "page.pptx",
        "preview": "preview.png",
        "contact_sheet": "split_assets_contact.png",
        "validation": "validation.json",
        "qa_review": "qa_review.json",
        "page_result": "page_result.json",
        "qa_note": "Smoke fixture completed.",
        "known_limits": [],
    }
    write_json(page_dir / "page_result.json", page_result)
    prompts = page_dir / "prompts"
    prompts.mkdir(exist_ok=True)
    (prompts / "dispatch.txt").write_text("smoke dispatch\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory(prefix="image-to-editable-ppt-smoke-") as tmp:
        tmpdir = Path(tmp)
        source = tmpdir / "source.png"
        make_source(source)
        out_root = tmpdir / "out"
        run_dir = out_root / "demo"
        run(
            [
                sys.executable,
                SCRIPT_DIR / "prepare_deck_run.py",
                source,
                "--out-root",
                out_root,
                "--job-dir",
                "demo",
                "--max-concurrent-pages",
                "1",
            ],
            SCRIPT_DIR.parent,
        )
        if not run_dir.exists():
            raise SystemExit(f"relative --job-dir was not created under --out-root: {run_dir}")
        run([sys.executable, SCRIPT_DIR / "page_job_status.py", run_dir, "--json"], SCRIPT_DIR.parent)
        make_page_artifacts(run_dir)
        run([sys.executable, SCRIPT_DIR / "record_page_dispatch.py", run_dir, "--page", "1", "--agent-id", "smoke", "--prompt-file", "prompts/dispatch.txt"], SCRIPT_DIR.parent)
        run([sys.executable, SCRIPT_DIR / "record_page_result.py", run_dir, "--page", "1", "--agent-id", "smoke"], SCRIPT_DIR.parent)
        run([sys.executable, SCRIPT_DIR / "finalize_deck_run.py", run_dir], SCRIPT_DIR.parent)
        final = run_dir / "final" / "source_edited.pptx"
        if not final.exists():
            raise SystemExit(f"missing final deck: {final}")
        print(f"smoke_ok={final}")


if __name__ == "__main__":
    main()
