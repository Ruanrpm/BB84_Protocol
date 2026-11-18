"""Execução da primeira etapa do BB84 pelo terminal."""

from bb84 import simular_bb84


def ler_inteiro(mensagem, padrao=None, minimo=None):
    """Aceita Enter para o padrão e repete a leitura se o valor for inválido."""
    while True:
        entrada = input(mensagem).strip()
        if entrada == "":
            return padrao
        try:
            valor = int(entrada)
        except ValueError:
            print("Digite um número inteiro válido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"Digite um número maior ou igual a {minimo}.")
            continue
        return valor


def ler_participacao_eve():
    """Por padrão, executa sem a interceptadora."""
    while True:
        entrada = input("Ativar Eve? [s/N]: ").strip().lower()
        if entrada in ("s", "sim"):
            return True
        if entrada in ("", "n", "não", "nao"):
            return False
        print("Responda com s (sim) ou n (não).")


def mostrar_resultados(resultado):
    """Exibe o resumo e as chaves separadas de Alice e Bob."""
    print("\nResultados da simulação BB84")
    print(f"Eve: {'ativada' if resultado['eve_ativa'] else 'desativada'}")
    print(f"Bits transmitidos: {resultado['quantidade_bits']}")
    print(f"Bases coincidentes: {resultado['bases_coincidentes']}")
    print(f"Bits descartados por bases diferentes: {resultado['bits_descartados']}")
    print(f"Tamanho da amostra revelada: {resultado['tamanho_amostra']}")
    print(f"Erros encontrados na amostra: {resultado['erros_encontrados']}")

    if resultado["qber"] is None:
        print("QBER: não calculado (amostra vazia).")
    else:
        print(f"QBER: {resultado['qber']:.2f}%")

    if resultado["bases_coincidentes"] == 0:
        print("Nenhuma base coincidiu; as chaves estão vazias.")
    print("A amostra contém 25% das posições mantidas, arredondados para baixo.")

    chaves = [
        ("Chave peneirada de Alice", "chave_peneirada_alice"),
        ("Chave peneirada de Bob", "chave_peneirada_bob"),
        ("Chave candidata de Alice", "chave_candidata_alice"),
        ("Chave candidata de Bob", "chave_candidata_bob"),
    ]
    for titulo, campo in chaves:
        bits = resultado[campo]
        texto = "".join(str(bit) for bit in bits) if bits else "(vazia)"
        print(f"\n{titulo} ({len(bits)} bits):\n{texto}")

    print("\nOs bits revelados foram removidos das chaves candidatas.")
    print("As chaves candidatas não têm garantia de segurança criptográfica.")
    print("Esta simulação não implementa correção de erros nem amplificação de privacidade.")


def main():
    print("Simulação didática do protocolo BB84 — canal ideal")
    quantidade = ler_inteiro("Quantidade de bits [256]: ", padrao=256, minimo=0)
    eve_ativa = ler_participacao_eve()
    semente = ler_inteiro("Semente opcional (Enter para não fixar): ")
    resultado = simular_bb84(quantidade, eve_ativa, semente)
    mostrar_resultados(resultado)


if __name__ == "__main__":
    main()
