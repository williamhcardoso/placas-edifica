"""
Backup diário do banco de placas.

Usa a API de backup online do SQLite, que copia um banco em uso sem risco de
pegar o arquivo pela metade — o serviço continua no ar durante a cópia.
Roda pelo timer systemd `placas-backup.timer`.
"""
import gzip
import shutil
import sqlite3
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
BANCO = BASE / "placas.db"
DESTINO = BASE / "backups"
DIAS = 14


def copiar():
    DESTINO.mkdir(exist_ok=True)
    bruto = DESTINO / ("placas-" + time.strftime("%Y%m%d") + ".db")
    origem = sqlite3.connect("file:" + str(BANCO) + "?mode=ro", uri=True)
    try:
        alvo = sqlite3.connect(bruto)
        with alvo:
            origem.backup(alvo)
        alvo.close()
    finally:
        origem.close()

    final = bruto.with_suffix(".db.gz")
    with open(bruto, "rb") as f, gzip.open(final, "wb", 9) as g:
        shutil.copyfileobj(f, g)
    bruto.unlink()
    return final


def limpar():
    """Mantém os últimos DIAS backups; os mais antigos saem."""
    arquivos = sorted(DESTINO.glob("placas-*.db.gz"))
    for velho in arquivos[:-DIAS]:
        velho.unlink()
    return len(arquivos[-DIAS:])


if __name__ == "__main__":
    feito = copiar()
    mantidos = limpar()
    print(feito.name, feito.stat().st_size, "bytes |", mantidos, "backup(s) em disco")
