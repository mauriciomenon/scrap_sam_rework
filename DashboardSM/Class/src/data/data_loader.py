# src/data/data_loader.py
import pandas as pd
import logging
from typing import List, Optional
from datetime import datetime
from ..utils.date_utils import diagnose_dates
from .ssa_data import SSAData
from .ssa_columns import SSAColumns

class DataLoader:
    """Carrega e prepara os dados das SSAs."""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.ssa_objects = []

    def validate_and_fix_date(self, date_str, row_num, logger=None):
        """
        Valida e corrige valores de data apenas quando necessário.
        """
        import pandas as pd
        from datetime import datetime

        def log_issue(message):
            if logger:
                logger.warning(f"Linha {row_num}: {message}")

        try:
            # Se já for timestamp válido, retorna diretamente
            if isinstance(date_str, pd.Timestamp):
                return date_str

            # Se for string vazia ou NaT/nan, então sim, precisamos tentar recuperar
            if pd.isna(date_str) or date_str == "" or date_str == "NaT":
                log_issue(f"Data vazia ou inválida (valor original = {date_str})")
                return None

            # Se for string com formato válido, converte
            try:
                # Primeiro tenta o formato padrão do sistema
                return pd.to_datetime(date_str, format="%d/%m/%Y %H:%M:%S")
            except:
                # Se falhar, tenta formato flexível
                try:
                    return pd.to_datetime(date_str)
                except:
                    log_issue(f"Formato de data não reconhecido: {date_str}")
                    return None

        except Exception as e:
            log_issue(f"Erro ao processar data: {str(e)}")
            return None

    def _convert_dates(self):
        """Converte e valida datas mantendo o tipo apropriado."""
        try:
            # Se a coluna já for datetime, não precisa converter
            if pd.api.types.is_datetime64_any_dtype(self.df.iloc[:, SSAColumns.EMITIDA_EM]):
                logging.info("Coluna já está em formato datetime")
                return

            # Converte diretamente para datetime usando o formato correto
            self.df.iloc[:, SSAColumns.EMITIDA_EM] = pd.to_datetime(
                self.df.iloc[:, SSAColumns.EMITIDA_EM],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce",
            )

            # Verifica se houve problemas
            invalid_mask = self.df.iloc[:, SSAColumns.EMITIDA_EM].isna()
            invalid_count = invalid_mask.sum()

            if invalid_count > 0:
                logging.error(f"Encontradas {invalid_count} datas inválidas")
                for idx in invalid_mask[invalid_mask].index:
                    logging.error(
                        f"Linha {idx + 1}: Data inválida - verificar valor original"
                    )

        except Exception as e:
            logging.error(f"Erro no processamento de datas: {str(e)}")
            raise

    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel com as configurações corretas."""
        try:
            # Carrega o Excel pulando a primeira linha (cabeçalho na segunda linha)
            self.df = pd.read_excel(
                self.excel_path,
                header=1,  # Cabeçalho na segunda linha
            )

            # NOVO: Diagnóstico de datas antes da conversão
            date_diagnosis = diagnose_dates(self.df, SSAColumns.EMITIDA_EM)
            if date_diagnosis['error_count'] > 0:
                logging.info("=== Diagnóstico de Datas ===")
                logging.info(f"Total de linhas: {date_diagnosis['total_rows']}")
                logging.info(f"Problemas encontrados: {date_diagnosis['error_count']}")
                for prob in date_diagnosis['problematic_rows']:
                    logging.info(f"\nLinha {prob['index'] + 1}:")
                    logging.info(f"  Valor encontrado: {prob['value']}")
                    logging.info(f"  Motivo: {prob['reason']}")
                    logging.info("  Dados da linha:")
                    for key, value in prob['row_data'].items():
                        logging.info(f"    {key}: {value}")

            # Converte as datas usando o novo método
            self._convert_dates()

            # Converte colunas string
            string_columns = [
                SSAColumns.NUMERO_SSA,
                SSAColumns.SITUACAO,
                SSAColumns.SEMANA_CADASTRO,
                SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                SSAColumns.SETOR_EXECUTOR,
                SSAColumns.DERIVADA,
                SSAColumns.LOCALIZACAO,
                SSAColumns.DESC_LOCALIZACAO,
                SSAColumns.EQUIPAMENTO,
                SSAColumns.DESC_SSA,
                SSAColumns.SETOR_EMISSOR,
                SSAColumns.SOLICITANTE,
                SSAColumns.SERVICO_ORIGEM,
                SSAColumns.EXECUCAO_SIMPLES,
                SSAColumns.SISTEMA_ORIGEM,
                SSAColumns.ANOMALIA,
            ]

            for col in string_columns:
                try:
                    self.df.iloc[:, col] = (
                        self.df.iloc[:, col]
                        .astype(str)
                        .str.strip()
                        .replace("nan", "")
                    )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna {col}: {str(e)}")

            # Padroniza prioridades para maiúsculas
            self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO] = (
                self.df.iloc[:, SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                .str.upper()
                .str.strip()
            )

            # Converte colunas opcionais
            optional_string_columns = [
                SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO,
                SSAColumns.RESPONSAVEL_PROGRAMACAO,
                SSAColumns.SEMANA_PROGRAMADA,
                SSAColumns.RESPONSAVEL_EXECUCAO,
                SSAColumns.DESCRICAO_EXECUCAO,
            ]

            for col in optional_string_columns:
                try:
                    self.df.iloc[:, col] = (
                        self.df.iloc[:, col]
                        .astype(str)
                        .replace("nan", None)
                        .replace("", None)
                    )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna opcional {col}: {str(e)}")

            # Remove linhas com número da SSA vazio
            self.df = self.df[self.df.iloc[:, SSAColumns.NUMERO_SSA].str.strip() != ""]

            # Trata semana cadastro e programada
            try:
                # Trata semana cadastro
                self.df.iloc[:, SSAColumns.SEMANA_CADASTRO] = (
                    pd.to_numeric(
                        self.df.iloc[:, SSAColumns.SEMANA_CADASTRO], 
                        errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                    .str.zfill(6)  # Garante 6 dígitos (AAASS)
                )

                # Trata semana programada
                self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA] = (
                    pd.to_numeric(
                        self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA], 
                        errors="coerce"
                    )
                    .fillna(0)
                    .astype(int)
                    .astype(str)
                    .str.zfill(6)
                )
                self.df.iloc[:, SSAColumns.SEMANA_PROGRAMADA] = self.df.iloc[
                    :, SSAColumns.SEMANA_PROGRAMADA
                ].replace("000000", None)

            except Exception as e:
                logging.error(f"Erro ao formatar semanas: {str(e)}")

            # Converte para objetos SSAData
            self._convert_to_objects()

            # Verifica a qualidade dos dados após todas as conversões
            self._validate_data_quality()

            return self.df

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def _validate_data_quality(self):
        """Valida a qualidade dos dados após as conversões."""
        issues = []

        # Verifica datas válidas
        valid_dates = self.df.iloc[:, SSAColumns.EMITIDA_EM].notna().sum()
        total_rows = len(self.df)
        if valid_dates < total_rows:
            diff = total_rows - valid_dates
            issues.append(
                f"{diff} data{'s' if diff > 1 else ''} inválida{'s' if diff > 1 else ''}"
            )

        # Verifica campos obrigatórios vazios
        for col in [
            SSAColumns.NUMERO_SSA,
            SSAColumns.SITUACAO,
            SSAColumns.GRAU_PRIORIDADE_EMISSAO,
        ]:
            empty_count = self.df.iloc[:, col].isna().sum()
            if empty_count > 0:
                issues.append(
                    f"{empty_count} {SSAColumns.get_name(col)} vazio{'s' if empty_count > 1 else ''}"
                )

        # Registra todos os problemas em uma única mensagem
        if issues:
            logging.warning("Problemas encontrados nos dados: " + "; ".join(issues))

    def _convert_to_objects(self):
        """Converte as linhas do DataFrame em objetos SSAData."""
        try:
            self.ssa_objects = []
            for idx, row in self.df.iterrows():
                try:
                    ssa = SSAData(
                        numero=str(row.iloc[SSAColumns.NUMERO_SSA]).strip(),
                        situacao=str(row.iloc[SSAColumns.SITUACAO]).strip(),
                        derivada=str(row.iloc[SSAColumns.DERIVADA]).strip() or None,
                        localizacao=str(row.iloc[SSAColumns.LOCALIZACAO]).strip(),
                        desc_localizacao=str(row.iloc[SSAColumns.DESC_LOCALIZACAO]).strip(),
                        equipamento=str(row.iloc[SSAColumns.EQUIPAMENTO]).strip(),
                        semana_cadastro=str(row.iloc[SSAColumns.SEMANA_CADASTRO]).strip(),
                        emitida_em=row.iloc[SSAColumns.EMITIDA_EM]
                            if pd.notna(row.iloc[SSAColumns.EMITIDA_EM])
                            else None,
                        descricao=str(row.iloc[SSAColumns.DESC_SSA]).strip(),
                        setor_emissor=str(row.iloc[SSAColumns.SETOR_EMISSOR]).strip(),
                        setor_executor=str(row.iloc[SSAColumns.SETOR_EXECUTOR]).strip(),
                        solicitante=str(row.iloc[SSAColumns.SOLICITANTE]).strip(),
                        servico_origem=str(row.iloc[SSAColumns.SERVICO_ORIGEM]).strip(),
                        prioridade_emissao=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_EMISSAO]
                        ).strip().upper(),
                        prioridade_planejamento=str(
                            row.iloc[SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO]
                        ).strip() or None,
                        execucao_simples=str(row.iloc[SSAColumns.EXECUCAO_SIMPLES]).strip(),
                        responsavel_programacao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_PROGRAMACAO]
                        ).strip() or None,
                        semana_programada=str(
                            row.iloc[SSAColumns.SEMANA_PROGRAMADA]
                        ).strip() or None,
                        responsavel_execucao=str(
                            row.iloc[SSAColumns.RESPONSAVEL_EXECUCAO]
                        ).strip() or None,
                        descricao_execucao=str(
                            row.iloc[SSAColumns.DESCRICAO_EXECUCAO]
                        ).strip() or None,
                        sistema_origem=str(row.iloc[SSAColumns.SISTEMA_ORIGEM]).strip(),
                        anomalia=str(row.iloc[SSAColumns.ANOMALIA]).strip() or None,
                    )
                    self.ssa_objects.append(ssa)
                except Exception as e:
                    logging.error(f"Erro ao converter linha {idx}: {str(e)}")
                    continue

            logging.info(f"Convertidos {len(self.ssa_objects)} registros para SSAData")

            # Log exemplo do primeiro objeto convertido para verificação
            if self.ssa_objects:
                first_ssa = self.ssa_objects[0]
                logging.info(f"Exemplo de primeiro objeto convertido:")
                logging.info(f"Número: {first_ssa.numero}")
                logging.info(f"Data de emissão: {first_ssa.emitida_em}")
                logging.info(f"Prioridade: {first_ssa.prioridade_emissao}")

        except Exception as e:
            logging.error(f"Erro durante conversão para objetos: {str(e)}")
            raise

    def get_ssa_objects(self) -> List[SSAData]:
        """Retorna a lista de objetos SSAData."""
        if not self.ssa_objects:
            self._convert_to_objects()
        return self.ssa_objects

    def filter_ssas(
        self,
        setor: str = None,
        prioridade: str = None,
        data_inicio: datetime = None,
        data_fim: datetime = None,
    ) -> List[SSAData]:
        """Filtra SSAs com base nos critérios fornecidos."""
        filtered_ssas = self.get_ssa_objects()

        if setor:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.setor_executor and ssa.setor_executor.upper() == setor.upper()
            ]

        if prioridade:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.prioridade_emissao
                and ssa.prioridade_emissao.upper() == prioridade.upper()
            ]

        if data_inicio:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.emitida_em and ssa.emitida_em >= data_inicio
            ]

        if data_fim:
            filtered_ssas = [
                ssa
                for ssa in filtered_ssas
                if ssa.emitida_em and ssa.emitida_em <= data_fim
            ]

        return filtered_ssas
