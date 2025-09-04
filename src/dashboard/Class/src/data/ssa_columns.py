# src/data/ssa_columns.py
from typing import Dict, Any
import pandas as pd
from datetime import datetime


class SSAColumns:
    """Mantém os índices e nomes das colunas."""

    # Índices
    NUMERO_SSA = 0
    SITUACAO = 1
    DERIVADA = 2
    LOCALIZACAO = 3
    DESC_LOCALIZACAO = 4
    EQUIPAMENTO = 5
    SEMANA_CADASTRO = 6
    EMITIDA_EM = 7
    DESC_SSA = 8
    SETOR_EMISSOR = 9
    SETOR_EXECUTOR = 10
    SOLICITANTE = 11
    SERVICO_ORIGEM = 12
    GRAU_PRIORIDADE_EMISSAO = 13
    GRAU_PRIORIDADE_PLANEJAMENTO = 14
    EXECUCAO_SIMPLES = 15
    RESPONSAVEL_PROGRAMACAO = 16
    SEMANA_PROGRAMADA = 17
    RESPONSAVEL_EXECUCAO = 18
    DESCRICAO_EXECUCAO = 19
    SISTEMA_ORIGEM = 20
    ANOMALIA = 21

    # Nomes para exibição
    COLUMN_NAMES = {
        NUMERO_SSA: "Número da SSA",
        SITUACAO: "Situação",
        DERIVADA: "Derivada de",
        LOCALIZACAO: "Localização",
        DESC_LOCALIZACAO: "Descrição da Localização",
        EQUIPAMENTO: "Equipamento",
        SEMANA_CADASTRO: "Semana de Cadastro",
        EMITIDA_EM: "Emitida Em",
        DESC_SSA: "Descrição da SSA",
        SETOR_EMISSOR: "Setor Emissor",
        SETOR_EXECUTOR: "Setor Executor",
        SOLICITANTE: "Solicitante",
        SERVICO_ORIGEM: "Serviço de Origem",
        GRAU_PRIORIDADE_EMISSAO: "Grau de Prioridade Emissão",
        GRAU_PRIORIDADE_PLANEJAMENTO: "Grau de Prioridade Planejamento",
        EXECUCAO_SIMPLES: "Execução Simples",
        RESPONSAVEL_PROGRAMACAO: "Responsável na Programação",
        SEMANA_PROGRAMADA: "Semana Programada",
        RESPONSAVEL_EXECUCAO: "Responsável na Execução",
        DESCRICAO_EXECUCAO: "Descrição Execução",
        SISTEMA_ORIGEM: "Sistema de Origem",
        ANOMALIA: "Anomalia",
    }

    # Descrições detalhadas dos estados
    STATE_DESCRIPTIONS = {
        "APL": "APL - AGUARDANDO PLANEJAMENTO",
        "APG": "APG - AGUARDANDO PROGRAMAÇÃO",
        "AAD": "AAD - AGUARDANDO ATUALIZAÇÃO DE DESENHOS",
        "ADM": "ADM - AGUARDANDO DEPARTAMENTO DE MANUTENÇÃO",
        "AAT": "AAT - AGAURDANDO ATENDIMENTO DE TERCEIROS",
        "APV": "APV - AGUARDANDO PROVISIONAMENTO",
        "AIM": "AIM - AGUARDANDO ENGENHARIA DE MANUTENÇÃO",
        "SCD": "SCD - SSA CANCELADA AGUARDANDO APROV. DIVISÃO",
        "ADI": "ADI - AGUARDANDO APROVAÇÃO DA DIVISÃO NA EMISSÃO",
    }

    # Cores para estados
    STATE_COLORS = {
        "APL": "#fd7e14",  # Laranja
        "APG": "#fd7e14",  # Laranja
        "AAD": "#007bff",  # Azul
        "ADM": "#007bff",  # Azul
        "AAT": "#007bff",  # Azul
        "APV": "#007bff",  # Azul
        "AIM": "#007bff",  # Azul
        "SCD": "#6c757d",  # Cinza
        "ADI": "#dc3545",  # Vermelho
    }

    # Tipos de dados esperados para cada coluna
    COLUMN_TYPES = {
        NUMERO_SSA: str,
        SITUACAO: str,
        DERIVADA: str,
        LOCALIZACAO: str,
        DESC_LOCALIZACAO: str,
        EQUIPAMENTO: str,
        SEMANA_CADASTRO: str,
        EMITIDA_EM: "datetime64[ns]",
        DESC_SSA: str,
        SETOR_EMISSOR: str,
        SETOR_EXECUTOR: str,
        SOLICITANTE: str,
        SERVICO_ORIGEM: str,
        GRAU_PRIORIDADE_EMISSAO: str,
        GRAU_PRIORIDADE_PLANEJAMENTO: str,
        EXECUCAO_SIMPLES: str,
        RESPONSAVEL_PROGRAMACAO: str,
        SEMANA_PROGRAMADA: str,
        RESPONSAVEL_EXECUCAO: str,
        DESCRICAO_EXECUCAO: str,
        SISTEMA_ORIGEM: str,
        ANOMALIA: str,
    }

    # Colunas obrigatórias
    REQUIRED_COLUMNS = {
        NUMERO_SSA,
        SITUACAO,
        GRAU_PRIORIDADE_EMISSAO,
        EMITIDA_EM,
        SETOR_EXECUTOR,
    }

    @classmethod
    def get_name(cls, index: int) -> str:
        """Retorna o nome da coluna pelo índice."""
        return cls.COLUMN_NAMES.get(index, f"Coluna {index}")

    @classmethod
    def get_state_description(cls, state: str) -> str:
        """Retorna a descrição completa do estado."""
        return cls.STATE_DESCRIPTIONS.get(state, state)

    @classmethod
    def get_state_color(cls, state: str) -> str:
        """Retorna a cor associada ao estado."""
        return cls.STATE_COLORS.get(state, "#6c757d")  # Cinza como cor padrão

    @classmethod
    def validate_column_type(cls, index: int, value: Any) -> bool:
        """Valida o tipo de dado de uma coluna."""
        expected_type = cls.COLUMN_TYPES.get(index)
        if not expected_type:
            return True  # Se não tiver tipo definido, considera válido

        if expected_type == "datetime64[ns]":
            return isinstance(value, (datetime, pd.Timestamp)) or pd.isna(value)

        return isinstance(value, expected_type) or pd.isna(value)

    @classmethod
    def is_required(cls, index: int) -> bool:
        """Verifica se a coluna é obrigatória."""
        return index in cls.REQUIRED_COLUMNS

    @classmethod
    def get_column_indices(cls) -> Dict[str, int]:
        """Retorna um dicionário com os nomes das colunas e seus índices."""
        return {name: idx for idx, name in cls.COLUMN_NAMES.items()}

    @classmethod
    def get_display_config(cls) -> Dict[str, Dict]:
        """Retorna configurações de exibição para as colunas."""
        return {
            cls.get_name(idx): {
                "width": (
                    "150px"
                    if idx not in [cls.DESC_SSA, cls.DESC_LOCALIZACAO]
                    else "300px"
                ),
                "textAlign": "left",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": (
                    "normal"
                    if idx in [cls.DESC_SSA, cls.DESC_LOCALIZACAO]
                    else "nowrap"
                ),
            }
            for idx in cls.COLUMN_NAMES.keys()
        }
