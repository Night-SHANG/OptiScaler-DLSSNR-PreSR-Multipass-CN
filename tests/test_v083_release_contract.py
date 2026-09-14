from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V083ReleaseContractTests(unittest.TestCase):
    def test_release_builds_standard_and_rtx40_mfg_variants(self):
        text = (ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('Build standard Release x64', text)
        self.assertIn('Build RTX 40 MFG Release x64 when supported', text)
        self.assertIn('/p:OptiScalerRtx40Mfg=true', text)
        self.assertIn('EnableRtx40Mfg', text)

    def test_release_only_builds_legacy_forwarder_when_project_exists(self):
        text = (ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('dlssnr_forwarder.vcxproj', text)
        self.assertIn('Test-Path -LiteralPath $forwarderProject', text)

    def test_packager_supports_both_legacy_hybrid_and_v083_dual_package_contracts(self):
        text = (ROOT / 'tools/package.ps1').read_text(encoding='utf-8')
        self.assertIn("ContainsKey('HybridAssetsDirectory')", text)
        self.assertIn("ContainsKey('EnableRtx40Mfg')", text)
        self.assertIn('-EnableRtx40Mfg', text)
        self.assertIn('get_hybrid_assets.ps1', text)
        self.assertIn('rtx40-mfg', text)
        self.assertIn('packages', text)


if __name__ == '__main__':
    unittest.main()
