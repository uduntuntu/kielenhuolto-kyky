# Kielenhuolto — Finnish Language Editing Skill for AI-agents

Kyky AI-agenteille - aluksi Claude Code ja OpenAI Codex. Parantaa suomen kielen laatua, poistaa AI-generoidun tekstin tunnusmerkkejä, noudattaa Kielitoimiston ohjepankin sääntöjä ja inhimillistää robottimaista tekstiä, eli tekee siitä luontevampaa.

---

## Mitä se tekee

**Inhimillistäminen** — Tunnistaa ja poistaa AI-generoidun tekstin tunnusmerkit (27 patternia). Tekee tekstistä sellaista, jonka suomalainen ihminen olisi voinut kirjoittaa.

**Kielenhuolto** — Tarkistaa oikeinkirjoituksen, kieliopin ja pilkutuksen Kielitoimiston ohjepankin sääntöjen mukaisesti.

### Tunnistettavat AI-patternit (27 kpl)

Suomenkieliset patternit:
- Passiivin ylikäyttö
- Nominaalirakenteet ("suorittaa tarkistuksen" → "tarkistaa")
- Pronominien ylikäyttö englannin mallin mukaan
- Puuttuvat partikkelit (-han/-hän, -pa/-pä, kyllä, vaan)
- Käännösrakenteet (englannin sanajärjestys suomessa)
- Genetiiviketjut
- Adjektiivikasaumat
- Ylipitkät virkkeet
- Joka/jotka-kasautuminen
- Virkakielisyys väärässä kontekstissa
- Astevaihtelun välttely
- Liiallinen kohteliaisuus

Universaalit patternit (suomeksi):
- Merkittävyyden liioittelu ("keskeinen", "ratkaiseva", "elintärkeä")
- Mainosmainen kieli
- Mielistelevä sävy ("Hyvä kysymys!")
- Liiallinen varautuminen
- Täytesanat ("On syytä huomata, että...")
- Geneerinen lopetus ("Tulevaisuus näyttää valoisalta")
- Epämääräiset viittaukset
- "Haasteista huolimatta" -kaava
- Kolmen sääntö ja synonyymikierto
- Partisiippirakenteet
- Kopulan välttely
- Negatiivinen rinnastus
- Keinotekoiset skaalaviittaukset
- Tietokatkos-vastuuvapauslausekkeet
- Kontrastiivinen kieltorakenne

### Kielioppisäännöt

- Yhdyssanat (yleisin virhetyyppi: "verkko sivusto" → verkkosivusto)
- Pilkutus (sivulauseet, Oxford-pilkku, desimaalipilkku)
- Iso/pieni alkukirjain (kansallisuudet, viikonpäivät, kuukaudet pienellä)
- Numerot ja lyhenteet (tuhaterotin välilyönti, EU:n, 15 %)
- Viivat (yhdysmerkki `-` vs. ajatusviiva `–`)

---

## Asennus

### AI-koodiagentit - aluksi Claude Code ja OpenAI Codex

```bash
# Claude Code
git clone https://github.com/uduntuntu/kielenhuolto-kyky ~/.claude/skills/kielenhuolto

# OpenAI Codex
git clone https://github.com/uduntuntu/kielenhuolto-kyky ~/.codex/skills/kielenhuolto
```

Kyky aktivoituu automaattisesti seuraavassa Claude Code- tai Codex-sessiossa.

### Manuaalinen asennus

1. Lataa tai kloonaa tämä repo
2. Kopioi kansio käyttämäsi agentin skills-kansioon: `~/.claude/skills/kielenhuolto/` tai `~/.codex/skills/kielenhuolto/`
3. Varmista rakenne:
   ```
   ~/.claude/skills/kielenhuolto/
     SKILL.md
     references/
       kielioppi.md
       patterns.md
     custom_references/    # valinnainen: omat lisäreferenssit
     custom_rules/         # valinnainen: omat lisäsäännöt
   ```

---

