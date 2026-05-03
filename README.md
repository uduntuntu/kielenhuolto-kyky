# Kielenhuolto-kyky

Suomen kielenhuolto AI-agenteille. Kyky tunnistaa robottimaisen tekstin
piirteet ja korjaa ne – ensin luonnollistaa, sitten huoltaa kieliopin.

Perustuu [Hakku/finnish-humanizer](https://github.com/Hakku/finnish-humanizer)-
ja [akunikkola/suomi-finnish-skill](https://github.com/akunikkola/suomi-finnish-skill)
-projekteihin. Forkattu [janneikola/suomettaja-skill](https://github.com/janneikola/suomettaja-skill)
-reposta.

---

## Brief introduction

Kielenhuolto-kyky is an Agent Skill for improving Finnish text. It is
based on Harri Sipola's [Hakku/finnish-humanizer](https://github.com/Hakku/finnish-humanizer),
Aku Nikkola's [akunikkola/suomi-finnish-skill](https://github.com/akunikkola/suomi-finnish-skill),
and is forked from Janne Ikola's [janneikola/suomettaja-skill](https://github.com/janneikola/suomettaja-skill).
It combines Finnish proofreading and grammar guidance with Finnish
Humanizer patterns that help remove robotic, AI-generated phrasing while
preserving meaning and register.

---

## Esimerkkejä

**#4 Puuttuvat partikkelit**
> Ennen: Tämä on totta. Kyse on kuitenkin siitä, että tilanne on monimutkainen.
> Jälkeen: Onhan se totta. Tilanne on vaan monimutkainen.

**#17 Täytesanat**
> Ennen: On syytä huomata, että tässä yhteydessä on tärkeää ymmärtää
> alustan arkkitehtuuri ennen käyttöönottoa.
> Jälkeen: Ymmärrä alustan arkkitehtuuri ennen käyttöönottoa.

---

## Asennus

```bash
git clone https://github.com/uduntuntu/kielenhuolto-kyky \
  <skills-hakemisto>/kielenhuolto-kyky
```

Tarvittava rakenne:

```
kielenhuolto-kyky/
  SKILL.md
  references/
    kielioppi.md
    patterns.md
  custom_references/    # valinnainen
  custom_rules/         # valinnainen
```

---

## Päivitys

```bash
cd <skills-hakemisto>/kielenhuolto-kyky && git pull
```

Omat tiedostot (`custom_rules/`, `custom_references/`) on suojattu
`.gitignore`lla – `git pull` ei ylikirjoita niitä.

---

## Mukautukset

Lisää `.md`-tiedostoja kansioihin ilman että pohjatiedostoja muokataan:

- **`custom_rules/`** – pakottavat tyylisäännöt (kielletyt sanat,
  pakolliset termit, brändikirjoitusasut)
- **`custom_references/`** – taustatietoa (brändin ääni, sanasto,
  kohdeyleisö)

Tarkemmat ohjeet: [`custom_references/README.md`](custom_references/README.md)
ja [`custom_rules/README.md`](custom_rules/README.md).

---

## Lisenssi

MIT – ks. [LICENSE](LICENSE)

---

## Huomioita kehittäjille

`references/patterns.md` ja `references/kielioppi.md` ovat kuratoituja
tiedostoja – ne eivät päivity automaattisesti upstream-projektien mukana.

Upstream-lähteet on liitetty Git-submoduleina `upstream/`-hakemistoon.
Kun upstream-projekteissa tapahtuu muutoksia, ne voi tarkistaa ja siirtää
paikallisiin referensseihin merge-skriptillä:

```bash
# Päivitä submodulet
git submodule update --remote

# Tarkista ja yhdistä muutokset (vaatii Pythonin)
pip install -r scripts/requirements.txt
python scripts/merge-upstream-references.py
```

Älä muokkaa `upstream/`-hakemiston tiedostoja suoraan.
