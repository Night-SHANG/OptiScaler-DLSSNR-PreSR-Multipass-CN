import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from ui_scan import find_ui_candidates
RULES = json.loads((ROOT / 'Localization/scanner-rules.json').read_text())
REL = 'OptiScaler/dlssnr/DlssNr_MenuControls.cpp'
class PreSrCoverageTests(unittest.TestCase):
    def test_moved_controls_and_model_names(self):
        code = '''static const char* names[] = { "Automatic", "Original", "Optimized" };
        DeferredSlider("Intensity", &x); Slider("Halo radius (NR pixels)", x);
        Checkbox("Reject stale history", x); slider("Skin colour", x);
        if (std::strcmp(label, "Intensity") == 0) {}'''
        got = find_ui_candidates(code, REL, RULES)
        for source in ('Automatic', 'Original', 'Optimized', 'Intensity', 'Halo radius (NR pixels)', 'Reject stale history', 'Skin colour'):
            self.assertIn(source, {c.source for c in got})
        self.assertEqual(2, sum(c.source == 'Intensity' for c in got))
    def test_pass_format_is_runtime_safe_candidate(self):
        got = find_ui_candidates('const auto label = std::format("Pass {}", pass + 1);', REL, RULES)
        self.assertEqual([('Pass {}', 'nested:std::format')], [(c.source,c.callee) for c in got])
    def test_non_ui_not_captured(self):
        got = find_ui_candidates('Slider("Internal", x); const auto label=std::format("Pass {}", x);', 'OptiScaler/dlssnr/Engine.cpp', RULES)
        self.assertEqual([], got)

    def test_combo_options_preserve_nul_delimiters(self):
        code = r'ImGui::Combo("Edit as", &edit, "Difference (added)\0Ratio (multiplied)\0");'
        got = find_ui_candidates(code, 'OptiScaler/dlssnr/DlssNr_Menu.cpp', RULES)
        self.assertIn('Difference (added)\0Ratio (multiplied)\0', {c.source for c in got})
    def test_deferred_format_injection_uses_loc_f(self):
        import tempfile
        from localize_source import instrument_file
        from loclib import key_for_source
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.cpp'
            path.write_text('const auto label = std::format("Pass {}", pass + 1);')
            instrument_file(path, REL, RULES, {'Pass {}': key_for_source('Pass {}')})
            out = path.read_text()
            self.assertIn('OptiScalerCN::Loc::F(', out)
            self.assertNotIn('std::format(', out)
            self.assertIn('"Pass {}", pass + 1)', out)
    def test_conditional_adjacent_literals_remain_one_expression(self):
        code = 'ImGui::TextWrapped(flag ? "Clean " "input" : "Edited " /* comment */ "output");'
        got = find_ui_candidates(code, 'OptiScaler/dlssnr/DlssNr_Menu.cpp', RULES)
        self.assertEqual({'Clean input', 'Edited output'}, {c.source for c in got})
    def test_pipeline_label_struct_and_constexpr_names_are_rewritable(self):
        import tempfile
        from localize_source import instrument_file
        from loclib import key_for_source
        rel = 'OptiScaler/dlssnr/DlssNr_PipelineUi.h'
        code = '''static constexpr const char* names[] = { "Placement", "Apply NR edit" };
        const Label labels[] = {{ "Game input", "Placement / routing" }};'''
        got = find_ui_candidates(code, rel, RULES)
        self.assertEqual({'Placement','Apply NR edit','Game input','Placement / routing'}, {c.source for c in got if c.rewrite})
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.h'; path.write_text(code)
            instrument_file(path, rel, RULES, {c.source:key_for_source(c.source) for c in got})
            self.assertNotIn('constexpr const char* names',path.read_text())
            self.assertEqual(4,path.read_text().count('OptiScalerCN::Loc::T('))
    def test_conditional_toast_member_is_discovered(self):
        got=find_ui_candidates('toast.setContent(flag ? "On" : "Off");','OptiScaler/menu/menu_common.cpp',RULES)
        self.assertEqual({'On','Off'},{c.source for c in got})
    def test_instrumented_dynamic_tooltips_are_still_translated(self):
        import tempfile
        from localize_source import patch_dynamic_helpers
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'menu_common.cpp'
            p.write_text('ImGui::SetTooltip(OptiScalerCN::Loc::T("key", "%s"), opt.tooltip.c_str());\nImGui::SetTooltip(OptiScalerCN::Loc::T("key", "%s"), flag.description.c_str());')
            patch_dynamic_helpers(p)
            self.assertIn('Loc::TL(opt.tooltip).c_str()',p.read_text())
            self.assertIn('Loc::TL(flag.description).c_str()',p.read_text())
    def test_dynamic_reset_button_translates_prefix_and_preserves_id(self):
        import tempfile
        from localize_source import patch_dynamic_helpers
        code = 'const std::string resetId = std::string("Reset##") + label;\nif (ImGui::SmallButton(resetId.c_str())) {}'
        with tempfile.TemporaryDirectory() as td:
            for name in ('DlssNr_MenuControls.cpp', 'DlssNr_MenuModel.cpp'):
                p = Path(td) / name
                p.write_text(code)
                patch_dynamic_helpers(p)
                self.assertIn('OptiScalerCN::Loc::TL("Reset") + "##" + label', p.read_text())
                first = p.read_text()
                patch_dynamic_helpers(p)
                self.assertEqual(first, p.read_text())
            p = Path(td) / 'Engine.cpp'
            p.write_text(code)
            patch_dynamic_helpers(p)
            self.assertEqual(code, p.read_text())
