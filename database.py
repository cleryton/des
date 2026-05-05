import sqlite3

def get_connection():
    """Retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect('assistente.db')
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    """Cria as tabelas se não existirem (executa o script SQL)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            titulo TEXT NOT NULL,
            descricao TEXT,
            concluida BOOLEAN DEFAULT 0,
            data_limite DATE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            titulo TEXT NOT NULL,
            conteudo TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            mensagem_usuario TEXT,
            resposta_ia TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    """)
    conn.commit()
    conn.close()
    print("✅ Tabelas criadas/verificadas com sucesso.")