# Probleme

### Versionierung

Wir wollen Worldgen-Features aus verschiedenen Versionen untersützen. Die API soll auf die neuste Version ausgelegt sein, aber auch Implementierungen für ältere Versionen bieten.
Letzteres wird höchstwahrscheinlich silent passieren. Funktionen, die in älteren Versionen garkeine Implementierung haben werden als solche nicht direkt ersichtlich sein, es sei denn wir fügen es zu den Docstrings hinzu.

1. Manche Density-Function-Types (z.B. `reciprocal`) haben ihren Namen geändert, sind aber an sich gleich geblieben. Rhombus sollte implizit wissen, in welcher Version es welche benutzt.
2. Manche Density-Function-Types (z.B. alle Kinder von `MappedDensityFunction`) haben mal den Namen eines Feldes geändert. Rhombus sollte implizit wissen, in welcher Version es welche Bezeichnungen benutzt.

## Lösungsansatz: Deklarative Metadaten in AST-Nodes

Da das Problem nicht nur Density Functions, sondern auch andere Konzepte (wie z.B. Noise-Konfigurationen in `rhombus.std.noise`) betrifft, bietet es sich an, die Versionierungslogik in der gemeinsamen Basisklasse `RhombusASTNode` zu implementieren.

### Syntax-Brainstorming

Hier sind verschiedene Anwendungsfälle und wie sie syntaktisch gelöst werden könnten.

#### 1. Feld-Umbenennungen (z.B. in `MappedDensityFunction`)

```python
class MappedDensityFunction(DensityFunction):
    input: DensityFunction = field(legacy_keys={111.0: "argument"})
                                   # legacy_keys.keys() sind die Versionen bis (exklusiv) zu denen die alten Feldnamen benutzt wurden.
```

#### 2. Konstanten-Umbenennungen (z.B. ID `invert` zu `reciprocal`)

```python
class reciprocal(MappedDensityFunction):
    id: ClassVar[str] = field("minecraft:reciprocal", legacy_values={111.0: "minecraft:invert"})
                                                      # legacy_values.keys() sind die Versionen bis (exklusiv) zu denen die alten Werte benutzt wurden.
```

*Lösung für mehrdeutige IDs:* Die explizite Registrierungslogik iteriert einfach über alle bekannten IDs einer Klasse (aktuell + legacy) und fügt sie alle in das `deserialization_register` ein. So werden alte und neue JSON-Keys automatisch auf die richtige, aktuellste Klasse gemappt, ohne das Register-Konzept ändern oder Seiteneffekte einführen zu müssen.

#### 3. Hinzugefügte Felder

```python
class someFunctionType(DensityFunction):
    id: ClassVar[str] = "minecraft:some_function_type"
    first_parameter: float
    new_parameter: float = field(added_with=120.0)
        # added_with setzt einen leeren Wert als default
```

#### 4. Entfernte Felder

```python
class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]
    min_value: float = field(removed_with=10.0)
    max_value: float = field(removed_with=10.0)
        # removed_with setzt automatisch einen leeren Wert als default
```

#### 5. Validierung

Ob wir das so streng einführen überlegen wir noch

```python
class clamp(DensityFunction):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction
    min: float = field(validate=lambda x: -1000000 <= x <= 1000000)
    max: float = field(validate=lambda x: -1000000 <= x <= 1000000)
```

#### 6. Typ-Versionierung

```python
class end_islands(SimpleDensityFunction, versions=(9, 113)):
        # versions entspricht (added_with, removed_with)
    id: ClassVar[str] = "minecraft:end_islands"
```


#### 7. Mod-Kompatibilität (Erweiterte Versions-Bedingungen)

Da Rhombus auch Addons/Mods unterstützt, reicht eine einfache Float-Zahl (für die Datapack-Version) oft nicht aus. Stattdessen können die Versions-Argumente (`added_with`, `removed_with`, `legacy_keys`, `versions`) auch abstrakte Bedingungen (z.B. Tupel) entgegennehmen.

```python
class lithostitched_noise(DensityFunction):
    id: ClassVar[str] = "lithostitched:noise"
    
    # Feld, das in Vanilla ab Version 113.0 existiert
    vanilla_param: float = field(added_with=113.0)
    
    # Feld, das erst ab einer bestimmten Version des Mods "lithostitched" existiert
    new_mod_param: float = field(added_with=("lithostitched", "1.2.0"))
```

Die Basisklasse fragt dann dynamisch das `RhombusEnvironment`, ob die Vanilla-Version hoch genug ist oder ob die benötigte Mod in ausreichender Version geladen ist. Dadurch leben Vanilla- und Mod-Typen völlig organisch im selben Pool und werden einheitlich evaluiert.

#### Komplexbeispiel

```python
class Noise(DatapackResource):
    base_octave: int = field(legacy_keys={113.0: "firstOctave"})
    amplitudes: list[float]
    base_amplitude: float = field(1.0, added_with=113.0)
    normalize: bool | Literal["legacy"] = field(True, added_with=113.0)
```