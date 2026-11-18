"""Etapas 1, 3 e 6: download dos dados brutos, com cache em `data/raw/`.

Cada função baixa só se o arquivo ainda não existe (ou se `refresh=True`) e
sempre devolve o conteúdo lido do disco. Assim, rodar o notebook de novo não
refaz centenas de requisições.
"""
import hashlib
import io
import json
import urllib.request
import zipfile

import pandas as pd

from src import chembl_api
from src.config import (
    ACTIVITIES_CSV, ACTIVITY_FIELDS, ACTIVITY_FILTERS, DOWNLOAD_INFO_JSON, KAGGLE_CSV, KAGGLE_CSV_NAME,
    KAGGLE_DOWNLOAD_URL, PROPERTIES_CSV, PROPERTY_COLUMNS, TARGETS,
)


def file_sha256(path):
    """Hash SHA-256 de um arquivo, para registrar exatamente qual versão dos dados foi usada."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_kaggle_dataset(refresh=False, path=KAGGLE_CSV):
    """Baixa o CSV original do Kaggle (só o CSV, o zip traz também imagens soltas) e devolve como DataFrame."""
    if refresh or not path.exists():
        with urllib.request.urlopen(KAGGLE_DOWNLOAD_URL, timeout=120) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        print("arquivos no zip:", archive.namelist())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(archive.read(KAGGLE_CSV_NAME))
    return pd.read_csv(path, index_col=0)


def load_activities(refresh=False, path=ACTIVITIES_CSV, info_path=DOWNLOAD_INFO_JSON):
    """Baixa as atividades dos 4 alvos com os filtros de `config.ACTIVITY_FILTERS`.

    Junto com o CSV, salva um JSON com a versão do ChEMBL, a data do download,
    os alvos e os filtros usados.
    """
    if refresh or not path.exists():
        frames = []
        for protein, target_id in TARGETS.items():
            rows = chembl_api.fetch_activities(target_id, ACTIVITY_FILTERS, ACTIVITY_FIELDS)
            print(f"{protein}: {len(rows)} atividades")
            frames.append(pd.DataFrame(rows, columns=ACTIVITY_FIELDS).assign(protein=protein))
        activities = pd.concat(frames, ignore_index=True)[["protein", *ACTIVITY_FIELDS]]
        path.parent.mkdir(parents=True, exist_ok=True)
        activities.to_csv(path, index=False)
        info_path.write_text(json.dumps({
            **chembl_api.get_status(),
            "downloaded_at": pd.Timestamp.now().isoformat(timespec="seconds"),
            "targets": TARGETS,
            "filters": ACTIVITY_FILTERS,
        }, indent=2))
    return pd.read_csv(path)


def load_download_info(path=DOWNLOAD_INFO_JSON):
    """Metadados do último download de atividades."""
    return json.loads(path.read_text())


def load_molecule_properties(molecule_ids, refresh=False, path=PROPERTIES_CSV):
    """Propriedades das moléculas pedidas. Só consulta a API para IDs que ainda não estão no cache."""
    columns = ["molecule_chembl_id", *PROPERTY_COLUMNS]
    cached = pd.read_csv(path) if path.exists() and not refresh else pd.DataFrame(columns=columns)
    missing = sorted(set(molecule_ids) - set(cached["molecule_chembl_id"]))
    print(f"buscadas na API: {len(missing)} moléculas")
    if missing:
        fetched = chembl_api.fetch_molecule_properties(missing, list(PROPERTY_COLUMNS))
        cached = pd.concat([cached, fetched], ignore_index=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        cached.to_csv(path, index=False)
    # A API devolve as propriedades como texto ("2.53"); converte para número.
    cached[list(PROPERTY_COLUMNS)] = cached[list(PROPERTY_COLUMNS)].apply(pd.to_numeric)
    return cached
