"""Prepara les 3 fotos del paisatge com a capes per a la web, en color.

Ús: python3 capes.py lluny.png mig.png aprop.png
Escriu capa-1.webp, capa-2.webp i capa-3.webp (amb transparència) al costat de l'index.html.
"""

import sys
from pathlib import Path

from PIL import Image

AMPLE = 1536  # prou per a pantalles grans; WebP les deixa en ~100-300 KB


def main() -> None:
    fotos = [Path(p) for p in sys.argv[1:]]
    if len(fotos) != 3:
        sys.exit("Calen 3 fotos, de més lluny a més a prop.")
    for n, foto in enumerate(fotos, start=1):
        im = Image.open(foto).convert("RGBA")
        if im.width > AMPLE:
            im = im.resize((AMPLE, round(im.height * AMPLE / im.width)), Image.LANCZOS)
        desti = Path(__file__).with_name(f"capa-{n}.webp")
        im.save(desti, "WEBP", quality=82, method=6)
        print(f"{foto.name} -> {desti.name} ({desti.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
