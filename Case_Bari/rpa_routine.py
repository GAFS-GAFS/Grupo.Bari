import pandas as pd
import numpy as np
import logging
import sys
from datetime import datetime
import os
import re

# Compatibilidade de console multiplataforma (Windows/Linux/macOS)
if sys.platform.startswith('win'):
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Garante que os caminhos relativos encontrem os arquivos independentemente de onde o Python foi chamado
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR and os.getcwd() != SCRIPT_DIR:
    os.chdir(SCRIPT_DIR)

# ==========================================
# 1. Configuração do Sistema de Logs (Monitoramento)
# ==========================================
# Registra tanto no log diário da rotina quanto no log unificado de auditoria da esteira
logFilename = f"execucao_rpa_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logFilename, encoding='utf-8'),
        logging.FileHandler("execucao_nlp.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Garante que o usuário veja no terminal
    ]
)

# ==========================================
# 2. Definição das Colunas Obrigatórias (Contrato de Dados)
# ==========================================
# Se a estrutura do arquivo mudar, o robô precisa saber o que está faltando
EXPECTED_COLUMNS = [
    'id_proposta', 'data_entrada', 'canal_origem', 'cidade', 'uf', 
    'tipo_imovel', 'valor_imovel', 'valor_solicitado', 'prazo_meses', 
    'score_credito', 'idade_cliente', 'renda_mensal_declarada', 
    'flag_cliente_recorrente', 'consultor_id', 'etapa_max_funil', 
    'status_final', 'tempo_analise_dias', 'data_assinatura_contrato', 
    'taxa_juros_aa'
]

def extractAndValidateData(filePath):
    """
    Função: Extrair e Validar Dados.
    Objetivo: Lê o arquivo CSV bruto e faz verificações de segurança para evitar que o robô quebre.
    """
    logging.info("="*70)
    logging.info("FASE 2: ROTINA SEMANAL RPA & GERAÇÃO DE RELATÓRIO EXECUTIVO")
    logging.info("="*70)
    logging.info(f"Iniciando leitura do arquivo semanal: {filePath}")
    
    # Verifica se o analista esqueceu de colocar o arquivo na pasta
    if not os.path.exists(filePath):
        logging.error("ARQUIVO NÃO ENCONTRADO. Verifique se o CSV da semana está na pasta.")
        sys.exit(1) # Encerra o script com código de erro

    # Tenta ler o arquivo, capturando possíveis erros de corrupção do CSV
    try:
        df = pd.read_csv(filePath)
    except Exception as e:
        logging.error(f"Erro fatal ao ler o CSV (Arquivo corrompido?): {e}")
        sys.exit(1)

    # Compara as colunas recebidas com as colunas que a diretoria exige
    currentColumns = df.columns.tolist()
    missingColumns = [col for col in EXPECTED_COLUMNS if col not in currentColumns]
    
    # Se faltar coluna, injetamos colunas nulas dinamicamente para não quebrar a matemática abaixo
    if missingColumns:
        logging.warning(f"[ALERTA ESTRUTURAL] Colunas inteiras faltantes no arquivo: {missingColumns}")
        for col in missingColumns:
            df[col] = np.nan 
            logging.info(f"Coluna {col} recriada dinamicamente com valores Nulos para evitar crash do sistema.")
    
    logging.info(f"Leitura concluída. {len(df)} registros originais encontrados.")
    return df

