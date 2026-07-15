import griffe
from griffe import Object, Module, Class, Function, TypeAlias
from pathlib import Path

def dedent(s: str) -> str:
    lines = s.split("\n")
    indentation_to_remove = 0 
    for line in lines:
        if line.strip(): # If the line is not empty (contains non-whitespace characters)
            indentation_to_remove = len(line) - len(line.lstrip())
            break # Found the first non-empty line, so we can stop
    dedented_lines = []
    for line in lines:
        if not line.strip():
            dedented_lines.append("") # Clear lines that are only whitespace
        elif len(line) >= indentation_to_remove and line[:indentation_to_remove].isspace():
            dedented_lines.append(line[indentation_to_remove:])
        else:
            dedented_lines.append(line) # Keep lines with less indent or non-whitespace prefix as is
    return "\n".join(dedented_lines).strip()


def render_module_or_class(obj: Module | Class, parent_path: Path = Path(".")) -> dict[Path, str]:
    files: dict[Path, str] = {}

    submodules: list[Module]     = sorted([m for m in obj.all_members.values() if isinstance(m, Module) if not m.name.startswith("_")], key=lambda m: m.name)
    classes: list[Class]         = sorted([m for m in obj.all_members.values() if isinstance(m, Class) if not m.name.startswith("_")], key=lambda m: m.name)
    functions: list[Function]    = sorted([m for m in obj.all_members.values() if isinstance(m, Function) if not m.name.startswith("_")], key=lambda m: m.name)
    typealiases: list[TypeAlias] = sorted([m for m in obj.all_members.values() if isinstance(m, TypeAlias) if not m.name.startswith("_")], key=lambda m: m.name)

    root = dedent(f"""
        ---
        title: {obj.name}
        ---

        <h6>{obj.__class__.__name__} <code>{obj.path}</code> {f"• <a href=\"{Path("..")}\">Go back</a>" if obj.parent else ""}</h6>
        {"# " + obj.name if not obj.docstring or (not obj.docstring.value.startswith("# ") and "\\n# " not in obj.docstring.value) else ""}

        {obj.docstring.value if obj.docstring else ""}

        {"### Modules" if submodules else ""}

        {"\n".join([f'- [`{module.name}`]({module.name})' for module in submodules])}

        {"### Classes" if classes else ""}

        {"\n".join([f'- [`{c.name}`]({c.name})' for c in classes])}

        {"### Types" if typealiases else ""}
        
        {"\n".join([f'- `{t.name}` defined by `{t.value}`' for t in typealiases])}

        {"### Functions" if functions else ""}
        
        {"\n".join([f'- [`{f.name}`]({f.name})' for f in functions])}

    """)

    for m in submodules:
        files.update(render_module_or_class(m, parent_path / obj.name))

    for c in classes:
        files.update(render_module_or_class(c, parent_path / obj.name))

    files[(parent_path / obj.name / "index")] = root
    return files



if __name__ == "__main__":
    files = render_module_or_class(griffe.load("rhombus"))

    for path, content in files.items():
        out_path = Path.cwd() / "docs/reference" / path.with_suffix(".md")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)