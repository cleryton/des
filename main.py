"""
main.py – Assistente com múltiplos papéis, engenharia de prompts,
          duas IAs e modos de uso (comparação ou roteamento por assunto)
======================================================================
Funcionalidades:
- Escolha de papel (persona) e estilo de prompt (simples, estruturado, especializado).
- Proteções contra prompt injection, comandos maliciosos e conteúdo inadequado.
- Duas IAs: Google Gemini e OpenAI.
- Dois modos de operação:
  1. comparar – ambas as IAs respondem e as respostas são exibidas lado a lado.
  2. rotear   – pergunta é classificada como 'tecnologia' ou 'geral' e enviada
                apenas para a IA mais adequada (tecnologia → Gemini, geral → OpenAI).
- Histórico salvo no banco SQLite.
"""

import config
from database import get_connection, criar_tabelas
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import PAPEIS, ESTILOS, filtrar_entrada

# ------------------------------------------------------------
# Função para classificar o assunto da pergunta (tecnologia ou geral)
# ------------------------------------------------------------
PALAVRAS_TECNOLOGIA = [
    "python", "java", "código", "programação", "algoritmo", "api", "banco de dados",
    "sql", "html", "css", "javascript", "rede", "servidor", "linux", "windows",
    "segurança", "hack", "criptografia", "ia", "inteligência artificial",
    "machine learning", "deep learning", "cloud", "docker", "kubernetes", "devops",
    "git", "frontend", "backend", "framework", "biblioteca", "compilador",
    "sistema operacional", "hardware", "roteador", "firewall", "vpn"
]

def classificar_assunto(pergunta: str) -> str:
    """
    Retorna 'tecnologia' se a pergunta contiver palavras-chave do universo tech,
    caso contrário retorna 'geral'.
    """
    pergunta_lower = pergunta.lower()
    for palavra in PALAVRAS_TECNOLOGIA:
        if palavra in pergunta_lower:
            return "tecnologia"
    return "geral"

# ------------------------------------------------------------
# Função que cria as chains com base no papel e estilo escolhidos
# ------------------------------------------------------------
def criar_chain(api_key_google, api_key_openai, modelo_google, modelo_openai, papel, estilo):
    prompt_text = ESTILOS[estilo]["template"].format(papel=PAPEIS[papel], pergunta="{pergunta}")
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Chain Gemini (sempre disponível se a chave for válida)
    chain_gemini = ChatGoogleGenerativeAI(
        model=modelo_google,
        api_key=api_key_google,
        temperature=0.7
    )
    chain_gemini = prompt | chain_gemini

    # Chain OpenAI (opcional)
    chain_openai = None
    if api_key_openai and api_key_openai not in ("sk-...", "sua-chave-openai"):
        llm_openai = ChatOpenAI(
            model=modelo_openai,
            api_key=api_key_openai,
            temperature=0.7
        )
        chain_openai = prompt | llm_openai

    return chain_gemini, chain_openai

# ------------------------------------------------------------
# Função para registrar a interação no banco
# ------------------------------------------------------------
def registrar_log(usuario_id, mensagem, resposta_gemini, resposta_openai, modo):
    texto_log = f"Modo: {modo}\nGemini: {resposta_gemini}"
    if resposta_openai:
        texto_log += f"\nOpenAI: {resposta_openai}"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_log (usuario_id, mensagem_usuario, resposta_ia) VALUES (?, ?, ?);",
        (usuario_id, mensagem, texto_log)
    )
    conn.commit()
    conn.close()

