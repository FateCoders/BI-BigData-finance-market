# **Simulador de Portfólio Interativo (B3)**

Este projeto é a implementação da parte de Business Intelligence (BI) do "Par Temático 3: Otimização de Portfólio no Mercado Financeiro (B3)".

Trata-se de uma aplicação web analítica, construída com **Dash** e **Plotly**, que permite ao usuário simular a performance de um portfólio de ações. O dashboard é interativo, permitindo que o usuário selecione um conjunto de ações (atualmente com dados mocados), defina pesos percentuais e um aporte inicial.

A aplicação então calcula e exibe a performance histórica do portfólio simulado em Reais (R$), comparando-o diretamente com um benchmark (SELIC, também mocado). Além disso, são exibidas métricas de risco e retorno essenciais.

## **Visualização**

*\[Insira aqui um screenshot da aplicação rodando\]*

## **Funcionalidades**

* **Interface Limpa (Tema Claro):** Layout moderno e intuitivo construído com Dash Bootstrap Components.  
* **Fluxo de Usuário Lógico:** A aplicação segue um fluxo vertical:  
  1. **Ativos Disponíveis:** Mostra os tickers disponíveis para simulação.  
  2. **Configurações da Simulação:** Formulário para seleção de ativos, pesos e aporte inicial.  
  3. **Resultados da Simulação:** Seção que aparece dinamicamente apenas após a simulação ser executada com sucesso.  
* **Simulação de Portfólio:** Permite ao usuário selecionar múltiplos ativos (PETR4, VALE3, ITUB4, MGLU3) em um dropdown.  
* **Alocação de Pesos:** Input para o usuário definir a alocação (pesos) de cada ativo no portfólio.  
* **Simulação de Aporte:** Permite definir um valor de "Aporte Inicial" (R$) para uma simulação financeira realista.  
* **Análise Comparativa:** Plota um gráfico da performance do portfólio (em R$) contra um benchmark (SELIC mocado).  
* **Métricas de Risco e Retorno:** Calcula e exibe 4 métricas principais em cards:  
  * Valor Final (Portfólio)  
  * Valor Final (SELIC)  
  * Volatilidade (anualizada)  
  * Sharpe Ratio  
* **Dados Mocados (Mock Data):** Utiliza dados simulados (random walk) para preços de ações e para a taxa SELIC (simulando a API do BCB). Isso permite o desenvolvimento e teste do front-end sem dependência do pipeline de dados (Big Data).

## **Tecnologias Utilizadas**

* **Python 3.10+**  
* **Dash:** Framework principal para a construção da aplicação web analítica.  
* **Plotly:** Biblioteca para a criação dos gráficos interativos.  
* **Dash Bootstrap Components (DBC):** Para layout e componentes visuais modernos (Cards, Rows, Cols, Badges).  
* **Pandas:** Para manipulação e processamento dos dados em DataFrames (preços, retornos, SELIC).  
* **Numpy:** Para cálculos numéricos (geração de dados mocados, pesos, métricas).

## **Como Rodar o Projeto**

Siga os passos abaixo para executar a aplicação localmente.

### **1\. Pré-requisitos**

* Ter o [Python 3.10](https://www.python.org/downloads/) ou superior instalado.  
* Ter o pip (gerenciador de pacotes do Python) atualizado.

### **2\. Clonar ou Baixar o Repositório**

Baixe os arquivos e coloque-os em uma pasta. O arquivo principal é o app.py.

### **3\. Criar um Ambiente Virtual (Recomendado)**

É uma boa prática isolar as dependências do projeto:

\# No Windows  
python \-m venv venv  
venv\\Scripts\\activate

\# No macOS/Linux  
python3 \-m venv venv  
source venv/bin/activate

### **4\. Instalar as Dependências**

As bibliotecas necessárias podem ser instaladas diretamente via pip. Você pode criar um arquivo requirements.txt com o conteúdo abaixo ou instalar as bibliotecas uma a uma.

**Arquivo requirements.txt:**

dash  
dash-bootstrap-components  
pandas  
numpy  
plotly

**Comando de instalação:**

pip install \-r requirements.txt

### **5\. Executar a Aplicação**

Com o ambiente virtual ativado e as dependências instaladas, execute o script principal:

python app.py

### **6\. Acessar o Dashboard**

Abra seu navegador e acesse o endereço que aparece no terminal, geralmente:

http://127.0.0.1:8050/

## **Estrutura do Projeto**

analise-do-mercado-financeiro/  
├── app.py            \# Script principal da aplicação Dash  
├── requirements.txt  \# Lista de dependências (recomendado)  
└── README.md         \# Este arquivo  