## Käyttö

Kyky aktivoituu automaattisesti kun:
- Kirjoitat tai muokkaat suomenkielistä tekstiä
- Pyydät "humanisoimaan", "oikolukemaan", "huolittelemaan" tai "parantamaan" suomea
- Teksti kuulostaa robottimaaiselta tai käyttää anglismeja

Voit myös kutsua sitä suoraan:

```
Huolittele tämä teksti: [teksti]
```

```
Oikolue ja luonnollista: [teksti]
```

### Esimerkki

**Ennen:**
> Tämä on erittäin merkittävä kehitysaskel, joka tulee vaikuttamaan laajasti alan tulevaisuuteen. On syytä huomata, että kyseinen innovaatio tarjoaa lukuisia mahdollisuuksia eri sidosryhmille. Haasteista huolimatta tulevaisuus näyttää valoisalta.

**Jälkeen:**
> Iso juttu alalle. En ole varma mihin tämä lopulta johtaa, mutta hyötyjiä on — varsinkin ne jotka ovat odottaneet tällaista jo vuosia.

---

## Tiedostorakenne

```
kielenhuolto/
  SKILL.md                  # Pääkyky: rooli, prosessi, säännöt
  references/
    patterns.md             # Kaikki 27 AI-patternia esimerkkeineen
    kielioppi.md            # Kielitoimiston ohjepankin säännöt
  custom_references/        # Omat lisäreferenssit (brändin ääni, sanastot)
    README.md
  custom_rules/             # Omat lisäsäännöt (kielletyt sanat, termit)
    README.md
  README.md
  LICENSE
```

---

## Mukautukset

Voit laajentaa Kielenhuolto-kykyä omilla tiedostoilla ilman että tätä kykyä (engl. skill) muokataan. Kaksi kansiota:

- **`custom_references/`** — kuvaileva taustamateriaali: brändin ääni, sanastot, hyvät esimerkit, kohdeyleisön kuvaus
- **`custom_rules/`** — käskevät direktiivit: kielletyt sanat, pakolliset termit, projektikohtaiset tyylivalinnat

Lisää vain `.md`-tiedostoja kansioihin. Kielenhuolto lukee ne automaattisesti seuraavassa käytössä.

**Esimerkki:**

```
custom_rules/
  brandin_termit.md    # "Acme Cloud" ei "acme cloud" tai "Acme-pilvi"
  kielletyt_sanat.md   # "ratkaisu", "innovatiivinen", "helppo"
```

**Sääntöhierarkia:** Kielioppi ja oikeinkirjoitus (`references/`) ovat aina voimassa. Omat säännöt (`custom_rules/`) voivat tiukentaa tyylivalintoja mutta eivät ohittaa kielioppisääntöjä.

Tarkemmat ohjeet ja esimerkit: [`custom_references/README.md`](custom_references/README.md) ja [`custom_rules/README.md`](custom_rules/README.md).

**Versionhallinta.** Omat tiedostot on ignoroitu `.gitignore`ssa, joten `git pull` ei riko mukautuksiasi.

---

## Lähteet

Kyky yhdistää kaksi MIT-lisensoitua avoimen lähdekoodin projektia:

- **[Hakku/finnish-humanizer](https://github.com/Hakku/finnish-humanizer)** — 27 AI-patternia ja suomalaisen kirjoittajaäänen kuvaus
- **[akunikkola/suomi-finnish-skill](https://github.com/akunikkola/suomi-finnish-skill)** — Kielitoimiston ohjepankkiin perustuva kielioppiohjeistus

Kielioppisäännöt perustuvat:
- [Kielitoimiston ohjepankki](https://kielitoimistonohjepankki.fi/)
- [Kielitoimiston sanakirja](https://www.kielitoimistonsanakirja.fi/)
- [Iso suomen kielioppi](https://kaino.kotus.fi/visk/etusivu.php)

---

## Lisenssi

MIT — ks. [LICENSE](LICENSE)
