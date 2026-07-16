# TODO: Show class metadata at the top of class pages

import re
import griffe
from griffe import Docstring, Object, Module, Class, Function, TypeAlias, Attribute
from pathlib import Path

def dedent(s: str) -> str:
    lines = s.split("\n")
    indentation_to_remove = 0 
    for line in lines:
        if line.strip():
            indentation_to_remove = len(line) - len(line.lstrip())
            break
    dedented_lines = []
    for line in lines:
        if not line.strip():
            dedented_lines.append("")
        elif len(line) >= indentation_to_remove and line[:indentation_to_remove].isspace():
            dedented_lines.append(line[indentation_to_remove:])
        else:
            dedented_lines.append(line)
    return "\n".join(dedented_lines).strip()

def escape_markdown(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+\-.!])", r"\\\1", text)

def render_docstring(docstring: Docstring) -> str:
    if not docstring:
        return ""
    
    parsed = docstring.parsed or None
    if not parsed:
        return docstring.value

    parts: list[str] = []
    for section in parsed:
        try:
            kind = section.kind.value
            if kind == "text":
                # IMPORTANT: Here we can post process
                out = re.sub(r"-{3,}", "", section.value)
                parts.append(out)

            elif kind == "parameters":
                parts.append("**Parameters:**\n")
                for param in section.value:
                    type_str = f" (`{param.annotation}`)" if getattr(param, "annotation", None) else ""
                    parts.append(f"- `{param.name}`{type_str}: {param.description}")
            elif kind == "returns":
                parts.append("**Returns:**\n")
                for ret in section.value:
                    type_str = f"`{ret.annotation}`: " if getattr(ret, "annotation", None) else ""
                    parts.append(f"- {type_str}{ret.description}")
            elif kind == "raises":
                parts.append("**Raises:**\n")
                for exc in section.value:
                    type_str = f"`{exc.annotation}`: " if getattr(exc, "annotation", None) else ""
                    parts.append(f"- {type_str}{exc.description}")
            else:
                parts.append(f"**{kind.capitalize()}:**\n")
                if isinstance(section.value, str):
                    parts.append(section.value)
                else:
                    parts.append(str(section.value))
        except Exception:
            parts.append(str(getattr(section, "value", "")))
            
        parts.append("\n")

    return "\n".join(parts).strip()

def render_function(func: Function) -> str:

    def format_function_signature(func: Function) -> str:
        params = []
        for p in func.parameters or []:
            s = p.name
            if p.annotation:
                s += f": {p.annotation}"
            if p.default:
                s += f" = {p.default}"
            params.append(s)
        
        returns = f" -> {func.returns}" if getattr(func, "returns", None) else ""
        
        decorators = ""
        labels = getattr(func, "labels", set())
        if "classmethod" in labels:
            decorators += "@classmethod\n"
        elif "staticmethod" in labels:
            decorators += "@staticmethod\n"
            
        return f"{decorators}def {func.name}({', '.join(params)}){returns}: ..."

    signatures = []
    if hasattr(func, "overloads") and func.overloads:
        for overload in func.overloads:
            signatures.append(format_function_signature(overload))
    else:
        signatures.append(format_function_signature(func))
    
    sig_block = "\n".join(signatures)
    
    return dedent(f"""
        ### {escape_markdown(func.name)}

        ```python
        {sig_block}
        ```

        {render_docstring(func.docstring)}
    """)

def render_property(attr: Attribute) -> str:
    annotation = f" -> {attr.annotation}" if attr.annotation else ""
    return dedent(f"""
        ### {escape_markdown(attr.name)}

        ```python
        @property
        def {attr.name}(self){annotation}: ...
        ```

        {render_docstring(attr.docstring)}
    """)

def render_typealias(obj: TypeAlias) -> str:
    return dedent(f"""
        ### {escape_markdown(obj.name)}

        ```python
        type {obj.name} = {obj.value}
        ```

        {render_docstring(obj.docstring)}
    """)

