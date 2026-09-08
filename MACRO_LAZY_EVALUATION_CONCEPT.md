# Konzept: Lazy Evaluation von Macros in Rhombus

## 1. Problemstellung

Aktuell wertet Rhombus Macros **sofort (eager)** beim Funktionsaufruf aus.
Wenn ein Nutzer ein Macro aufruft, prüft der `MacroDispatcher` die aktuell in der Umgebung gesetzte `env.datapack_version`, wählt die passende Implementierung, führt sie aus und gibt direkt die resultierende, fertige AST-Node (eingepackt in ein `Density`-Objekt) zurück.

**Der Nachteil:**
Sobald das Python-Skript durchgelaufen ist, ist der generierte Abstract Syntax Tree (AST) fest an die Version gebunden, die zu Beginn eingestellt war. 
Möchte ein Creator sein Projekt für Minecraft 1.18, 1.20 und 1.21 kompilieren, muss er den gesamten Python-Build-Prozess dreimal starten. Ein einzelner Skript-Durchlauf mit anschließendem mehrfachen Serialisieren für verschiedene Versionen ist nicht möglich, da die Macros sich bereits beim Aufbau des Baumes "entschieden" haben.

## 2. Die Lösung: Lazy Binding durch `UnresolvedMacroNode`

Anstatt ein Datenmodell pro Macro zu definieren (was massiven Boilerplate verursachen würde), behalten wir die funktionalen Macros bei. Wir ändern jedoch das Verhalten des Dispatchers:

Wenn ein Macro aufgerufen wird, rechnet es **nichts** aus. Stattdessen wird eine generische, künstliche AST-Node vom Typ `UnresolvedMacroNode` erzeugt. Diese Node merkt sich lediglich die übergebenen Argumente und die Referenz auf den Dispatcher. 

Die tatsächliche Auswertung findet erst im allerletzten Schritt statt: beim Kompilieren / Serialisieren des Baumes.

### 2.1 Die homogene Node-Klasse

Wir fügen dem Core (z. B. in `rhombus.core.node` oder `rhombus.std.macros`) eine neue Klasse hinzu:

```python
from dataclasses import dataclass, field
from rhombus.core.node import RhombusASTNode
from rhombus.core.environment import env
from typing import Any

@dataclass
class UnresolvedMacroNode(RhombusASTNode):
    dispatcher: "MacroDispatcher" = field(repr=False, compare=False)
    args: tuple[Any, ...] = field(repr=False, compare=False)
    kwargs: dict[str, Any] = field(repr=False, compare=False)
    
    # Caching, um mehrfache Ausführung desselben Macros bei mehrfacher Serialisierung zu vermeiden
    _cached_version: float | None = field(init=False, default=None, repr=False, compare=False)
    _cached_node: RhombusASTNode | None = field(init=False, default=None, repr=False, compare=False)

    @property
    def resolved_node(self) -> RhombusASTNode:
        """Löst das Macro für die *aktuelle* Environment-Version auf (mit Caching)."""
        current_version = float(env.datapack_version) if env.datapack_version else 0.0
        
        # Cache prüfen, damit das Macro pro Version nur einmal berechnet wird
        if self._cached_version == current_version and self._cached_node is not None:
            return self._cached_node
            
        # Macro tatsächlich ausführen (gibt ein Density-Objekt zurück)
        density_result = self.dispatcher._execute_for_version(current_version, *self.args, **self.kwargs)
        
        self._cached_version = current_version
        self._cached_node = density_result.AST
        return self._cached_node

    # --- Weiterleiten der AST-Methoden an die aufgelöste Node ---

    def serialize_inline(self) -> Any:
        return self.resolved_node.serialize_inline()

    def serialize_toplevel(self) -> Any:
        return self.resolved_node.serialize_toplevel()

    @property
    def inscribed_toplevel_nodes(self) -> set["RhombusASTNode"]:
        return self.resolved_node.inscribed_toplevel_nodes
        
    def get_size(self) -> int:
        return self.resolved_node.get_size()
```

*(Hinweis: Da diese Node nie aus JSON deserialisiert wird, braucht sie keine `id` und keine komplexen `field()`-Eigenschaften).*

### 2.2 Anpassung des `MacroDispatcher`

Der `MacroDispatcher` in `rhombus.std.macros` fungiert derzeit sowohl als Evaluator als auch als Wrapper. 

Seine `__call__`-Methode wird nun extrem simpel:

```python
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        from rhombus.std.density import Density
        
        # Erzeuge eine generische Lazy-Node
        lazy_node = UnresolvedMacroNode(
            dispatcher=self,
            args=args,
            kwargs=kwargs
        )
        
        # Da Macros Density-Objekte zurückgeben, verpacken wir die Node
        return Density(lazy_node)
```

Die eigentliche Auswertungslogik (die momentan in `__call__` liegt), zieht in eine interne Methode um, z. B. `_execute_for_version(self, target_version: float, *args, **kwargs)`.

## 3. Workflow & Vorteile

Der neue Workflow für den Endnutzer sieht so aus:

```python
# script.py
from rhombus.std import *

# 1. Baum aufbauen (Macros werden hier NICHT ausgewertet, nur registriert)
surface = macro_a(macro_b(10)) 
out = DatapackResource("my:surface", surface)

# 2. Baum für Version 1.18 kompilieren
env.set_version(1.18)
out.serialize_toplevel() # Löst macro_a und macro_b auf 1.18 Basis auf

# 3. Baum für Version 1.21 kompilieren
env.set_version(1.21)
out.serialize_toplevel() # Löst macro_a und macro_b auf 1.21 Basis auf
```

**Vorteile:**
1. **Performance & Flexibilität:** Ein Skript generiert einen massiven AST, der dank der Lazy-Nodes dynamisch bleibt. Multi-Version-Datapacks aus einer Laufzeit sind problemlos machbar.
2. **Kein Boilerplate:** Nutzer müssen für ihre Macros keine komplexen Klassen oder Modelle anlegen. Das `@macro`-Paradigma bleibt zu 100% unverändert erhalten.
3. **Transparent:** Für die Density-Klasse (z. B. bei Additionen `surface + 5`) macht es keinen Unterschied, ob in ihr eine fertige `math`-Node oder eine `UnresolvedMacroNode` steckt. Beide sind vom Typ `RhombusASTNode`.

## 4. Edge Cases

- **Fehlerbehandlung:** Wenn ein Nutzer falsche Parameter in ein Macro steckt, wirft das System den Fehler nicht mehr sofort in der Zeile des Python-Aufrufs, sondern erst beim Aufruf von `serialize_toplevel()`. Da in der Exception jedoch der Traceback des aufgerufenen Macros auftaucht, bleibt es gut debugbar.
- **Inspektion:** Ein `print(surface.AST)` gibt nun eine Repräsentation des `UnresolvedMacroNode`-Objekts zurück, was den Baum stark abstrahiert, da man die tatsächliche Struktur (z. B. die vielen tiefen `math`-Operationen) erst sieht, wenn man `.resolved_node` aufruft. Dies ist für die Übersichtlichkeit von ASTs in der Konsole jedoch oft sogar ein Vorteil.
