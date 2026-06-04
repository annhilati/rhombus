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