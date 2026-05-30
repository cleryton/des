"""
app.py – Interface gráfica com Streamlit para o Assistente Pessoal
=================================================================
Este arquivo transforma o assistente de terminal em uma aplicação web.
Requer: streamlit (pip install streamlit)
Para executar: streamlit run app.py
"""

import streamlit as st
import config
from database import criar_tabelas, get_connection
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import PAPEIS, ESTILOS, filtrar_entrada
from main import classificar_assunto, criar_chain  # reaproveita funções do main.py
import time

# Configuração da página
st.set_page_config(page_title="Assistente Pessoal IA", page_icon="🤖", layout="wide")
st.title("🤖 Assistente Pessoal com IA")

# Inicializa o banco de dados (cria tabelas se não existirem)
criar_tabelas()

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configuração")
    
    # Modo de operação
    modo = st.radio(
        "Modo de operação:",
        ("comparar", "rotear"),
        help="Comparar: ambas as IAs respondem.\nRoteirizar: envia para a IA mais adequada ao assunto."
    )
    
    # Papel (persona)
    papel = st.selectbox("Papel do assistente:", list(PAPEIS.keys()))
    
    # Estilo de prompt
    estilo = st.selectbox("Estilo de prompt:", list(ESTILOS.keys()))
    
    st.markdown("---")
    st.caption(f"🔹 Gemini: gemini-2.5-flash")
    if hasattr(config, "OPENAI_API_KEY") and config.OPENAI_API_KEY not in ("sk-...", ""):
        st.caption("🔹 OpenAI: gpt-3.5-turbo")
    else:
        st.caption("🔹 OpenAI: não configurada")

# Inicializa o histórico da sessão
if "historico" not in st.session_state:
    st.session_state.historico = []  # Lista de tuplas (pergunta, resposta_gemini, resposta_openai, modo, assunto)

# Função para executar a chain e obter resposta
def executar_chain(chain, pergunta):
    try:
        resposta = chain.invoke({"pergunta": pergunta})
        return resposta.content
    except Exception as e:
        return f"❌ Erro: {e}"

# Área principal: entrada do usuário
pergunta = st.chat_input("Digite sua pergunta...")

# Quando o usuário envia uma pergunta
if pergunta:
    # Verifica proteções
    erro = filtrar_entrada(pergunta)
    if erro:
        st.error(erro)
        st.stop()
    
    # Cria as chains com as configurações atuais
    google_key = config.GOOGLE_API_KEY
    openai_key = getattr(config, "OPENAI_API_KEY", None)
    chain_gemini, chain_openai = criar_chain(
        google_key, openai_key,
        modelo_google="gemini-2.5-flash",
        modelo_openai="gpt-3.5-turbo",
        papel=papel,
        estilo=estilo
    )
    
    # Inicializa respostas
    resposta_gemini = ""
    resposta_openai = ""
    assunto = ""
    
    if modo == "comparar":
        # Modo comparação: executa ambas
        with st.spinner("Consultando Gemini..."):
            resposta_gemini = executar_chain(chain_gemini, pergunta)
        if chain_openai:
            with st.spinner("Consultando OpenAI..."):
                resposta_openai = executar_chain(chain_openai, pergunta)
        else:
            resposta_openai = "[OpenAI não configurada]"
    
    else:  # modo rotear
        assunto = classificar_assunto(pergunta)
        st.info(f"🔍 Assunto classificado como: **{assunto}**")
        if assunto == "tecnologia":
            with st.spinner("Roteando para Gemini (tecnologia)..."):
                resposta_gemini = executar_chain(chain_gemini, pergunta)
        else:
            if chain_openai:
                with st.spinner("Roteando para OpenAI (geral)..."):
                    resposta_openai = executar_chain(chain_openai, pergunta)
            else:
                # Fallback para Gemini se OpenAI não estiver disponível
                with st.spinner("OpenAI indisponível, usando Gemini..."):
                    resposta_gemini = executar_chain(chain_gemini, pergunta)
    
    # Armazena no histórico
    st.session_state.historico.append(
        (pergunta, resposta_gemini, resposta_openai, modo, assunto)
    )
    
    # Registra no banco de dados
    from main import registrar_log
    registrar_log(1, pergunta, resposta_gemini, resposta_openai, modo)

# Exibe o histórico da conversa
for i, (pergunta, resp_g, resp_o, modo_hist, assunto_hist) in enumerate(st.session_state.historico):
    with st.chat_message("user"):
        st.markdown(pergunta)
    
    # Exibe respostas lado a lado no modo comparar
    if modo_hist == "comparar":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Gemini**")
            st.markdown(resp_g)
        with col2:
            st.markdown("**OpenAI**")
            st.markdown(resp_o)
    else:
        # Modo rotear: exibe a IA que respondeu
        if resp_g:
            st.markdown("**Gemini (tecnologia)**")
            st.markdown(resp_g)
        if resp_o:
            st.markdown("**OpenAI (geral)**")
            st.markdown(resp_o)
    st.divider()