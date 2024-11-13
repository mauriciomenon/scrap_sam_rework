# src/utils/data_validator.py
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from ..data.ssa_data import SSAData

@dataclass
class ValidationResult:
    """Resultado da validação de dados."""
    is_valid: bool
    issues: List[str]
    statistics: Dict
    timestamp: datetime

class SSADataValidator:
    """Classe para validação de dados das SSAs."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_data_consistency(self, ssa_objects: List[SSAData]) -> ValidationResult:
        """Valida consistência dos dados."""
        issues = []
        stats = {}

        try:
            # 1. Contagem por responsável
            resp_counts = {}
            for ssa in ssa_objects:
                if ssa.responsavel_execucao:
                    resp_counts[ssa.responsavel_execucao] = resp_counts.get(ssa.responsavel_execucao, 0) + 1

            stats['resp_counts'] = resp_counts

            # 2. Verificação de inconsistências
            for resp, count in resp_counts.items():
                ssas_list = [s for s in ssa_objects if s.responsavel_execucao == resp]
                if len(ssas_list) != count:
                    issues.append(f"Inconsistência na contagem para {resp}: contagem={count}, real={len(ssas_list)}")

            # 3. Verificação de estados
            for ssa in ssa_objects:
                # Verifica combinações inválidas de estados
                if ssa.responsavel_execucao and not ssa.setor_executor:
                    issues.append(f"SSA {ssa.numero} tem responsável mas não tem setor executor")

            # 4. Estatísticas gerais
            stats.update({
                'total_ssas': len(ssa_objects),
                'ssas_com_responsavel': len([s for s in ssa_objects if s.responsavel_execucao]),
                'ssas_sem_responsavel': len([s for s in ssa_objects if not s.responsavel_execucao]),
                'setores_executores': len(set(s.setor_executor for s in ssa_objects if s.setor_executor)),
                'timestamp': datetime.now(),
            })

        except Exception as e:
            self.logger.error(f"Erro na validação: {str(e)}")
            issues.append(f"Erro na validação: {str(e)}")

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            statistics=stats,
            timestamp=datetime.now()
        )

    def verify_data_integrity(self, ssa_objects: List[SSAData]) -> Dict:
        """Verifica integridade periódica dos dados."""
        integrity_report = {
            'timestamp': datetime.now(),
            'total_records': len(ssa_objects),
            'checks': [],
            'warnings': []
        }

        try:
            # 1. Verificação de dados obrigatórios
            missing_required = [
                ssa.numero for ssa in ssa_objects 
                if not all([ssa.numero, ssa.situacao, ssa.prioridade_emissao])
            ]
            if missing_required:
                integrity_report['warnings'].append(
                    f"SSAs com dados obrigatórios faltando: {', '.join(missing_required)}"
                )

            # 2. Verificação de datas
            future_dates = [
                ssa.numero for ssa in ssa_objects 
                if ssa.emitida_em and ssa.emitida_em > datetime.now()
            ]
            if future_dates:
                integrity_report['warnings'].append(
                    f"SSAs com datas futuras: {', '.join(future_dates)}"
                )

            # 3. Verificação de duplicatas
            numeros_ssa = [ssa.numero for ssa in ssa_objects]
            duplicates = set([num for num in numeros_ssa if numeros_ssa.count(num) > 1])
            if duplicates:
                integrity_report['warnings'].append(
                    f"SSAs duplicadas encontradas: {', '.join(duplicates)}"
                )

            # 4. Estatísticas
            integrity_report['checks'] = {
                'duplicates_found': len(duplicates),
                'future_dates_found': len(future_dates),
                'missing_required_found': len(missing_required),
                'total_warnings': len(integrity_report['warnings'])
            }

        except Exception as e:
            self.logger.error(f"Erro na verificação de integridade: {str(e)}")
            integrity_report['warnings'].append(f"Erro na verificação: {str(e)}")

        return integrity_report

    def check_graph_data_consistency(self, ssa_objects: List[SSAData], 
                                   graph_data: Dict) -> List[str]:
        """Verifica consistência entre dados do gráfico e objetos SSA."""
        inconsistencies = []

        try:
            # Contagem real por responsável
            real_counts = {}
            for ssa in ssa_objects:
                if ssa.responsavel_execucao:
                    real_counts[ssa.responsavel_execucao] = real_counts.get(
                        ssa.responsavel_execucao, 0
                    ) + 1

            # Compara com dados do gráfico
            for resp, count in graph_data.items():
                real_count = real_counts.get(resp, 0)
                if count != real_count:
                    inconsistencies.append(
                        f"Inconsistência para {resp}: "
                        f"gráfico={count}, dados={real_count}"
                    )
                    self.logger.warning(
                        f"SSAs para {resp}: "
                        f"{[s.numero for s in ssa_objects if s.responsavel_execucao == resp]}"
                    )

        except Exception as e:
            self.logger.error(f"Erro na verificação de consistência do gráfico: {str(e)}")
            inconsistencies.append(f"Erro na verificação: {str(e)}")

        return inconsistencies



    def diagnose_responsavel_data(
        self, ssa_objects: List[SSAData], area_emissora: str = None
    ) -> Dict:
        """Diagnóstico detalhado dos dados de responsáveis."""
        try:
            diagnostico = {
                "total_ssas": len(ssa_objects),
                "por_responsavel_exec": {},
                "por_responsavel_prog": {},
                "problemas": [],
            }

            # Filtra por área emissora se especificada
            ssas_filtradas = ssa_objects
            if area_emissora:
                ssas_filtradas = [
                    ssa
                    for ssa in ssa_objects
                    if ssa.setor_emissor
                    and ssa.setor_emissor.upper() == area_emissora.upper()
                ]
                diagnostico["total_filtrado"] = len(ssas_filtradas)

            # Contagem por responsável execução
            for ssa in ssas_filtradas:
                if ssa.responsavel_execucao:
                    resp_exec = ssa.responsavel_execucao.strip().upper()
                    if resp_exec not in diagnostico["por_responsavel_exec"]:
                        diagnostico["por_responsavel_exec"][resp_exec] = {
                            "total": 0,
                            "ssas": [],
                        }
                    diagnostico["por_responsavel_exec"][resp_exec]["total"] += 1
                    diagnostico["por_responsavel_exec"][resp_exec]["ssas"].append(
                        ssa.numero
                    )

                if ssa.responsavel_programacao:
                    resp_prog = ssa.responsavel_programacao.strip().upper()
                    if resp_prog not in diagnostico["por_responsavel_prog"]:
                        diagnostico["por_responsavel_prog"][resp_prog] = {
                            "total": 0,
                            "ssas": [],
                        }
                    diagnostico["por_responsavel_prog"][resp_prog]["total"] += 1
                    diagnostico["por_responsavel_prog"][resp_prog]["ssas"].append(
                        ssa.numero
                    )

            return diagnostico

        except Exception as e:
            logging.error(f"Erro no diagnóstico: {str(e)}")
            return None


    # Atualize a classe SSADataValidator para incluir verificações específicas:
    def validate_responsavel_consistency(
        self, ssa_objects: List[SSAData], area_emissora: str = None
    ) -> List[str]:
        """Valida consistência dos dados de responsáveis."""
        issues = []
        try:
            diagnostico = self.diagnose_responsavel_data(ssa_objects, area_emissora)

            # Verifica inconsistências
            for resp, dados in diagnostico["por_responsavel_exec"].items():
                if dados["total"] != len(dados["ssas"]):
                    issues.append(
                        f"Inconsistência na contagem de SSAs para responsável execução {resp}: "
                        f"contagem={dados['total']}, real={len(dados['ssas'])}"
                    )
                    issues.append(f"SSAs do responsável {resp}: {', '.join(dados['ssas'])}")

            for resp, dados in diagnostico["por_responsavel_prog"].items():
                if dados["total"] != len(dados["ssas"]):
                    issues.append(
                        f"Inconsistência na contagem de SSAs para responsável programação {resp}: "
                        f"contagem={dados['total']}, real={len(dados['ssas'])}"
                    )
                    issues.append(f"SSAs do responsável {resp}: {', '.join(dados['ssas'])}")

            # Verifica dados nulos ou malformados
            for ssa in ssa_objects:
                if ssa.responsavel_execucao and not isinstance(
                    ssa.responsavel_execucao, str
                ):
                    issues.append(
                        f"Tipo inválido para responsável execução na SSA {ssa.numero}: "
                        f"{type(ssa.responsavel_execucao)}"
                    )

                if ssa.responsavel_programacao and not isinstance(
                    ssa.responsavel_programacao, str
                ):
                    issues.append(
                        f"Tipo inválido para responsável programação na SSA {ssa.numero}: "
                        f"{type(ssa.responsavel_programacao)}"
                    )

            return issues

        except Exception as e:
            logging.error(f"Erro na validação: {str(e)}")
            return [f"Erro na validação: {str(e)}"]
