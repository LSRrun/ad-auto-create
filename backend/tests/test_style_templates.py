import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import styles
from app.ai.schemas import ModelConfig
from app.style_templates import repository
from app.style_templates.html_sanitizer import apply_bindings, sanitize_html
from app.style_templates.layout_compiler import compile_reference_style
from app.style_templates.schemas import DraftUpdate, ReferenceStyleSpec
from app.style_templates.service import import_html_template, import_reference_template, publish, update_draft


class HtmlSanitizerTests(unittest.TestCase):
    def test_removes_scripts_events_and_remote_resources(self):
        result = sanitize_html(
            """
            <article onclick="steal()">
              <script>window.parent.location='https://bad.example'</script>
              <h1 data-ad-field="headline">Old title</h1>
              <img data-ad-field="productImage" src="https://bad.example/tracker.png" onerror="steal()">
              <p>Long product description for automatic mapping.</p>
            </article>
            """
        )
        self.assertNotIn("<script", result.html.lower())
        self.assertNotIn("onclick", result.html.lower())
        self.assertNotIn("onerror", result.html.lower())
        self.assertNotIn("bad.example", result.html)
        self.assertEqual(result.bindings["headline"], "node-2")
        self.assertIn("productImage", result.bindings)

    def test_replaces_existing_mapping_when_user_changes_it(self):
        result = sanitize_html("<article><h1>First</h1><h2>Second</h2><img src=\"{{productImage}}\"></article>")
        second_heading = next(node["id"] for node in result.nodes if node["tag"] == "h2")
        bindings = {**result.bindings, "headline": second_heading}
        bindings.pop("productName", None)
        changed = apply_bindings(result.html, bindings)
        self.assertIn(f'data-template-node="{second_heading}" data-ad-field="headline"', changed)


class ReferenceCompilerTests(unittest.TestCase):
    def test_compiles_validated_layout_without_scripts(self):
        spec = ReferenceStyleSpec.model_validate(
            {
                "name": "Warm editorial",
                "description": "Warm split layout",
                "palette": {"background": "#F0ECE5", "surface": "#FFFFFF", "text": "#202020", "accent": "#896C4B"},
                "product_slot": {"x": 470, "y": 120, "width": 480, "height": 800},
                "text_slots": [
                    {"field": "headline", "x": 60, "y": 210, "width": 350, "height": 180, "color": "#202020"},
                    {"field": "productName", "x": 60, "y": 420, "width": 350, "height": 80, "color": "#896C4B"},
                ],
                "copy_tone": "Restrained and warm",
                "visual_direction": "Warm editorial bathroom advertising",
            }
        )
        template, bindings = compile_reference_style(spec)
        self.assertNotIn("<script", template.lower())
        self.assertIn('data-ad-field="productImage"', template)
        self.assertIn("headline", bindings)
        self.assertIn("productName", bindings)


class TemplateLifecycleTests(unittest.TestCase):
    def test_html_draft_can_be_updated_published_and_listed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            drafts = root / "drafts"
            templates = root / "templates"
            with (
                patch.object(repository, "DRAFTS_DIR", drafts),
                patch.object(repository, "TEMPLATES_DIR", templates),
                patch.object(styles, "TEMPLATES_DIR", templates),
            ):
                draft = import_html_template(
                    "warm.html",
                    b'<article style="background:#f0ece5"><h1 data-ad-field="headline">Title</h1><img data-ad-field="productImage" src="{{productImage}}"></article>',
                )
                updated = update_draft(
                    draft["draft_id"],
                    DraftUpdate(name="My reusable style", description="A reusable imported HTML style"),
                )
                self.assertEqual(updated["name"], "My reusable style")
                published = publish(draft["draft_id"])
                self.assertTrue((templates / published["id"] / "manifest.json").exists())
                self.assertEqual(styles.get_style(published["id"])["render_mode"], "sandbox_html")


class ReferenceLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_reference_analysis_result_becomes_reusable_draft(self):
        spec = ReferenceStyleSpec.model_validate(
            {
                "name": "Reference style",
                "description": "Generated from a reference image",
                "palette": {"background": "#F0ECE5", "surface": "#FFFFFF", "text": "#202020", "accent": "#896C4B"},
                "product_slot": {"x": 470, "y": 120, "width": 480, "height": 800},
                "text_slots": [
                    {"field": "headline", "x": 60, "y": 210, "width": 350, "height": 180, "color": "#202020"},
                    {"field": "productName", "x": 60, "y": 420, "width": 350, "height": 80, "color": "#896C4B"},
                ],
                "copy_tone": "Restrained and warm",
                "visual_direction": "Warm editorial bathroom advertising",
            }
        )
        config = ModelConfig(provider="custom", model="vision-model", base_url="https://example.com/v1", api_key="test")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch.object(repository, "DRAFTS_DIR", root / "drafts"),
                patch.object(repository, "TEMPLATES_DIR", root / "templates"),
                patch("app.style_templates.service.analyze_reference", return_value=spec),
            ):
                draft = await import_reference_template("reference.png", b"fake-image", "image/png", config, "")
                self.assertEqual(draft["source_type"], "reference_image")
                self.assertEqual(draft["bindings"]["productImage"], "slot-product-image")
                self.assertIn('data-ad-field="headline"', draft["templateHtml"])


if __name__ == "__main__":
    unittest.main()
