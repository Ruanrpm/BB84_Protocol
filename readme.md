# Simulador BB84

Simulador didático do protocolo BB84 de distribuição quântica de chaves, implementado em Python. O projeto modela a transmissão em um canal ideal, com interceptação opcional por Eve, e permite acompanhar como Alice e Bob formam suas chaves e estimam a taxa de erros.

## Requisitos

- Python 3 (testado com a versão 3.14.7).
- Tkinter disponível na instalação do Python para abrir a interface gráfica. Para verificar, execute `python -m tkinter`.

O projeto usa apenas a biblioteca padrão do Python.

## Como executar

Execute os comandos abaixo no terminal, na pasta que contém os arquivos do projeto.

### Interface gráfica

```sh
python interface.py
```

A janela abre com uma simulação de **256 bits**, Eve desativada e o campo de semente vazio. O campo de quantidade aceita inteiros a partir de zero. Para alterar o cenário, ajuste os campos e clique em **Executar simulação**. Uma semente inteira permite repetir o resultado com os mesmos parâmetros.

- **Transmissão** — mostra, a partir da posição zero, o bit e a base de Alice, a base e o bit medido por Eve quando ativa, e a base e o bit medido por Bob. A última coluna indica se a posição foi descartada, usada na amostra ou mantida na chave candidata.
- **Resultados** — mostra a quantidade de bits transmitidos, bases coincidentes, posições descartadas, bits na amostra, erros e QBER. As chaves peneiradas e candidatas de Alice e Bob aparecem em uma área com rolagem.

### Versão pelo terminal

```sh
python main.py
```

Informe a quantidade de bits, responda `s` ou `n` para indicar a participação de Eve e preencha a semente, se desejar. Pressione **Enter** em cada pergunta para usar 256 bits, sem Eve e sem semente fixa.

## Como a simulação funciona

1. Alice gera bits e escolhe uma base (`Z` ou `X`) para cada posição. Bob escolhe suas bases de medição independentemente.
2. Com Eve ativa, ela mede cada estado em uma base aleatória e reenvia um estado preparado a partir da própria medição. Bob mede o estado que recebe. No modelo, medir na base de preparação preserva o bit. Medir na outra base produz um bit aleatório.
3. Alice e Bob conservam as posições em que suas bases coincidem. Os bits dessas posições formam as **chaves peneiradas**.
4. A simulação revela uma amostra aleatória de **25%** das posições peneiradas, arredondando o tamanho para baixo. Alice e Bob comparam os bits da amostra e retiram essas posições das chaves peneiradas para formar as **chaves candidatas**.

### Interpretação do QBER

O QBER (*Quantum Bit Error Rate*) é a porcentagem de erros na amostra, calculada por `100 × erros encontrados ÷ bits comparados`. Quando a amostra está vazia, a interface exibe **QBER não calculado**.

No canal ideal, o QBER esperado é de **0% sem Eve** e de aproximadamente **25%** quando Eve intercepta, mede e reenvia todos os estados. A taxa observada com Eve varia conforme as medições e a amostra. Um QBER elevado indica divergências entre os bits comparados e, por si só, é insuficiente para confirmar uma interceptação.

Para reproduzir os resultados da tabela, use **256 bits** e **semente 42** e execute a simulação com **Interceptação por Eve** desmarcada e depois marcada.

| Interceptação | Bases coincidentes | Bits na amostra | Erros na amostra | QBER |
| --- | ---: | ---: | ---: | ---: |
| Desativada | 133 | 33 | 0 | 0,00% |
| Ativada | 133 | 33 | 10 | 30,30% |

A transmissão é simulada em software. As chaves candidatas servem para fins didáticos, pois a implementação termina antes da correção de erros e da amplificação de privacidade.

## Estrutura do projeto

| Arquivo | Responsabilidade |
| --- | --- |
| [`bb84.py`](bb84.py) | Implementa `simular_bb84` e retorna os dados da transmissão, as chaves e as estatísticas. |
| [`interface.py`](interface.py) | Exibe os resultados da simulação em uma janela Tkinter. |
| [`main.py`](main.py) | Executa a mesma simulação pelo terminal. |
| [`test_bb84.py`](test_bb84.py) | Contém os testes automatizados do protocolo. |

## Testes

```sh
python -m unittest -v test_bb84
```

Os 13 testes verificam o modelo de medição, a interceptação, o cálculo do QBER, a seleção das chaves, as entradas inválidas e a repetição de resultados com uma mesma semente.
