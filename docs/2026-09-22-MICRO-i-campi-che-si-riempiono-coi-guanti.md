# MICRO — i campi che si riempiono coi guanti sporchi · referto

*Ramo `templates/02-il-campo`, creato da `main` (`fedb546`). **Non ho committato.***

---

## 0 · Due note prima di cominciare

**Il repository git c'è, ma ha un commit e non tredici.** Il controllo che hai
messo in testa al prompt l'ho eseguito alla lettera:

```
$ git rev-parse --is-inside-work-tree
true
```

`git log --oneline` dice `fedb546 Initial import: reference implementation +
templates`, uno solo: hai importato la notte in un commit invece che in tredici.
Non cambia niente per questo micro — il ramo si crea sopra `main` e l'ho creato
— e lo dico solo perché il prompt si aspettava tredici e chi legge il referto fra
sei mesi vedrà uno.

**E una decisione l'ho presa io, dichiarata qui:** il prompt chiede tre valori e
mi lascia scegliere i nomi. Li ho scelti, e il §1 spiega perché.

---

## 1 · Il marcatore — `recorded_in`, e perché questi nomi

`SPEC.md` §1.6, nuova sezione. Sintassi:

```yaml
- id: descrizione
  labels: {it: "DESCRIZIONE"}
  type: longtext
  recorded_in: trench       # trench | lab | unknown — assente = unknown
```

| valore | vuol dire |
|---|---|
| `trench` | si compila **durante l'atto di scavo**, da chi ha le mani nella terra |
| `lab` | si compila **dopo quell'atto** — laboratorio, ufficio, archivio |
| `unknown` | **la definizione non l'ha detto** — ed è il default |

**Le due righe di motivazione, come chiedevi.** `recorded_in` nomina un **luogo e
un momento**: `priority` o `level` avrebbero detto che un campo da laboratorio
conta meno, e non è vero — è scritto in un altro momento, spesso da un'altra
persona, e niente qui ordina. `lab` è l'abbreviazione che la disciplina usa per
«non mentre si scava»: non è un'affermazione su una stanza, e un numero di
catalogo compilato in ufficio è `lab` come un'analisi al microscopio.

Sta **dentro la definizione**, accanto a `type` e `required`, come l'etichetta e
l'obbligatorietà. Nessun file a parte.

### Il criterio, e la sua origine — due basi, entrambe citabili

**Base A — le parole che una persona dice sul campo.** Da
`stratigraph-chatbot/app/tools.py`, che dichiara la propria provenienza in testa:
i sette intenti nascono dalla **scheda da campo di Elisa Dalla Longa**, *«i
comandi che ci sono sopra SONO gli intenti, nelle parole che una persona dice con
le mani nella terra.»* Quindi un campo che uno degli intenti nomina — come slot o
dentro una frase riconosciuta — è da trincea, **e la giustificazione è il numero
di riga**.

**Base B — le parole dello standard stesso, e questa non l'aveva prevista
nessuno.** Leggendo le etichette della US ICCD 2021 per marcarle ho trovato che
lo standard **fa la distinzione da sé**:

```
RESPONSABILE COMPILAZIONE SUL CAMPO      ← «sul campo», scritto dall'ICCD
DATA RILEVAMENTO SUL CAMPO               ← idem
DATA RIELABORAZIONE                      ← e poche righe sotto, il contrario
RESPONSABILE RIELABORAZIONE
```

Non è una mia lettura: è la scheda che contrappone il campo alla rielaborazione
nelle proprie caselle. Dove una scheda fa quella distinzione, **è la sua a
valere**, e questa base è più forte della prima perché non passa da un altro
repository.

Tutto il resto è `unknown`, e ci resta.

---

## 2 · La US ICCD 2021 marcata — i tre conteggi

```
$ python -c "…find_template('iccd-us-2021').recorded_in_counts()"
{'unknown': 48, 'trench': 8, 'lab': 3}   · totale 59
```

**Gli otto da trincea, con la riga che li giustifica:**

