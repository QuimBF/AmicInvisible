"""Amic invisible: cicle hamiltonià aleatori en un graf on només hi ha arestes
entre persones de grups diferents. Cadascú regala al següent del cicle.

Ús:
  python3 sorteig.py https://.../ [--grups FITXER]          fa el sorteig i imprimeix l'enllaç de cada persona
  python3 sorteig.py --verifica [--grups FITXER] < fitxer   comprova uns codis sense ensenyar cap nom

Els grups es llegeixen de grups.json (no es puja al repositori); el format és el
de grups.example.json: una llista de grups, cada grup una llista de noms.

Qui organitza només veu el codi hex; cadascú el desxifra amb un convertidor
"hex to text" (UTF-8).
"""

import argparse
import json
import random
import re
import sys

PREFIX = "Et toca fer el regal a: "

rng = random.SystemRandom()


def carrega_grups(path: str) -> list[list[str]]:
    """Llegeix els grups d'un fitxer JSON i comprova que tinguin bona forma."""
    try:
        with open(path, encoding="utf-8") as f:
            grups = json.load(f)
    except FileNotFoundError:
        sys.exit(f"No trobo {path}. Copia grups.example.json a {path} i posa-hi els noms de la família.")
    except json.JSONDecodeError as e:
        sys.exit(f"{path} no és JSON vàlid: {e}")
    if not (
        isinstance(grups, list)
        and grups
        and all(isinstance(g, list) and g for g in grups)
        and all(isinstance(n, str) and n.strip() for g in grups for n in g)
    ):
        sys.exit(
            f"{path} ha de ser una llista de grups no buits, cada grup una llista de noms (text no buit)."
        )
    noms = [n for g in grups for n in g]
    if len(set(noms)) != len(noms):
        sys.exit(f"{path} té noms repetits.")
    return grups


def cicle_hamiltonia(grups: list[list[str]]) -> list[str]:
    """Cicle aleatori que passa per tothom sense dos veïns del mateix grup."""
    grup = {nom: i for i, g in enumerate(grups) for nom in g}
    noms = list(grup)
    if len(set(noms)) != sum(len(g) for g in grups):
        sys.exit("Hi ha noms repetits.")
    veins = {a: [b for b in noms if grup[b] != grup[a]] for a in noms}

    def cerca(cami: list[str], vistos: set[str]) -> list[str] | None:
        if len(cami) == len(noms):
            return cami if cami[0] in veins[cami[-1]] else None
        candidats = [v for v in veins[cami[-1]] if v not in vistos]
        rng.shuffle(candidats)
        for v in candidats:
            vistos.add(v)
            if r := cerca(cami + [v], vistos):
                return r
            vistos.remove(v)
        return None

    inici = rng.choice(noms)
    cicle = cerca([inici], {inici})
    if cicle is None:
        sys.exit("No hi ha cap sorteig possible: algun grup és massa gran.")
    return cicle


def genera(grups: list[list[str]], url: str) -> str:
    """Fa el sorteig i en retorna la sortida: un enllaç url#codi-hex per persona."""
    cicle = cicle_hamiltonia(grups)
    resultat = dict(zip(cicle, cicle[1:] + cicle[:1], strict=True))
    noms = [n for g in grups for n in g]
    # Mateixa llargada per a tots els codis, i ordre fix (no el del cicle) per no donar pistes.
    llarg = max(len(n.encode()) for n in noms)
    blocs = []
    for qui in noms:
        codi = (PREFIX.encode() + resultat[qui].encode().ljust(llarg)).hex()
        blocs.append(f"--- {qui} ---\n{url}#{codi}\n")
    return "\n".join(blocs)


def llegeix(sortida: str) -> list[tuple[str, str]]:
    """Treu de la sortida les parelles (persona, codi): el codi va després del # de l'enllaç."""
    parelles = []
    for bloc in re.split(r"^--- (?=.+ ---$)", sortida, flags=re.MULTILINE)[1:]:
        cap, *resta = [s.strip() for s in bloc.splitlines() if s.strip()]
        parelles.append((cap.removesuffix(" ---"), resta[-1].rsplit("#", 1)[-1] if resta else ""))
    return parelles


