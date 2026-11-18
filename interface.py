"""Interface gráfica do simulador didático BB84."""

import tkinter as tk
from tkinter import messagebox, ttk

from bb84 import simular_bb84


def criar_tabela(painel):
    colunas = [
        ("Posição", 65), ("Bit de Alice", 90), ("Base de Alice", 100),
        ("Base de Eve", 90), ("Eve mediu", 85), ("Base de Bob", 95),
        ("Bob mediu", 85), ("Situação", 180),
    ]
    tabela = ttk.Treeview(
        painel, columns=[nome for nome, _ in colunas], show="headings", height=7
    )
    for nome, largura in colunas:
        tabela.heading(nome, text=nome)
        tabela.column(nome, width=largura, minwidth=largura, anchor="center")

    tabela.tag_configure("Descartada", background="#f0f1f2")
    tabela.tag_configure("Utilizada na amostra", background="#fff1ce")
    tabela.tag_configure("Mantida na chave candidata", background="#e1f1e6")

    vertical = ttk.Scrollbar(painel, orient="vertical", command=tabela.yview)
    horizontal = ttk.Scrollbar(painel, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tabela.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    painel.rowconfigure(0, weight=1)
    painel.columnconfigure(0, weight=1)
    return tabela


def mostrar_transmissoes(tabela, transmissoes):
    tabela.delete(*tabela.get_children())
    for envio in transmissoes:
        if envio["revelada"]:
            situacao = "Utilizada na amostra"
        elif envio["mantida"]:
            situacao = "Mantida na chave candidata"
        else:
            situacao = "Descartada"

        alice = envio["estado_enviado"]
        valores = (
            envio["indice"], alice["bit"], alice["base"],
            envio["base_eve"] if envio["base_eve"] is not None else "—",
            envio["bit_eve"] if envio["bit_eve"] is not None else "—",
            envio["base_bob"], envio["bit_bob"], situacao,
        )
        tabela.insert("", "end", values=valores, tags=(situacao,))
    tabela.yview_moveto(0)


def mostrar_chaves(caixa, resultado):
    caixa.configure(state="normal")
    caixa.delete("1.0", "end")
    for tipo in ("peneirada", "candidata"):
        for pessoa in ("Alice", "Bob"):
            bits = resultado[f"chave_{tipo}_{pessoa.lower()}"]
            sequencia = "".join(map(str, bits))
            grupos = [sequencia[i:i + 8] for i in range(0, len(sequencia), 8)]
            caixa.insert("end", f"Chave {tipo} de {pessoa} ({len(bits)} bits)\n", "titulo")
            caixa.insert("end", (" ".join(grupos) or "(vazia)") + "\n")
    caixa.yview_moveto(0)
    caixa.configure(state="disabled")


def criar_interface(janela):
    janela.title("Simulador BB84 — Distribuição Quântica de Chaves")
    janela.minsize(720, 520)
    painel = ttk.Frame(janela, padding=10)
    painel.pack(fill="both", expand=True)
    painel.columnconfigure(0, weight=1)
    painel.rowconfigure(1, weight=1)
    painel.rowconfigure(2, weight=1)

    config = ttk.LabelFrame(painel, text="Configurações", padding=8)
    config.grid(row=0, column=0, sticky="ew")
    config.columnconfigure(4, weight=1)
    ttk.Label(config, text="Quantidade de bits").grid(row=0, column=0)
    quantidade = ttk.Entry(config, width=8)
    quantidade.insert(0, "256")
    quantidade.grid(row=0, column=1, padx=(5, 16))
    ttk.Label(config, text="Semente (opcional)").grid(row=0, column=2)
    semente = ttk.Entry(config, width=9)
    semente.grid(row=0, column=3, padx=(5, 16))
    eve = tk.BooleanVar(master=janela, value=False)
    ttk.Checkbutton(config, text="Interceptação por Eve", variable=eve).grid(
        row=0, column=4, sticky="w"
    )

    transmissao = ttk.LabelFrame(painel, text="Transmissão", padding=6)
    transmissao.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
    tabela = criar_tabela(transmissao)

    resultados = ttk.LabelFrame(painel, text="Resultados", padding=8)
    resultados.grid(row=2, column=0, sticky="nsew", pady=8)
    resultados.columnconfigure(0, weight=1)
    resultados.rowconfigure(1, weight=1)
    resumo = ttk.Frame(resultados)
    resumo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
    indicadores = []
    for i in range(6):
        rotulo = ttk.Label(resumo)
        rotulo.grid(row=i // 3, column=i % 3, sticky="w")
        resumo.columnconfigure(i % 3, weight=1, uniform="indicador")
        indicadores.append(rotulo)

    chaves = tk.Text(resultados, width=1, height=8, wrap="word", font="TkFixedFont",
                     padx=6, pady=4, relief="flat", state="disabled")
    chaves.tag_configure("titulo", font="TkHeadingFont")
    barra = ttk.Scrollbar(resultados, orient="vertical", command=chaves.yview)
    chaves.configure(yscrollcommand=barra.set)
    chaves.grid(row=1, column=0, sticky="nsew")
    barra.grid(row=1, column=1, sticky="ns")

    explicacao = ttk.LabelFrame(painel, text="Interpretação dos resultados", padding=8)
    explicacao.grid(row=3, column=0, sticky="ew")
    texto = ttk.Label(explicacao, wraplength=750, text=(
        "Em um canal ideal, o QBER esperado é 0% sem interceptação e aproximadamente "
        "25% quando Eve intercepta, mede e reenvia todos os estados. Os valores "
        "observados podem variar devido à aleatoriedade.\n"
        "Um QBER elevado indica erros, mas não comprova sozinho a presença de Eve. "
        "As chaves candidatas não têm garantia de segurança criptográfica, pois a "
        "simulação não implementa correção de erros nem amplificação de privacidade."
    ))
    texto.pack(fill="x")
    texto.bind("<Configure>", lambda evento: texto.configure(wraplength=evento.width))

    def executar():
        try:
            bits = int(quantidade.get())
            if bits < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Quantidade inválida", "Informe um número inteiro de bits maior ou igual a zero.", parent=janela)
            quantidade.focus_set()
            return
        try:
            entrada = semente.get().strip()
            valor_semente = int(entrada) if entrada else None
        except ValueError:
            messagebox.showerror("Semente inválida", "Informe uma semente inteira ou deixe o campo vazio.", parent=janela)
            semente.focus_set()
            return

        resultado = simular_bb84(bits, eve.get(), valor_semente)
        mostrar_transmissoes(tabela, resultado["transmissoes"])
        qber = resultado["qber"]
        taxa = "QBER não calculado" if qber is None else f"QBER: {qber:.2f}%".replace(".", ",")
        valores = (
            f"Bits transmitidos: {resultado['quantidade_bits']}",
            f"Bases coincidentes: {resultado['bases_coincidentes']}",
            f"Posições descartadas: {resultado['bits_descartados']}",
            f"Bits na amostra: {resultado['tamanho_amostra']}",
            f"Erros na amostra: {resultado['erros_encontrados']}",
            taxa,
        )
        for rotulo, valor in zip(indicadores, valores):
            rotulo.configure(text=valor)
        mostrar_chaves(chaves, resultado)

    ttk.Button(config, text="Executar simulação", command=executar).grid(
        row=0, column=5, padx=(12, 0)
    )
    executar()


if __name__ == "__main__":
    janela = tk.Tk()
    criar_interface(janela)
    janela.mainloop()
