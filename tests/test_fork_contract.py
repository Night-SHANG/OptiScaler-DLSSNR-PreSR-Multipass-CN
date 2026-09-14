from pathlib import Path
import json, unittest

ROOT=Path(__file__).resolve().parents[1]

class ForkContractTests(unittest.TestCase):
    def test_upstream_identity(self):
        cfg=json.loads((ROOT/'upstream.json').read_text(encoding='utf-8'))
        self.assertEqual(cfg['repository'], 'https://github.com/wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass.git')
        self.assertEqual(cfg['branch'], 'main')
        self.assertEqual(cfg['package_prefix'], 'OptiScaler-DLSSNR-PreSR-Multipass-CN')

    def test_builds_dlssnr_forwarder_before_solution_on_legacy_main(self):
        build=(ROOT/'.github/workflows/build.yml').read_text(encoding='utf-8')
        self.assertIn(r'OptiScaler\dlssnr\forwarder\dlssnr_forwarder.vcxproj', build)
        self.assertIn(r'OptiScaler.sln', build)

        release=(ROOT/'.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn('dlssnr_forwarder.vcxproj', release)
        self.assertIn('Test-Path -LiteralPath $forwarderProject', release)
        self.assertIn(r'OptiScaler.sln', release)

    def test_package_wrapper_uses_fork_packager_and_never_mentions_proprietary_runtime_as_payload(self):
        text=(ROOT/'tools/package.ps1').read_text(encoding='utf-8')
        self.assertIn('package_release.ps1',text)
        self.assertIn('-SkipBuild',text)
        self.assertNotIn('Copy-Item nvngx_dlssnr.dll',text)

    def test_public_package_includes_verified_upstream_hybrid_assets_for_legacy_contract(self):
        text=(ROOT/'tools/package.ps1').read_text(encoding='utf-8')
        self.assertIn('get_hybrid_assets.ps1', text)
        self.assertIn('HybridAssetsDirectory', text)
        self.assertIn('asset-manifest.json', text)

    def test_hybrid_fetch_destination_must_not_exist_before_fetch(self):
        text=(ROOT/'tools/package.ps1').read_text(encoding='utf-8')
        fetch_pos=text.index('& $hybridFetcher @invokeArgs')
        prefix=text[:fetch_pos]
        self.assertNotIn('New-Item -ItemType Directory -Force -Path $hybridScratch', prefix)

    def test_scanner_covers_dlssnr_sources(self):
        rules=json.loads((ROOT/'Localization/scanner-rules.json').read_text(encoding='utf-8'))
        self.assertIn('OptiScaler/dlssnr/**/*.cpp',rules['include_globs'])
        self.assertIn('OptiScaler/dlssnr/**/*.cpp',rules['c_string_array_globs'])

if __name__=='__main__': unittest.main()
