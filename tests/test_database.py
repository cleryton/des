"""
test_database.py
================
Testes unitários para as funções do módulo database.py.
"""

import os
import sys
import pytest
import sqlite3

# Ajusta o path para importar o módulo database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_connection, criar_tabelas

# Banco de dados temporário para testes
TEST_DB = 'test_assistente.db'

@pytest.fixture
def setup_banco():
    """Fixture que cria as tabelas antes de cada teste e remove o banco ao final."""
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    # Força o uso do banco de teste no módulo database
    import database
    original = database.DB_NAME
    database.DB_NAME = TEST_DB
    criar_tabelas()
    yield conn
    conn.close()
    # Restaura o nome original
    database.DB_NAME = original
    # Remove o arquivo de banco
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_criar_tabelas(setup_banco):
    """Verifica se as tabelas são criadas corretamente."""
    conn = setup_banco
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tabelas = [row[0] for row in cur.fetchall()]
    assert 'usuarios' in tabelas
    assert 'tarefas' in tabelas
    assert 'notas' in tabelas
    assert 'chat_log' in tabelas

def test_inserir_usuario(setup_banco):
    """Testa a inserção de um novo usuário."""
    conn = setup_banco
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nome, email) VALUES ('Teste', 'teste@email.com')")
    conn.commit()
    cur.execute("SELECT * FROM usuarios WHERE email='teste@email.com'")
    usuario = cur.fetchone()
    assert usuario is not None
    assert usuario['nome'] == 'Teste'

def test_get_connection():
    """Testa se a conexão é retornada corretamente."""
    conn = get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()