# ------------------------------------------------------------
# Função principal
# ------------------------------------------------------------
def main():
    criar_tabelas()

    # Validação das chaves
    google_key = config.GOOGLE_API_KEY
    if not google_key or google_key == "AIza...":
        print("❌ Configure GOOGLE_API_KEY no config.py")
        return

    openai_key = getattr(config, "OPENAI_API_KEY", None)
    usar_openai = openai_key and openai_key not in ("sk-...", "sua-chave-openai")

    modelo_google = "gemini-2.5-flash"
    modelo_openai = "gpt-3.5-turbo"

    # Escolha do modo de operação
    print("Modo de operação:")
    print("  1. comparar – ambas as IAs respondem, você compara as respostas")
    print("  2. rotear   – pergunta é enviada à IA mais adequada (tecnologia → Gemini, geral → OpenAI)")
    modo_op = input("Escolha (1 ou 2): ").strip()
    if modo_op == "2":
        modo = "rotear"
        if not usar_openai:
            print("⚠️  OpenAI não configurada. Todas as perguntas serão enviadas ao Gemini.")
            usar_openai = False   # forçamos a flag
    else:
        modo = "comparar"

    # Escolha do papel
    print("\nEscolha o papel (modo) do assistente:")
    papeis_keys = list(PAPEIS.keys())
    for i, p in enumerate(papeis_keys, 1):
        print(f"  {i}. {p}")
    op = input("Opção (1-5): ")
    try:
        papel = papeis_keys[int(op)-1]
    except:
        print("Opção inválida, usando modo 'técnico'.")
        papel = "tecnico"

    # Escolha do estilo de prompt
    print("\nEscolha o estilo de prompt:")
    estilos_keys = list(ESTILOS.keys())
    for i, e in enumerate(estilos_keys, 1):
        print(f"  {i}. {e} ({ESTILOS[e]['descricao']})")
    op2 = input("Opção (1-3): ")
    try:
        estilo = estilos_keys[int(op2)-1]
    except:
        print("Opção inválida, usando estilo 'simples'.")
        estilo = "simples"

    # Criação das chains
    chain_gemini, chain_openai = criar_chain(google_key, openai_key, modelo_google, modelo_openai, papel, estilo)

    print(f"\n🤖 Assistente configurado: papel = '{papel}', estilo = '{estilo}', modo = '{modo}'.")
    print("Digite 'sair' para encerrar.\n")

    while True:
        pergunta = input("Você: ")
        if pergunta.lower() == 'sair':
            print("Até logo!")
            break

        # Aplica proteções
        erro = filtrar_entrada(pergunta)
        if erro:
            print(f"❌ {erro}")
            continue

        # Inicializa respostas como vazias
        texto_gemini = ""
        texto_openai = ""

        if modo == "comparar":
            # --- Modo comparação: ambas as IAs respondem ---
            try:
                resp = chain_gemini.invoke({"pergunta": pergunta})
                texto_gemini = resp.content
            except Exception as e:
                texto_gemini = f"[Erro Gemini: {e}]"

            if chain_openai:
                try:
                    resp = chain_openai.invoke({"pergunta": pergunta})
                    texto_openai = resp.content
                except Exception as e:
                    texto_openai = f"[Erro OpenAI: {e}]"
            else:
                texto_openai = "[OpenAI não configurada]"

            print(f"\n--- Resposta Gemini ({papel}, {estilo}) ---")
            print(texto_gemini)
            if chain_openai:
                print(f"\n--- Resposta OpenAI ({papel}, {estilo}) ---")
                print(texto_openai)
            print()

        else:
            # --- Modo roteamento: classifica e usa a IA mais adequada ---
            assunto = classificar_assunto(pergunta)
            print(f"🔍 Assunto classificado como: {assunto}")
            if assunto == "tecnologia":
                # Tecnologia → Gemini
                try:
                    resp = chain_gemini.invoke({"pergunta": pergunta})
                    texto_gemini = resp.content
                except Exception as e:
                    texto_gemini = f"[Erro Gemini: {e}]"
                print(f"\n--- Resposta Gemini (tecnologia) ---")
                print(texto_gemini)
            else:
                # Geral → OpenAI (se disponível), senão Gemini
                if chain_openai:
                    try:
                        resp = chain_openai.invoke({"pergunta": pergunta})
                        texto_openai = resp.content
                    except Exception as e:
                        texto_openai = f"[Erro OpenAI: {e}]"
                    print(f"\n--- Resposta OpenAI (geral) ---")
                    print(texto_openai)
                else:
                    # Fallback para Gemini se OpenAI não estiver configurada
                    try:
                        resp = chain_gemini.invoke({"pergunta": pergunta})
                        texto_gemini = resp.content
                    except Exception as e:
                        texto_gemini = f"[Erro Gemini: {e}]"
                    print(f"\n--- Resposta Gemini (geral - fallback) ---")
                    print(texto_gemini)
            print()

        # Registra no banco
        registrar_log(1, pergunta, texto_gemini, texto_openai, modo)

if __name__ == "__main__":
    main()