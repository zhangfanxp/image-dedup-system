import zipfile
from pathlib import Path


def unzip(zip_path: Path, extract_dir: Path):
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in z.infolist():
            try:
                # 处理中文路径
                info.filename = info.filename.encode('cp437').decode('utf-8')
            except Exception:
                pass
            z.extract(info, extract_dir)