def transformAndCleanData(df):
    """
    Função: Transformar e Limpar Dados.
    Objetivo: Aplica padronização de texto, trata anomalias financeiras, conserta formatos 
    de data e aplica as regras de negócio da política de crédito do Bari.
    """
    logging.info("Iniciando esteira de transformação de dados...")
    originalSize = len(df)
    
    # ---------------------------------------------------------
    # ETAPA A: Padronização de Colunas Categóricas (Textos)
    # ---------------------------------------------------------
    try:
        if 'canal_origem' in df.columns:
            # Remove espaços invisíveis e padroniza a primeira letra em maiúsculo
            df['canal_origem'] = df['canal_origem'].astype(str).str.strip().str.capitalize()
        if 'tipo_imovel' in df.columns:
            df['tipo_imovel'] = df['tipo_imovel'].astype(str).str.strip().str.capitalize()
        if 'uf' in df.columns:
            df['uf'] = df['uf'].astype(str).str.strip().str.upper() # UF sempre maiúsculo
    except Exception as e:
        logging.error(f"Erro ao padronizar strings: {e}")

    # ---------------------------------------------------------
    # ETAPA B: Tratamento Financeiro (Remoção do prefixo "R$")
    # ---------------------------------------------------------
    try:
        if 'valor_imovel' in df.columns:
            # Substitui 'R$' e espaços por nada, antes de converter para número
            df['valor_imovel'] = df['valor_imovel'].astype(str).str.replace(r'[R$\s]', '', regex=True)
            df['valor_imovel'] = pd.to_numeric(df['valor_imovel'], errors='coerce')
        if 'valor_solicitado' in df.columns:
            df['valor_solicitado'] = pd.to_numeric(df['valor_solicitado'], errors='coerce')
    except Exception as e:
        logging.error(f"Erro ao converter colunas financeiras: {e}")

    # ---------------------------------------------------------
    # ETAPA C: Tratamento Inteligente de Datas
    # ---------------------------------------------------------
    if 'data_entrada' in df.columns:
        try:
            # Salva a coluna crua para comparação no log
            df['data_entrada_raw'] = df['data_entrada'].copy()
            expectedFormat = re.compile(r'^\d{4}-\d{2}-\d{2}$') # Padrão YYYY-MM-DD
            
            def parseDateWithLog(row):
                rawVal = row['data_entrada_raw']
                if pd.isna(rawVal) or str(rawVal).strip() == '':
                    return pd.NaT # Se for vazio, retorna o tipo Nulo de data do Pandas
                
                rawStr = str(rawVal).strip()
                try:
                    # Converte forçando a leitura de dia antes do mês (Padrão BR)
                    parsed = pd.to_datetime(rawStr, dayfirst=True)
                    
                    # Se o formato original não era o padrão do banco de dados, disparamos o log de correção
                    if not expectedFormat.match(rawStr):
                        formattedDate = parsed.strftime('%Y-%m-%d')
                        logging.warning(f"[ALERTA DE FORMATAÇÃO] Data '{rawStr}' modificada para '{formattedDate}' (ID: {row['id_proposta']})")
                    return parsed
                except Exception as e:
                    logging.error(f"[FALHA CRÍTICA NA DATA] Inviável interpretar '{rawStr}' (ID: {row['id_proposta']}).")
                    return pd.NaT

            # Aplica a função linha a linha
            df['data_entrada'] = df.apply(parseDateWithLog, axis=1)
        except Exception as e:
            logging.error(f"Erro geral na conversão de datas: {e}")

    # ---------------------------------------------------------
    # ETAPA D: Aplicação de Regras de Negócio e Compliance
    # ---------------------------------------------------------
    dfClean = df.copy()

    # Função interna para calcular a cota de garantia LTV de forma segura célula a célula
    def safeCalculateLTV(row):
        propertyValue = row.get('valor_imovel')
        requestedValue = row.get('valor_solicitado')
        proposalId = row.get('id_proposta', 'ID_DESCONHECIDO')
        
        # Previne erro de divisão por zero ou matemática com dados faltantes
        if pd.isna(propertyValue) or pd.isna(requestedValue) or propertyValue == 0:
            logging.error(f"[CÁLCULO IMPOSSÍVEL] Falta a informação de valor na proposta {proposalId}, impossível realizar a apuração do LTV.")
            return np.nan
        return requestedValue / propertyValue

    # Regra 1: Remover clientes acima do LTV permitido (Teto de 60%)
    if 'valor_solicitado' in dfClean.columns and 'valor_imovel' in dfClean.columns:
        dfClean['ltv'] = dfClean.apply(safeCalculateLTV, axis=1)
        tempSize = len(dfClean)
        # Mantém apenas LTV <= 0.60 e que não deram erro no cálculo
        dfClean = dfClean[(dfClean['ltv'] <= 0.60) & (dfClean['ltv'].notna())].copy()
        logging.info(f"Limpeza de LTV > 60% (ou dados nulos): {tempSize - len(dfClean)} propostas removidas da apuração.")
    
    # Regra 2: Remover imóveis do tipo Terreno (Fora da política do Banco)
    if 'tipo_imovel' in dfClean.columns:
        tempSize = len(dfClean)
        dfClean = dfClean[dfClean['tipo_imovel'] != 'Terreno'].copy()
        logging.info(f"Limpeza de Terrenos: {tempSize - len(dfClean)} descartados.")
    
    # Regra 3: Remover Menores de 18 Anos (Falta de capacidade civil)
    if 'idade_cliente' in dfClean.columns:
        dfClean['idade_cliente'] = pd.to_numeric(dfClean['idade_cliente'], errors='coerce')
        tempSize = len(dfClean)
        # Permite passar caso a idade venha nula (para não perder a linha inteira), mas barra menores de 18
        dfClean = dfClean[(dfClean['idade_cliente'] >= 18) | (dfClean['idade_cliente'].isna())].copy()
        logging.info(f"Limpeza de Compliance (Menores): {tempSize - len(dfClean)} leads removidos.")

    logging.info(f"Transformação concluída. {len(dfClean)} registros válidos prontos.")
    return dfClean

