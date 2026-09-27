# DIÁRIO DE BORDO
**Candidato:** Gabriel Augusto Fabri Soltovski
### 1° Uso de Inteligência Artificial
**Ferramentas:** Claude 3.7 Sonnet (análise de dados, RPA, validação de regras de negócio) e Gemini API 3.5 Flash Lite via Google AI Studio (extração estruturada em NLP). Atuaram como copilotos, exigindo correção humana constante.
**Situações concretas de falha da IA e minhas intervenções:**
* **Falsos Positivos em Qualidade de Dados:** A IA rodou a exploração inicial do CSV e declarou a base "limpa". Vetei a conclusão e exigi um teste de estresse de *edge cases*. O script então revelou strings `"R$"` em colunas float (gerando exclusões falsas por `NaN`) e um tomador com 14 anos de idade (violação direta de compliance).
* **Alucinação em Ambiguidade Textual (Laudo 17):** O perito informou duas áreas divergentes no laudo (82 m² e 74 m²). O modelo tentou arbitrar uma média matemática. Intervenção: Refatorei o prompt do Gemini aplicando uma trava semântica estrita, forçando o retorno da string `"CONTRADIÇÃO DETECTADA"` ao invés de inventar números arbitrários para garantias.
* **Loop Infinito no Rate Limit (HTTP 429):** Ao implementar *retries* na API do Gemini, a IA falhou ao incrementar o contador no bloco `except`, congelando a execução em um loop infinito. Interrompi o terminal, analisei o log de rede e implementei um backoff exponencial com mecanismo de *fallback* estrutural, blindando o pipeline de RPA contra cotas externas.
* **Débito Técnico Arquitetural:** A IA sugeriu criar uma interface desktop em Tkinter para a automação. Recusei a abordagem com base em regras de negócio: processos analíticos bancários rodam em servidores *headless*. Limpei as dependências (X11, threads) e padronizei a execução via CLI estrita através de shell script (`run_project.sh`).
### 2° O que Aprendi do Zero: LTV Regulatório e Alienação Fiduciária
Antes deste desafio, meu conhecimento de crédito limitava-se a Score e Renda. Precisei aprender do zero o arcabouço jurídico do **Home Equity** e a fundamentação do limite de **60% de LTV** (Loan-to-Value). 
Aprendi que essa restrição de LTV garante que, caso o devedor fique inadimplente e o imóvel vá a leilão extrajudicial (Lei nº 9.514/1997), a segunda praça imponha deságios severos. A "gordura" de 40% retida pelo banco assegura que custos cartorários e o desconto do leilão não se transformem em perda financeira para a instituição. Compreendi também o veto a terrenos na base devido à baixíssima liquidez.
* **Fonte de estudo:** Normas do Banco Central, Lei 9.514 e artigos sobre risco de crédito imobiliário. (Tempo investido: ~2h).
### 3° Autocrítica
**O que sei que está fraco na minha entrega:**
* **Persistência Simples:** A saída dos laudos em `.json` é válida como contrato de dados, mas ineficiente para consumo analítico. O ideal seria persistência colunar (Apache Parquet).
* **Fragilidade Visual:** Desenhar o One-Pager executivo injetando coordenadas estáticas no Matplotlib é uma solução difícil de escalar. O ideal seria renderização HTML/CSS em WeasyPrint ou Typst.
* **Testes:** A validação dependeu da execução direta. Faltou uma suíte formal no padrão `pytest` para testes unitários.
  
**O que faria com mais 40 horas:**
* **Modelo Preditivo (AVM):** Treinaria um XGBoost usando os dados extraídos dos laudos (bairro, área, ano) para prever automaticamente o valor dos imóveis, criando um alerta contra avaliações periciais infladas.
* **Busca Semântica (RAG):** Indexaria os 17 laudos textuais em um banco vetorial (ChromaDB) para permitir que a equipe jurídica consultasse gargalos (ex: "matrículas com penhora ativa") em linguagem natural.
* **Pipeline Medallion:** Integraria o CSV sujo e os laudos extraídos em um fluxo validado pelo Pydantic, isolando os dados brutos (Bronze) dos tratados (Prata/Ouro).

**Qual pergunta eu gostaria de ter feito ao negócio:**
*"Na Análise de Crédito, perdemos R$ 507,7 Milhões (35,4% da evasão financeira total). Qual é a raiz exata dessa quebra: pendências na matrícula do imóvel (ônus), reprovação tardia de Score/Renda, ou o cliente abandona a proposta por discordar do valor final do laudo?"*
Ter essa granularidade definiria se o plano de ação requer um pré-simulador de garantias ou um esquadrão focado em regularização imobiliária.