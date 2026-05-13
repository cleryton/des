from database import get_connection, criar_tabelas

def popular_banco():
    """Insere dados de exemplo no banco de dados."""
    criar_tabelas()

    conn = get_connection()
    cur = conn.cursor()

    # Usuário padrão
    cur.execute("SELECT id FROM usuarios WHERE email = 'user@exemplo.com';")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO usuarios (nome, email) VALUES ('Usuário Principal', 'user@exemplo.com');")
    cur.execute("SELECT id FROM usuarios WHERE email = 'user@exemplo.com';")
    user_id = cur.fetchone()[0]

    # Tarefas
    tarefas = [
        (user_id, 'Revisar relatório', 'Relatório financeiro Q3', 0, '2025-05-10'),
        (user_id, 'Comprar presentes', 'Aniversário da Maria', 0, '2025-05-05'),
        (user_id, 'Agendar médico', 'Check-up anual', 0, '2025-05-15')
    ]
    cur.executemany("INSERT INTO tarefas (usuario_id, titulo, descricao, concluida, data_limite) VALUES (?, ?, ?, ?, ?);", tarefas)

    # Notas
    notas = [
        (user_id, 'Ideias de projeto', 'Criar um assistente com IA...'),
        (user_id, 'Lista de compras', 'Leite, pão, ovos')
    ]
    cur.executemany("INSERT INTO notas (usuario_id, titulo, conteudo) VALUES (?, ?, ?);", notas)

    conn.commit()
    conn.close()
    print("✅ Banco populado com dados de exemplo.")

if __name__ == '__main__':
    popular_banco()