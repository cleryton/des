import config
from openai import OpenAI
from database import get_connection, criar_tabelas

def registrar_log(usuario_id, mensagem, resposta):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_log (usuario_id, mensagem_usuario, resposta_ia)
        VALUES (?, ?, ?);
    """, (usuario_id, mensagem, resposta))
    conn.commit()
    cur.close()
    conn.close()

def main():
    # Garante que as tabelas existam
    criar_tabelas()

    api_key = config.OPENAI_API_KEY
    if not api_key or api_key == "sk-sua-chave-aqui":
        print("❌ ERRO: Substitua a chave da API no arquivo config.py")
        return

    client = OpenAI(api_key=api_key)

    try:
        modelos = client.models.list()
        lista = list(modelos)
        print(f"✅ Conectado à OpenAI. Modelos disponíveis: {len(lista)}")

        pergunta = "Diga olá em português"
        resposta = "Olá, assistente pessoal!"
        print(f"🤖 Resposta: {resposta}")

        registrar_log(1, pergunta, resposta)
        print("📝 Interação salva no banco de dados (chat_log).")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()