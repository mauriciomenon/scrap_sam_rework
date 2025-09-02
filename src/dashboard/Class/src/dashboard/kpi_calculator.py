import pandas as pd
from datetime import datetime
from typing import Dict
from ..data.ssa_columns import SSAColumns


class KPICalculator:
    """Calcula KPIs e métricas de performance das SSAs."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def calculate_efficiency_metrics(self) -> Dict:
        """Calcula métricas de eficiência."""
        total_ssas = len(self.df)
        if total_ssas == 0:
            return {
                "taxa_programacao": 0,
                "taxa_execucao_simples": 0,
                "distribuicao_prioridade": {},
            }

        return {
            "taxa_programacao": len(
                self.df[self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()]
            )
            / total_ssas,
            "taxa_execucao_simples": len(
                self.df[self.df.iloc[:, SSAColumns.EXECUCAO_SIMPLES] == "Sim"]
            )
            / total_ssas,
            "distribuicao_prioridade": self.df.iloc[
                :, SSAColumns.GRAU_PRIORIDADE_EMISSAO
            ]
            .value_counts(normalize=True)
            .to_dict(),
        }

    def get_overall_health_score(self) -> float:
        """Calcula um score geral de saúde do sistema."""
        metrics = self.calculate_efficiency_metrics()
        score = (
            metrics["taxa_programacao"] * 0.5 + metrics["taxa_execucao_simples"] * 0.5
        )
        return round(score * 100, 2)

    def calculate_response_times(self) -> Dict[str, float]:
        """Calcula tempos de resposta médios por prioridade."""
        response_times = {}

        for priority in self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO].unique():
            mask = self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == priority
            priority_data = self.df[mask]

            if len(priority_data) > 0:
                # Calcula tempo médio desde emissão até programação
                mean_time = (
                    priority_data.iloc[:, SSAColumns.SEMANA_PROGRAMADA].astype(float)
                    - priority_data.iloc[:, SSAColumns.SEMANA_CADASTRO].astype(float)
                ).mean()

                response_times[priority] = mean_time if not pd.isna(mean_time) else None

        return response_times

    def calculate_sector_performance(self) -> pd.DataFrame:
        """Calcula performance por setor."""
        sector_metrics = []

        for sector in self.df.iloc[:, SSAColumns.SETOR_EXECUTOR].unique():
            sector_data = self.df[self.df.iloc[:, SSAColumns.SETOR_EXECUTOR] == sector]

            total_ssas = len(sector_data)
            if total_ssas == 0:
                continue

            programmed_ssas = len(
                sector_data[sector_data.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()]
            )
            critical_ssas = len(
                sector_data[
                    sector_data.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
                ]
            )

            sector_metrics.append(
                {
                    "setor": sector,
                    "total_ssas": total_ssas,
                    "taxa_programacao": (
                        (programmed_ssas / total_ssas) if total_ssas > 0 else 0
                    ),
                    "ssas_criticas": critical_ssas,
                    "percentual_criticas": (
                        (critical_ssas / total_ssas * 100) if total_ssas > 0 else 0
                    ),
                }
            )

        return pd.DataFrame(sector_metrics)

    def calculate_weekly_trends(self) -> pd.DataFrame:
        """Calcula tendências semanais de SSAs."""
        weekly_data = []

        for week in sorted(self.df.iloc[:, SSAColumns.SEMANA_CADASTRO].unique()):
            week_data = self.df[self.df.iloc[:, SSAColumns.SEMANA_CADASTRO] == week]

            total_ssas = len(week_data)
            if total_ssas == 0:
                continue

            programmed = len(
                week_data[week_data.iloc[:, SSAColumns.SEMANA_PROGRAMADA].notna()]
            )
            critical = len(
                week_data[
                    week_data.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] == "S3.7"
                ]
            )

            weekly_data.append(
                {
                    "semana": week,
                    "total_ssas": total_ssas,
                    "programadas": programmed,
                    "criticas": critical,
                    "taxa_programacao": (
                        (programmed / total_ssas) if total_ssas > 0 else 0
                    ),
                }
            )

        return pd.DataFrame(weekly_data)

    def get_key_metrics_summary(self) -> Dict:
        """Retorna um resumo das métricas principais."""
        total_ssas = len(self.df)
        metrics = self.calculate_efficiency_metrics()
        health_score = self.get_overall_health_score()

        # Calcula média de tempo de resposta para SSAs críticas
        response_times = self.calculate_response_times()
        critical_response = response_times.get("S3.7")

        return {
            "total_ssas": total_ssas,
            "health_score": health_score,
            "taxa_programacao": metrics["taxa_programacao"] * 100,
            "taxa_execucao_simples": metrics["taxa_execucao_simples"] * 100,
            "tempo_resposta_criticas": critical_response,
            "distribuicao_prioridade": metrics["distribuicao_prioridade"],
        }
