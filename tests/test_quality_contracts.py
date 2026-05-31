import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills/image-to-editable-ppt/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from PIL import Image  # noqa: E402
from validate_pptx import (  # noqa: E402
    ALLOWED_SOURCE_TYPES,
    alpha_edge_violations,
    page_contract_violations,
    quality_contract_violations,
)
from build_pptx_from_manifest import shape_xml  # noqa: E402


def base_manifest():
    return {
        "visual_layer_plan": {
            "strategy": "imagegen-first-layered-reconstruction",
            "primary_text_to_rebuild": [],
            "generated_background": {
                "asset_id": "bg_clean",
                "path": "generated/clean_background.png",
                "source_type": "imagegen-clean-background",
            },
            "generated_picture_assets": [],
            "art_text_assets": [],
            "native_text_boxes": [],
            "minimal_native_shapes": [],
            "background_decorative_text_policy": "none",
        },
        "visual_inventory": [],
        "background_strategy": {
            "mode": "imagegen-full-clean-background",
            "comparison_note": "background checked against source",
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
        "shapes": [],
    }


class QualityContractTest(unittest.TestCase):
    def test_quality_checks_are_required(self):
        violations = quality_contract_violations({})
        fields = {item["field"] for item in violations}
        self.assertIn("visual_layer_plan", fields)
        self.assertIn("visual_inventory", fields)
        self.assertIn("background_strategy", fields)
        self.assertIn("quality_checks", fields)

    def test_round_rect_requires_source_evidence(self):
        manifest = base_manifest()
        manifest["shapes"] = [{"type": "roundRect", "box_px": [0, 0, 100, 40]}]
        violations = quality_contract_violations(manifest)
        self.assertEqual(["shapes[0]"], [item["field"] for item in violations])

    def test_rect_does_not_need_corner_evidence(self):
        manifest = base_manifest()
        manifest["shapes"] = [{"type": "rect", "box_px": [0, 0, 100, 40]}]
        self.assertEqual([], quality_contract_violations(manifest))

    def test_source_derived_assets_are_allowed(self):
        self.assertIn("source-derived-rasterization", ALLOWED_SOURCE_TYPES)

    def test_imagegen_first_source_types_are_allowed(self):
        self.assertIn("imagegen-clean-background", ALLOWED_SOURCE_TYPES)
        self.assertIn("imagegen-picture-reconstruction", ALLOWED_SOURCE_TYPES)
        self.assertIn("imagegen-art-text", ALLOWED_SOURCE_TYPES)
        self.assertIn("imagegen-visual-asset", ALLOWED_SOURCE_TYPES)

    def test_full_slide_imagegen_background_can_sit_under_editable_text(self):
        manifest = {
            "slide": {"width": 13.333, "height": 7.5},
            "images": [{"path": "generated/clean_background.png", "left": 0, "top": 0, "width": 13.333, "height": 7.5}],
            "text_boxes": [{"text": "Editable title"}],
            "asset_provenance": [
                {"path": "generated/clean_background.png", "source_type": "imagegen-clean-background"}
            ],
        }
        self.assertEqual([], page_contract_violations(manifest))

    def test_full_slide_source_background_under_text_is_rejected(self):
        manifest = {
            "slide": {"width": 13.333, "height": 7.5},
            "images": [{"path": "source.png", "left": 0, "top": 0, "width": 13.333, "height": 7.5}],
            "text_boxes": [{"text": "Editable title"}],
            "asset_provenance": [{"path": "source.png", "source_type": "source-derived-rasterization"}],
        }
        reasons = [item["reason"] for item in page_contract_violations(manifest)]
        self.assertTrue(any("imagegen clean background" in reason for reason in reasons))

    def test_svg_assets_are_rejected(self):
        manifest = {
            "slide": {"width": 13.333, "height": 7.5},
            "images": [{"path": "assets/icon.svg", "left": 1, "top": 1, "width": 1, "height": 1}],
            "text_boxes": [],
            "asset_provenance": [{"path": "assets/icon.svg", "source_type": "imagegen-visual-asset"}],
        }
        reasons = [item["reason"] for item in page_contract_violations(manifest)]
        self.assertTrue(any("SVG assets are not allowed" in reason for reason in reasons))

    def test_round_rect_writes_ooxml_adjustment(self):
        xml = shape_xml(
            2,
            {
                "type": "roundRect",
                "box_px": [0, 0, 400, 200],
                "left": 0,
                "top": 0,
                "width": 4,
                "height": 2,
                "source_corner_radius_px": 10,
                "fill": "none",
                "stroke": "#000000",
            },
        )
        self.assertIn('prst="roundRect"', xml)
        self.assertIn('name="adj"', xml)
        self.assertIn('fmla="val 5000"', xml)

    def test_alpha_edge_helper_reports_visible_pixels_touching_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clipped.png"
            image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
            for x in range(0, 5):
                image.putpixel((x, 5), (0, 0, 255, 255))
            image.save(path)
            violations = alpha_edge_violations(path)
        self.assertTrue(violations)


if __name__ == "__main__":
    unittest.main()
