
import config                     # contém a chave GOOGLE_API_KEY (NÃO versionada)
from database import get_connection, criar_tabelas
from langchain_google_genai import ChatGoogleGenerativeAI  # wrapper LangChain para o Gemini
from langchain_core.prompts import ChatPromptTemplate      # template de prompt reutilizável

# ------------------------------------------------------------
# Função auxiliar para gravar cada interação no banco de dados
# ------------------------------------------------------------
def registrar_log(usuario_id, mensagem, resposta):
    """
    Insere um registro na tabela chat_log.
    Parâmetros:
        usuario_id (int): identificador do usuário (fixo como 1 neste exemplo)
        mensagem (str): pergunta feita pelo usuário
        resposta (str): resposta do assistente (real ou simulada)
    """
    conn = get_connection()  # obtém uma conexão com o SQLite
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_log (usuario_id, mensagem_usuario, resposta_ia) VALUES (?, ?, ?);",
        (usuario_id, mensagem, resposta)
    )
    conn.commit()  # efetiva a inserção
    conn.close()

# ------------------------------------------------------------
# Função principal do assistente
# ------------------------------------------------------------
def main():
    # 1. Garantir que as tabelas existam no banco de dados
    criar_tabelas()

    # 2. Obter a chave da API do Gemini a partir de config.py
    google_api_key = config.GOOGLE_API_KEY
    if not google_api_key or google_api_key == "AIza-sua-chave-aqui":
        print("❌ Configure GOOGLE_API_KEY no arquivo config.py")
        return  # encerra se a chave não estiver configurada

    # 3. Instanciar o modelo de linguagem (LLM) via LangChain
    #    Usamos o wrapper ChatGoogleGenerativeAI, que abstrai a API do Gemini.
    #    Parâmetros:
    #      - model: nome do modelo (gemini-2.5-flash é o mais atual)
    #      - api_key: a chave obtida do config.py
    #      - temperature: controla a criatividade (0.0 = determinístico, 1.0 = bem criativo)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=google_api_key,
        temperature=0.7
    )

    # 4. Criar um template de prompt reutilizável
    #    {pergunta} será substituído pela entrada do usuário a cada interação.
    prompt = ChatPromptTemplate.from_template(
        "Você é um assistente pessoal prestativo e especialista em tecnologia.\n\n"
        "Responda à seguinte pergunta de forma clara e útil:\n{pergunta}"
    )

    # 5. Construir a chain (prompt | modelo)
    #    O operador "|" conecta o template ao LLM.
    #    Quando invocada, a chain formata o prompt e envia ao Gemini.
    chain = prompt | llm

    # 6. Loop de conversa com o usuário
    print("🤖 Assistente Gemini pronto. Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Você: ")
        if pergunta.lower() == 'sair':
            print("Até logo!")
            break  # sai do loop

        try:
            # Invoca a chain: envia a pergunta ao Gemini e recebe a resposta
            resposta = chain.invoke({"pergunta": pergunta})
            texto_resposta = resposta.content  # extrai o texto da resposta

        except Exception as e:
            # Se a cota gratuita estiver esgotada (erro 429), usa uma resposta simulada
            if "RESOURCE_EXHAUSTED" in str(e):
                texto_resposta = (
                    f"[Simulação – quota excedida] Você perguntou: '{pergunta}'.\n"
                    "Esta é uma resposta de demonstração enquanto a cota não renova."
                )
                print(f"⚠️  {e}")  # exibe o erro original para ciência
            else:
                # Outros erros (ex.: chave inválida, rede) são exibidos e o loop continua
                print(f"❌ Erro: {e}")
                continue

        # Exibe a resposta (real ou simulada) no terminal
        print(f"Assistente: {texto_resposta}\n")

        # Grava a interação no banco de dados (usuário id = 1)
        registrar_log(1, pergunta, texto_resposta)

# ------------------------------------------------------------
# Ponto de entrada do script
# ------------------------------------------------------------
if __name__ == "__main__":
    main()