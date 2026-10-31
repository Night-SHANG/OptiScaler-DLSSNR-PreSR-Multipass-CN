import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from generate_cpp import render_status_header
from localize_source import patch_status_display
DATA=json.loads((ROOT/'Localization/status.zh-CN.json').read_text())

class StatusLocalizationTests(unittest.TestCase):
    def test_resources_have_source_integrity_and_preserved_parameters(self):
        for row in DATA['entries']:
            self.assertEqual(hashlib.sha256(row['source'].encode()).hexdigest(),row['source_hash'])
            self.assertEqual(row['source'].count('{}'),row['text'].count('{}'))
            self.assertTrue(row['occurrences'])
        render_status_header(DATA)
    def test_invalid_template_is_rejected(self):
        with self.assertRaises(ValueError):
            render_status_header({'entries':[{'source':'value {}','text':'数值','pattern':True,'state':'machine_translated','source_hash':hashlib.sha256(b'value {}').hexdigest()}]})
    def test_display_wrapper_does_not_modify_state_or_logs(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'DlssNr_Menu.cpp'
            p.write_text('ImGui::TextWrapped("%s", DlssNr::FinishedVkStatus().c_str());\n')
            patch_status_display(p)
            self.assertIn('Loc::DS(DlssNr::FinishedVkStatus()).c_str()',p.read_text())
            first=p.read_text();patch_status_display(p);self.assertEqual(first,p.read_text())
            p=Path(td)/'Renderer.cpp';p.write_text('state.reason = "Off"; LOG_INFO("{}", state.reason);')
            before=p.read_text();patch_status_display(p);self.assertEqual(before,p.read_text())
    def test_producer_audit_catches_helpers_and_does_not_treat_logs_as_ui(self):
        from audit_status_sources import inventory
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);scope=root/'OptiScaler/dlssnr';scope.mkdir(parents=True)
            (scope/'Fixture.cpp').write_text('Say("waiting"); Fail("failure"); state.reason = "reason"; Say(flag ? "active" : "inactive"); LOG_INFO("internal only");')
            exact,dynamic=inventory(root)
            self.assertEqual({'waiting','failure','reason','active','inactive'},set(exact))
            self.assertEqual([],dynamic)
    @unittest.skipUnless(shutil.which('g++'),'portable C++ compiler unavailable')
    def test_real_resource_runtime_fallback_and_parameter_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'generated').mkdir()
            shutil.copy(ROOT/'overlay/OptiScaler/localization/StatusLocalization.h',root/'StatusLocalization.h')
            (root/'generated/Status.generated.h').write_text(render_status_header(DATA))
            overlay=(ROOT/'overlay/OptiScaler/localization/Localization.h').read_text()
            ds=overlay[overlay.index('inline std::string DS('):overlay.index('template <typename... Args>')]
            shim='#include "generated/Status.generated.h"\nnamespace OptiScalerCN::Loc { namespace detail { inline std::string activeLanguage="zh-CN"; } inline void Initialize() {}\n'+ds+'}\n'
            (root/'test.cpp').write_text(shim+r'''
#include "generated/Status.generated.h"
#include <cassert>
int main() {
 using OptiScalerCN::Status::Translate;
 assert(OptiScalerCN::Loc::DS("private DLSS SR created; waiting for a later submission epoch [1:1 pass 2.35 ms, private SR 1.20 ms]")=="独立 DLSS SR 已创建；正在等待后续提交周期 [1:1 Pass 2.35 ms，独立 SR 1.20 ms]");
 assert(OptiScalerCN::Loc::DS("unknown status [1:1 pass 2.35 ms]")=="unknown status [1:1 pass 2.35 ms]");
 const auto& rows = OptiScalerCN::Generated::kStatusTranslations;
 assert(Translate("Off",rows)=="关闭");
 constexpr OptiScalerCN::Status::Entry boundary[] = {
  {"prefix {} suffix", "前缀 {} 后缀", true},
  {"prefix exact suffix", "精确优先", false},
  {"broken {}{}", "坏 {}{}", true},
  {"mismatch {}", "错 {} {}", true}
 };
 assert(Translate("prefix exact suffix",boundary)=="精确优先");
 assert(Translate("prefix {}路径/C:\\GPU suffix",boundary)=="前缀 {}路径/C:\\GPU 后缀");
 assert(Translate("prefix  suffix",boundary)=="prefix  suffix");
 assert(Translate("prefix C:\\a suffix folder suffix",boundary)=="prefix C:\\a suffix folder suffix");
 assert(Translate("broken abc",boundary)=="broken abc");
 assert(Translate("mismatch value",boundary)=="mismatch value");
 const std::string longValue(100000,'x');
 assert(Translate("prefix "+longValue+" suffix",boundary)=="前缀 "+longValue+" 后缀");

 assert(Translate("Off",rows,false)=="Off");
 assert(Translate("unknown GPU error 0xBAD0000B C:\\runtime.dll",rows)=="unknown GPU error 0xBAD0000B C:\\runtime.dll");
 assert(Translate("DX12 peripheral compression: 1920x1080 -> 960x540",rows)=="DX12 外围压缩：1920x1080 -> 960x540");
 assert(Translate("private DLSS SR creation failed: 0xBAD0000B C:\\runtime.dll",rows)=="独立 DLSS SR 创建失败：0xBAD0000B C:\\runtime.dll");
 assert(Translate("Private DLSS SR: Off",rows)=="独立 DLSS SR：Off");
 assert(Translate("DX12 peripheral compression: x1080 -> 960x540",rows)=="DX12 peripheral compression: x1080 -> 960x540");
}
''')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(root/'test.cpp'),'-o',str(root/'test')],check=True)
            subprocess.run([str(root/'test')],check=True)
