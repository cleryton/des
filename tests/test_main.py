"""
test_main.py
============
Testes unitários para funções auxiliares do main.py.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import classificar_assunto
from database import get_connection, criar_tabelas
import sqlite3
import pytest

# Testa a classificação de assunto
def test_classificar_tecnologia():
    assert classificar_assunto("Como escrever um loop em Python?") == "tecnologia"
    assert classificar_assunto("O que é docker?") == "tecnologia"
    assert classificar_assunto("Qual a capital do Brasil?") == "geral"
    assert classificar_assunto("Me dê uma receita de bolo") == "geral"

# Testa a função registrar_log usando um banco temporário
TEST_DB = 'test_main_assistente.db'

@pytest.fixture
def setup_log():
    # Configura banco de teste
    import database
    original = database.DB_NAME
    database.DB_NAME = TEST_DB
    criar_tabelas()
    yield
    # Limpa
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS chat_log")
    cur.execute("DROP TABLE IF EXISTS usuarios")
    conn.commit()
    conn.close()
    database.DB_NAME = original
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_registrar_log(setup_log):
    from main import registrar_log
    registrar_log(1, "Teste pergunta", "Resposta IA", "Resposta OpenAI", "comparar")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM chat_log WHERE usuario_id=1")
    log = cur.fetchone()
    conn.close()
    assert log is not None
    assert "Teste pergunta" in log["mensagem_usuario"]
    assert "Resposta IA" in log["resposta_ia"]