def render_class_members(obj: Class) -> str:
    constructors: list[Function] = []
    properties: list[Attribute] = []
    methods: list[Function] = []
    static_methods: list[Function] = []


    for m in obj.all_members.values():
        if m.name.startswith("_") and not m.name.startswith("__"):
            continue
            
        if isinstance(m, Function):
            labels = m.labels or set()
            
            if m.name in ("__init__", "__new__"):
                constructors.append(m)
            elif "classmethod" in labels and getattr(m, "returns", None) and (obj.name in str(m.returns) or "Self" in str(m.returns)):
                constructors.append(m) 
            elif "staticmethod" in labels or "classmethod" in labels:
                static_methods.append(m)
            else:
                methods.append(m)
                
        elif isinstance(m, Attribute):
            labels = m.labels or set()
            if "property" in labels:
                properties.append(m)

    constructors    .sort(key=lambda m: m.name)
    properties      .sort(key=lambda m: m.name)
    methods         .sort(key=lambda m: (m.name.startswith("__"), m.name))
    static_methods  .sort(key=lambda m: m.name)

    if not (constructors or properties or methods or static_methods):
        return ""

    return dedent(f"""
        {"## Constructors" if constructors else ""}
        
        {"\n\n---\n".join([render_function(f) for f in constructors])}

        {"## Properties" if properties else ""}
        
        {"\n\n---\n".join([render_property(p) for p in properties])}

        {"## Methods" if methods else ""}
        
        {"\n\n---\n".join([render_function(f) for f in methods])}

        {"## Static & Class Methods" if static_methods else ""}
        
        {"\n\n---\n".join([render_function(f) for f in static_methods])}
    """)

def render_module_functions(obj: Module) -> str:
    regular_functions = sorted([m for m in obj.all_members.values() if isinstance(m, Function) and not m.name.startswith("_")], key=lambda m: m.name)
    
    if not regular_functions:
        return ""
        
    return dedent(f"""
        ## Functions
        
        {"\n\n---\n".join([render_function(f) for f in regular_functions])}
    """)

def render_module_or_class(obj: Module | Class, parent_path: Path = Path(".")) -> dict[Path, str]:
    files: dict[Path, str] = {}

    submodules:  list[Module]    = sorted([m for m in obj.all_members.values() if isinstance(m, Module) and not m.name.startswith("_")], key=lambda m: m.name)
    classes:     list[Class]     = sorted([m for m in obj.all_members.values() if isinstance(m, Class) and not m.name.startswith("_")], key=lambda m: m.name)
    typealiases: list[TypeAlias] = sorted([m for m in obj.all_members.values() if isinstance(m, TypeAlias) and not m.name.startswith("_")], key=lambda m: m.name)
    
    functions_block = render_class_members(obj) if isinstance(obj, Class) else render_module_functions(obj)

    root = dedent(f"""
        ---
        title: {obj.name}
        ---

        <h6>{obj.__class__.__name__} <code>{obj.path}</code> {f'• <a href="../index.md">Go back</a>' if obj.parent else ""}</h6>
        {"# " + escape_markdown(obj.name) if not obj.docstring or (not obj.docstring.value.startswith("# ") and "\n# " not in obj.docstring.value) else ""}

        {render_docstring(obj.docstring)}

        {"## Modules" if submodules else ""}

        {"\n".join([f'- [`{module.name}`]({module.name})' for module in submodules])}

        {"## Classes" if classes else ""}

        {"\n".join([f'- [`{c.name}`]({c.name})' for c in classes])}

        {"## Types" if typealiases else ""}
        
        {"\n\n".join([render_typealias(t) for t in typealiases])}
        
        {functions_block}
    """)

    for m in submodules:
        files.update(render_module_or_class(m, parent_path / obj.name))

    for c in classes:
        files.update(render_module_or_class(c, parent_path / obj.name))

    files[(parent_path / obj.name / "index")] = root
    return files

if __name__ == "__main__":
    files = render_module_or_class(griffe.load("rhombus", docstring_parser="google"))

    for path, content in files.items():
        out_path = Path.cwd() / "docs/reference" / path.with_suffix(".md")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)