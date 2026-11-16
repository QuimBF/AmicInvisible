"""Static checks on the published site: assets, build contents, no real names leaked."""

import json
import re
import tempfile
import unittest
from pathlib import Path

import publica

ARREL = Path(__file__).parent
INDEX = (ARREL / "index.html").read_text(encoding="utf-8")


def assets_locals(html: str) -> set[str]:
    refs = re.findall(r'\b(?:href|src)\s*=\s*["\']([^"\']+)["\']', html)
    refs += re.findall(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', html)
    return {r for r in refs if not re.match(r"(?:https?|data):", r) and not r.startswith("#")}


class TestWeb(unittest.TestCase):
    def test_assets_existeixen_i_es_publiquen(self):
        refs = assets_locals(INDEX)
        self.assertTrue(refs)
        for ref in refs:
            self.assertTrue((ARREL / ref).is_file(), ref)
            self.assertIn(ref, publica.FITXERS)

    def test_construeix_nomes_els_fitxers(self):
        with tempfile.TemporaryDirectory() as tmp:
            desti = publica.construeix(Path(tmp) / "site")
            fets = {str(p.relative_to(desti)) for p in desti.rglob("*")}
        self.assertEqual(fets, set(publica.FITXERS) | {".nojekyll"})

    def test_no_hi_ha_noms_reals(self):
        grups = ARREL / "grups.json"
        if not grups.exists():
            self.skipTest("grups.json absent")
        noms = {n for g in json.loads(grups.read_text(encoding="utf-8")) for n in g}
        patro = re.compile(r"\b(?:" + "|".join(map(re.escape, noms)) + r")\b", re.IGNORECASE)
        with tempfile.TemporaryDirectory() as tmp:
            desti = publica.construeix(Path(tmp) / "site")
            for p in desti.iterdir():
                text = p.read_bytes().decode("utf-8", errors="ignore")
                # Never put the match in the message: it would print a real name.
                self.assertIsNone(patro.search(text), f"nom real a {p.name}")

    def test_noindex(self):
        self.assertRegex(INDEX, r'<meta name="robots" content="noindex"\s*/?>')


if __name__ == "__main__":
    unittest.main()
