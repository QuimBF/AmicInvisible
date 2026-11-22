"""Tests de la sortida de sorteig.py.  Ús: python3 -m unittest -v"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from sorteig import PREFIX, carrega_grups, cicle_hamiltonia, genera, llegeix, verifica, xifra

URL = "https://exemple.test/"
EXEMPLE = "grups.example.json"
GRUPS = carrega_grups(EXEMPLE)

NOMS = [n for g in GRUPS for n in g]
LLARG = max(len(n.encode()) for n in NOMS)


def sortida_de(resultat: dict[str, str], ordre: list[str] = NOMS, llarg: int = LLARG) -> str:
    """Construeix una sortida amb el mateix format que sorteig.py a partir d'un repartiment."""
    blocs = []
    for qui in ordre:
        codi = xifra(qui, (PREFIX + resultat[qui]).encode().ljust(len(PREFIX) + llarg)).hex()
        blocs.append(f"--- {qui} ---\n{URL}#{qui.replace(' ', '_')}.{codi}\n")
    return "\n".join(blocs)


def desxifra(sortida: str) -> dict[str, str]:
    return {
        q: xifra(q, bytes.fromhex(c.rpartition(".")[2])).decode()[len(PREFIX) :].rstrip()
        for q, c in llegeix(sortida)
    }


# Un cicle vàlid fix per construir casos trencats a partir d'ell.
CICLE_BO = ["Anna", "Laia", "Pau", "Pere", "Marta", "Rosa", "Joan", "Martí", "Clara"]
BO = dict(zip(CICLE_BO, CICLE_BO[1:] + CICLE_BO[:1], strict=True))


