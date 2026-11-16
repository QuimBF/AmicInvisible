# Amic Invisible

Web estàtica per a l'amic invisible de la família, més un script en Python que fa el sorteig.
Cada persona rep un enllaç secret que només li revela a qui ha de fer el regal.
Ningú no regala a algú del seu propi grup (parella o nucli familiar).

Publicada a <https://quimbf.github.io/AmicInvisible/>.

## Grups

Els noms reals van a `grups.json`, que està al `.gitignore` i no es puja mai.
Crea'l a partir de l'exemple:

```sh
cp grups.example.json grups.json
```

És una llista de grups; cada grup és una llista de noms:

```json
[["Anna", "Pau", "Marta", "Joan"], ["Laia", "Pere", "Rosa"], ["Martí"], ["Clara"]]
```

## Sorteig

```sh
python3 sorteig.py https://quimbf.github.io/AmicInvisible/ > ~/enllacos.txt
```

Surt un bloc per persona amb el seu enllaç (desa-ho fora del repositori). Envia a cadascú només el seu.
Per fer servir un altre fitxer de grups: `--grups FITXER`.

Per comprovar que el sorteig és vàlid:

```sh
python3 sorteig.py --verifica < ~/enllacos.txt
```

## Tests

```sh
python3 -m unittest
uvx ruff@0.17.5 check . && uvx ruff@0.17.5 format --check .
npm ci && npx playwright test
```

## Publicació

Cada push a la branca per defecte del repositori passa per la CI (gitleaks, lint, tests i e2e)
i, si tot va bé, es desplega a GitHub Pages amb `publica.py`.

Abans del primer push, a *Settings > Pages* posa *Source: GitHub Actions*.