| campo | base | la riga |
|---|---|---|
| `us` | A | `tools.py:162` — `Slot("us", "string", True, "il numero dell'unità")`, lo slot **obbligatorio** di quattro dei sette intenti; e `intent.py:78` riconosce «scheda numero 12» |
| `localita` | A | `tools.py:171` — `Slot("sito", …, "il sito, quando il record lo dice")`. **Divergenza dichiarata**: lo slot si chiama `sito`, la casella ICCD è LOCALITÀ — vicini, non identici; il marcatore poggia sullo slot, non su un'equivalenza che nessuno ha dichiarato |
| `area` | A | `tools.py:172` — `Slot("area", …, "l'area: una US è unica dentro la sua")` |
| `descrizione` | A | `tools.py:165` — `Slot("description", …, "cosa c'è (crm:P3_has_note)")` |
| `interpretazione` | A | `tools.py:166-168` — `Slot("interpretation", …, "cosa si pensa che sia — **nota di campo**, non ancora una property con la sua catena di evidenza")`. Lo slot dice di sé che è di campo, e `tools.py:118-119` aggiunge che la versione con evidenza «is a different act, **done at the desk**» |
| `fotografie` | A | `tools.py:264-270` (`attach_photo_to_su`, «questa foto è per la US 12») e `315-319` (`ingest_photos`, «ti passo delle foto») |
| `responsabile_compilazione` | B | l'etichetta ICCD **è** «RESPONSABILE COMPILAZIONE SUL CAMPO» |
| `data_rilevamento` | B | l'etichetta ICCD **è** «DATA RILEVAMENTO SUL CAMPO» |

**I tre da laboratorio:**

| campo | perché |
|---|---|
| `data_rielaborazione` | B · «DATA RIELABORAZIONE», in contrasto esplicito con le due caselle SUL CAMPO poche righe sopra |
| `responsabile_rielaborazione` | B · stessa contrapposizione |
| `riferimenti_tabelle_materiali` | **strutturale, non un'opinione**: è un `edge` verso un'ALTRA scheda (TMA). Un rimando non si scrive prima che la scheda esista, e la TMA nasce quando i reperti sono studiati |

La giustificazione sta **nel dato**: ognuna delle undici righe `recorded_in:` ha
sotto un commento YAML che cita la base, e c'è un test
(`test_every_marked_iccd_field_carries_its_justification`) che pretende che sia
così e che il commento nomini una base.

**I 48 incerti li ho lasciati incerti**, e il §7 spiega perché è la scoperta di
questo micro e non una resa.

---

## 3 · LA SCOPERTA — il criterio non copre la scheda

Il prompt la prevedeva come motivo per fermarsi, e si è verificata. La riporto
invece di colmarla a intuito.

**Nessuno dei sette intenti permette di registrare un rapporto stratigrafico a
voce.** Misurato:

```
$ grep -inE "copre|coperto|taglia|riempi|appoggia|uguale|posterior|anterior|is_after|overlies|cuts|fills|abuts" app/tools.py app/intent.py
(nessuna riga)
```

E non è una dimenticanza silenziosa: `tools.py:126-133` lo dice, mettendo i
rapporti fra le cose **portate e non capite** —

> *«PyArchInit's `rapporti`, its `unita_misura`, whatever ATRIUM adds next
> release. Kept under one key rather than spread across `data`, so a reader can
> always tell what this service UNDERSTOOD from what it merely carried.»*

Quindi i rapporti arrivano nel grafo **solo se un adattatore li consegna**, mai
dalla voce di chi scava. Lo stesso vale per `definizione` (che è
**obbligatoria**), `quote`, `misure`, `formazione_natura`, `formazione_segno`:
`create_su` ha sei slot in tutto — `us`, `description`, `interpretation`,
`extra`, `sito`, `area` — e `intent.py:66-70` dichiara che l'estrazione di slot
è *«deliberately narrow: a unit NUMBER, because that is the one value the MVP
commands carry.»*

**Il conto della copertura:** la Base A giustifica **6** campi su 59; la Base B
ne aggiunge 2 in trincea e 2 in laboratorio. Undici marcati, 48 no.

**Che cosa NON ho fatto, ed è il punto.** Una persona in trincea dice «la 12
copre la 18» — lo dice tutto il giorno. Marcarle `trench` per questo sarebbe
stato ragionevole **e sarebbe stato inventare il criterio**, cioè esattamente
quello che il §2 del prompt vieta. Restano `unknown`.

