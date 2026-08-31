import json
import os
import tkinter as tk
from tkinter import messagebox
from google import genai
from pydantic import BaseModel, Field
import threading

# Inicialize o cliente do Gemini
client = genai.Client(api_key="COLOQUE API AQUI")

def carregar_dados():
    caminho = "Final2/maria.json" if os.path.exists("Teste3/cliente.json") else "cliente.json"
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    caminho = "Final2/maria.json" if os.path.exists("Teste3/cliente.json") else "cliente.json"
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def tokens(resposta, total_tokens):
    tokens_input = resposta.usage_metadata.prompt_token_count
    tokens_output = resposta.usage_metadata.candidates_token_count

    print("\n📊 [CONTROLE DE TOKENS DA IA]")
    print(f"📥 Entrada (Prompt): {tokens_input} tokens")
    print(f"📤 Saída (Resposta): {tokens_output} tokens")

    total_tokens[0] += tokens_input
    total_tokens[1] += tokens_output

    print("Até agora foram gastos um total de:")
    print(f"📥 Entrada (Prompt): {total_tokens[0]} tokens")
    print(f"📤 Saída (Resposta): {total_tokens[1]} tokens")

    return total_tokens

class PlanejamentoMensal(BaseModel):
    resumo_mes: str = Field(description="Mensagem amigável curta e um resumo curto do planejamento mensal, sem valores. Além de dicas para o mês")
    dizer_planejamento: str = Field(description="Mensagem explicando como o cliente deveria separar o dinheiro dele, COM VALORES. Lembrando que seguir os conselhos é opcional")
    valor_custos_fixos: float = Field(description="Valor sugerido para já garantir os custos fixos do mês. Adicionando nos fundos de investimento")
    valor_dividas_saldo: float = Field(description="Valor sugerido para processo de quitamento de dívidas esse mês, sendo retirado do saldo em conta corrente.")
    valor_dividas_investido: float = Field(description="Valor sugerido para processo de quitamento de dívidas esse mês, sendo retirado do fundo de investimentos.")
    valor_planejamento: float = Field(description="Valor sugerido para separar para seus planejamentos")
    outros_valores: float = Field(description="Valor sugerido a ser guardado no fundo de investimentos para outros motivos, como emergência")

class FazerConta(BaseModel):
    sobre_conta: str = Field(description="Mensagem amigável e curta, avisando sobre a conta e aconselhando o que o cliente deveria fazer")
    pagar_com_saldo: bool = Field(description="Pagar com o saldo da conta corrente?")
    retirar_saldo: float = Field(description="Valor a ser retirado do saldo da conta corrente para pagar a conta")
    pagar_com_investimento: bool = Field(description="Pagar com valor investido?")
    retirar_investimento: float = Field(description="Valor a ser retirado do fundo de investimentos para pagar a conta")
    sem_dinheiro: str = Field(description="Caso o cliente não tenha dinheiro para pagar a conta, dê dicas do que ele poderia fazer")


