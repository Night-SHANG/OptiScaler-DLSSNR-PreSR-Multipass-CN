import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from loclib import find_candidates

RULES = json.loads((ROOT / "Localization" / "scanner-rules.json").read_text(encoding="utf-8"))


class FullUiCoverageTests(unittest.TestCase):
    def sources(self, text: str, rel: str):
        return {c.source: c for c in find_candidates(text, rel, RULES)}

    def test_dlssnr_help_marker_and_wrapped_checkbox_are_discovered(self):
        text = '''
        PipelineUi::CheckboxWrapped("Enable Neural Rendering", &enabled, 200.0f);
        HelpMarker("Enable NR processing and show the result.");
        '''
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_Menu.cpp")
        self.assertIn("Enable Neural Rendering", got)
        self.assertIn("Enable NR processing and show the result.", got)

    def test_deferred_slider_label_is_catalogued_without_rewriting_logic_key(self):
        text = 'DeferredSlider("Intensity", &config->DlssNrIntensity, 0.0f, 2.0f, 1.0f);\n'
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_MenuModel.cpp")
        self.assertIn("Intensity", got)
        self.assertFalse(got["Intensity"].rewrite)

    def test_dlssnr_snprintf_visible_format_is_discovered(self):
        text = 'snprintf(lbl, sizeof(lbl), "Paper white (editing point %d)", index + 1);\n'
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_MenuInput.cpp")
        self.assertIn("Paper white (editing point %d)", got)

    def test_pipeline_ui_dynamic_fragments_are_discovered(self):
        text = '''
        const auto add = [&](int lane, int row, const char* title, std::string detail, int section = -1) { return 0; };
        add(0, 0, "Prepare NR input", "HDR / exposure / " + std::to_string(scalePercent) + "%");
        add(0, 1, "NR model", std::to_string(passes) + (passes == 1 ? " pass" : " passes"));
        '''
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_PipelineUi.h")
        for expected in ("Prepare NR input", "HDR / exposure / ", "NR model", " pass", " passes"):
            self.assertIn(expected, got)

    def test_pipeline_section_name_return_literals_are_discovered(self):
        text = '''
        inline const char* SectionName(Section section) {
            if (section == Section::Placement) return "Placement";
            if (section == Section::Input) return "Input";
            return "Model passes";
        }
        '''
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_PipelineUi.h")
        for expected in ("Placement", "Input", "Model passes"):
            self.assertIn(expected, got)

    def test_overlay_conditional_labels_are_discovered(self):
        text = '''
        const char* leftText = swap ? "DLSS NR : ON" : "DLSS NR : OFF";
        const char* rightText = swap ? "DLSS NR : OFF" : "DLSS NR : ON";
        '''
        got = self.sources(text, "OptiScaler/dlssnr/DlssNr_MenuOverlay.cpp")
        self.assertIn("DLSS NR : ON", got)
        self.assertIn("DLSS NR : OFF", got)


if __name__ == "__main__":
    unittest.main()