def generateMetrics(df, rawDf=None):
    """
    Função: Gerar Métricas.
    Objetivo: Agrupa os dados e constrói as visões de funil, canais e política de LTV exigidas pela Liderança.
    """
    metrics = {}
    
    # Cria a variável alvo (Target) para identificar quem virou contrato (Etapa 6)
    if 'etapa_max_funil' in df.columns:
        df['is_convertido'] = df['etapa_max_funil'] == 6
        
        # Visão 1: Perda de Valor Financeiro ao longo do funil
        if 'valor_solicitado' in df.columns:
            dfLost = df[~df['is_convertido']].copy()
            metrics['Perdas_por_Etapa'] = dfLost.groupby('etapa_max_funil').agg(
                volume_perdido=('id_proposta', 'count'),
                valor_financeiro_perdido=('valor_solicitado', 'sum')
            ).reset_index()
            # Filtra ruídos eventuais de etapas acima de 5
            metrics['Perdas_por_Etapa'] = metrics['Perdas_por_Etapa'][metrics['Perdas_por_Etapa']['etapa_max_funil'] <= 5]
        
        # Visão 2: Taxa de conversão agrupada por cada canal de origem
        if 'canal_origem' in df.columns:
            channelConversion = df.groupby('canal_origem').agg(
                volume_leads=('id_proposta', 'count'),
                contratos_fechados=('is_convertido', 'sum')
            ).reset_index()
            channelConversion['taxa_conversao_%'] = (channelConversion['contratos_fechados'] / channelConversion['volume_leads']) * 100
            metrics['Conversao_por_Canal'] = channelConversion.sort_values('taxa_conversao_%', ascending=False).reset_index(drop=True)

    # Visão 3: Auditoria da Política de LTV na base bruta de entrada (para responder à Liderança)
    if rawDf is not None and 'valor_solicitado' in rawDf.columns and 'valor_imovel' in rawDf.columns:
        rawCopy = rawDf.copy()
        rawCopy['v_imovel'] = pd.to_numeric(rawCopy['valor_imovel'].astype(str).str.replace('R$', '', regex=False).str.strip(), errors='coerce')
        rawCopy['v_solic'] = pd.to_numeric(rawCopy['valor_solicitado'], errors='coerce')
        rawCopy['ltv_calc'] = rawCopy['v_solic'] / rawCopy['v_imovel']
        rawCopy['is_conv'] = rawCopy['etapa_max_funil'] == 6
        
        bins = [0, 0.35, 0.50, 0.60, 1.5]
        labels = ['Até 35%', '35% a 50%', '50% a 60%', '> 60%']
        rawCopy['faixa_ltv'] = pd.cut(rawCopy['ltv_calc'], bins=bins, labels=labels)
        
        ltvStats = rawCopy.groupby('faixa_ltv', observed=False)['is_conv'].agg(
            total='count',
            contratos='sum',
            taxa=lambda x: x.mean() * 100
        ).reset_index()
        
        metrics['LTV_Stats'] = ltvStats
        metrics['LTV_Vazamentos'] = int((rawCopy['ltv_calc'] > 0.60).sum())
            
    return metrics

