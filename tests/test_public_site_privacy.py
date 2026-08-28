#!/usr/bin/env python3
from __future__ import annotations
import json, pathlib, shutil, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts")); import build_public_site as builder

def stage():
    shutil.rmtree(builder.SITE,ignore_errors=True); (builder.SITE/"docs").mkdir(parents=True); shutil.copy(ROOT/"docs"/"catalog-status.svg",builder.PUBLIC_SVG); payload=builder.build(); builder.PUBLIC_STATE.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); builder.build_index(); assert not builder.build_design_studio(); return payload

class PublicSitePrivacyTests(unittest.TestCase):
    def tearDown(self): shutil.rmtree(builder.SITE,ignore_errors=True)
    def test_clean_build_passes(self):
        payload=stage(); self.assertEqual([],builder.verify(payload)); self.assertEqual([],payload["repos"]); self.assertIs(True,payload["public"])
    def test_private_markup_is_removed(self):
        stage(); private=(ROOT/"index.html").read_text(encoding="utf-8"); public=builder.PUBLIC_INDEX.read_text(encoding="utf-8"); self.assertIn("data-private",private); self.assertNotIn("data-private",public); self.assertLess(len(public),len(private)); self.assertEqual([],sorted(n for n in builder.private_repo_names()-{builder.OWN_REPO} if n in public))
        # The public artifact must still be a working page, not a stripped husk.
        for keep in ("Catalog health","loadHealth","Public privacy mode","Your setup",
                     "Full system","Hybrid model routing","hardware-profiles","platSeg"):
            with self.subTest(keep=keep): self.assertIn(keep,public)
        # The repo-by-repo table now lives behind data-private, so it must NOT survive.
        for drop in ('id="healthRows"','Private rows','data-private'):
            with self.subTest(drop=drop): self.assertNotIn(drop,public)
    def test_verifier_rejects_per_repo_rows(self):
        payload=stage(); payload["repos"]=[{"repo":"FlowiseAI/Flowise","note":"x"}]; self.assertTrue(builder.verify(payload))
    def test_verifier_rejects_extra_private_keys(self):
        payload=stage(); payload["note"]="clamav HIGH"; self.assertTrue(builder.verify(payload))
    def test_verifier_rejects_repo_slug_in_value(self):
        payload=stage(); payload["updated"]="see thedotmack/claude-mem"; self.assertTrue(builder.verify(payload))
    def test_verifier_rejects_unstripped_index(self):
        payload=stage(); shutil.copy(ROOT/"index.html",builder.PUBLIC_INDEX); problems=builder.verify(payload); self.assertTrue(problems); self.assertTrue(any("data-private" in p for p in problems))
    def test_design_studio_is_public_and_complete(self):
        payload=stage(); self.assertEqual([],builder.verify(payload)); self.assertTrue(builder.PUBLIC_DESIGN_STUDIO.exists()); self.assertTrue(builder.PUBLIC_DESIGN_STUDIO_JS.exists()); page=builder.PUBLIC_DESIGN_STUDIO.read_text(encoding="utf-8"); runtime=builder.PUBLIC_DESIGN_STUDIO_JS.read_text(encoding="utf-8"); self.assertIn('src="design-options.js"',page); self.assertIn("const DESIGNS",runtime)

if __name__=="__main__": unittest.main()
