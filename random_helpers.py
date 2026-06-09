from pathlib import Path

import zipfile, requests, shutil

def download_vanilla_data(version: str, outputtdir: Path) -> None:

    url = f"https://github.com/misode/mcmeta/archive/refs/tags/{version}-data.zip"
    
    outputtdir.mkdir(exist_ok=True)
    zip_path = outputtdir / "mcmeta.zip"

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(outputtdir)

    extracted_root = next(
        p for p in outputtdir.iterdir()
        if p.is_dir() and p.name.startswith("mcmeta-")
    )

    for item in extracted_root.iterdir():
        target = outputtdir / item.name

        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    shutil.rmtree(extracted_root)
    zip_path.unlink(True)

def debug_dft(d: dict[str, type]):
    """Get the complete module path of a type."""
    from builtins import max
    d = {k: v for k, v in sorted(d.items())}
    width = max((len(str(id)) for id in d), default=0)
    info = "\n".join([
        f"{str(id).ljust(width)} : {typ.__module__}.{typ.__qualname__}" for id, typ in d.items()
    ])
    return info