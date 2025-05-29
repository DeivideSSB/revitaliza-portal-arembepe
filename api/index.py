import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)

# --- Configuração de Segurança e CORS para Render.com ---
# ATENÇÃO: Para produção, você deve substituir origins="*"
# por origins=["https://sua-url-do-frontend.onrender.com"] para maior segurança.
CORS(app, origins="*") # Permitir todas as origens temporariamente para facilitar o deploy inicial


# Configura a chave da API do Gemini
# EM PRODUÇÃO: A chave deve ser configurada como uma variável de ambiente no Render.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

if not GEMINI_API_KEY:
    # Se a chave não estiver configurada no ambiente do Render, retorna um erro.
    @app.route('/chat', methods=['POST']) # Adiciona um handler de erro para este caso
    def api_key_missing_error():
        print("ERRO CRÍTICO: Variável de ambiente GEMINI_API_KEY não definida no servidor.")
        return jsonify({"error": "Erro no servidor: Chave API do Gemini não configurada."}), 500

# Se a chave existir, configure a API do Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Contexto Rico sobre o Projeto e Arembepe para a IA (Gerenciado no Backend) ---
community_content_context = """
Este portal e o projeto "Revitaliza Portal de Arembepe" são iniciativas de moradores do condomínio Portal de Arembepe, distrito litorâneo de Camaçari (BA), focadas na melhoria da qualidade de vida e do meio ambiente através de revitalização, limpeza e preservação ambiental.

**Origem do Projeto:**
O projeto foi idealizado por Dêivide Sobral da Silva Bezerra, morador de Arembepe e entusiasta do desenvolvimento comunitário. Ele se inspirou em EcoPEVs e cooperativas de reciclagem para mobilizar a comunidade.

**Projetos e Iniciativas Específicas do Condomínio Portal:**
1.  **Coleta seletiva comunitária:** O Condomínio Portal organiza mutirões de coleta seletiva com apoio do **EcoPEV municipal** (Ponto de Entrega Voluntária, que recebe entulho, volumosos e recicláveis com capacidade de até 30m³ para entulho e 20m³ para volumosos) e da **Limpec** (empresa municipal com ações de coleta seletiva e educação ambiental em Camaçari). O objetivo é aumentar o volume de recicláveis e reduzir o descarte irregular em dunas, lagoas e praias. O **EcoPEV Arembepe** é uma estrutura para recebimento e triagem de materiais.
2.  **Reflorestamento das dunas:** Em parceria com o ativista **Rivelino Martins** (líder de projeto que visa restaurar a vegetação nativa das dunas para preservar solos e biodiversidade), o Condomínio Portal apoia o reflorestamento das dunas de Arembepe, plantando mudas de espécies nativas com envolvimento familiar.
3.  **Educação ambiental e eventos:** O grupo realiza palestras e oficinas no **Centro de Educação Ambiental de Arembepe**, inaugurado em 1992 ao lado da Aldeia Hippie, criado pelo **Projeto Tamar** (que foca em pesquisa, conservação de tartarugas marinhas e inclusão social). Temas abordados incluem reciclagem, compostagem caseira e manejo de resíduos de óleo, com especialistas e catadores da **Coopama** (cooperativa de reciclagem e gestão de resíduos que atua na coleta, triagem e destinação correta de resíduos, gerando renda e impacto positivo).
4.  **Limpeza e conservação das lagoas:** O grupo atua em parceria com vereadores e órgãos ambientais para limpeza das lagoas de Areias e Arembepe. Existe um **pedido legislativo** (por vereador de Camaçari) para a limpeza das lagoas, enfatizando a importância de sua conservação.
5.  **Remoção de resíduos de óleo:** A **Defesa Civil** e a **Naturalle** (empresa especializada) realizam ações conjuntas para retirada de resíduos de óleo nas praias de Arembepe.

**Motivação e Riscos (Benefícios de agir / Malefícios da inação):**
* **Benefícios de agir:** Valorização de imóveis, redução de doenças (controle de lixo/entulho), convivência harmoniosa, maior contato com a natureza e educação ambiental.
* **Malefícios da inação:** Proliferação de insetos/animais peçonhentos (lixo/mato alto), degradação de áreas comuns/vias, desvalorização do bairro, conflitos entre moradores.

**Medidas Propostas pelo Condomínio Portal:**
* Atuar com mutirões.
* Sinalização educativa.
* Lixeiras apropriadas.
* Comunicação direta com a administração.
* Envolvimento das famílias nas ações.

**Engajamento Comunitário:**
Moradores participam de mutirões de limpeza (como o **Dia Mundial da Limpeza em Arembepe**, um evento anual de mobilização para limpeza de praias, rios, lagoas e áreas verdes) e utilizam o **Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS) de Camaçari** para sugerir melhorias e fiscalizar metas. O PMGIRS é um documento oficial de Camaçari (inclui Arembepe) com políticas, metas e ações para manejo de resíduos, com investimentos acima da média nacional. A comunicação interna ocorre via o Portal virtual.

**Impactos e Perspectivas:**
Já foram coletadas mais de 5 toneladas de recicláveis, plantadas mais de 300 mudas nas dunas, e mobilizadas mais de 100 famílias em ações de educação. Há expectativa de expandir parcerias (universidades, institutos de pesquisa) e conseguir financiamento para campanhas futuras (prevenção de resíduos de óleo, educação ambiental, limpeza contínua).
O projeto **Reflora Camaçari** é uma iniciativa da Secretaria de Desenvolvimento Urbano para revitalização de áreas degradadas com plantio de espécies nativas e restauração de corredores verdes.

**Conclusão do Projeto:**
O Condomínio Portal de Arembepe é um modelo replicável de gestão comunitária e ambiental, demonstrando que iniciativas de base podem gerar transformações concretas e duradouras com união e consciência.
"""

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint para processar as mensagens do chatbot.
    Recebe o histórico da conversa e a nova mensagem do usuário,
    chama a API do Gemini e retorna a resposta da IA.
    """
    try:
        data = request.get_json()
        user_message = data.get('user_message')
        chat_history_from_frontend = data.get('chat_history', [])

        if not user_message:
            return jsonify({"error": "Mensagem do usuário não fornecida."}), 400

        # Verifica novamente se a API Key foi configurada (para o caso de ser a primeira requisição)
        if not GEMINI_API_KEY:
            print("Erro: Tentativa de usar a API Gemini sem GEMINI_API_KEY configurada.")
            return jsonify({"error": "Erro no servidor: Chave API do Gemini não configurada."}), 500


        # --- Construção do Histórico para a API do Gemini ---
        # 1. Instruções do Sistema e Contexto Rico
        system_instruction_part = {
            "role": "user",
            "parts": [{
                "text": f"""Você é um assistente de IA focado em responder perguntas sobre o condomínio Portal de Arembepe e seu projeto de revitalização. Sua função é fornecer informações precisas e úteis **exclusivamente com base no "Contexto do Projeto" fornecido**.

