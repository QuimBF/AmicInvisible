"""Prepara la carpeta que es publica a GitHub Pages: només la web, res de scripts ni noms.

Ús: python3 publica.py [desti]   (per defecte: _site)
"""

import shutil
import sys
from pathlib import Path

ARREL = Path(__file__).parent
FITXERS = [
    "index.html",
    "cel.webp",
    "capa-1.webp",
    "capa-2.webp",
    "capa-3.webp",
    "outfit.woff2",
    "OUTFIT-LICENSE.txt",
]


def construeix(desti: str | Path) -> Path:
    desti = Path(desti)
    shutil.rmtree(desti, ignore_errors=True)
    desti.mkdir(parents=True)
    for nom in FITXERS:
        shutil.copy2(ARREL / nom, desti / nom)
    (desti / ".nojekyll").touch()  # serve files as-is, no Jekyll processing
    return desti


if __name__ == "__main__":
    print(construeix(sys.argv[1] if len(sys.argv) > 1 else ARREL / "_site"))
