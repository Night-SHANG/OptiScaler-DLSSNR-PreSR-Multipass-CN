import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import localize_source


class DlssNrLocalizeSourceTests(unittest.TestCase):
    def test_deferred_slider_translates_display_without_changing_english_logic_key(self):
        source = '''
        static bool DeferredSlider(const char* label) {
            const ImGuiID id = ImGui::GetID(label);
            ImGui::SliderFloat(label, &value, 0.0f, 2.0f, "%.2f");
            if (std::strcmp(label, "Intensity") == 0) return true;
            return false;
        }
        '''
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "DlssNr_MenuModel.cpp"
            path.write_text(source, encoding="utf-8")
            localize_source.patch_dlssnr_dynamic_helpers(path, "OptiScaler/dlssnr/DlssNr_MenuModel.cpp")
            patched = path.read_text(encoding="utf-8")
        self.assertIn('ImGui::SliderFloat(OptiScalerCN::Loc::TL(label).c_str(),', patched)
        self.assertIn('std::strcmp(label, "Intensity")', patched)
        self.assertNotIn('std::strcmp(OptiScalerCN::Loc::TL(label).c_str()', patched)


if __name__ == "__main__":
    unittest.main()