class SortidaReal(unittest.TestCase):
    """Propietats que ha de complir qualsevol sorteig generat."""

    def test_molts_sortejos_son_correctes(self):
        for _ in range(500):
            self.assertEqual(verifica(genera(GRUPS, URL), GRUPS), [])

    def test_propietats_comprovades_a_ma(self):
        # Les mateixes propietats, comprovades aquí sense passar per verifica().
        grup = {n: i for i, g in enumerate(GRUPS) for n in g}
        for _ in range(200):
            r = desxifra(genera(GRUPS, URL))
            self.assertEqual(sorted(r), sorted(NOMS), "tothom regala un cop")
            self.assertEqual(sorted(r.values()), sorted(NOMS), "tothom rep un cop")
            for q, a in r.items():
                self.assertNotEqual(q, a, "ningú es regala a si mateix")
                self.assertNotEqual(grup[q], grup[a], "mai dins del mateix grup")
            vistos, actual = set(), NOMS[0]
            while actual not in vistos:
                vistos.add(actual)
                actual = r[actual]
            self.assertEqual(len(vistos), len(NOMS), "una sola rotllana")

    def test_codis_mateixa_llargada_i_ordre_fix(self):
        parelles = llegeix(genera(GRUPS, URL))
        self.assertEqual([q for q, _ in parelles], NOMS)
        self.assertEqual(len({len(c.rpartition(".")[2]) for _, c in parelles}), 1)

    def test_cada_bloc_es_un_missatge_complet(self):
        blocs = genera(GRUPS, URL).split("--- ")[1:]
        self.assertEqual(len(blocs), len(NOMS))
        for bloc in blocs:
            enllac = bloc.strip().splitlines()[-1]
            self.assertTrue(enllac.startswith(URL + "#"), enllac)
            nom, _, codi = enllac.removeprefix(URL + "#").rpartition(".")
            bytes.fromhex(codi)  # el codi és hex vàlid
            self.assertNotIn(PREFIX.encode().hex(), codi)  # i no és el text en clar

    def test_es_aleatori(self):
        resultats = [desxifra(genera(GRUPS, URL)) for _ in range(300)]
        self.assertGreater(len({tuple(sorted(r.items())) for r in resultats}), 50)
        for nom in NOMS:  # ningú té el destinatari fixat
            self.assertGreater(len({r[nom] for r in resultats}), 1, nom)

    def test_executat_com_a_script(self):
        p = subprocess.run(
            [sys.executable, "sorteig.py", URL, "--grups", EXEMPLE],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.returncode, 0)
        v = subprocess.run(
            [sys.executable, "sorteig.py", "--verifica", "--grups", EXEMPLE],
            input=p.stdout,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual((v.returncode, v.stdout.strip()), (0, "Sorteig correcte."))

    def test_sense_url_no_fa_el_sorteig(self):
        p = subprocess.run([sys.executable, "sorteig.py"], check=False, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_sense_fitxer_de_grups(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run(
                [sys.executable, "sorteig.py", URL, "--grups", os.path.join(d, "grups.json")],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")
        self.assertIn("grups.example.json", p.stderr)

    def test_carrega_grups_rebutja_fitxers_dolents(self):
        dolents = [
            {},
            [],
            [[]],
            [["Anna"], []],
            [["Anna", ""]],
            [["Anna", 3]],
            ["Anna"],
            [["Anna", "Pau"], ["Anna"]],
        ]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "g.json")
            for contingut in [json.dumps(x) for x in dolents] + ["no és json"]:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(contingut)
                with self.subTest(contingut=contingut), self.assertRaises(SystemExit):
                    carrega_grups(path)

    def test_grups_impossibles(self):
        with self.assertRaises(SystemExit):
            cicle_hamiltonia([["A", "B", "C"], ["D"]])
        with self.assertRaises(SystemExit):
            cicle_hamiltonia([["A", "B"], ["A"]])


class VerificadorDetectaErrors(unittest.TestCase):
    """El verificador ha de rebutjar sortejos trencats; si no, que digui OK no demostra res."""

    def assert_error(self, sortida: str, fragment: str):
        errors = verifica(sortida, GRUPS)
        self.assertTrue(any(fragment in e for e in errors), f"esperava '{fragment}', tinc {errors}")

    def test_el_cas_bo_passa(self):
        self.assertEqual(verifica(sortida_de(BO), GRUPS), [])

    def test_es_regala_a_si_mateix(self):
        self.assert_error(sortida_de(BO | {"Anna": "Anna"}), "si mateix")

    def test_algu_rep_dos_regals(self):
        self.assert_error(sortida_de(BO | {"Anna": BO["Pau"]}), "més d'un regal")

    def test_regala_dins_del_grup(self):
        # Anna↔Pau intercanviats: segueix sent una permutació, però dins del grup 1.
        r = BO | {"Anna": "Pau", "Pau": "Anna", "Clara": BO["Anna"], "Laia": BO["Pau"]}
        self.assertEqual(sorted(r.values()), sorted(NOMS))
        self.assert_error(sortida_de(r), "del seu grup")

    def test_dues_rotllanes(self):
        # Anna↔Laia tancats entre ells i la resta en una altra rotllana: tot legal menys el cicle únic.
        resta = ["Pau", "Pere", "Marta", "Rosa", "Joan", "Martí", "Clara"]
        r = {"Anna": "Laia", "Laia": "Anna"} | dict(zip(resta, resta[1:] + resta[:1], strict=True))
        self.assert_error(sortida_de(r), "més d'una rotllana")

    def test_falta_una_persona(self):
        self.assert_error(sortida_de(BO, ordre=NOMS[:-1]), "no coincideix")

    def test_persona_repetida(self):
        self.assert_error(sortida_de(BO, ordre=NOMS[:-1] + NOMS[:1]), "no coincideix")

    def test_nom_desconegut(self):
        self.assert_error(sortida_de(BO | {"Anna": "Pep"}), "no és de cap grup")

    def test_codi_no_hex(self):
        self.assert_error(re.sub(r"#Anna\...", "#Anna.zz", sortida_de(BO)), "hexadecimal")

    def test_enllac_amb_un_altre_nom(self):
        self.assert_error(sortida_de(BO).replace("#Anna.", "#Pau.", 1), "no porta el seu nom")

    def test_codis_de_llargada_diferent(self):
        self.assert_error(re.sub(r"(#Anna\.\w+)..\n", r"\1\n", sortida_de(BO)), "mateixa llargada")

    def test_ordre_del_cicle_dona_pistes(self):
        self.assert_error(sortida_de(BO, ordre=CICLE_BO), "ordre")


if __name__ == "__main__":
    unittest.main()
