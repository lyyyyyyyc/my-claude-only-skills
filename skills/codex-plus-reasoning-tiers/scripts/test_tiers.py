import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tiers


class NativeMetadataRegressionTest(unittest.TestCase):
    def test_patch_persists_fields_consumed_by_native_catalog_generator(self):
        slug = "gpt-6.1-terra"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            catalog_file = home / "model-catalogs" / "fixture.json"
            catalog_file.parent.mkdir()
            catalog_file.write_text(json.dumps({"models": [{
                "slug": slug,
                "display_name": slug,
                "default_reasoning_level": "medium",
                "supported_reasoning_levels": [{"effort": "high", "description": "High"}],
            }]}), encoding="utf-8")
            config = 'model_catalog_json = "model-catalogs/fixture.json"\n'
            (home / "config.toml").write_bytes(config.encode("utf-8"))
            original_config = (home / "config.toml").read_bytes()
            settings = {
                "activeRelayId": "fixture",
                "relayProfiles": [{
                    "id": "fixture",
                    "configContents": config,
                    "modelMetadata": json.dumps({"unrelated": {"description": "Preserved"}}),
                }],
            }

            class Session:
                def bridge(self, route, payload=None):
                    if route == "/settings/get":
                        return copy.deepcopy(settings)
                    settings.update(payload)
                    return copy.deepcopy(settings)

                def close(self):
                    pass

            with (
                patch.object(tiers, "read_settings", return_value=copy.deepcopy(settings)),
                patch.object(tiers, "codex_home", return_value=home),
                patch.object(tiers, "probe", return_value={"available": True}),
                patch.object(tiers, "CdpSession", Session),
            ):
                self.assertEqual(tiers.patch(slug, ["max"], "max", False), 0)

            metadata = json.loads(settings["relayProfiles"][0]["modelMetadata"])
            entry = metadata[slug]
            self.assertIn("supported_reasoning_levels", entry,
                          "UI metadata keys are ignored by the native catalog generator")
            self.assertEqual(entry["default_reasoning_level"], "max")
            self.assertIn("max", [item["effort"] for item in entry["supported_reasoning_levels"]])
            self.assertNotIn("supportedReasoningEfforts", entry)
            self.assertEqual(metadata["unrelated"], {"description": "Preserved"})
            self.assertEqual(list(catalog_file.parent.glob("*.json")), [catalog_file])
            self.assertEqual((home / "config.toml").read_bytes(), original_config)


if __name__ == "__main__":
    unittest.main()