**E questa scoperta ha un destinatario**: non è un difetto della scheda né del
formato, è un **buco negli intenti del field assistant**. I dieci rapporti della
sequenza fisica, i due della stratigrafica e la DEFINIZIONE obbligatoria sono i
candidati più forti per gli intenti che mancano a `stratigraph-chatbot` — e il
giorno che ci saranno, marcarli sarà una riga di `tools.py` da citare, non una
discussione.

---

## 4 · La `ficha ES demo` marcata — con un sottoinsieme DIVERSO, misurato

```
es-ue-demo-2026    {'unknown': 0, 'trench': 14, 'lab': 1}   · totale 15
```

La base qui **non è la A**: gli intenti del field assistant sono in italiano
(`intent.py:COMMAND_LANGUAGE = "it"`) e non parlano di questa scheda. È il suo
**autore** che decide — e per una scheda `invented: true` l'autore è questo
repository. È dichiarato in ogni commento del file, perché «l'ho deciso io» detto
ad alta voce è un'altra cosa da «l'ho deciso io» taciuto.

**E le due schede non sono d'accordo.** Tredici concetti analoghi, accostati a
mano perché le due schede non condividono gli id (che è il motivo per cui il
marcatore è per standard):

```
US ICCD 2021                              ficha ES demo                d'accordo?
--------------------------------------------------------------------------------
us                           trench       contexto         trench      sì
localita                     trench       yacimiento       trench      sì
definizione                  unknown      definicion       trench      NO
descrizione                  trench       descripcion      trench      sì
interpretazione              trench       interpretacion   trench      sì
uguale_a                     unknown      igual_a          trench      NO
copre                        unknown      cubre            trench      NO
coperto_da                   unknown      cubierto_por     trench      NO
taglia                       unknown      corta            trench      NO
tagliato_da                  unknown      cortado_por      trench      NO
quote                        unknown      cota             trench      NO
responsabile_compilazione    trench       responsable      trench      sì
data_rilevamento             trench       fecha            trench      sì
--------------------------------------------------------------------------------
concetti analoghi confrontati : 13
  stesso marcatore            : 6
  marcatore DIVERSO           : 7
```

**Sette su tredici divergono**, e le divergenze sono quelle che portano
significato: la DEFINIZIONE è `unknown` nella scheda italiana e `trench` in
quella spagnola; le dieci caselle dei rapporti della US sono `unknown` e le
cinque della ficha sono `trench`. **Stesso concetto, marcatore diverso, e la
differenza è la BASE non il concetto.**

Il solo `lab` della ficha è anche il più istruttivo: `crs`, il sistema di
riferimento. Si stabilisce una volta all'apertura del cantiere, non a ogni
unità — e non è meno importante delle coordinate, è deciso in un altro momento,
che è esattamente ciò che il marcatore dice.

C'è un test (`test_the_two_sheets_do_not_agree_on_the_same_concepts`) che
pretende **7** divergenze: se scende a zero, il marcatore ha smesso di essere
per standard e ha iniziato a descrivere il nostro pregiudizio.

---

## 5 · Il diff dell'implementazione — NON è vuoto, e ti spiego perché

```
$ git diff --stat src/
 src/stratigraph_templates/loader.py | 26 ++++++++++++++-
 src/stratigraph_templates/model.py  | 65 +++++++++++++++++++++++++++++++++++++
 2 files changed, 90 insertions(+), 1 deletion(-)

render.py: NON toccato
```

**Novanta righe.** La tesi del repository è che *aggiungere uno **standard**
costa scrivere una definizione* — e questo non è uno standard: è **il formato che
acquista una chiave**, quindi il lettore del formato ha dovuto impararla.
`_FIELD_KEYS` in `loader.py` è un cancello severo sulle chiavi ignote (ed è
giusto che lo sia), quindi una chiave nuova passa da lì per costruzione.

**La distinzione, misurata invece che affermata.** I nomi propri delle due
schede — id di scheda, di campo, di paragrafo: 90 nomi — cercati nelle 90 righe
aggiunte, con i confini di parola:

```
nomi di scheda o di campo comparsi nel diff : NESSUNO
```

*(Una nota sul mio stesso errore: la prima misura, con una ricerca per
sottostringa, dava un falso positivo — `anno`, che stava dentro «c**anno**t» in
un commento inglese. Con `\b` non resta niente.)*

Il codice ha imparato **una chiave del formato**, non che cosa sia la US ICCD
2021. Le due definizioni hanno acquisito il marcatore senza una riga di codice
loro, e `test_no_standard_is_named_in_the_implementation` **continua a passare**.