class AppFinanceiro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assistente Virtual Itaú - Renan")
        self.geometry("740x670")
        self.configure(bg="#EC7000") # Laranja Itaú
        
        self.dia_atual = 1
        self.dados = carregar_dados()
        self.simulacao_rodando = False
        self.total_tokens = [0, 0]
        
        # Variáveis de controle do Fluxo de Caixa do dia
        self.entradas_dia = 0.0
        self.saidas_dia = 0.0
        
        self.setup_ui()
        
    def setup_ui(self):
        # ---------------------------------------------------------
        # HEADER: Nome + Estrelas + Dia à Esquerda | Logo à Direita
        # ---------------------------------------------------------
        top_frame = tk.Frame(self, bg="#EC7000")
        top_frame.pack(fill="x", padx=20, pady=(12, 5))
        
        # Lado Esquerdo
        left_frame = tk.Frame(top_frame, bg="#EC7000")
        left_frame.pack(side="left", anchor="w")
        
        nome_cliente = self.dados.get("nome", "Cliente")
        lbl_nome = tk.Label(left_frame, text=f"{nome_cliente}", font=("Arial", 18, "bold"), bg="#EC7000", fg="white")
        lbl_nome.pack(side="left", padx=(0, 4))

        # Container reservado para até 5 estrelas
        stars_frame = tk.Frame(left_frame, bg="#EC7000")
        stars_frame.pack(side="left", padx=(0, 12))

        # Lê a quantidade de estrelas do cliente no JSON (default 2, máximo 5)
        qtd_estrelas = min(self.dados.get("estrelas", 2), 5)

        try:
            # .subsample(25, 25) reduz a imagem tornando a estrela ligeiramente menor
            self.img_estrela = tk.PhotoImage(file="Final2/logo_estrela.png").subsample(25, 25)
            for i in range(qtd_estrelas):
                lbl_e = tk.Label(stars_frame, image=self.img_estrela, bg="#EC7000")
                lbl_e.pack(side="left", padx=1) # Espaçamento reduzido entre as estrelas (1px)
        except tk.TclError:
            for i in range(qtd_estrelas):
                lbl_e = tk.Label(stars_frame, text="⭐", font=("Arial", 10), bg="#EC7000", fg="#FFD700")
                lbl_e.pack(side="left", padx=0)
        
        self.lbl_dia = tk.Label(
            left_frame, text="| Dia: 1", font=("Arial", 18, "bold"), 
            bg="#EC7000", fg="white"
        )
        self.lbl_dia.pack(side="left")

        # Lado Direito (Logo)
        try:
            self.logo_img = tk.PhotoImage(file="Final2/logo_itau.png")
            lbl_logo = tk.Label(top_frame, image=self.logo_img, bg="#EC7000")
            lbl_logo.pack(side="right", padx=5)
        except tk.TclError:
            lbl_logo = tk.Label(
                top_frame, text=" [ ITAÚ ] ", font=("Arial", 18, "bold"), 
                bg="white", fg="#EC7000", bd=2, relief="solid"
            )
            lbl_logo.pack(side="right", padx=5)

        # ---------------------------------------------------------
        # PAINEL FINANCEIRO (4 Cards)
        # ---------------------------------------------------------
        cards_container = tk.Frame(self, bg="#EC7000")
        cards_container.pack(fill="x", padx=20, pady=(8, 5))

        card_saldo = tk.Frame(cards_container, bg="white", bd=1, relief="solid", padx=8, pady=6)
        card_saldo.pack(side="left", expand=True, fill="both", padx=3)
        tk.Label(card_saldo, text="Saldo CC", font=("Arial", 8, "bold"), bg="white", fg="#555555").pack()
        self.lbl_saldo = tk.Label(card_saldo, text="R$ 0,00", font=("Arial", 10, "bold"), bg="white", fg="#0047BB")
        self.lbl_saldo.pack(pady=(2, 0))

        card_invest = tk.Frame(cards_container, bg="white", bd=1, relief="solid", padx=8, pady=6)
        card_invest.pack(side="left", expand=True, fill="both", padx=3)
        tk.Label(card_invest, text="Investimentos", font=("Arial", 8, "bold"), bg="white", fg="#555555").pack()
        self.lbl_invest = tk.Label(card_invest, text="R$ 0,00", font=("Arial", 10, "bold"), bg="white", fg="#0047BB")
        self.lbl_invest.pack(pady=(2, 0))

        card_cofrinho = tk.Frame(cards_container, bg="white", bd=1, relief="solid", padx=8, pady=6)
        card_cofrinho.pack(side="left", expand=True, fill="both", padx=3)
        self.lbl_titulo_cofrinho = tk.Label(card_cofrinho, text="🐷 Cofrinho", font=("Arial", 8, "bold"), bg="white", fg="#555555")
        self.lbl_titulo_cofrinho.pack()
        self.lbl_cofrinho = tk.Label(card_cofrinho, text="R$ 0,00", font=("Arial", 10, "bold"), bg="white", fg="#2E7D32")
        self.lbl_cofrinho.pack(pady=(2, 0))

        card_divida = tk.Frame(cards_container, bg="white", bd=1, relief="solid", padx=8, pady=6)
        card_divida.pack(side="left", expand=True, fill="both", padx=3)
        tk.Label(card_divida, text="Dívidas do Mês", font=("Arial", 8, "bold"), bg="white", fg="#555555").pack()
        self.lbl_divida = tk.Label(card_divida, text="R$ 0,00", font=("Arial", 10, "bold"), bg="white", fg="#B71C1C")
        self.lbl_divida.pack(pady=(2, 0))

        # BARRA DE FLUXO DE CAIXA DO DIA (CASH FLOW)
        fluxo_frame = tk.Frame(self, bg="#EC7000")
        fluxo_frame.pack(fill="x", padx=20, pady=(2, 8))
        
        self.lbl_fluxo = tk.Label(
            fluxo_frame, text="Fluxo de Caixa Hoje: +R$ 0,00  |  -R$ 0,00", 
            font=("Arial", 10, "bold"), bg="#EC7000", fg="#FFF8E1"
        )
        self.lbl_fluxo.pack()

        self.atualizar_saldos_ui()

        # CONTAINER CENTRAL BRANCO
        self.container = tk.Frame(self, bg="white", bd=2, relief="solid")
        self.container.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.lbl_titulo_resumo = tk.Label(
            self.container, 
            text="Bem-vindo à simulação!\nClique abaixo para iniciar o mês.", 
            font=("Arial", 13, "bold"), bg="white", fg="#0047BB", justify="center", wraplength=550
        )
        self.lbl_titulo_resumo.pack(pady=(15, 5))

        # --- CAIXA DE DIÁLOGO DA IA ---
        self.ai_frame = tk.Frame(self.container, bg="#EBF3FE", bd=1, relief="solid")
        
        try:
            self.bot_img = tk.PhotoImage(file="Final2/logo_bot.png").subsample(4, 4) 
            lbl_bot = tk.Label(self.ai_frame, image=self.bot_img, bg="#EBF3FE")
            lbl_bot.pack(side="left", padx=(6, 2), pady=4)
        except tk.TclError:
            lbl_bot = tk.Label(self.ai_frame, text="🤖", font=("Arial", 22), bg="#EBF3FE")
            lbl_bot.pack(side="left", padx=(6, 2), pady=4)

        self.lbl_ai_text = tk.Label(
            self.ai_frame, text="", font=("Arial", 9, "italic"), 
            bg="#EBF3FE", fg="#222222", justify="left", wraplength=480
        )
        self.lbl_ai_text.pack(side="left", fill="both", expand=True, padx=(2, 8), pady=4)

        self.lbl_detalhes = tk.Label(
            self.container, 
            text="", 
            font=("Arial", 11, "bold"), bg="white", fg="#EC7000", justify="center", wraplength=520
        )
        self.lbl_detalhes.pack(pady=10)

        # BOTÃO INICIAL DE SIMULAÇÃO
        self.btn_acao = tk.Button(
            self, text="🚀 Iniciar Simulação", font=("Arial", 12, "bold"), 
            bg="#0047BB", fg="white", command=self.iniciar_simulacao,
            relief="flat", padx=25, pady=8, cursor="hand2"
        )
        self.btn_acao.pack(pady=12)

    def atualizar_saldos_ui(self):
        saldo_cc = self.dados.get("saldo_conta_corrente", 0.0)
        invest = self.dados.get("investimentos_cdb", 0.0)
        
        dividas_info = self.dados.get("dividas_e_creditos", {})
        fatura_cartao = dividas_info.get("cartao_credito_fatura_aberta", 0.0)
        emp_info = dividas_info.get("emprestimos_ativos", {})
        saldo_devedor_emp = abs(emp_info.get("saldo_devedor", 0.0)) if isinstance(emp_info, dict) else 0.0
        divida_total = fatura_cartao + saldo_devedor_emp

        pf = self.dados.get("planejamentos_futuros", {})
        valor_cofrinho = 0.0
        nome_meta = "Sonho"
        if isinstance(pf, dict):
            valor_cofrinho = pf.get("valor_guardado_atual", 0.0)
            nome_meta = pf.get("meta", "Sonho")
        elif isinstance(pf, list) and len(pf) > 0:
            valor_cofrinho = pf[0].get("valor_guardado_atual", 0.0)
            nome_meta = pf[0].get("meta", "Sonho")

        self.lbl_saldo.config(text=f"R$ {saldo_cc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_invest.config(text=f"R$ {invest:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_divida.config(text=f"R$ {divida_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        meta_curta = (nome_meta[:11] + "..") if len(nome_meta) > 13 else nome_meta
        self.lbl_titulo_cofrinho.config(text=f"🐷 {meta_curta}")
        self.lbl_cofrinho.config(text=f"R$ {valor_cofrinho:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Atualiza a barra do Cash Flow do Dia
        str_in = f"R$ {self.entradas_dia:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        str_out = f"R$ {self.saidas_dia:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.lbl_fluxo.config(text=f"Fluxo do Dia:  + {str_in}   |   - {str_out}")

        self.update_idletasks()

    def iniciar_simulacao(self):
        if not self.simulacao_rodando:
            self.simulacao_rodando = True
            self.btn_acao.pack_forget() # Oculta o botão inicial
            self.avancar_dia()

    def atualizar_tela_info(self, titulo, detalhes="", cor_titulo="#0047BB"):
        self.lbl_titulo_resumo.config(text=titulo, fg=cor_titulo)
        self.lbl_detalhes.config(text=detalhes)
        self.update()

    def avancar_dia(self):
        if self.dia_atual > 30:
            self.ai_frame.pack_forget()
            self.atualizar_tela_info("🏁 Fim do Mês!", "Simulação encerrada com sucesso.")
            return

        self.ai_frame.pack_forget()

        # Reseta o fluxo de caixa para o novo dia
        self.entradas_dia = 0.0
        self.saidas_dia = 0.0

        self.dados = carregar_dados()
        self.dados["dia_atual"] = self.dia_atual
        salvar_dados(self.dados)
        
        self.lbl_dia.config(text=f"| Dia: {self.dia_atual}")
        self.atualizar_saldos_ui()
        
        # ENTRADA DE SALÁRIO
        if self.dia_atual == self.dados.get("evento_salario", {}).get("dia_recebimento"):
            self.processar_salario()
            
        # AVISO DE CONTAS A VENCER
        elif self.verificar_contas():
            pass
            
        else:
            # Dia sem interações: exibe e avança sozinho após 2 segundos (2000 ms)
            self.atualizar_tela_info(f"Dia {self.dia_atual}", "Nenhuma movimentação pendente para hoje.", cor_titulo="#888888")
            self.dia_atual += 1
            self.after(2000, self.avancar_dia)

    def processar_salario(self):
        salario = self.dados["evento_salario"]["valor"]
        self.dados["saldo_conta_corrente"] += salario
        self.entradas_dia += salario # Registra no Cash Flow de entrada do dia
        
        salvar_dados(self.dados)
        self.atualizar_saldos_ui()
        
        self.atualizar_tela_info(
            "💰 Salário Recebido!", 
            "Analisando seus dados com IA...\nAguarde um momento."
        )
        
        threading.Thread(target=self.chamar_ia_salario, args=(salario,)).start()

    def chamar_ia_salario(self, salario):
        prompt_salario = f"""
        Você é o Assistente Financeiro do Itaú. O cliente {self.dados['nome']} recebeu um salário de R$ {salario:.2f}. No primeiro dia do mês (1).

        O saldo atual é R$ {self.dados['saldo_conta_corrente']:.2f} e ele tem investimentos de R$ {self.dados['investimentos_cdb']:.2f}.

        As seguintes contas estão programadas para esse mês: {self.dados["contas_futuras_mes"]}

        Ele teve os seguintes gastos no mês passado: {self.dados["historico_despesas_mes_anterior"]}

        Ele tem as seguintes dívidas e/ou créditos: {self.dados["dividas_e_creditos"]}

        E ele deseja planejar: {self.dados['planejamentos_futuros']}.

        Ajude ele a gerenciar as finanças do mês. Recomendando valores para guardar, pagar dívidas, etc.

        Lembre que para os gastos imediatos, como compras em mercado, delivery, etc.. Devem estar suficientes no saldo da conta corrente, para a compra ser realizada durante todo o mês.

        Leve muito em conta caso o cliente esteja com muitas dívidas e contas atrasadas.
        """
        
        try:
            resposta_salario = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt_salario,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PlanejamentoMensal
                }
            )
            self.total_tokens = tokens(resposta_salario, self.total_tokens)
            dados_ia = json.loads(resposta_salario.text)
            self.after(0, lambda: self.aplicar_conselhos_ia(dados_ia))
        except Exception as e:
            self.after(0, lambda: self.tratar_erro_api(e))

    def aplicar_conselhos_ia(self, dados_ia):
        texto_ia = f'"{dados_ia.get("dizer_planejamento", dados_ia.get("resumo_mes", ""))}"'
        self.lbl_ai_text.config(text=texto_ia)
        self.ai_frame.pack(fill="x", padx=20, pady=5, after=self.lbl_titulo_resumo)
        
        texto_detalhes = (
            f"Custos Fixos: R$ {dados_ia['valor_custos_fixos']:.2f}\n\n"
            f"Dívidas (Saldo): R$ {dados_ia['valor_dividas_saldo']:.2f}\n\n"
            f"Dívidas (Investimentos): R$ {dados_ia['valor_dividas_investido']:.2f}\n\n"
            f"Planejamento/Metas: R$ {dados_ia['valor_planejamento']:.2f}\n\n"
            f"Fundo de Emergência: R$ {dados_ia['outros_valores']:.2f}"
        )
        
        self.atualizar_tela_info("Com base no seu perfil, chegamos aos seguintes valores:", texto_detalhes)

        tirar_saldo, tirar_investido, adicionar_investimento, pagar_dividas = 0, 0, 0, 0

        if messagebox.askyesno("Custos Fixos", f"Deseja colocar R$ {dados_ia['valor_custos_fixos']:.2f} do seu saldo no fundo de investimento para garantir o pagamento das contas?"):
            tirar_saldo += dados_ia["valor_custos_fixos"]
            adicionar_investimento += dados_ia["valor_custos_fixos"]

        if dados_ia["valor_dividas_saldo"] > 0 and messagebox.askyesno("Dívidas", f"Deseja retirar R$ {dados_ia['valor_dividas_saldo']:.2f} do saldo para dívidas?"):
            tirar_saldo += dados_ia["valor_dividas_saldo"]
            pagar_dividas += dados_ia["valor_dividas_saldo"]

        if dados_ia["valor_dividas_investido"] > 0 and messagebox.askyesno("Dívidas", f"Deseja retirar R$ {dados_ia['valor_dividas_investido']:.2f} dos investimentos para dívidas?"):
            tirar_investido += dados_ia["valor_dividas_investido"]
            pagar_dividas += dados_ia["valor_dividas_investido"]

        if dados_ia["valor_planejamento"] > 0:
            meta_nome = "sua meta"
            pf = self.dados.get("planejamentos_futuros")
            if isinstance(pf, dict):
                meta_nome = pf.get("meta", "sua meta")
            elif isinstance(pf, list) and len(pf) > 0:
                meta_nome = pf[0].get("meta", "sua meta")

            if messagebox.askyesno("Metas", f"Deseja guardar R$ {dados_ia['valor_planejamento']:.2f} para {meta_nome}?"):
                tirar_saldo += dados_ia["valor_planejamento"]
                if isinstance(pf, dict):
                    pf["valor_guardado_atual"] += dados_ia["valor_planejamento"]
                elif isinstance(pf, list) and len(pf) > 0:
                    pf[0]["valor_guardado_atual"] += dados_ia["valor_planejamento"]

        if dados_ia["outros_valores"] > 0 and messagebox.askyesno("Emergência", f"Deseja guardar R$ {dados_ia['outros_valores']:.2f} para emergências?"):
            tirar_saldo += dados_ia["outros_valores"]
            adicionar_investimento += dados_ia["outros_valores"]

        # Aplica saídas no saldo da conta corrente
        self.dados["saldo_conta_corrente"] -= tirar_saldo
        self.dados["investimentos_cdb"] += adicionar_investimento - tirar_investido
        
        # Registra total retirado do saldo CC no Cash Flow de saída
        self.saidas_dia += tirar_saldo

        emp = self.dados.get("dividas_e_creditos", {}).get("emprestimos_ativos", {})
        if isinstance(emp, dict) and "saldo_devedor" in emp:
            if emp["saldo_devedor"] < 0:
                emp["saldo_devedor"] += pagar_dividas
                if emp["saldo_devedor"] > 0:
                    emp["saldo_devedor"] = 0.0
            else:
                emp["saldo_devedor"] -= pagar_dividas
                if emp["saldo_devedor"] < 0:
                    emp["saldo_devedor"] = 0.0

        salvar_dados(self.dados)
        self.atualizar_saldos_ui()
        messagebox.showinfo("Sucesso", "Planejamento mensal aplicado com sucesso!")
        
        # Avança automaticamente após 2 segundos (2000 ms)
        self.dia_atual += 1
        self.after(2000, self.avancar_dia)

    def verificar_contas(self):
        contas_para_avisar = [
            c for c in self.dados.get("contas_futuras_mes", []) 
            if c.get("status") == "pendente" and (c.get("dia_vencimento", 0) - self.dia_atual <= 2)
        ]
        
        if contas_para_avisar:
            conta = contas_para_avisar[0]
            dias_venc = conta.get('dia_vencimento', 0) - self.dia_atual
            venc_str = "hoje!" if dias_venc == 0 else f"em {dias_venc} dia(s)."
            
            self.atualizar_tela_info(
                f"🚨 Alerta de Vencimento: {conta['descricao']}",
                f"Valor: R$ {conta['valor']:.2f} | Vence {venc_str}\nAnalisando com IA a melhor forma de pagamento..."
            )
            threading.Thread(target=self.chamar_ia_conta, args=(conta,)).start()
            return True
            
        return False

    def chamar_ia_conta(self, conta):
        prompt_conta = f"""
        Você é o Assistente Financeiro do Itaú. O cliente {self.dados["nome"]} está com uma conta para pagar em {conta['dia_vencimento'] - self.dia_atual} dia(s).

        O saldo atual é R$ {self.dados['saldo_conta_corrente']:.2f} e ele tem investimentos de R$ {self.dados['investimentos_cdb']:.2f}.
        
        As seguintes contas estão programadas para esse mês: {self.dados["contas_futuras_mes"]}

        Ele teve os seguintes gastos no mês passado: {self.dados["historico_despesas_mes_anterior"]}

        Ele tem as seguintes dívidas e/ou créditos: {self.dados["dividas_e_creditos"]}

        E ele deseja planejar: {self.dados['planejamentos_futuros']}.

        No início do mês talvez ele tenha já separado um valor do salário e colocou no fundo de investimentos
        para garantir o pagamento das contas do mês. Avalie se esse parece ser o caso, se for aconselhe retirar apenas o valor do fundo de investimentos.

        Como você acha que ele deveria fazer com essa conta? E qual é a situação financeira dele nesse momento?
        """
        
        try:
            resposta_conta = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt_conta,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": FazerConta
                }
            )
            self.total_tokens = tokens(resposta_conta, self.total_tokens)
            conta_ia = json.loads(resposta_conta.text)
            self.after(0, lambda: self.processar_resposta_conta_ia(conta, conta_ia))
        except Exception as e:
            self.after(0, lambda: self.tratar_erro_api(e))

    def processar_resposta_conta_ia(self, conta, conta_ia):
        texto_ia = f'"{conta_ia.get("sobre_conta", "")}"'
        self.lbl_ai_text.config(text=texto_ia)
        self.ai_frame.pack(fill="x", padx=20, pady=5, after=self.lbl_titulo_resumo)

        dias_venc = conta['dia_vencimento'] - self.dia_atual
        venc_str = "hoje!" if dias_venc == 0 else f"em {dias_venc} dia(s)."
        texto_detalhes = f"Valor: R$ {conta['valor']:.2f} | Vencimento: {venc_str}"
        self.atualizar_tela_info(f"🚨 Alerta de Vencimento: {conta['descricao']}", texto_detalhes)
        
        self.update()

        p_saldo = bool(conta_ia.get("pagar_com_saldo", False))
        p_invest = bool(conta_ia.get("pagar_com_investimento", False))
        ret_saldo = float(conta_ia.get("retirar_saldo", conta["valor"]))
        ret_invest = float(conta_ia.get("retirar_investimento", conta["valor"]))

        pago = False

        if p_saldo and not p_invest:
            if messagebox.askyesno("Pagar Conta", f"A IA recomenda pagar com Saldo CC.\n\nDeseja retirar R$ {ret_saldo:.2f} da conta corrente para pagar '{conta['descricao']}'?"):
                self.dados["saldo_conta_corrente"] -= ret_saldo
                self.saidas_dia += ret_saldo # Cash flow de saída
                pago = True

        elif not p_saldo and p_invest:
            if messagebox.askyesno("Pagar Conta", f"A IA recomenda pagar com Investimentos.\n\nDeseja retirar R$ {ret_invest:.2f} dos investimentos para pagar '{conta['descricao']}'?"):
                self.dados["investimentos_cdb"] -= ret_invest
                pago = True

        elif p_saldo and p_invest:
            msg = f"A IA recomenda usar Saldo CC e Investimentos.\n\nDeseja retirar R$ {ret_saldo:.2f} do saldo e R$ {ret_invest:.2f} dos investimentos para pagar '{conta['descricao']}'?"
            if messagebox.askyesno("Pagar Conta", msg):
                self.dados["saldo_conta_corrente"] -= ret_saldo
                self.dados["investimentos_cdb"] -= ret_invest
                self.saidas_dia += ret_saldo # Cash flow de saída
                pago = True

        else:
            msg_sem_dinheiro = conta_ia.get("sem_dinheiro", "Saldo insuficiente.")
            if messagebox.askyesno("Aviso Financeiro", f"{msg_sem_dinheiro}\n\nDeseja tentar pagar a conta usando seu Saldo CC (R$ {conta['valor']:.2f})?"):
                if self.dados["saldo_conta_corrente"] >= conta["valor"]:
                    self.dados["saldo_conta_corrente"] -= conta["valor"]
                    self.saidas_dia += conta["valor"]
                    pago = True
                else:
                    messagebox.showerror("Saldo Insuficiente", "Saldo em conta corrente insuficiente.")

        if pago:
            for c in self.dados["contas_futuras_mes"]:
                if c["id"] == conta["id"]:
                    c["status"] = "pago"
            salvar_dados(self.dados)
            self.atualizar_saldos_ui()
            messagebox.showinfo("Sucesso", f"A conta '{conta['descricao']}' foi paga com sucesso!")

        # Avança automaticamente após 2 segundos (2000 ms)
        self.dia_atual += 1
        self.after(2000, self.avancar_dia)

    def tratar_erro_api(self, e):
        messagebox.showerror("Erro de API", f"Não foi possível conectar à IA: {e}")
        self.dia_atual += 1
        self.after(2000, self.avancar_dia)

if __name__ == "__main__":
    app = AppFinanceiro()
    app.mainloop()
