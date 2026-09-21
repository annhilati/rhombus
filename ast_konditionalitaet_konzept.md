# Konzept: Native Python Konditionalität in Rhombus (AST Transformation)

## 1. Problemstellung
Bisher wird Konditionalität für Density Functions in Rhombus über ein Fluent-Interface abgebildet (`when(x).equals(1).then(10).otherwise(0)`). Dies ist funktional, jedoch weicht es von der gewohnten Python-Syntax ab. 
Der naheliegende Versuch, Pythons `if`-Statement über die `__bool__`-Methode (Magic Method) zur Laufzeit abzufangen, scheitert am Kontrollfluss des Python-Interpreters: Bei einem `if` fordert Python zwingend einen eindeutigen Wahrheitswert an, um exakt **einen** Pfad auszuführen. Für den Density-Graphen (`range_choice` / `interval_select`) müssen jedoch **beide** Pfade erfasst werden. Das Erzwingen der Ausführung beider Pfade zur Laufzeit führt unweigerlich zu massiven Problemen und unerwünschten Seiteneffekten.

## 2. Der Lösungsansatz: AST-Transformation (Ahead-of-Time)
Die branchenübliche Lösung (wie sie z.B. bei TensorFlows `@tf.function` AutoGraph eingesetzt wird) ist die Modifikation des *Abstract Syntax Trees (AST)* **vor** der eigentlichen Ausführung der Funktion.

### Ablauf
1. Ein Decorator (z.B. `@density_macro` oder ein dedizierter `@dsl`-Decorator) wird an der Funktion verwendet.
2. Beim Laden der Funktion wird ihr Quellcode (`inspect.getsource`) gelesen.
3. Der Code wird mittels `ast.parse` in einen Syntaxbaum (AST) umgewandelt.
4. Ein `ast.NodeTransformer` durchsucht den Baum nach `if`-Statements (`ast.If`) und Inline-Bedingungen (`ast.IfExp`).
5. Diese Knoten werden so umgeschrieben, dass sie stattdessen die internen Fluent-Interface-Methoden oder direkt die `range_choice` Makros aufrufen.
6. Der manipulierte Baum wird via `compile` neu kompiliert und ersetzt die ursprüngliche Funktion.

## 3. Analyse der Syntax-Fälle

### Fall 1: Inline-Konditionalität (Ternary Operator)
**Python-Syntax:**
```python
out = 10.0 if input == 1.0 else 20.0
```
**AST-Knoten:** `ast.IfExp`
**Transformation:** `out = when(input == 1.0).then(10.0).otherwise(20.0)`
**Bewertung:** Sehr einfach umzusetzen. Da es sich um Ausdrücke (Expressions) handelt, entstehen keine Scoping-Probleme oder Seiteneffekte. Dies ist der ideale Startpunkt.

### Fall 2: Einfaches Block-If mit Else
**Python-Syntax:**
```python
if input == 1.0:
    out = 10.0
else:
    out = 20.0
```
**AST-Knoten:** `ast.If`
**Transformation:**
Hier muss der Transformer erkennen, dass in beiden Blöcken die Variable `out` deklariert wird, und dies umschreiben zu:
`out = when(input == 1.0).then(10.0).otherwise(20.0)`
**Bewertung:** Mittelschwer. Erfordert das Tracken von Zuweisungen (`ast.Assign`) innerhalb der jeweiligen Blöcke.

### Fall 3: Elif-Ketten
**Python-Syntax:**
```python
if input == 1.0:
    out = 10.0
elif input == 2.0:
    out = 20.0
```
**AST-Knoten:** Rekursive `ast.If` Knoten im `orelse`-Block.
**Transformation:**
Ein `elif` existiert im Python-AST nicht als eigenständiger Knoten, sondern ist nur ein `If` im Else-Zweig des Eltern-Ifs. Das harmoniert perfekt mit unserer bestehenden `.elsewhen()`-Architektur und lässt sich durch eine einfache Rekursion im NodeTransformer abbilden.

### Fall 4: Unvollständige Konditionalität (fehlendes Else)
**Python-Syntax:**
```python
out = 0.0
if input == 1.0:
    out = 10.0
```
**Transformation:**
Die Variable behält ihren vorherigen Wert: `out = when(input == 1.0).then(10.0).otherwise(out)`
**Bewertung:** Komplex. Der Transformer muss theoretisch wissen, welche Variable gemeint ist und dass sie vorher bereits im Scope definiert wurde (Dataflow Analysis).

## 4. Fazit & Nächste Schritte
Die AST-Transformation ist ein solider und sicherer Weg, um native Syntax zu unterstützen, ohne die Ausführungslogik von Python zu kompromittieren. 

**Vorgeschlagener erster Meilenstein:**
Implementierung des AST-Transformers für `ast.IfExp` (Inline-Konditionalität). Dies erfordert keine komplexe Variablen-Analyse und bringt sofort massiven Mehrwert bei Zuweisungen und Return-Statements.