**Il renderer non l'ho toccato**, e non serviva: il marcatore non cambia come si
stampa un foglio. Il selettore per il consumatore (`Template.recorded_in`) sta
nel **modello**, non nel renderer e non nel consumatore — un consumatore che
filtra da sé è una seconda lettura della stessa dichiarazione, cioè la specie di
seconda-fonte-di-verità che questo repository esiste per non produrre.

---

## 6 · Il default che non promette niente, rotto per dimostrarlo

`tests/fixtures/minimal.yaml` non dichiara `recorded_in` da nessuna parte. Il
test verifica **l'effetto**, non una sostituzione:

```python
# il cancello: la definizione TACE per davvero
for f in t.fields:
    assert f.recorded_in == RECORDED_IN_UNKNOWN

# l'effetto: chi monta la scheda telefono non ottiene NIENTE
assert t.recorded_in(RECORDED_IN_TRENCH) == []
assert [f.id for f in t.fields if f.recorded_in_trench] == []
```

**E la prova che quella guardia può scattare** — perché una guardia che non morde
dà lo stesso verde di una che funziona, e in questo ecosistema tre prove sono
state no-op. `test_that_the_check_above_can_actually_fire` prende la **stessa**
definizione, marca **un** campo, verifica che la sostituzione sia entrata, e
pretende che il selettore torni esattamente quell'uno:

```
assert [f.id for f in t.recorded_in("trench")] == ["nota"]
```

Se anche così tornasse vuoto, il test del default passerebbe per un bug del
selettore invece che per il default.

**Tre difese in più contro la lettura sbagliata:**

1. **Un valore che non è uno dei tre è un errore**, non un ripiego silenzioso su
   `unknown` — sette casi parametrizzati (`Trench`, `field`, `trincea`, `lab `,
   `""`, `None`, `True`). Una definizione che intendeva `trench` e ha scritto
   `Trench` sparirebbe dalla scheda telefono senza che niente dica perché, e il
   suo autore non potrebbe distinguerlo da un campo lasciato indeciso.
2. **`Field.recorded_in_trench`** è una property, così nessun consumatore deve
   ricordarsi qual è il default — e `unknown` non può essere preso per un sì da
   chi scrive `!= "lab"`, che è la forma in cui questo codice imputridirebbe.
3. **`unknown` è il primo di `RECORDED_IN_VALUES`**, con un test: chi legge
   l'elenco vede per primo il valore che non afferma niente.

---

## 7 · Come il formato rende esprimibile la distinzione del §4

**`required` e `recorded_in` sono ortogonali di proposito**, e insieme rendono la
distinzione calcolabile per campo:

| `required` | `recorded_in` | valore assente vuol dire |
|---|---|---|
| `true` | `trench` | **manca qualcosa**: era compilabile sullo scavo |
| `true` | `lab` | **incompleta per costruzione**, se la scheda è ancora di campo |
| `true` | `unknown` | **non si può decidere** — ed è la risposta onesta |

La terza riga è il motivo per cui `unknown` non può essere un sinonimo di `lab`:
«non lo so» e «si compila dopo» portano un validatore a due conclusioni diverse,
e una delle due **assolverebbe una scheda incompleta senza averne il diritto**.

**E il caso interessante esiste davvero nei dati**, non è ipotetico. I tre campi
obbligatori della US ICCD 2021:

```
us           → trench     (manca? allora manca qualcosa)
localita     → trench     (idem)
definizione  → unknown    (manca? NON SI PUÒ DECIDERE)
```

C'è un test che pretende che `definizione` resti obbligatoria e `unknown`,
perché senza un obbligatorio-incerto la terza riga della tabella non ha più un
esempio.

### Quello che il formato NON può dire, e lo dico adesso che costa poco

La definizione rende la distinzione calcolabile **per campo**. Per **applicarla**
serve una cosa in più che non c'è: sapere se *quella scheda compilata* è ancora
di campo o già rielaborata. **È uno stato del record, non della definizione**, e
oggi un record (`SPEC.md` §5) non lo dichiara.

