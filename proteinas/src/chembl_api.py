"""Cliente mínimo da API REST do ChEMBL.

Só faz requisições e devolve os dados. Não salva arquivos nem aplica regras de
curadoria: isso fica em `download.py` e `curation.py`.
"""
import json
import time
import urllib.parse
import urllib.request

import pandas as pd

from src.config import CHEMBL_API, CHEMBL_HOST

MOLECULE_BATCH_SIZE = 100


def get_json(url, retries=5):
    """GET com novas tentativas e espera exponencial (a API do ChEMBL às vezes oscila)."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                return json.load(response)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    # Nunca executa (a última tentativa retorna ou relança o erro), mas deixa explícito
    # para o verificador de tipos que a função não devolve None.
    raise RuntimeError(f"falha ao buscar {url}")


def query(endpoint, **params):
    """Consulta um endpoint da API, por exemplo `query("activity", target_chembl_id="CHEMBL203")`."""
    return get_json(f"{CHEMBL_API}/{endpoint}.json?{urllib.parse.urlencode(params)}")


def get_status():
    """Versão e data de lançamento da base do ChEMBL em uso na API."""
    status = get_json(f"{CHEMBL_API}/status.json")
    return {key: status[key] for key in ["chembl_db_version", "chembl_release_date"]}


def describe_targets(target_ids):
    """Nome, organismo e tipo de cada alvo de um dicionário {rótulo: target_chembl_id}."""
    rows = []
    for label, target_id in target_ids.items():
        target = get_json(f"{CHEMBL_API}/target/{target_id}.json")
        rows.append({"rótulo": label, "target_chembl_id": target_id, **{key: target[key] for key in ["pref_name", "organism", "target_type"]}})
    return pd.DataFrame(rows)


def search_targets(text, limit=5):
    """Busca alvos pelo nome."""
    targets = query("target/search", q=text, limit=limit)["targets"]
    return pd.DataFrame(targets)[["target_chembl_id", "pref_name", "organism", "target_type"]]


def count_activities(target_id, **filters):
    """Quantidade de atividades de um alvo que atendem aos filtros, sem baixá-las."""
    return query("activity", target_chembl_id=target_id, limit=1, only="activity_id", **filters)["page_meta"]["total_count"]


def fetch_activities(target_id, filters, fields):
    """Baixa todas as atividades de um alvo, percorrendo as páginas da API (1.000 por página)."""
    params = {"target_chembl_id": target_id, **filters, "limit": 1000, "only": ",".join(fields)}
    url = f"{CHEMBL_API}/activity.json?{urllib.parse.urlencode(params)}"
    rows = []
    while url:
        page = get_json(url)
        rows += page["activities"]
        url = CHEMBL_HOST + page["page_meta"]["next"] if page["page_meta"]["next"] else None
    return rows


def fetch_molecule_properties(molecule_ids, properties):
    """Busca propriedades de várias moléculas, em lotes de 100 IDs por requisição."""
    molecule_ids = list(molecule_ids)
    rows = []
    for start in range(0, len(molecule_ids), MOLECULE_BATCH_SIZE):
        batch = molecule_ids[start:start + MOLECULE_BATCH_SIZE]
        page = query("molecule", molecule_chembl_id__in=",".join(batch), only="molecule_chembl_id,molecule_properties", limit=MOLECULE_BATCH_SIZE)
        for molecule in page["molecules"]:
            values = molecule["molecule_properties"] or {}
            rows.append({"molecule_chembl_id": molecule["molecule_chembl_id"], **{key: values.get(key) for key in properties}})
    return pd.DataFrame(rows, columns=["molecule_chembl_id", *properties])