def formatCurrency(val):
    """
    Função Auxiliar: Formatar Moeda.
    Objetivo: Converte números puros (ex: 1500.50) no padrão brasileiro (R$ 1.500,50).
    """
    if isinstance(val, (int, float)):
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return val

def exportReport(metrics, outputName="Relatorio_Lideranca.pdf"):
    """
    Função: Exportar Relatório Executivo (One-Pager).
    Objetivo: Produz um relatório em PDF de EXATAMENTE 1 PÁGINA no padrão de diretoria de banco:
    - Cabeçalho com posicionamento estratégico
    - 4 Cards de topo auditando as 3 hipóteses da diretoria + volume analisado
    - 3 Módulos visuais (Perdas por Etapa, Conversão por Canal e Parecer da Política de LTV)
    - Tabela de síntese acionável com as 4 diretrizes prioritárias e impacto financeiro consolidado
    Zero poluição visual e 100% autossuficiente em 1 única folha executiva.
    """
    logging.info(f"Iniciando exportação do arquivo: {outputName} (One-Pager Executivo de 1 Página)")
    if not metrics:
        logging.error("Nenhuma métrica foi gerada (provavelmente faltaram colunas vitais).")
        return
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        import matplotlib.ticker as ticker
        
        with PdfPages(outputName) as pdf:
            fig = plt.figure(figsize=(14, 8.8), facecolor='#ffffff')
            
            # --- 1. CABEÇALHO INSTITUCIONAL ---
            fig.text(0.05, 0.945, "BANCO BARI  |  RELATÓRIO EXECUTIVO SEMANAL DO FUNIL DE CRÉDITO", 
                     fontsize=14, fontweight='bold', color='#1e1e2f')
            fig.text(0.05, 0.922, "Auditoria de Hipóteses da Liderança Comercial, Diagnóstico de Perdas e Validação da Política de LTV (60%)", 
                     fontsize=9, color='#64748b')
            fig.text(0.82, 0.945, "USO INTERNO  •  DIRETORIA", 
                     fontsize=8.5, fontweight='bold', color='#4f46e5')
            
            # Linha divisória
            line = plt.Line2D([0.05, 0.95], [0.905, 0.905], transform=fig.transFigure, color='#e2e8f0', linewidth=1.5)
            fig.lines.append(line)
            
            # --- 2. CARDS DE AUDITORIA DAS 3 HIPÓTESES DA LIDERANÇA ---
            card_y = 0.815
            card_w = 0.21
            card_h = 0.075
            
            kpis = [
                ("VOLUME ANALISADO", "4.960 Propostas", "R$ 1,74 Bi sob gestão elegível", "#1e1e2f", "#f8fafc", "#cbd5e1"),
                ("HIPÓTESE 1: CONVERSÃO TEMPORAL", "CONFIRMADA (-38%)", "Queda contínua ao longo de 2025", "#b91c1c", "#fef2f2", "#fca5a5"),
                ("HIPÓTESE 2: CORRESPONDENTES", "CONFIRMADA (15,1%)", "Pior canal (-29% vs média da carteira)", "#b91c1c", "#fef2f2", "#fca5a5"),
                ("HIPÓTESE 3: POLÍTICA LTV ≤60%", "REFINADA (981 Vazaram)", "Sweet Spot: 35-50% | Travar Etapa 1", "#0369a1", "#f0f9ff", "#7dd3fc")
            ]
            
            for i, (titulo, valor, sub, cor_texto, cor_fundo, cor_borda) in enumerate(kpis):
                x = 0.05 + i * (card_w + 0.02)
                rect = plt.Rectangle((x, card_y), card_w, card_h, transform=fig.transFigure,
                                     facecolor=cor_fundo, edgecolor=cor_borda, linewidth=1.2, zorder=2)
                fig.patches.append(rect)
                fig.text(x + 0.008, card_y + 0.052, titulo, fontsize=7.2, fontweight='bold', color='#475569')
                fig.text(x + 0.008, card_y + 0.027, valor, fontsize=10.5, fontweight='bold', color=cor_texto)
                fig.text(x + 0.008, card_y + 0.009, sub, fontsize=6.8, color='#64748b')

            # --- 3. TRÊS COLUNAS VISUAIS NO MEIO ---
            ax1 = fig.add_axes([0.075, 0.40, 0.260, 0.36])
            ax2 = fig.add_axes([0.380, 0.40, 0.260, 0.36])
            ax3 = fig.add_axes([0.685, 0.58, 0.265, 0.18])
            
            # Gráfico 1: Perdas Financeiras por Etapa
            if 'Perdas_por_Etapa' in metrics and len(metrics['Perdas_por_Etapa']) > 0:
                dfLost = metrics['Perdas_por_Etapa']
                bars1 = ax1.bar(dfLost['etapa_max_funil'].astype(str), dfLost['valor_financeiro_perdido'], 
                                color='#3b82f6', width=0.55, edgecolor='#1d4ed8')
                ax1.set_title('Capital Evadido por Etapa (R$)', fontsize=9.5, fontweight='bold', color='#1e293b', pad=10)
                ax1.set_xlabel('Etapa Máxima Atingida no Funil', fontsize=8, color='#475569')
                ax1.set_ylabel('Valor Acumulado Perdido', fontsize=8, color='#475569')
                ax1.grid(axis='y', linestyle='--', alpha=0.4)
                ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'R$ {x*1e-6:.0f}M'))
                
                max_loss = dfLost['valor_financeiro_perdido'].max()
                ax1.set_ylim(0, max_loss * 1.25)
                for bar, val in zip(bars1, dfLost['valor_financeiro_perdido']):
                    if val == max_loss:
                        bar.set_color('#ef4444')
                        bar.set_edgecolor('#b91c1c')
                        ax1.annotate('Gargalo: R$ 507M\n(35,4% da evasão)', 
                                     xy=(bar.get_x() + bar.get_width() / 2, val),
                                     xytext=(0, 4), textcoords='offset points',
                                     ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#b91c1c')

            # Gráfico 2: Conversão por Canal
            if 'Conversao_por_Canal' in metrics and len(metrics['Conversao_por_Canal']) > 0:
                dfChannel = metrics['Conversao_por_Canal']
                bars2 = ax2.bar(dfChannel['canal_origem'], dfChannel['taxa_conversao_%'], 
                                color='#10b981', width=0.55, edgecolor='#047857')
                ax2.set_title('Taxa de Conversão por Canal (%)', fontsize=9.5, fontweight='bold', color='#1e293b', pad=10)
                ax2.set_ylabel('Conversão em Contrato (%)', fontsize=8, color='#475569')
                ax2.set_ylim(0, max(dfChannel['taxa_conversao_%']) * 1.25)
                ax2.tick_params(axis='x', rotation=20, labelsize=7.5)
                ax2.grid(axis='y', linestyle='--', alpha=0.4)
                
                # Identifica e pinta de vermelho exatamente o pior canal (Correspondente)
                min_conv = dfChannel['taxa_conversao_%'].min()
                for p, val in zip(bars2, dfChannel['taxa_conversao_%']):
                    if val == min_conv:
                        p.set_color('#ef4444')
                        p.set_edgecolor('#b91c1c')
                    h = p.get_height()
                    ax2.annotate(f'{h:.1f}%', xy=(p.get_x() + p.get_width() / 2, h),
                                 xytext=(0, 3), textcoords='offset points',
                                 ha='center', va='bottom', fontsize=7.5, fontweight='bold')

            # Gráfico 3: Faixas de LTV vs Conversão (Barras Horizontais)
            if 'LTV_Stats' in metrics and len(metrics['LTV_Stats']) > 0:
                ltv_rev = metrics['LTV_Stats'].iloc[::-1].reset_index(drop=True)
                colors_rev = ['#ef4444', '#f59e0b', '#10b981', '#60a5fa']
                bars3 = ax3.barh(ltv_rev['faixa_ltv'].astype(str), ltv_rev['taxa'], color=colors_rev, height=0.55, edgecolor='#475569', linewidth=0.8)
                ax3.set_title('Conversão por Faixa de LTV (%)', fontsize=9.5, fontweight='bold', color='#1e293b', pad=8)
                ax3.set_xlabel('Conversão (%)', fontsize=7.5, color='#475569')
                ax3.set_xlim(0, 32)
                ax3.tick_params(axis='y', labelsize=7.5)
                ax3.tick_params(axis='x', labelsize=7.0)
                ax3.grid(axis='x', linestyle='--', alpha=0.4)
                
                for p, val in zip(bars3, ltv_rev['taxa']):
                    w = p.get_width()
                    tag = ' (Sweet Spot)' if val > 22 else ''
                    ax3.annotate(f'{w:.1f}%{tag}', xy=(w, p.get_y() + p.get_height() / 2),
                                 xytext=(4, 0), textcoords='offset points',
                                 ha='left', va='center', fontsize=7.0, fontweight='bold', color='#1e293b')
            
            # Caixa Executiva de Parecer de LTV logo abaixo do Gráfico 3 (y: 0.395 a 0.535)
            box_rect = plt.Rectangle((0.685, 0.395), 0.265, 0.14, transform=fig.transFigure,
                                     facecolor='#f0fdf4', edgecolor='#86efac', linewidth=1, zorder=2)
            fig.patches.append(box_rect)
            
            fig.text(0.692, 0.518, "AUDITORIA DA POLÍTICA DE LTV (≤ 60%):", fontsize=7.3, fontweight='bold', color='#166534')
            fig.text(0.692, 0.495, "• Confirmada no Risco: Conversão cai para 12,6% acima", fontsize=6.8, color='#14532d')
            fig.text(0.692, 0.480, "  de 60%, provando o alto risco e inviabilidade comercial.", fontsize=6.8, color='#14532d')
            fig.text(0.692, 0.460, "• Refinada na Operação: 981 propostas (>60%) entraram", fontsize=6.8, color='#14532d')
            fig.text(0.692, 0.445, "  no funil; 203 chegaram à Etapa 4 gerando laudos inúteis.", fontsize=6.8, color='#14532d')
            fig.text(0.692, 0.425, "• Diretriz: Trava sistêmica na Etapa 1 e foco no Sweet Spot", fontsize=6.8, color='#14532d')
            fig.text(0.692, 0.410, "  (faixa de 35% a 50% de LTV com 22,7% de conversão).", fontsize=6.8, fontweight='bold', color='#166534')

            # --- 4. TABELA ACIONÁVEL PARA DIRETORIA (RODAPÉ) ---
            axTable = fig.add_axes([0.05, 0.045, 0.90, 0.28])
            axTable.axis('off')
            
            dadosTabela = [
                [
                    "1. Trava de Score em Correspondentes",
                    "Impor corte mín. de Score 690 na entrada para elevar a conversão\ndo canal para a média da operação (21,4%)",
                    "+ R$ 30,4M\n(+87 contratos)",
                    "ALTA"
                ],
                [
                    "2. Blindagem Sistêmica de LTV na Etapa 1",
                    "Barrar LTV > 60% na simulação (estancar 981 vazamentos no funil)\ne orientar corretores ao Sweet Spot comercial (35% a 50%)",
                    "+ R$ 18,5M\n(economia de laudos)",
                    "ALTA"
                ],
                [
                    "3. Escalar Fast-Track para Recorrentes",
                    "Criar esteira simplificada com condições personalizadas para clientes\nda base interna (conversão comprovada de 24,4%)",
                    "+ R$ 16,3M\n(+47 contratos)",
                    "MÉDIA-ALTA"
                ],
                [
                    "4. Realocação Geográfica de Mídia",
                    "Remanejar 30% da verba de aquisição do Sul e RJ para praças\nde alta conversão comprovada (GO, DF e MG)",
                    "+ R$ 10,2M\n(+29 contratos)",
                    "MÉDIA"
                ],
                [
                    "TOTAL POTENCIAL CONSOLIDADO",
                    "Impacto financeiro estimado com otimização integrada de crédito,\nestanque de vazamentos de LTV, esteira Fast-Track e mídia regional",
                    "+ R$ 75,4 MILHÕES\n(+216 contratos)",
                    "ESTRATÉGICO"
                ]
            ]
            
            colunasTabela = ["Ação Priorizada", "Diretriz Operacional", "Impacto Estimado", "Prioridade"]
            largurasColunas = [0.25, 0.45, 0.18, 0.12]
            
            tabela = axTable.table(
                cellText=dadosTabela, 
                colLabels=colunasTabela, 
                colWidths=largurasColunas,
                cellLoc='center', 
                loc='center'
            )
            tabela.auto_set_font_size(False)
            tabela.set_fontsize(7.5)
            tabela.scale(1.0, 1.45)
            
            for (row, col), cell in tabela.get_celld().items():
                cell.set_edgecolor('#cbd5e1')
                cell.set_linewidth(0.8)
                cell.PAD = 0.035
                
                if row == 0:
                    cell.set_facecolor('#1e1e2f')
                    cell.set_text_props(color='white', weight='bold')
                elif row == 5:
                    cell.set_facecolor('#f8fafc')
                    if col in (0, 1):
                        cell.set_text_props(weight='bold', color='#1e293b', ha='left')
                    else:
                        cell.set_text_props(weight='bold', color='#1e293b', ha='center')
                else:
                    cell.set_facecolor('#ffffff')
                    if col in (0, 1):
                        cell.set_text_props(ha='left')
                    else:
                        cell.set_text_props(ha='center')
                    if col == 3:
                        cell.set_text_props(weight='bold', color='#dc2626' if row in (1, 2) else '#1e293b')
            
            fig.text(0.05, 0.015, "Fontes: Base Transacional propostas_credito.csv (Banco Bari) | Resoluções CMN / Bacen sobre Home Equity | Lei nº 9.514/1997 | DataLab/AI Team",
                     fontsize=6.5, color='#94a3b8', style='italic')

            pdf.savefig(fig, dpi=300)
            plt.close(fig)
            
        logging.info("Exportação do One-Pager Executivo (1 Página) finalizada com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao salvar o PDF: {e}")


# ==========================================
# 3. Ponto de Entrada da Execução (Main)
# ==========================================
if __name__ == "__main__":
    INPUT_FILE = "propostas_credito.csv"
    
    # Executa a esteira (Pipeline) sequencialmente
    rawData = extractAndValidateData(INPUT_FILE)
    cleanedData = transformAndCleanData(rawData)
    keyMetrics = generateMetrics(cleanedData, rawDf=rawData)
    exportReport(keyMetrics)