Quindi: **il formato delle definizioni è a posto; manca una sola dichiarazione
sul lato record.** Un validatore di schede compilate — quando esisterà, e stanotte
non l'ho costruito — avrà bisogno di quell'unica aggiunta; tutto il resto ce l'ha
già. L'ho scritto in `SPEC.md` §1.6 invece di lasciarlo in questo referto, perché
chi scriverà il template ungherese legge la SPEC e non i referti.

---

## 8 · Suite e `git status --porcelain`

Baseline sul ramo, **prima** di toccare qualsiasi cosa — il riferimento del
prompt:

```
$ .venv/bin/python -m pytest -q
45 passed in 6.66s
```

Alla fine:

```
$ .venv/bin/python -m pytest -q
63 passed in 6.82s
```

**+18, tutti in `tests/test_recorded_in.py`**, nessun rosso, nessuno dei 45
toccato. E la stampa non è regredita:

```
$ … print iccd-us-2021 --record examples/us-3014-cencelle.yaml --lang it
out/us-3014-it.pdf — ICCD US 2021, 2 side(s) → 2 page(s), language 'it'
```

```
$ git status --porcelain
 M SPEC.md
 M src/stratigraph_templates/loader.py
 M src/stratigraph_templates/model.py
 M templates/es-ue-demo-2026/template.yaml
 M templates/iccd-us-2021/template.yaml
?? docs/2026-09-22-MICRO-i-campi-che-si-riempiono-coi-guanti.md
?? tests/test_recorded_in.py
```

---

## 9 · I miei inciampi

- **Un'ancora non univoca ha messo la chiave nel posto sbagliato.** Il mio
  `note=doc.get("note"),\n    )` compariva **due** volte in `loader.py`, e la
  sostituzione è finita su `GraphBinding` invece che su `Field`:
  `TypeError: GraphBinding.__init__() got an unexpected keyword argument`. 23
  test rossi in un colpo. La seconda volta ho verificato `s.count(...) == 1`
  prima di sostituire.
- **Il primo script di marcatura ha marcato zero campi.** Aveva l'indentazione
  scritta a mano (`^  - id:`) mentre il file usa quattro spazi. **Me l'ha detto
  l'assert finale, non i test**: la suite avrebbe continuato a dare 45 verdi
  sopra una definizione non marcata. La seconda versione **legge l'indentazione
  dal file**.
- **La misura sui nomi propri nel diff dava un falso positivo** per
  sottostringa (`anno` dentro «cannot»). Rifatta con i confini di parola.

---

## 10 · Repo da committare

**`stratigraph-templates`**, ramo `templates/02-il-campo`:

```
Add recorded_in: where each field of a sheet is filled in

Per field, three values and no fourth: trench (during the act of excavating),
lab (after it — laboratory, office, archive), unknown (the definition has not
said). The default is unknown, because it is the value that promises nothing: a
consumer must not be able to read silence as "then it is a trench field", and a
value that is not one of the three is refused rather than falling back.

The names are a place and a moment, never a rank — priority or level would have
implied a lab field matters less, and it does not: it is written at another
time, often by another person.

The criterion is not this format's opinion. Base A: a field one of the seven
field-assistant intents names is a trench field, justified by the line number
(stratigraph-chatbot/app/tools.py, grown from Elisa Dalla Longa's field card).
Base B, found while marking: the ICCD sheet draws the distinction in its own
labels — RESPONSABILE COMPILAZIONE SUL CAMPO against DATA RIELABORAZIONE.

US ICCD 2021: 8 trench, 3 lab, 48 unknown, each mark carrying its citation in
the datum. The demo ES sheet: 14 trench, 1 lab — a DIFFERENT subset, and 7 of 13
analogous concepts disagree, which is the test that keeps the marker per
standard instead of describing our own prejudice.

required and recorded_in are orthogonal, which is what makes "incomplete because
we are still on the dig" expressible; the one thing still missing is a record's
own declaration of its state, named in SPEC §1.6 rather than left implicit.

REPORTED, NOT FILLED IN: no intent covers a stratigraphic relationship — tools.py
carries `rapporti` explicitly as "merely carried", not understood — so the twelve
relationship boxes and the required DEFINIZIONE stay unknown. That is a gap in
the field assistant's intents, not in the sheet.

Implementation diff: 90 lines in model.py and loader.py, the format learning one
key; no field or standard name enters the code (measured with word boundaries),
the renderer is untouched, and test_no_standard_is_named_in_the_implementation
still passes.

Suite: 45 → 63 passed.
```
