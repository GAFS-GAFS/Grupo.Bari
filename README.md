# Banco Bari — Central de Inteligência de Crédito & Automação RPA
**Case Técnico Prático — Estágio AI / DataLab**

Este repositório contém a solução ponta a ponta desenvolvida para otimizar e auditar a esteira de análise de crédito com garantia imobiliária (Home Equity) do Banco Bari. O pipeline assegura a aderência estrita às políticas de concessão, barrando automaticamente desde operações com LTV estourado até a oferta de garantias rurais ou ilíquidas (como loteamentos isolados ou terrenos de plantação de abacaxi), compreendendo:

1. **Diagnóstico Estratégico do Funil de Crédito** (Análise de perdas financeiras, comportamento temporal e fatores determinantes de conversão).
2. **Rotina Semanal Automatizada (RPA)** com tratamento defensivo de dados, logs de auditoria e geração de **Relatório Executivo (One-Pager de 1 página)** para a diretoria comercial.
3. **Extrator Inteligente de Laudos Técnicos (NLP / IA)** com arquitetura de alta disponibilidade (Google Gemini API + Motor Local de Resiliência), validação contra Gabarito Humano (Ground Truth) e política anti-alucinação.

---

## 📦 Dependências e Instalação

O projeto requer Python 3.8+ e utiliza apenas 3 bibliotecas externas. Para instalá-las em qualquer ambiente:

```bash
pip install -r requirements.txt
```

* `pandas` — Manipulação de dados, agrupamentos analíticos e esteira RPA.
* `numpy` — Cálculos matriciais e coeficientes estatísticos de correlação.
* `matplotlib` — Renderização do relatório executivo em PDF de 1 página.

---

## 🚀 Como Executar o Projeto em 1 Comando

O projeto é 100% autônomo, multiplataforma (Linux, Windows e macOS) e não requer interface gráfica:

* **Linux / macOS (Terminal Bash):**
  ```bash
  ./run_project.sh
  ```
* **Windows (Prompt de Comando CMD / Duplo clique):**
  ```cmd
  run_project.bat
  ```
* **Windows (PowerShell):**
  ```powershell
  .\run_project.ps1
  ```

### O que os scripts orquestradores fazem automaticamente:
* Ativam o ambiente virtual Python (`.venv` ou `.venv\Scripts`).
* Executam a **Parte 1** (`funnel_analysis.py`): extrai os insights financeiros e correlações no console.
* Executam a **Parte 2** (`rpa_routine.py`): higieniza os dados e gera o arquivo `Relatorio_Lideranca.pdf` de 1 página.
* Executam a **Parte 3** (`ai_extraction.py`): processa os 17 laudos não estruturados e salva o `laudos_extraidos.json`.

---

## 📁 Estrutura do Repositório e Entregáveis

```text
├── README.md                   # Instruções de execução, visão geral dos arquivos e tempo dedicado
├── requirements.txt            # Dependências do projeto (pip install -r requirements.txt)
├── Relatorio_Lideranca.pdf     # [Parte 2] One-Pager Executivo de 1 Página (A4 Paisagem) para diretoria
├── laudos_extraidos.json       # [Parte 3] Base final dos 17 laudos estruturados nas 9 chaves estritas
│
├── run_project.sh              # Orquestrador mestre para Linux / macOS
├── run_project.bat             # Orquestrador mestre para Windows (CMD / Duplo clique)
├── run_project.ps1             # Orquestrador mestre para Windows (PowerShell)
│
├── Case_Bari/                  # Diretório com os códigos-fonte, base bruta e diário
│   ├── DIARIO.md               # [Parte 4] Diário de bordo, aprendizado do zero e autocrítica
│   ├── Diario Gabriel Fabri.pdf # [Parte 4] Versão em PDF diagramada do Diário de Bordo
│   ├── funnel_analysis.py      # [Parte 1] Diagnóstico estatístico, perdas financeiras e correlações
│   ├── rpa_routine.py          # [Parte 2] Pipeline defensivo semanal e gerador do One-Pager PDF
│   ├── ai_extraction.py        # [Parte 3] Extrator de laudos imobiliários com IA Gemini e Fallback Local
│   ├── execucao_nlp.log        # Log unificado de auditoria da esteira (Fases 1, 2 e 3 integradas)
│   ├── propostas_credito.csv   # Base bruta original de 6.400 propostas (imutável em disco)
│   └── laudos_avaliacao/       # Diretório contendo os 17 laudos técnicos em formato de texto livre
└── .gitignore                  # Regras para exclusão de caches e ambientes virtuais
```

---

## ⏱️ Tempo Total Dedicado ao Projeto

O desenvolvimento completo deste case consumiu aproximadamente **25 horas** de dedicação técnica estruturada:
* **Entendimento de Negócio & Pesquisa de Home Equity (LTV):** ~2 horas (estudo da Lei nº 9.514/1997, resoluções do CMN/Bacen e margem de segurança de leilão).
* **Parte 1 — Diagnóstico do Funil & Análise Bivariada:** ~4 horas (mapeamento de gargalos, perdas de capital e plano acionável).
* **Parte 2 — Engenharia RPA & Relatório Executivo PDF:** ~6 horas (tratamento defensivo de dados, resiliência a colunas ausentes e diagramação precisa do One-Pager).
* **Parte 3 — Extração com IA & Motor de Resiliência Local:** ~7 horas (engenharia de prompts, contorno do erro 429 de cota, arquitetura de fallback local e validação Ground Truth 100%).
* **Parte 4 — DIARIO.md, Autoavaliação e Documentação:** ~3 horas (consolidação do diário de bordo, autocrítica técnica e auditoria).
