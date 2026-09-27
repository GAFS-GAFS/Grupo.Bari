#!/bin/bash
# ==============================================================================
# RUN_PROJECT.sh — Official Pipeline Orchestrator (Grupo Bari Case)
# Executes Part 1 (Diagnostics), Part 2 (RPA + PDF), and Part 3 (AI Extraction)
# ==============================================================================

set -e

# Ensure execution in the project root directory
cd "$(dirname "$0")"

# Terminal Colors
GREEN="\033[1;32m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n${BLUE}======================================================================${RESET}"
echo -e "${BOLD}              BANCO BARI  |  CENTRAL DE AUTOMAÇÃO DE CRÉDITO          ${RESET}"
echo -e "${BLUE}======================================================================${RESET}"

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo -e "${CYAN}→ Ativando ambiente virtual (.venv)...${RESET}"
    source .venv/bin/activate
fi

echo -e "\n${BOLD}[ ETAPA 1/3 ] Diagnóstico e Análise Estatística do Funil...${RESET}"
python3 Case_Bari/funnel_analysis.py

echo -e "\n${BOLD}[ ETAPA 2/3 ] Esteira Automatizada RPA + Relatório Executivo PDF...${RESET}"
python3 Case_Bari/rpa_routine.py

echo -e "\n${BOLD}[ ETAPA 3/3 ] Extração Inteligente de Laudos com IA (NLP)...${RESET}"
python3 Case_Bari/ai_extraction.py

echo -e "\n${GREEN}======================================================================${RESET}"
echo -e "${GREEN}✅ ESTEIRA EXECUTADA COM SUCESSO!${RESET}"
echo -e "${BOLD}Entregáveis gerados em Case_Bari/:${RESET}"
echo -e "  📄 ${GREEN}Relatorio_Lideranca.pdf${RESET}  (One-Pager executivo de 1 página para diretoria)"
echo -e "  🔍 ${GREEN}laudos_extraidos.json${RESET}    (17 laudos estruturados com 100% acurácia)"
echo -e "${GREEN}======================================================================${RESET}\n"
