from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V083ReleaseContractTests(unittest.TestCase):
    def test_release_builds_standard_and_rtx40_mfg_variants(self):
        text = (ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('Build standard Release x64', text)
        self.assertIn('Build RTX 40 MFG Release x64', text)
        self.assertIn('/p:OptiScalerRtx40Mfg=true', text)

    def test_release_does_not_build_removed_dlssnr_forwarder(self):
        text = (ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertNotIn('dlssnr_forwarder.vcxproj', text)

    def test_packager_uses_new_upstream_interface_and_emits_both_variants(self):
        text = (ROOT / 'tools/package.ps1').read_text(encoding='utf-8')
        self.assertNotIn('HybridAssetsDirectory', text)
        self.assertNotIn('get_hybrid_assets.ps1', text)
        self.assertIn('-EnableRtx40Mfg', text)
        self.assertIn('rtx40-mfg', text)
        self.assertIn('packages', text)


if __name__ == '__main__':
    unittest.main()
