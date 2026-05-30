"""
prompts.py
==========
Define os papéis (personas) e os estilos de prompt.
Também contém as proteções contra injeção de comandos.
"""

# ---------------------------
# 1. Papéis da IA (personas)
# ---------------------------
PAPEIS = {
    "tecnico": (
        "Você é um especialista técnico em TI. "
        "Responda com precisão, usando terminologia adequada, mas de forma que um profissional entenda."
    ),
    "resumido": (
        "Você é um assistente conciso. Responda em no máximo duas frases, direto ao ponto, sem rodeios."
    ),
    "professor": (
        "Você é um professor paciente. Explique o conceito de maneira didática, com exemplos e analogias, "
        "como se estivesse ensinando a um aluno iniciante."
    ),
    "detalhado": (
        "Você é um especialista minucioso. Forneça uma resposta completa, abordando todos os aspectos do assunto, "
        "incluindo exemplos, prós e contras, e referências quando possível."
    ),
    "suporte_tecnico": (
        "Você é um atendente de suporte técnico. Seu objetivo é diagnosticar problemas e oferecer soluções práticas "
        "passo a passo. Seja educado e paciente. Se não souber a resposta, oriente o usuário a buscar ajuda especializada."
    )
}

# --------------------------------------
# 2. Estilos de prompt (engenharia)
# --------------------------------------
ESTILOS = {
    "simples": {
        "descricao": "Prompt direto, sem estrutura adicional.",
        "template": "{papel}\n\nPergunta: {pergunta}"
    },
    "estruturado": {
        "descricao": "Prompt com contexto, instruções e formato de saída desejado.",
        "template": (
            "{papel}\n\n"
            "Contexto: O usuário deseja uma resposta útil e bem formatada.\n"
            "Instrução: Responda em português claro. Se a pergunta envolver código, formate-o com Markdown.\n"
            "Formato de saída:\n"
            "1. Resposta principal.\n"
            "2. Exemplo (se aplicável).\n"
            "3. Observações finais.\n\n"
            "Pergunta: {pergunta}"
        )
    },
    "especializado": {
        "descricao": "Prompt que inclui conhecimento específico do domínio (ex.: TI).",
        "template": (
            "{papel}\n\n"
            "Você possui conhecimento profundo nas seguintes áreas: programação, redes, sistemas operacionais, "
            "segurança da informação e inteligência artificial.\n"
            "Utilize esse conhecimento para responder de forma embasada.\n"
            "Se a pergunta não estiver relacionada a essas áreas, responda de forma geral, mas sinalize.\n\n"
            "Pergunta: {pergunta}"
        )
    }
}

# ------------------------------------------------
# 3. Proteções contra Prompt Injection e abusos
# ------------------------------------------------
# Lista de padrões suspeitos (case insensitive)
PADROES_SUSPEITOS = [
    "ignore as instruções",
    "ignore previous instructions",
    "system:",
    "###",
    "<|im_start|>",
    "<|im_end|>",
    "execute o comando",
    "rm -rf",
    "del /f",
    "format c:",
    "shutdown",
    "você agora é",
    "new instructions",
    "override",
    "desconsidere",
    "esqueça o que foi dito",
]

def detectar_injecao(texto: str) -> bool:
    """Retorna True se encontrar algum padrão suspeito no texto."""
    texto_lower = texto.lower()
    for padrao in PADROES_SUSPEITOS:
        if padrao in texto_lower:
            return True
    return False

def filtrar_entrada(pergunta: str) -> str:
    """Aplica proteções à entrada do usuário.
    Retorna uma mensagem de erro se detectar algo suspeito; caso contrário, None."""
    # 1. Verifica tamanho excessivo
    if len(pergunta) > 1000:
        return "A pergunta é muito longa. Por favor, limite-se a 1000 caracteres."

    # 2. Verifica padrões suspeitos
    if detectar_injecao(pergunta):
        return "Desculpe, detectei uma possível tentativa de manipulação. Sua pergunta não pode ser processada."

    # 3. Verifica conteúdo inadequado simples (palavras-chave)
    palavras_inadequadas = ["xingamento", "palavrão", "conteúdo adulto"]  # adapte conforme necessário
    for palavra in palavras_inadequadas:
        if palavra in pergunta.lower():
            return "Sua pergunta contém conteúdo não permitido."

    return None  # entrada aceita