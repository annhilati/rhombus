- [x] §1 Decode Datapack Resources dynamically from `DensityFunction` subclasses
  - [x] §1.1 Annotate with concrete Datapack Resource classes instead of `DatapackResource` in `DensityFunction` fields
- [x] §2 Decode density functions from a `DataPack`
  - [x] §2.1 Implement a datapack context
- [ ] §3a Warn for potential invalid values in fields of `DensityFunction` subclasses by some sort of generic description
- [ ] §3b Warn for potential invalid values in fields of `DatapackResource` subclasses by some sort of generic description
- [ ] §4 Perform AST simplification on encoding
  - Wrap raw references
  - Merge literal arithmetic
  - Remove canonically false `range_choice`
- [x] §6 Don't use factories, that utilize `__new__`
- [x] §7 Implement a universal decoding and encoding system that can be used anywhere
  - Perhaps a large configurable function with type specific lambdas?
  - [x] §5 Add support for Unions, Tuples and Optionals for DensityFunction fields
- [x] §8 Unify wizards in a single fabric, dont use on as a decorator and a fabric
- [x] §9 New system for DataPackResources to store references. They shouldn't be a field in the init. (Not make them frozen anymore?)
  - [x] §9.1 Implement the referenced classmethod in the base class (utilize the field util when instanciating?)
  - [x] §9.2 Implement property setting and store reference secretly
  - [x] §10 Implement separation rules for caching functions
  - [ ] §11 Abstract compiler instructions, so that completely new classes can be hooked in




# TODO Features
- Examine, whether to use frozen dataclasses for nodes
- Rethink, where to auto cache and how and what to repr for cached situations






Klar. Hier ist eine kompakte Übergabe-Nachricht für eine neue Codex-Instanz:

```text
Wir debuggen ein Python/Rhombus-Projekt `Aetherial-Islands` mit einer DSL für Minecraft Density Functions. Es gibt einen mysteriösen Bug: Sobald ein bestimmter Import wegen zyklischer Imports aktiviert wird, generiert die Welt monolithisch/falsch. Es geht vermutlich um falsche Bindung oder falsche Konstruktion eines Density-Werts, nicht um Export allein.

Wichtige Erkenntnisse bisher:

1. Ein Diff zwischen gutem und kaputtem Build zeigte:
   In `data/aetherial_islands/worldgen/density_function/terrain/final.json` wird überall
   `rhombus:partitioned/2d4faf6ba77f879c009cd307e66cc420`
   ersetzt durch
   `rhombus:partitioned/9fb521b4594b339349bc7c1458a04a3e`.

2. Die Datei `2d4...` vs. `9fb...` unterscheidet sich konkret in einer Spline-Coordinate:
   ```diff
   - "coordinate": "rhombus:partitioned/68471d7f5104504927fafef10232c116"
   + "coordinate": "rhombus:partitioned/68142a228074884e2f0950d24a285ba1"
   ```
   Das passiert bei Spline-Punkten mit markanten Locations `96` und `-0.14`.

3. Der passende Source-Code steht in `terrain/terrain.py`:
   ```python
   terrain_pre_caves = cache_once(spline(
       coordinate=continents_base,
       points=[
           (-1.06, spline(
               coordinate=coords.y(),
               points=[
                   (80, -0.1, 0),
                   (96, spline(
                       coordinate=islands_FINAL,
                       points=[
                           (-1, -1.0, 1),
                           (1, 1.0, 1)
                       ]
                   ), 0)
               ]), 0),
           (-1.06, -0.1, 0),
           (-0.17, -0.1, 0),
           (-0.14, spline(
               coordinate=islands_FINAL,
               points=[
                   (-1, -1.0, 1),
                   (1, 1.0, 1)
               ]
           ), 0)
       ]
   ))
   ```
   Also der verdächtige Wert ist `islands_FINAL`.

4. Im guten Zustand:
   `islands_FINAL` hash = `68471d7f5104504927fafef10232c116`
   `terrain_pre_caves` hash = `2d4faf6ba77f879c009cd307e66cc420`

5. Im kaputten Zustand:
   Direkt nach Import in `terrain.py`:
   `islands_FINAL` hash = `68142a228074884e2f0950d24a285ba1`
   `terrain_pre_caves` hash = `9fb521b4594b339349bc7c1458a04a3e`

6. In `terrain.py` wurde getestet:
   ```python
   import terrain.islands as islands_module
   print(uuid_hash(islands_FINAL.as_dict()))
   print(uuid_hash(islands_module.islands_FINAL.as_dict()))
   print(islands_FINAL is islands_module.islands_FINAL)
   ```
   Ergebnis:
   Beide `68142...`, `same object: True`.
   Also `terrain.py` überschreibt den Namen nicht; `terrain.islands.islands_FINAL` ist bereits falsch.

7. In `terrain/islands.py` direkt nach der Definition von `islands_FINAL`:
   `islands.py islands_FINAL after definition: 68142a228074884e2f0950d24a285ba1`
   Also `islands_FINAL` wird nicht später überschrieben, sondern direkt falsch konstruiert.

8. Ziel für die neue Instanz:
   Autonom im Projekt nachsehen, besonders `terrain/islands.py`, `terrain/island_layers.py`, `terrain/ridges.py`, `terrain/noise_router.py`, `build.py`.
   Finde heraus, welcher Eingabewert/Baustein in der Definition von `islands_FINAL` durch den mysteriösen Import kippt.
   Suche nach zyklischen Imports, `import *`, direkten gleichnamigen Imports, und spät/lokal gesetzten Imports.
   Nutze Hash-Debugging mit:
   ```python
   from rhombus.core.utils import uuid_hash

   def h(name, value):
       try:
           print(name, uuid_hash(value.as_dict()))
       except Exception as e:
           print(name, type(e).__name__, e)
   ```
   Direkt vor `islands_FINAL` alle verwendeten Density-Bausteine printen. Im guten und kaputten Zustand vergleichen.
   Der erste Baustein, der von gut zu kaputt wechselt, ist wahrscheinlich die Ursache.

9. Auffällige semantische Differenz:
   Guter `islands_FINAL` (`68471...`) beginnt als:
   - `minecraft:cache_once`
   - `minecraft:range_choice`
   - `input`: `rhombus:partitioned/4e43...`
   - `min_inclusive`: `-64.0`
   - `max_exclusive`: `0.0`
   - danach Y-Bänder `48`, `96`, `144`, `192`, `256`

   Kaputter `islands_FINAL` (`68142...`) beginnt als:
   - `minecraft:cache_once`
   - `minecraft:range_choice`
   - `input`: `rhombus:partitioned/80506...`
   - `min_inclusive`: `-0.565`
   - `max_exclusive`: `10.0`
   - deutlich größere/andere Funktion

10. Wichtig: Vorherige Rhombus-Core-Patches in anderem Workspace haben das Problem nicht gelöst und sind vermutlich nicht in diesem Projekt aktiv, weil dieses Projekt die installierte Rhombus-Version aus `site-packages` nutzt. Nicht davon ablenken lassen.

Bitte als Agent übernehmen: Dateien lesen, gezielt Debug-Instrumentierung oder statische Analyse machen, Ursache finden und möglichst fixen. Keine destruktiven Git-Kommandos. Wenn du Dateien änderst, minimal und erklären.
```

