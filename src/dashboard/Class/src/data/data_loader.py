# src/data/data_loader.py
import pandas as pd
import warnings
import logging
import traceback
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import unicodedata
from ..utils.date_utils import diagnose_dates
from .ssa_data import SSAData
from .ssa_columns import SSAColumns
from ..utils.data_validator import SSADataValidator


class DataLoader:
    """Carrega e prepara os dados das SSAs."""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.ssa_objects = []
        self.validator = SSADataValidator()
        self._col_labels = {}  # Mapeia índice SSAColumns -> rótulo real no DF
        # self.file_manager = FileManager(os.path.dirname(excel_path)) # Evitar ref circular

    # -----------------------
    # Helpers de normalização
    # -----------------------
    def _normalize_label(self, s: str) -> str:
        s = str(s or "").strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return "".join(ch for ch in s if ch.isalnum())

    def _synonyms(self) -> Dict[int, List[str]]:
        return {
            SSAColumns.NUMERO_SSA: [
                "numero",
                "numerodassa",
                "nssa",
                "nossa",
                "nºssa",
                "ssa",
                "numeroordem",
            ],
            SSAColumns.EMITIDA_EM: [
                "emitidaem",
                "dataemissao",
                "dataemissao",
                "data",
                "dtemissao",
                "dtem",
                "emissao",
            ],
            SSAColumns.GRAU_PRIORIDADE_EMISSAO: [
                "graudeprioridade",
                "prioridade",
                "prioridadeemissao",
            ],
            SSAColumns.SETOR_EXECUTOR: [
                "setorexecutor",
                "setorexec",
                "executora",
                "areaexecutora",
                "executor",
            ],
            SSAColumns.SEMANA_CADASTRO: [
                "semanacadastro",
                "semana",
                "semanadecadastro",
            ],
            SSAColumns.SEMANA_PROGRAMADA: [
                "semanaprogramada",
                "semanaprog",
                "programada",
            ],
        }

    def _detect_header_row(self, max_rows: int = 25) -> int:
        """Detecta automaticamente a linha de cabeçalho no Excel.

        Estratégia: lê as primeiras linhas sem cabeçalho e escolhe a linha
        com maior cobertura de nomes esperados/sinônimos.
        """
        try:
            tmp = pd.read_excel(self.excel_path, header=None, nrows=max_rows)
        except Exception:
            # fallback seguro
            return 1

        # prepara conjunto de chaves esperadas normalizadas
        expected = {self._normalize_label(n) for n in SSAColumns.COLUMN_NAMES.values()}
        for idx, alts in self._synonyms().items():
            expected.update({self._normalize_label(a) for a in alts})

        best_row = 1
        best_score = -1
        for i in range(min(len(tmp), max_rows)):
            row_vals = [self._normalize_label(v) for v in list(tmp.iloc[i].values)]
            if not any(row_vals):
                continue
            score = sum(1 for v in row_vals if v in expected)
            if score > best_score:
                best_score = score
                best_row = i

        # Se cobertura muito baixa, mantém padrão 1 (linha 1 = segunda linha zero-based)
        return int(best_row)

    def _infer_columns_from_data(self, sample_rows: int = 200) -> None:
        """Para planilhas sem cabeçalho, infere colunas-chave por padrão de dados.

        Atualiza self._col_labels para índices ainda não resolvidos:
        - Número SSA: valores tipo 'SSA-1234'
        - Prioridade Emissão: valores tipo 'S3.7', 'S3', 'S4.0'
        - Emitida Em: valores parseáveis como datetime
        - Semana Cadastro: valores 6 dígitos (ex: 202534)
        - Situação: códigos 3 letras conhecidos (APL, APG, AAD, ...)
        """
        if self.df is None:
            return
        df = self.df.head(sample_rows)
        cols = list(df.columns)

        def frac(series, cond):
            s = series.astype(str)
            total = max(len(s), 1)
            return (cond(s)).sum() / total

        # Helper condicoes
        import re
        state_keys = set(SSAColumns.STATE_DESCRIPTIONS.keys())

        def is_numero(s: pd.Series):
            return s.str.match(r"^ssa-?\d+\b", case=False, na=False)

        def is_prioridade(s: pd.Series):
            return s.str.match(r"^s\d(\.\d)?$", case=False, na=False)

        def is_semana(s: pd.Series):
            return s.str.match(r"^[12]\d{5}$", na=False)

        def is_situacao(s: pd.Series):
            return s.str.upper().isin(state_keys)

        def is_datetime_like(series: pd.Series):
            try:
                # Silence pandas format inference warnings during heuristic probing
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
                return parsed.notna()
            except Exception:
                return pd.Series([False] * len(series))

        # Avoid duplicate assignment
        assigned = set()
        current = dict(self._col_labels)

        # Compute scores for each column
        scores = {}
        for c in cols:
            s = df[c]
            scores[c] = {
                "numero": frac(s, is_numero),
                "prioridade": frac(s, is_prioridade),
                "semana": frac(s, is_semana),
                "situacao": frac(s, is_situacao),
                "datetime": is_datetime_like(s).mean(),
            }

        # Select best candidates above thresholds
        def best_col(key, threshold):
            cand = [
                (c, sc[key]) for c, sc in scores.items() if sc[key] >= threshold and c not in assigned
            ]
            if not cand:
                return None
            cand.sort(key=lambda x: x[1], reverse=True)
            assigned.add(cand[0][0])
            return cand[0][0]

        # Only fill if not already mapped
        if self._get_label(SSAColumns.NUMERO_SSA) is None:
            col = best_col("numero", 0.3)
            if col is not None:
                self._col_labels[SSAColumns.NUMERO_SSA] = col

        if self._get_label(SSAColumns.GRAU_PRIORIDADE_EMISSAO) is None:
            col = best_col("prioridade", 0.3)
            if col is not None:
                self._col_labels[SSAColumns.GRAU_PRIORIDADE_EMISSAO] = col

        if self._get_label(SSAColumns.EMITIDA_EM) is None:
            col = best_col("datetime", 0.3)
            if col is not None:
                self._col_labels[SSAColumns.EMITIDA_EM] = col

        if self._get_label(SSAColumns.SEMANA_CADASTRO) is None:
            col = best_col("semana", 0.4)
            if col is not None:
                self._col_labels[SSAColumns.SEMANA_CADASTRO] = col

        if self._get_label(SSAColumns.SITUACAO) is None:
            col = best_col("situacao", 0.3)
            if col is not None:
                self._col_labels[SSAColumns.SITUACAO] = col

    def validate_and_fix_date(self, date_str, row_num, logger=None):
        """
        Valida e corrige valores de data apenas quando necessário.
        """
        # usa pandas importado no módulo

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
        """Converte e valida datas mantendo o tipo apropriado e dtype consistente."""
        try:
            if self.df is None:
                raise ValueError("DataFrame não carregado antes da conversão de datas")
            col_label = self._get_label(SSAColumns.EMITIDA_EM)
            if (col_label is None) or (col_label not in self.df.columns):
                logging.warning("Coluna 'Emitida Em' ausente; pulando conversão de datas")
                return
            # Converte diretamente para datetime usando o formato correto; always enforce dtype
            converted = pd.to_datetime(
                self.df[col_label],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce",
                dayfirst=True,
            )
            # Ensure dtype is datetime64[ns]
            self.df[col_label] = converted.astype("datetime64[ns]")

            # Verifica se houve problemas
            invalid_mask = self.df[col_label].isna()
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

    def _to_canonical_dataframe(self):
        """Reorganiza o DataFrame para a ordem canônica de colunas baseada em SSAColumns.

        - Garante que df tenha todas as colunas esperadas nas posições corretas
        - Preenche colunas ausentes com valores padrão seguros
        - Mantém os tipos básicos (datetime para EMITIDA_EM, strings para demais)
        """
        if self.df is None:
            return

        n = len(self.df)
        canonical_cols = []
        data = {}

        # Helpers de defaults por tipo esperado
        def default_series(idx: int):
            expected = SSAColumns.COLUMN_TYPES.get(idx)
            if expected == "datetime64[ns]":
                return pd.Series([pd.NaT] * n, dtype="datetime64[ns]")
            # default string
            return pd.Series([""] * n, dtype="object")

        # Ordem canônica: pelos índices definidos
        for idx in sorted(SSAColumns.COLUMN_NAMES.keys()):
            lbl = self._get_label(idx)
            if lbl is not None and lbl in self.df.columns:
                s = self.df[lbl]
            else:
                s = default_series(idx)

            # Ajuste de dtype mínimo
            expected = SSAColumns.COLUMN_TYPES.get(idx)
            if expected == "datetime64[ns]":
                try:
                    s = pd.to_datetime(s, errors="coerce")
                except Exception:
                    s = default_series(idx)
            else:
                # força para string segura
                s = s.astype("string").fillna("").astype("object")

            data[idx] = s
            canonical_cols.append(idx)

        # Cria novo DF com as colunas na ordem desejada
        new_df = pd.DataFrame({i: data[i] for i in canonical_cols})
        # Substitui
        self.df = new_df

    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel com as configurações corretas."""
        try:
            # Inicializa validador se ainda não existe
            if not hasattr(self, "validator"):
                self.validator = SSADataValidator()

            logging.info(f"Iniciando carregamento do arquivo: {self.excel_path}")

            # Detecta automaticamente a linha de cabeçalho
            header_row = self._detect_header_row()
            self.df = pd.read_excel(
                self.excel_path,
                header=header_row,
            )

            logging.info(f"Arquivo carregado. Total de linhas: {len(self.df)}")

            # Constrói mapeamento de colunas esperadas -> rótulos reais
            self._build_column_mapping()

            # Verifica cobertura de colunas essenciais; se muito baixa, tenta modo posicional (planilha sem cabeçalho)
            required = [
                SSAColumns.NUMERO_SSA,
                SSAColumns.SITUACAO,
                SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                SSAColumns.EMITIDA_EM,
                SSAColumns.SETOR_EXECUTOR,
            ]
            coverage = sum(1 for r in required if self._get_label(r) in getattr(self.df, 'columns', []))
            if coverage <= 2:
                logging.warning("Cobertura baixa de colunas esperadas; assumindo planilha sem cabeçalho e usando mapeamento posicional")
                # Recarrega sem cabeçalho para não perder a primeira linha de dados
                self.df = pd.read_excel(self.excel_path, header=None)
                # Mapeia índices esperados para posições
                self._col_labels = {}
                for idx in SSAColumns.COLUMN_NAMES.keys():
                    if idx < self.df.shape[1]:
                        self._col_labels[idx] = self.df.columns[idx]
                logging.info(f"Mapeamento posicional aplicado para {len(self._col_labels)} colunas")
                # Tenta inferir rótulos-chave baseado nos dados
                self._infer_columns_from_data()
                # Normalizações mínimas para colunas-chave
                for key_idx in [
                    SSAColumns.NUMERO_SSA,
                    SSAColumns.SITUACAO,
                    SSAColumns.GRAU_PRIORIDADE_EMISSAO,
                    SSAColumns.SETOR_EXECUTOR,
                ]:
                    lbl = self._get_label(key_idx)
                    if lbl in self.df.columns:
                        self.df[lbl] = self.df[lbl].astype(str).str.strip()

            # Diagnóstico inicial de datas (se a coluna existir)
            em_label = self._get_label(SSAColumns.EMITIDA_EM)
            if (em_label is not None) and (em_label in self.df.columns):
                # Resolve integer index robustly even if duplicate columns exist
                try:
                    idx_arr = self.df.columns.get_indexer_for([em_label])
                    if len(idx_arr) == 1 and idx_arr[0] != -1:
                        date_col_index = int(idx_arr[0])
                    else:
                        # Se colunas são inteiras, o próprio label pode ser o índice
                        date_col_index = int(em_label) if isinstance(em_label, int) else None
                except Exception:
                    date_col_index = int(em_label) if isinstance(em_label, int) else None
                date_diagnosis = None
                if date_col_index is not None:
                    date_diagnosis = diagnose_dates(self.df, date_col_index)
                if date_diagnosis and date_diagnosis["error_count"] > 0:
                    logging.info("=== Diagnóstico de Datas ===")
                    logging.info(f"Total de linhas: {date_diagnosis['total_rows']}")
                    logging.info(f"Problemas encontrados: {date_diagnosis['error_count']}")
                    for prob in date_diagnosis["problematic_rows"]:
                        logging.info(f"\nLinha {prob['index'] + 1}:")
                        logging.info(f"  Valor encontrado: {prob['value']}")
                        logging.info(f"  Motivo: {prob['reason']}")
                        logging.info("  Dados da linha:")
                        for key, value in prob["row_data"].items():
                            logging.info(f"    {key}: {value}")

            # Converte as datas
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
                    label = self._get_label(col)
                    if (label is not None) and (label in self.df.columns):
                        self.df[label] = (
                            self.df[label].astype(str).str.strip().replace("nan", "")
                        )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna {col}: {str(e)}")

            # Padroniza prioridades para maiúsculas
            pri_label = self._get_label(SSAColumns.GRAU_PRIORIDADE_EMISSAO)
            if (pri_label is not None) and (pri_label in self.df.columns):
                self.df[pri_label] = self.df[pri_label].str.upper().str.strip()

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
                    label = self._get_label(col)
                    if (label is not None) and (label in self.df.columns):
                        self.df[label] = (
                            self.df[label].astype(str).replace("nan", None).replace("", None)
                        )
                except Exception as e:
                    logging.error(f"Erro ao converter coluna opcional {col}: {str(e)}")

            # Remove linhas com número da SSA vazio
            num_label = self._get_label(SSAColumns.NUMERO_SSA)
            if (num_label is not None) and (num_label in self.df.columns):
                empty_ssa_count = (self.df[num_label].astype(str).str.strip() == "").sum()
                if empty_ssa_count > 0:
                    logging.warning(
                        f"Removendo {empty_ssa_count} linhas com número de SSA vazio"
                    )
                self.df = self.df[self.df[num_label].astype(str).str.strip() != ""]

            # Trata semana cadastro e programada
            try:
                # Trata semana cadastro
                cad_label = self._get_label(SSAColumns.SEMANA_CADASTRO)
                if (cad_label is not None) and (cad_label in self.df.columns):
                    self.df[cad_label] = (
                        pd.to_numeric(self.df[cad_label], errors="coerce")
                        .fillna(0)
                        .astype(int)
                        .astype(str)
                        .str.zfill(6)  # Garante 6 dígitos (AAASS)
                    )

                # Trata semana programada
                prog_label = self._get_label(SSAColumns.SEMANA_PROGRAMADA)
                if (prog_label is not None) and (prog_label in self.df.columns):
                    self.df[prog_label] = (
                        pd.to_numeric(self.df[prog_label], errors="coerce")
                        .fillna(0)
                        .astype(int)
                        .astype(str)
                        .str.zfill(6)
                    )
                    self.df[prog_label] = self.df[prog_label].replace("000000", None)

            except Exception as e:
                logging.error(f"Erro ao formatar semanas: {str(e)}")

            # Converte para objetos SSAData
            self._convert_to_objects()

            # NOVO: Validação com o SSADataValidator
            validation_result = self.validator.validate_data_consistency(self.ssa_objects)
            if not validation_result.is_valid:
                logging.warning("=== Problemas de Consistência Encontrados ===")
                for issue in validation_result.issues:
                    logging.warning(issue)

            # NOVO: Verifica integridade dos dados
            integrity_report = self.validator.verify_data_integrity(self.ssa_objects)
            if integrity_report["warnings"]:
                logging.warning("=== Avisos de Integridade ===")
                for warning in integrity_report["warnings"]:
                    logging.warning(warning)

            # Log de estatísticas
            logging.info("=== Estatísticas do Carregamento ===")
            logging.info(f"Total de registros: {len(self.df)}")
            logging.info(f"SSAs válidas: {len(self.ssa_objects)}")
            if validation_result.statistics:
                for key, value in validation_result.statistics.items():
                    if isinstance(
                        value, (int, float, str)
                    ):  # Não loga dicionários aninhados
                        logging.info(f"{key}: {value}")

            # Verifica a qualidade dos dados após todas as conversões
            self._validate_data_quality()

            # Reorganiza para formato canônico esperado pelo dashboard (posicional)
            # Observação: fazer isso após todas as validações e conversões internas,
            # pois a partir daqui a ordem das colunas será a canônica (por índice SSAColumns)
            self._to_canonical_dataframe()

            # Verifica a qualidade dos dados após todas as conversões
            return self.df

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def _validate_data_quality(self):
        """Valida a qualidade dos dados após as conversões."""
        issues = []

        # Verifica datas válidas
        if self.df is None:
            logging.warning("DataFrame ainda não carregado para validação de qualidade.")
            return
        em_label = self._get_label(SSAColumns.EMITIDA_EM)
        valid_dates = (
            self.df[em_label].notna().sum() if em_label and em_label in self.df.columns else 0
        )
        total_rows = len(self.df)
        if valid_dates < total_rows:
            diff = total_rows - valid_dates
            issues.append(
                f"{diff} data{'s' if diff > 1 else ''} inválida{'s' if diff > 1 else ''}"
            )

        # Verifica campos obrigatórios vazios
        for col in [SSAColumns.NUMERO_SSA, SSAColumns.SITUACAO, SSAColumns.GRAU_PRIORIDADE_EMISSAO]:
            label = self._get_label(col)
            if label and label in self.df.columns:
                empty_count = self.df[label].isna().sum()
                if empty_count > 0:
                    issues.append(
                        f"{empty_count} {SSAColumns.get_name(col)} vazio{'s' if empty_count > 1 else ''}"
                    )

        # Registra todos os problemas em uma única mensagem
        if issues:
            logging.warning("Problemas encontrados nos dados: " + "; ".join(issues))

    def _convert_to_objects(self) -> int:
        """
        Converte as linhas do DataFrame em objetos SSAData.

        Returns:
            int: Número de objetos convertidos com sucesso

        Raises:
            Exception: Se houver erro durante a conversão
        """
        try:
            self.ssa_objects = []
            unique_responsaveis = set()
            unique_responsaveis_prog = set()
            conversions = {
                "exec": {"total": 0, "errors": 0},
                "prog": {"total": 0, "errors": 0},
            }

            assert self.df is not None
            for idx, row in self.df.iterrows():
                try:
                    # Helpers para recuperar valores por rótulo
                    def gv(i):
                        lbl = self._get_label(i)
                        if lbl is None:
                            return None
                        # row is a Series: membership checks column label presence
                        return row[lbl] if (lbl in row.index or lbl in row) else None

                    # Processamento do responsável execução
                    raw_resp = gv(SSAColumns.RESPONSAVEL_EXECUCAO)
                    responsavel = str(raw_resp).strip() if raw_resp is not None else ""
                    if responsavel.lower() in ["nan", "none", ""]:
                        responsavel = None
                    elif responsavel:
                        responsavel = responsavel.upper()
                        unique_responsaveis.add(responsavel)
                        conversions["exec"]["total"] += 1

                    # Processamento do responsável programação
                    raw_prog = gv(SSAColumns.RESPONSAVEL_PROGRAMACAO)
                    resp_prog = str(raw_prog).strip() if raw_prog is not None else ""
                    if resp_prog.lower() in ["nan", "none", ""]:
                        resp_prog = None
                    elif resp_prog:
                        resp_prog = resp_prog.upper()
                        unique_responsaveis_prog.add(resp_prog)
                        conversions["prog"]["total"] += 1

                    # Criação do objeto SSA
                    ssa = SSAData(
                        numero=str(gv(SSAColumns.NUMERO_SSA) or "").strip(),
                        situacao=str(gv(SSAColumns.SITUACAO) or "").strip(),
                        derivada=(str(gv(SSAColumns.DERIVADA) or "").strip() or None),
                        localizacao=str(gv(SSAColumns.LOCALIZACAO) or "").strip(),
                        desc_localizacao=str(gv(SSAColumns.DESC_LOCALIZACAO) or "").strip(),
                        equipamento=str(gv(SSAColumns.EQUIPAMENTO) or "").strip(),
                        semana_cadastro=str(gv(SSAColumns.SEMANA_CADASTRO) or "").strip(),
                        emitida_em=(gv(SSAColumns.EMITIDA_EM) if pd.notna(gv(SSAColumns.EMITIDA_EM)) else None),
                        descricao=str(gv(SSAColumns.DESC_SSA) or "").strip(),
                        setor_emissor=str(gv(SSAColumns.SETOR_EMISSOR) or "").strip(),
                        setor_executor=str(gv(SSAColumns.SETOR_EXECUTOR) or "").strip(),
                        solicitante=str(gv(SSAColumns.SOLICITANTE) or "").strip(),
                        servico_origem=str(gv(SSAColumns.SERVICO_ORIGEM) or "").strip(),
                        prioridade_emissao=str(gv(SSAColumns.GRAU_PRIORIDADE_EMISSAO) or "").strip().upper(),
                        prioridade_planejamento=(str(gv(SSAColumns.GRAU_PRIORIDADE_PLANEJAMENTO) or "").strip() or None),
                        execucao_simples=str(gv(SSAColumns.EXECUCAO_SIMPLES) or "").strip(),
                        responsavel_programacao=resp_prog,  # Já processado acima
                        semana_programada=(str(gv(SSAColumns.SEMANA_PROGRAMADA) or "").strip() or None),
                        responsavel_execucao=responsavel,  # Já processado acima, não é mais tupla
                        descricao_execucao=(str(gv(SSAColumns.DESCRICAO_EXECUCAO) or "").strip() or None),
                        sistema_origem=str(gv(SSAColumns.SISTEMA_ORIGEM) or "").strip(),
                        anomalia=(str(gv(SSAColumns.ANOMALIA) or "").strip() or None),
                    )
                    self.ssa_objects.append(ssa)

                except Exception as e:
                    logging.error(f"Erro ao converter linha {idx}: {str(e)}")
                    if responsavel:
                        conversions["exec"]["errors"] += 1
                    if resp_prog:
                        conversions["prog"]["errors"] += 1
                    continue

            # Log de estatísticas e validações
            logging.info("=== Estatísticas de Conversão ===")
            logging.info(f"Total de registros convertidos: {len(self.ssa_objects)}")
            logging.info(f"Responsáveis execução únicos: {len(unique_responsaveis)}")
            logging.info(
                f"Responsáveis programação únicos: {len(unique_responsaveis_prog)}"
            )

            # Validação detalhada de responsáveis
            if self.ssa_objects:
                self._log_responsaveis_detalhes(
                    unique_responsaveis, unique_responsaveis_prog
                )
                self._log_primeiro_objeto()

            # Log de erros de conversão
            if conversions["exec"]["errors"] > 0 or conversions["prog"]["errors"] > 0:
                logging.warning("\n=== Erros de Conversão ===")
                logging.warning(
                    f"Erros em responsável execução: {conversions['exec']['errors']}"
                )
                logging.warning(
                    f"Erros em responsável programação: {conversions['prog']['errors']}"
                )

            return len(self.ssa_objects)

        except Exception as e:
            logging.error(f"Erro durante conversão para objetos: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def _log_responsaveis_detalhes(
        self, unique_responsaveis: set, unique_responsaveis_prog: set
    ):
        """Log detalhado dos responsáveis."""
        logging.info("\n=== Validação de Responsáveis Execução ===")
        for resp in sorted(unique_responsaveis):
            ssas_resp = [
                ssa
                for ssa in self.ssa_objects
                if ssa.responsavel_execucao and ssa.responsavel_execucao.upper() == resp
            ]
            logging.info(f"\nResponsável Execução: '{resp}'")
            logging.info(f"Total SSAs: {len(ssas_resp)}")
            logging.info("Números das SSAs:")
            for ssa in ssas_resp:
                logging.info(f"  - SSA {ssa.numero}: {ssa.situacao}")

        logging.info("\n=== Validação de Responsáveis Programação ===")
        for resp in sorted(unique_responsaveis_prog):
            ssas_resp = [
                ssa
                for ssa in self.ssa_objects
                if ssa.responsavel_programacao
                and ssa.responsavel_programacao.upper() == resp
            ]
            logging.info(f"\nResponsável Programação: '{resp}'")
            logging.info(f"Total SSAs: {len(ssas_resp)}")
            logging.info("Números das SSAs:")
            for ssa in ssas_resp:
                logging.info(f"  - SSA {ssa.numero}: {ssa.situacao}")

    def _log_primeiro_objeto(self):
        """Log do primeiro objeto para verificação."""
        first_ssa = self.ssa_objects[0]
        logging.info("\n=== Primeiro Objeto Convertido (Verificação) ===")
        logging.info(f"Número: {first_ssa.numero}")
        logging.info(f"Data de emissão: {first_ssa.emitida_em}")
        logging.info(f"Prioridade: {first_ssa.prioridade_emissao}")
        logging.info(f"Setor executor: {first_ssa.setor_executor}")
        logging.info(f"Responsável execução: {first_ssa.responsavel_execucao}")
        logging.info(f"Responsável programação: {first_ssa.responsavel_programacao}")

    def get_ssa_objects(self) -> List[SSAData]:
        """Retorna a lista de objetos SSAData."""
        if not self.ssa_objects:
            self._convert_to_objects()
        return self.ssa_objects

    def _build_column_mapping(self):
        """Mapeia os índices de SSAColumns para os rótulos reais das colunas no DataFrame."""
        self._col_labels = {}
        if self.df is None:
            return
        existing = list(self.df.columns)
        # Tabela de normalizacao -> rótulo original
        norm_existing = {self._normalize_label(c): c for c in existing}
        synonyms = self._synonyms()

        for idx, expected in SSAColumns.COLUMN_NAMES.items():
            label = None
            expected_key = self._normalize_label(expected)

            # 1) Match exato normalizado
            if expected_key in norm_existing:
                label = norm_existing[expected_key]
            else:
                # 2) Tenta sinônimos
                for alt in synonyms.get(idx, []):
                    key = self._normalize_label(alt)
                    if key in norm_existing:
                        label = norm_existing[key]
                        break
                # 3) Fallback: varredura case-insensitive simples (para compatibilidade antiga)
                if not label:
                    for c in existing:
                        if str(c).strip().lower() == str(expected).strip().lower():
                            label = c
                            break

            self._col_labels[idx] = label

    def _get_label(self, idx: int) -> Optional[str]:
        """Retorna o rótulo real da coluna para um índice SSAColumns, se existente."""
        return self._col_labels.get(idx)

    def filter_ssas(
        self,
        setor: Optional[str] = None,
        prioridade: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> Tuple[List[SSAData], Optional[Dict]]:
        """
        Filtra SSAs com base nos critérios fornecidos.

        Args:
            setor: Setor para filtrar
            prioridade: Prioridade para filtrar
            data_inicio: Data inicial do período
            data_fim: Data final do período

        Returns:
            Tupla contendo (lista de SSAs filtradas, dicionário de diagnóstico)

        Raises:
            ValueError: Se os tipos de dados fornecidos forem inválidos
        """
        try:
            filtered_ssas = self.get_ssa_objects()
            diagnostico = None

            # Validação de tipos
            if setor is not None and not isinstance(setor, str):
                raise ValueError(f"Setor deve ser string, recebido {type(setor)}")
            if prioridade is not None and not isinstance(prioridade, str):
                raise ValueError(
                    f"Prioridade deve ser string, recebido {type(prioridade)}"
                )
            if data_inicio is not None and not isinstance(data_inicio, datetime):
                raise ValueError(
                    f"Data início deve ser datetime, recebido {type(data_inicio)}"
                )
            if data_fim is not None and not isinstance(data_fim, datetime):
                raise ValueError(
                    f"Data fim deve ser datetime, recebido {type(data_fim)}"
                )

            # Filtro por setor com validação melhorada
            if setor:
                setor = setor.strip().upper()
                filtered_ssas = [
                    ssa
                    for ssa in filtered_ssas
                    if ssa.setor_executor
                    and ssa.setor_executor.strip().upper() == setor
                ]
                logging.info(f"Filtro por setor '{setor}': {len(filtered_ssas)} SSAs")

            # Filtro por prioridade
            if prioridade:
                prioridade = prioridade.strip().upper()
                filtered_ssas = [
                    ssa
                    for ssa in filtered_ssas
                    if ssa.prioridade_emissao
                    and ssa.prioridade_emissao.strip().upper() == prioridade
                ]
                logging.info(
                    f"Filtro por prioridade '{prioridade}': {len(filtered_ssas)} SSAs"
                )

            # Filtro por data inicial
            if data_inicio:
                filtered_ssas = [
                    ssa
                    for ssa in filtered_ssas
                    if ssa.emitida_em and ssa.emitida_em >= data_inicio
                ]
                logging.info(
                    f"Filtro por data início {data_inicio}: {len(filtered_ssas)} SSAs"
                )

            # Filtro por data final
            if data_fim:
                filtered_ssas = [
                    ssa
                    for ssa in filtered_ssas
                    if ssa.emitida_em and ssa.emitida_em <= data_fim
                ]
                logging.info(
                    f"Filtro por data fim {data_fim}: {len(filtered_ssas)} SSAs"
                )

            # Diagnóstico após todos os filtros
            if filtered_ssas:
                diagnostico = self.validator.diagnose_responsavel_data(
                    filtered_ssas, setor or ""
                )
                logging.info("=== Diagnóstico após Filtros ===")
                logging.info(f"Total de SSAs filtradas: {len(filtered_ssas)}")
                logging.info("Responsáveis na Execução:")
                for resp, dados in diagnostico["por_responsavel_exec"].items():
                    logging.info(f"  - {resp}: {dados['total']} SSAs")
                    logging.info(f"    Números: {', '.join(dados['ssas'])}")

                if diagnostico.get("por_responsavel_prog"):
                    logging.info("Responsáveis na Programação:")
                    for resp, dados in diagnostico["por_responsavel_prog"].items():
                        logging.info(f"  - {resp}: {dados['total']} SSAs")
                        logging.info(f"    Números: {', '.join(dados['ssas'])}")

            return filtered_ssas, diagnostico

        except Exception as e:
            logging.error(f"Erro durante filtragem: {str(e)}")
            logging.error(traceback.format_exc())
            raise
