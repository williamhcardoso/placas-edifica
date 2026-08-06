"""
Gerador de Placas de Obra — Edifica MT
API de sincronização das placas + entrega do app.

As placas ficam em SQLite; o JSON de cada uma carrega a fachada em base64
(comprimida a 1600 px pelo próprio app antes de subir), o que dispensa
gerenciar arquivos soltos em disco e mantém o backup em um único banco.

Acesso protegido por senha única compartilhada: o cliente envia
Authorization: Bearer <token>, onde token = sha256(senha + SALT).
Sem sessão no servidor — qualquer instância valida o mesmo token.
"""
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent
DB = BASE / "placas.db"
STATIC = BASE / "static"
# Senha e salt vêm do ambiente (no VPS, de /opt/placas/.env com chmod 600).
# O salt fora do código impede quebrar a senha por força bruta offline a partir
# de um token capturado — o acesso é http, sem TLS. Os valores abaixo são só
# para rodar localmente; em produção os dois SEMPRE vêm do .env.
SALT = os.environ.get("PLACAS_SALT", "salt-de-desenvolvimento")
SENHA = os.environ.get("PLACAS_SENHA", "edifica2026")
TOKEN_OK = hashlib.sha256((SENHA + SALT).encode()).hexdigest()

app = FastAPI(title="Placas Edifica MT", docs_url=None, redoc_url=None)


def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with conectar() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS placas (
                   id         TEXT PRIMARY KEY,
                   nome       TEXT NOT NULL,
                   criado     TEXT NOT NULL,
                   atualizado TEXT NOT NULL,
                   dados      TEXT NOT NULL
               )"""
        )


init_db()


def autenticar(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "").strip()
    if token != TOKEN_OK:
        raise HTTPException(status_code=401, detail="Senha inválida")
    return True


class Login(BaseModel):
    senha: str


class Placa(BaseModel):
    id: str
    nome: str
    criadoEm: str = ""
    atualizadoEm: str = ""
    dados: dict


@app.get("/api/health")
def health():
    return {"ok": True, "app": "placas-edifica", "versao": 1}


@app.post("/api/login")
def login(body: Login):
    token = hashlib.sha256((body.senha + SALT).encode()).hexdigest()
    if token != TOKEN_OK:
        raise HTTPException(status_code=401, detail="Senha inválida")
    return {"token": token}


@app.get("/api/placas")
def listar(_=Depends(autenticar)):
    with conectar() as con:
        linhas = con.execute(
            "SELECT id, nome, criado, atualizado, dados FROM placas ORDER BY atualizado DESC"
        ).fetchall()
    return [
        {
            "id": l["id"],
            "nome": l["nome"],
            "criadoEm": l["criado"],
            "atualizadoEm": l["atualizado"],
            "dados": json.loads(l["dados"]),
        }
        for l in linhas
    ]


@app.put("/api/placas/{placa_id}")
def gravar(placa_id: str, p: Placa, _=Depends(autenticar)):
    agora = p.atualizadoEm or time.strftime("%Y-%m-%dT%H:%M:%S")
    with conectar() as con:
        existente = con.execute("SELECT criado FROM placas WHERE id = ?", (placa_id,)).fetchone()
        criado = existente["criado"] if existente else (p.criadoEm or agora)
        con.execute(
            "INSERT INTO placas (id, nome, criado, atualizado, dados) VALUES (?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, atualizado=excluded.atualizado, dados=excluded.dados",
            (placa_id, p.nome, criado, agora, json.dumps(p.dados)),
        )
    return {"ok": True, "id": placa_id, "atualizadoEm": agora}


@app.delete("/api/placas/{placa_id}")
def excluir(placa_id: str, _=Depends(autenticar)):
    with conectar() as con:
        con.execute("DELETE FROM placas WHERE id = ?", (placa_id,))
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/{arquivo}")
def estatico(arquivo: str):
    caminho = (STATIC / arquivo).resolve()
    if not str(caminho).startswith(str(STATIC.resolve())) or not caminho.is_file():
        return JSONResponse({"erro": "não encontrado"}, status_code=404)
    return FileResponse(caminho)