def verifica(sortida: str, grups: list[list[str]]) -> list[str]:
    """Comprova la sortida d'un sorteig. Retorna la llista d'errors (buida = correcte).

    Els missatges no diuen mai a qui regala ningú.
    """
    grup = {nom: i for i, g in enumerate(grups) for nom in g}
    noms = list(grup)
    errors: list[str] = []

    # 1. Format: un bloc "--- Nom ---" per persona, amb el codi a l'última línia.
    parelles = llegeix(sortida)
    if not parelles:
        return ["Format incorrecte: no hi ha cap bloc '--- Nom ---'."]
    qui_dona = [q for q, _ in parelles]
    codis = [c for _, c in parelles]

    # 2. Hi surt tothom, un sol cop, i en l'ordre fix dels grups (no el del cicle).
    if sorted(qui_dona) != sorted(noms):
        errors.append("La llista de persones no coincideix amb els grups (falta, sobra o es repeteix algú).")
        return errors
    if qui_dona != noms:
        errors.append("L'ordre de la sortida no és el dels grups i podria donar pistes del cicle.")

    # 3. Tots els codis fan la mateixa llargada: no es pot endevinar res per la mida.
    if len({len(c) for c in codis}) != 1:
        errors.append("Els codis no fan tots la mateixa llargada.")

    # 4. Cada codi és hex vàlid, es desxifra i conté un nom conegut.
    resultat: dict[str, str] = {}
    for qui, codi in zip(qui_dona, codis, strict=True):
        try:
            text = bytes.fromhex(codi).decode()
        except ValueError:
            errors.append(f"El codi de {qui} no és hexadecimal UTF-8 vàlid.")
            continue
        if not text.startswith(PREFIX):
            errors.append(f"El codi de {qui} no comença amb el text esperat.")
            continue
        a_qui = text[len(PREFIX) :].rstrip(" ")
        if a_qui not in grup:
            errors.append(f"El codi de {qui} porta un nom que no és de cap grup.")
            continue
        resultat[qui] = a_qui
    if errors:
        return errors

    # 5. Ningú es regala a si mateix.
    errors += [f"{q} es regala a si mateix." for q, a in resultat.items() if q == a]
    # 6. Tothom rep exactament un regal.
    if sorted(resultat.values()) != sorted(noms):
        errors.append("Algú rep més d'un regal i algú altre cap.")
    # 7. Ningú regala a algú del seu grup (ni, per tant, rep d'algú del seu grup).
    errors += [f"{q} regala a algú del seu grup." for q, a in resultat.items() if grup[q] == grup[a]]
    # 8. És una sola rotllana: seguint els regals es passa per tothom abans de tornar a l'inici.
    if not errors:
        actual, passos = resultat[noms[0]], 1
        while actual != noms[0]:
            actual, passos = resultat[actual], passos + 1
        if passos != len(noms):
            errors.append("El sorteig forma més d'una rotllana, no un sol cicle.")
    return errors


def main() -> None:
    p = argparse.ArgumentParser(description="Sorteig de l'amic invisible.")
    p.add_argument("url", nargs="?", help="adreça de la web, p. ex. https://on-esta-la-web/")
    p.add_argument(
        "--verifica", action="store_true", help="comprova una sortida llegida de l'entrada estàndard"
    )
    p.add_argument(
        "--grups", default="grups.json", help="fitxer JSON amb els grups (per defecte: grups.json)"
    )
    args = p.parse_args()

    if args.verifica:
        if args.url:
            p.error("--verifica no porta URL")
        grups = carrega_grups(args.grups)
        errors = verifica(sys.stdin.read(), grups)
        print("\n".join(errors) if errors else "Sorteig correcte.")
        sys.exit(1 if errors else 0)

    if not args.url or not args.url.startswith(("http://", "https://")):
        sys.exit("Ús: python3 sorteig.py https://on-esta-la-web/ [--grups FITXER]")
    grups = carrega_grups(args.grups)
    sortida = genera(grups, args.url.rstrip("#"))
    if errors := verifica(sortida, grups):
        sys.exit("Sorteig invàlid, no l'enviïs:\n" + "\n".join(errors))
    print(sortida)


if __name__ == "__main__":
    main()