Am besten gibst du der neuen Instanz auch direkt Zugriff auf das richtige Projektverzeichnis `C:\Users\Annhilati\Documents\GitHub\Aetherial-Islands`, nicht auf `quinarity`.


---


Ja, das Problem liegt sehr wahrscheinlich in Rhombus, nicht in deinem Projekt.

Der Bug sitzt in:

[C:\Users\Annhilati\AppData\Local\Programs\Python\Python313\Lib\site-packages\rhombus\macros\conditional.py:247](C:/Users/Annhilati/AppData/Local/Programs/Python/Python313/Lib/site-packages/rhombus/macros/conditional.py:247)

```python
def __post_init__(self):
    self.elsewhen._chain = self
```

`elsewhen` ist dort eine verschachtelte Klasse, und `_chain` ist ein `ClassVar`. Das heißt: Jede neue `when(...).then(...)`-Kette überschreibt global, zu welcher `Causality`-Instanz `.elsewhen(...)` gehört.

Minimaler Repro, unabhängig von deinem Projekt:

```python
a = when(y).atleast_but_less(0, 1).then(10)
b = when(y).atleast_but_less(100, 200).then(20).otherwise(30)
c = a.elsewhen(y).atleast_but_less(1, 2).then(11).otherwise(12)
```

`c` beginnt fälschlich mit dem `100..200`-Case aus `b`, nicht mit dem `0..1`-Case aus `a`.

Genau das passiert bei dir:

```text
islands.py baut islands_FINAL
  -> layer_depth_top()
    -> import terrain.ridges
      -> ridges.py baut eigene when(...)-Ketten
  -> islands_FINAL macht weiter mit .elsewhen(...)
```

Ab da hängt `.elsewhen(...)` nicht mehr an der Insel-Kette, sondern an der zuletzt gebauten Ridge-Kette. Deshalb wird `islands_FINAL` plötzlich zu `68142...` und sieht strukturell wie `ridges_FINAL` aus.

Der richtige Rhombus-Fix wäre: `elsewhen` darf keinen globalen Klassenzustand benutzen. Es muss pro `Causality`-Instanz ein gebundener Proxy sein, z. B. konzeptionell:

```python
@property
def elsewhen(self):
    return ElseWhen(self)
```

statt `self.elsewhen._chain = self`.

Mein vorheriger String-Reference-Fix war also nur ein Workaround, weil er den problematischen Import während der offenen `when`-Kette vermeidet. Für dein Ziel, `interpolated(ridges_noise)` als Python-Symbol zu benutzen, muss Rhombus’ Conditional-Builder repariert werden.