Para melhorar a compreensão das suas perguntas, por favor, siga estas diretrizes:
* **Reconhecimento de interações simples:** Entenda saudações ("Olá", "Oi", "Bom dia"), agradecimentos ("Obrigado", "Valeu"), e despedidas ("Tchau", "Até mais"). Responda de forma apropriada e amigável.
* **Tolerância a erros ortográficos:** Tente inferir a intenção por trás de pequenos erros de digitação ou ortografia (ex: "arembepe" vs "aremebepe").
* **Interpretação de abreviações:** Se uma abreviação for comum no contexto de projetos comunitários ou meio ambiente, tente compreendê-la (ex: "recicl." para "reciclagem", "adm." para "administração").
* **Foco no contexto:** Se a pergunta não puder ser respondida com base **APENAS** no "Contexto do Projeto", diga educadamente: "Não tenho informações específicas sobre isso no contexto do Portal de Arembepe. Minhas respostas são baseadas apenas nos dados fornecidos sobre o projeto." Não tente inventar informações.

---
**Contexto do Projeto "Revitaliza Portal de Arembepe":**
{community_content_context}
---
"""
            }]
        }

        # 2. Saudação Inicial da IA (para garantir que o chat comece corretamente)
        initial_ai_greeting_part = {
            "role": "model",
            "parts": [{
                "text": "Olá! Eu sou a IA do Portal de Arembepe. Posso responder a perguntas sobre o condomínio, seus desafios e as medidas propostas para a revitalização. Em que posso ajudar?"
            }]
        }

        # 3. Histórico de Conversa real vindo do Frontend
        # O histórico para a API inclui as instruções do sistema, a saudação inicial da IA,
        # e todas as mensagens anteriores da conversa.
        history_for_gemini = [system_instruction_part, initial_ai_greeting_part]
        history_for_gemini.extend(chat_history_from_frontend)

        # Inicializa o modelo Gemini
        model = genai.GenerativeModel('gemini-2.0-flash') # Usando gemini-2.0-flash

        # Inicia o chat com o histórico completo.
        # A última mensagem do histórico (a atual do usuário) é enviada via send_message.
        chat_session = model.start_chat(history=history_for_gemini)

        # Envia a mensagem do usuário atual para a IA
        response = chat_session.send_message(user_message)
        
        # Retorna a resposta da IA
        ai_response_text = response.text
        return jsonify({"ai_response": ai_response_text})

    except Exception as e:
        print(f"Erro no backend: {e}") # Loga o erro no console do servidor
        return jsonify({"error": "Ocorreu um erro no servidor."}), 500

# Remove o bloco if __name__ == '__main__': para deploy em ambientes como Render/Vercel
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
