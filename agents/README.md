# agents/

Tämä hakemisto sisältää alustakohtaiset metadatatiedostot, jotka rekisteröivät
kyvyn eri AI-ympäristöihin.

- `openai.yaml`: OpenAI Codex -rekisteröinti. Määrittelee näyttönimen,
  lyhytkuvauksen ja kutsupolitiikan.

Varsinainen kyvyn määrittely on `SKILL.md`:ssä — alustakohtaiset tiedostot
viittaavat siihen eivätkä toista sen sisältöä.

## Huomio: Claude Code

Claude Code ei käytä `agents/`-hakemistoa. Se lukee `SKILL.md`:n suoraan
hakemiston nimen perusteella.

## Uuden alustan lisääminen

Lisää uusi `.yaml`- tai `.json`-tiedosto tähän hakemistoon alustan ohjeiden
mukaisesti. `SKILL.md` pysyy yhteiseksi määrittelyksi.
