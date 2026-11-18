"""Testes do canal ideal, da interceptação e da seleção das chaves."""

import random
import unittest
from unittest.mock import patch

from bb84 import medir_estado, simular_bb84


class TestBB84(unittest.TestCase):
    def test_quantidade_padrao(self):
        resultado = simular_bb84(semente=42)
        self.assertEqual(resultado["quantidade_bits"], 256)
        self.assertEqual(len(resultado["transmissoes"]), 256)
        self.assertFalse(resultado["eve_ativa"])

    def test_medicao_na_mesma_base_preserva_bit(self):
        gerador = random.Random(42)
        for bit in (0, 1):
            for base in ("Z", "X"):
                with self.subTest(bit=bit, base=base):
                    estado = {"bit": bit, "base": base}
                    self.assertEqual(medir_estado(estado, base, gerador), bit)

    def test_medicao_em_base_diferente_pode_dar_ambos_os_bits(self):
        gerador = random.Random(42)
        for base_alice, base_bob in (("Z", "X"), ("X", "Z")):
            for bit in (0, 1):
                estado = {"bit": bit, "base": base_alice}
                resultados = [medir_estado(estado, base_bob, gerador) for _ in range(100)]
                self.assertEqual(set(resultados), {0, 1})

    def test_sem_eve_bits_mantidos_sao_iguais(self):
        resultado = simular_bb84(2048, eve_ativa=False, semente=42)
        self.assertGreater(resultado["tamanho_amostra"], 0)
        self.assertEqual(resultado["qber"], 0.0)
        self.assertEqual(resultado["chave_peneirada_alice"], resultado["chave_peneirada_bob"])
        self.assertEqual(resultado["chave_candidata_alice"], resultado["chave_candidata_bob"])
        for transmissao in resultado["transmissoes"]:
            self.assertIsNone(transmissao["base_eve"])
            self.assertIsNone(transmissao["bit_eve"])
            self.assertEqual(transmissao["estado_enviado"], transmissao["estado_recebido"])
            if transmissao["mantida"]:
                self.assertEqual(transmissao["estado_enviado"]["bit"], transmissao["bit_bob"])

    def test_bases_diferentes_sao_descartadas(self):
        for eve_ativa in (False, True):
            resultado = simular_bb84(256, eve_ativa=eve_ativa, semente=7)
            esperados = []
            for transmissao in resultado["transmissoes"]:
                coincide = transmissao["estado_enviado"]["base"] == transmissao["base_bob"]
                self.assertEqual(transmissao["mantida"], coincide)
                if coincide:
                    esperados.append(transmissao["indice"])
                else:
                    self.assertFalse(transmissao["revelada"])
            self.assertEqual(resultado["indices_mantidos"], esperados)
            self.assertEqual(resultado["bits_descartados"], 256 - len(esperados))

    def test_bob_recebe_o_estado_reenviado_por_eve(self):
        resultado = simular_bb84(4096, eve_ativa=True, semente=21)
        casos_com_estado_alterado = 0
        for transmissao in resultado["transmissoes"]:
            recebido = transmissao["estado_recebido"]
            self.assertIn(transmissao["base_eve"], ("Z", "X"))
            self.assertIn(transmissao["bit_eve"], (0, 1))
            self.assertEqual(recebido, {
                "bit": transmissao["bit_eve"], "base": transmissao["base_eve"]
            })
            if transmissao["base_bob"] == transmissao["base_eve"]:
                self.assertEqual(transmissao["bit_bob"], transmissao["bit_eve"])
                if recebido != transmissao["estado_enviado"]:
                    casos_com_estado_alterado += 1
        self.assertGreater(casos_com_estado_alterado, 0)

    def test_qber_com_eve_se_aproxima_de_25_por_cento(self):
        total_erros = 0
        total_comparados = 0
        # Muitas transmissões e sementes fixas evitam um teste instável.
        for semente in range(50):
            resultado = simular_bb84(2000, eve_ativa=True, semente=semente)
            total_erros += resultado["erros_encontrados"]
            total_comparados += resultado["tamanho_amostra"]
        qber_agregado = total_erros / total_comparados * 100
        self.assertAlmostEqual(qber_agregado, 25.0, delta=2.0)

    def test_amostra_e_removida_das_duas_candidatas(self):
        for eve_ativa in (False, True):
            resultado = simular_bb84(1024, eve_ativa=eve_ativa, semente=18)
            mantidos = resultado["indices_mantidos"]
            amostra = resultado["indices_amostra"]
            candidatos = resultado["indices_candidatos"]
            self.assertEqual(len(amostra), len(mantidos) // 4)
            self.assertEqual(len(set(amostra)), len(amostra))
            self.assertTrue(set(amostra).issubset(mantidos))
            self.assertTrue(set(amostra).isdisjoint(candidatos))
            self.assertEqual(candidatos, [i for i in mantidos if i not in amostra])

            for nome, indices in (("peneirada", mantidos), ("candidata", candidatos)):
                alice = [resultado["transmissoes"][i]["estado_enviado"]["bit"] for i in indices]
                bob = [resultado["transmissoes"][i]["bit_bob"] for i in indices]
                self.assertEqual(resultado[f"chave_{nome}_alice"], alice)
                self.assertEqual(resultado[f"chave_{nome}_bob"], bob)

            erros = 0
            for transmissao in resultado["transmissoes"]:
                revelada = transmissao["indice"] in amostra
                self.assertEqual(transmissao["revelada"], revelada)
                if revelada and transmissao["estado_enviado"]["bit"] != transmissao["bit_bob"]:
                    erros += 1
            self.assertEqual(resultado["erros_encontrados"], erros)
            self.assertAlmostEqual(resultado["qber"], erros / len(amostra) * 100)

    def test_sem_bases_coincidentes(self):
        # Força o caso limite sem depender de encontrar uma semente específica.
        with patch("bb84.gerar_bases", side_effect=[["Z"] * 8, ["X"] * 8]):
            resultado = simular_bb84(8, semente=1)
        self.assertEqual(resultado["bases_coincidentes"], 0)
        self.assertEqual(resultado["bits_descartados"], 8)
        self.assertEqual(resultado["tamanho_amostra"], 0)
        self.assertEqual(resultado["erros_encontrados"], 0)
        self.assertIsNone(resultado["qber"])
        self.assertEqual(resultado["indices_mantidos"], [])
        self.assertEqual(resultado["indices_amostra"], [])
        self.assertEqual(resultado["indices_candidatos"], [])
        for participante in ("alice", "bob"):
            self.assertEqual(resultado[f"chave_peneirada_{participante}"], [])
            self.assertEqual(resultado[f"chave_candidata_{participante}"], [])

    def test_amostra_vazia_com_bits_mantidos(self):
        for quantidade in (1, 2, 3):
            with patch("bb84.gerar_bases", return_value=["Z"] * quantidade):
                resultado = simular_bb84(quantidade, semente=1)
            self.assertEqual(resultado["bases_coincidentes"], quantidade)
            self.assertEqual(resultado["tamanho_amostra"], 0)
            self.assertEqual(resultado["erros_encontrados"], 0)
            self.assertIsNone(resultado["qber"])
            for participante in ("alice", "bob"):
                self.assertEqual(
                    resultado[f"chave_peneirada_{participante}"],
                    resultado[f"chave_candidata_{participante}"],
                )

    def test_diferentes_quantidades_de_bits(self):
        for quantidade in (0, 1, 2, 3, 4, 10, 64, 256, 1000):
            for eve_ativa in (False, True):
                with self.subTest(quantidade=quantidade, eve_ativa=eve_ativa):
                    resultado = simular_bb84(quantidade, eve_ativa=eve_ativa, semente=42)
                    mantidos = resultado["bases_coincidentes"]
                    amostra = resultado["tamanho_amostra"]
                    self.assertEqual(len(resultado["transmissoes"]), quantidade)
                    self.assertEqual(mantidos + resultado["bits_descartados"], quantidade)
                    self.assertEqual(amostra, mantidos // 4)
                    for participante in ("alice", "bob"):
                        self.assertEqual(len(resultado[f"chave_peneirada_{participante}"]), mantidos)
                        self.assertEqual(len(resultado[f"chave_candidata_{participante}"]), mantidos - amostra)
                    if amostra == 0:
                        self.assertIsNone(resultado["qber"])

    def test_semente_reproduz_resultados(self):
        for eve_ativa in (False, True):
            self.assertEqual(
                simular_bb84(256, eve_ativa=eve_ativa, semente=123),
                simular_bb84(256, eve_ativa=eve_ativa, semente=123),
            )

    def test_quantidades_invalidas(self):
        for quantidade in (-1, 1.5, "256", None):
            with self.subTest(quantidade=quantidade):
                with self.assertRaisesRegex(ValueError, "inteiro não negativo"):
                    simular_bb84(quantidade)


if __name__ == "__main__":
    unittest.main()
