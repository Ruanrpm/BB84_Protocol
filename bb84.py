"""Simulação didática do BB84 em um canal ideal, sem qubits reais."""

import random


def gerar_bits(quantidade, gerador):
    """Gera uma lista de bits usando o gerador aleatório recebido."""
    return [gerador.choice([0, 1]) for _ in range(quantidade)]


def gerar_bases(quantidade, gerador):
    """Escolhe uma base Z ou X para cada posição."""
    return [gerador.choice(["Z", "X"]) for _ in range(quantidade)]


def medir_estado(estado, base_medicao, gerador):
    """A base correta preserva o bit; uma base diferente dá um bit aleatório."""
    if estado["base"] == base_medicao:
        return estado["bit"]
    return gerador.choice([0, 1])


def simular_bb84(quantidade_bits=256, eve_ativa=False, semente=None):
    """Retorna as transmissões, as chaves e as estatísticas da simulação.

    Os índices começam em zero e indicam posições na transmissão original.
    A amostra usa 25% das posições mantidas, arredondados para baixo.
    Sem amostra, o QBER é None, pois não há bits comparados.
    As chaves candidatas não passam por correção de erros nem por
    amplificação de privacidade e não têm garantia de segurança.
    """
    if not isinstance(quantidade_bits, int) or quantidade_bits < 0:
        raise ValueError("A quantidade de bits deve ser um inteiro não negativo.")

    # Sem semente, as execuções normais não ficam presas a uma sequência fixa.
    gerador = random.Random(semente)
    bits_alice = gerar_bits(quantidade_bits, gerador)
    bases_alice = gerar_bases(quantidade_bits, gerador)
    bases_bob = gerar_bases(quantidade_bits, gerador)

    transmissoes = []
    indices_mantidos = []
    chave_peneirada_alice = []
    chave_peneirada_bob = []

    for indice in range(quantidade_bits):
        estado_enviado = {"bit": bits_alice[indice], "base": bases_alice[indice]}
        estado_recebido = estado_enviado.copy()
        base_eve = None
        bit_eve = None

        if eve_ativa:
            base_eve = gerador.choice(["Z", "X"])
            bit_eve = medir_estado(estado_enviado, base_eve, gerador)
            # Eve prepara um novo estado com sua própria base e seu resultado.
            estado_recebido = {"bit": bit_eve, "base": base_eve}

        bit_bob = medir_estado(estado_recebido, bases_bob[indice], gerador)
        mantida = bases_alice[indice] == bases_bob[indice]

        transmissoes.append({
            "indice": indice,
            "estado_enviado": estado_enviado,
            "estado_recebido": estado_recebido,
            "base_eve": base_eve,
            "bit_eve": bit_eve,
            "base_bob": bases_bob[indice],
            "bit_bob": bit_bob,
            "mantida": mantida,
            "revelada": False,
        })

        # A seleção usa somente as bases originais de Alice e Bob.
        if mantida:
            indices_mantidos.append(indice)
            chave_peneirada_alice.append(bits_alice[indice])
            chave_peneirada_bob.append(bit_bob)

    tamanho_amostra = len(indices_mantidos) // 4
    indices_amostra = sorted(gerador.sample(indices_mantidos, tamanho_amostra))
    erros_encontrados = 0

    for indice in indices_amostra:
        transmissao = transmissoes[indice]
        transmissao["revelada"] = True
        if transmissao["estado_enviado"]["bit"] != transmissao["bit_bob"]:
            erros_encontrados += 1

    qber = None
    if tamanho_amostra > 0:
        qber = erros_encontrados / tamanho_amostra * 100

    indices_candidatos = []
    chave_candidata_alice = []
    chave_candidata_bob = []

    for indice in indices_mantidos:
        transmissao = transmissoes[indice]
        # Bits divulgados para estimar o QBER saem das duas candidatas.
        if not transmissao["revelada"]:
            indices_candidatos.append(indice)
            chave_candidata_alice.append(transmissao["estado_enviado"]["bit"])
            chave_candidata_bob.append(transmissao["bit_bob"])

    return {
        "quantidade_bits": quantidade_bits,
        "eve_ativa": eve_ativa,
        "transmissoes": transmissoes,
        "indices_mantidos": indices_mantidos,
        "indices_amostra": indices_amostra,
        "indices_candidatos": indices_candidatos,
        "bases_coincidentes": len(indices_mantidos),
        "bits_descartados": quantidade_bits - len(indices_mantidos),
        "tamanho_amostra": tamanho_amostra,
        "erros_encontrados": erros_encontrados,
        "qber": qber,
        "chave_peneirada_alice": chave_peneirada_alice,
        "chave_peneirada_bob": chave_peneirada_bob,
        "chave_candidata_alice": chave_candidata_alice,
        "chave_candidata_bob": chave_candidata_bob,
    }
