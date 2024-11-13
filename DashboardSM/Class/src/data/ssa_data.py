# src/data/ssa_data.py
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

@dataclass
class SSAData:
    """Estrutura de dados para uma SSA."""
    numero: str
    situacao: str
    derivada: Optional[str]
    localizacao: str
    desc_localizacao: str
    equipamento: str
    semana_cadastro: str
    emitida_em: datetime
    descricao: str
    setor_emissor: str
    setor_executor: str
    solicitante: str
    servico_origem: str
    prioridade_emissao: str
    prioridade_planejamento: Optional[str]
    execucao_simples: str
    responsavel_programacao: Optional[str]
    semana_programada: Optional[str]
    responsavel_execucao: Optional[str]
    descricao_execucao: Optional[str]
    sistema_origem: str
    anomalia: Optional[str]

    def __post_init__(self):
        """Validação dos dados após inicialização."""
        # Garante que strings não sejam None
        for field in fields(self):
            if field.type == str and not field.default:
                value = getattr(self, field.name)
                if value is None:
                    setattr(self, field.name, "")

        # Normaliza strings
        for field in fields(self):
            if field.type == str:
                value = getattr(self, field.name)
                if isinstance(value, str):
                    setattr(self, field.name, value.strip())

        # Validações específicas
        if not self.numero:
            raise ValueError("Número da SSA não pode ser vazio")

        if not self.situacao:
            raise ValueError("Situação não pode ser vazia")

        if not self.prioridade_emissao:
            raise ValueError("Prioridade de emissão não pode ser vazia")

    def to_dict(self) -> Dict:
        """Converte o objeto para dicionário."""
        return {
            "numero": self.numero,
            "situacao": self.situacao,
            "derivada": self.derivada,
            "localizacao": self.localizacao,
            "desc_localizacao": self.desc_localizacao,
            "equipamento": self.equipamento,
            "semana_cadastro": self.semana_cadastro,
            "emitida_em": self.emitida_em.strftime("%Y-%m-%d %H:%M:%S") if self.emitida_em else None,
            "descricao": self.descricao,
            "setor_emissor": self.setor_emissor,
            "setor_executor": self.setor_executor,
            "solicitante": self.solicitante,
            "servico_origem": self.servico_origem,
            "prioridade_emissao": self.prioridade_emissao,
            "prioridade_planejamento": self.prioridade_planejamento,
            "execucao_simples": self.execucao_simples,
            "responsavel_programacao": self.responsavel_programacao,
            "semana_programada": self.semana_programada,
            "responsavel_execucao": self.responsavel_execucao,
            "descricao_execucao": self.descricao_execucao,
            "sistema_origem": self.sistema_origem,
            "anomalia": self.anomalia,
        }

    def to_display_dict(self) -> Dict:
        """Converte o objeto para dicionário formatado para exibição."""
        return {
            "Número": self.numero,
            "Situação": self.situacao,
            "Derivada de": self.derivada or "-",
            "Localização": self.localizacao,
            "Desc. Localização": self.desc_localizacao,
            "Equipamento": self.equipamento,
            "Semana Cadastro": self.semana_cadastro,
            "Emitida em": self.emitida_em.strftime("%d/%m/%Y %H:%M") if self.emitida_em else "-",
            "Descrição": self.descricao,
            "Setor Emissor": self.setor_emissor,
            "Setor Executor": self.setor_executor,
            "Solicitante": self.solicitante,
            "Serviço Origem": self.servico_origem,
            "Prioridade": self.prioridade_emissao,
            "Prioridade Plan.": self.prioridade_planejamento or "-",
            "Execução Simples": self.execucao_simples,
            "Resp. Programação": self.responsavel_programacao or "-",
            "Semana Programada": self.semana_programada or "-",
            "Resp. Execução": self.responsavel_execucao or "-",
            "Desc. Execução": self.descricao_execucao or "-",
            "Sistema Origem": self.sistema_origem,
            "Anomalia": self.anomalia or "-",
        }

    def __str__(self) -> str:
        """Representação em string do objeto."""
        return f"SSA {self.numero} ({self.situacao}) - {self.prioridade_emissao}"

    def get_age_in_days(self) -> Optional[int]:
        """Retorna a idade da SSA em dias."""
        if not self.emitida_em:
            return None
        return (datetime.now() - self.emitida_em).days

    def is_critical(self) -> bool:
        """Verifica se a SSA é crítica."""
        return self.prioridade_emissao.upper() == "S3.7"

    def is_programmed(self) -> bool:
        """Verifica se a SSA está programada."""
        return bool(self.semana_programada)

    def has_responsible(self) -> bool:
        """Verifica se a SSA tem responsável designado."""
        return bool(self.responsavel_programacao or self.responsavel_execucao)
