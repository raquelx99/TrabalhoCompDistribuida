# TrabalhoCompDistribuida

Resolução dos Exercícios I da disciplina de Computação Distribuída (Prof. Nabor C.
Mendonça), respondendo aos Exercícios 1.1, 1.2 e 1.3.

## Estrutura do projeto

| Arquivo | Conteúdo |
|---|---|
| `trabalho-nabor-notebook.ipynb` | Exercício 1.2: cálculo analítico da fórmula de disponibilidade e simulador estocástico, com tabelas e gráficos. |
| `main.py` | Exercício 1.2 (versão interativa/bônus): app desktop em `pygame` que roda o mesmo simulador estocástico ao vivo, com controles de n/k/p e um "jardim" de servidores. |
| `assets/fonts/` | Fontes Baloo 2 e Nunito (licença SIL OFL) usadas pelo app. |
| `requirements.txt` | Dependências Python do projeto. |

### Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# notebook (célula a célula, ou via CLI):
jupyter nbconvert --to notebook --execute --inplace trabalho-nabor-notebook.ipynb

# app interativo:
python main.py
```

---

## Exercício 1.1 - Fórmula de disponibilidade

**Enunciado:** deduzir a disponibilidade de um serviço replicado em `n`
servidores, que exige pelo menos `k` servidores disponíveis para ser acessado
de forma consistente, onde cada servidor está disponível com probabilidade
`p` (independente dos demais).

### Fórmula

```
A(n, k, p) = 1 - Σ (i=0 até k-1) [ n! / (i! (n-i)!) ] · p^i · (1 - p)^(n-i)
```

---

## Exercício 1.2 - Cálculo analítico e simulação estocástica

### 1. Cálculo analítico

A fórmula `A(n, k, p) = 1 - Σ_{i<k} C(n,i) p^i (1-p)^(n-i)` foi implementada em
Python no notebook (`calcular_probabilidade_sistema_disponivel`) e avaliada
para `n ∈ {2, 4, 6, 10, 20, 50}`, `p ∈ {0.1, 0.25, 0.5, 0.75, 0.9, 0.99}` e os
três regimes de quórum `k = 1`, `k = n/2` e `k = n`, gerando uma tabela com
102 combinações e gráficos 2D (disponibilidade × p e disponibilidade × n)
comparando os três regimes. Os gráficos confirmam o comportamento previsto em
1.1: `k=1` satura perto de 100% rapidamente conforme `n` ou `p` crescem;
`k=n` cai conforme `n` cresce, para o mesmo `p`; `k=n/2` fica entre os dois
extremos.

### 2. Simulador estocástico

Também no notebook, para cada combinação de `n`, `k`, `p` são rodadas 100.000
rodadas independentes: em cada rodada, cada servidor sorteia um número
aleatório uniforme em `[0,1]` e é considerado disponível se o número for
`≤ p`; o sistema é bem-sucedido na rodada se pelo menos `k` servidores caírem
disponíveis. A frequência de rodadas bem-sucedidas (frequência experimental)
é comparada ao valor analítico na mesma tabela. Resultado: diferença absoluta
máxima entre analítico e experimental de ≈ 0,32 p.p. e diferença média de
≈ 0,04 p.p. nas 102 combinações, a simulação converge bem para a
fórmula fechada, como esperado pela Lei dos Grandes Números.

### 3. App interativo

Além do notebook, `main.py` implementa o mesmo método de simulação em um app
desktop (`pygame`/`pygame-ce`), separado do notebook para não misturar
exploração de dados com uma ferramenta de demonstração ao vivo. Cada servidor
é desenhado como uma flor (disponível) ou um botão fechado (indisponível);
sliders permitem alterar `n`, `k` e `p` em tempo real, o que reinicia a
amostragem, e um gráfico de convergência mostra a frequência experimental
acumulada se aproximando do valor analítico enquanto as rodadas rodam
continuamente.

---

## Exercício 1.3 - Particionamento e replicação

Cenário considerado (ver figura do enunciado): os conjuntos `A` e `B` são
particionados por faixa de chave entre dois nós, `Node 1` guarda
`A[0..100]` e `B[a..n]`, `Node 2` guarda `A[101..200]` e `B[o..z]`, enquanto
`C` é replicado integralmente nos dois nós.

### a) Impacto do particionamento de A no desempenho de leitura/escrita

O particionamento do conjunto A pode melhorar o desempenho porque divide os
dados entre diferentes nós, permitindo que consultas e escritas sobre partes
distintas sejam executadas em paralelo. Além disso, cada nó precisa acessar
uma quantidade menor de dados.

Por exemplo, uma leitura sobre um elemento de A[0...100] pode ser atendida
diretamente pelo Nó 1, enquanto outra leitura sobre A[101...200] pode ser
processada pelo Nó 2.

Por outro lado, o particionamento pode prejudicar o desempenho quando uma
operação precisa acessar dados presentes em mais de uma partição, pois será
necessário consultar múltiplos nós e combinar os resultados, aumentando a
comunicação e a latência.

### b) Efeito de uma demanda desigual sobre B

Se o conjunto B for muito mais acessado que os demais, a estratégia de
distribuição deve considerar essa maior carga. Uma alternativa seria
reorganizar suas partições para distribuir melhor os acessos entre os nós ou
replicar B, total ou parcialmente, permitindo que mais de um nó atenda às
requisições.

A replicação pode melhorar o desempenho porque permite utilizar mais banda e
poder computacional, além de possibilitar o processamento em paralelo.

### c) Efeito de uma taxa de falha maior no Node 2

Se o Nó 2 apresentar uma taxa de falha significativamente maior, seria
necessário reconsiderar a distribuição dos dados armazenados exclusivamente
nele. As partições de A e B presentes no Nó 2 poderiam ser replicadas em
outro nó mais confiável, evitando que esses dados fiquem indisponíveis em
caso de falha.

O conjunto C já apresenta maior tolerância a falhas, pois está replicado nos
dois nós. A replicação aumenta a disponibilidade, pois cria cópias adicionais
dos dados, embora também exija a manutenção da consistência entre essas
cópias.

### d) Cenário que exigiria reorganizar as faixas particionadas

A reorganização dos intervalos particionados pode ser necessária quando
houver desequilíbrio de carga entre os nós. Por exemplo, se uma parte
específica de A ou B passar a receber muito mais acessos que as demais, o nó
responsável por essa partição pode ficar sobrecarregado.

Nesse caso, os limites das partições podem ser alterados ou os dados podem
ser redistribuídos entre mais nós. Essa reorganização pode ser causada por
fatores como aumento do volume de dados, mudança no padrão de acesso,
crescimento do número de usuários, sobrecarga ou falhas frequentes em
determinado nó. A estratégia de alocação deve considerar a carga e a
confiabilidade das máquinas.
