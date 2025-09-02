from typing import Dict
import pandas as pd
from datetime import datetime


def diagnose_dates(df: pd.DataFrame, date_column_index: int) -> Dict:
    """
    Diagnostica problemas com datas em um DataFrame.

    Args:
        df: DataFrame com os dados
        date_column_index: índice da coluna de data

    Returns:
        Dict com informações de diagnóstico
        {
            'total_rows': número total de linhas,
            'problematic_rows': lista de dicionários com detalhes dos problemas,
            'error_count': número total de erros,
            'error_details': detalhamento dos tipos de erro
        }
    """
    problematic_rows = []

    for idx, row in df.iterrows():
        date_value = row.iloc[date_column_index]
        try:
            # Verifica valores nulos
            if pd.isna(date_value):
                problematic_rows.append(
                    {
                        "index": idx,
                        "value": date_value,
                        "reason": "Valor nulo ou NaN",
                        "row_data": row.to_dict(),
                    }
                )
            # Verifica strings que deveriam ser datas
            elif isinstance(date_value, str):
                try:
                    pd.to_datetime(date_value, dayfirst=True)
                    pd.to_datetime(date_value)
                except Exception as e:
                    problematic_rows.append(
                        {
                            "index": idx,
                            "value": date_value,
                            "reason": f"Erro na conversão: {str(e)}",
                            "row_data": row.to_dict(),
                        }
                    )
            # Verifica se é um tipo válido de data
            elif not isinstance(date_value, (pd.Timestamp, datetime)):
                problematic_rows.append(
                    {
                        "index": idx,
                        "value": date_value,
                        "reason": f"Tipo inválido: {type(date_value)}",
                        "row_data": row.to_dict(),
                    }
                )
            # Verifica se a data está em um intervalo razoável (últimos 30 anos até 1 ano futuro)
            elif isinstance(date_value, (pd.Timestamp, datetime)):
                now = pd.Timestamp.now()
                min_date = now - pd.DateOffset(years=30)
                max_date = now + pd.DateOffset(years=1)

                if not (min_date <= date_value <= max_date):
                    problematic_rows.append(
                        {
                            "index": idx,
                            "value": date_value,
                            "reason": "Data fora do intervalo esperado",
                            "row_data": row.to_dict(),
                        }
                    )

        except Exception as e:
            problematic_rows.append(
                {
                    "index": idx,
                    "value": date_value,
                    "reason": f"Erro não esperado: {str(e)}",
                    "row_data": row.to_dict(),
                }
            )

    # Agrupa os erros por tipo
    error_types = {
        "null_count": sum(
            1 for row in problematic_rows if "nulo" in row["reason"].lower()
        ),
        "format_errors": sum(
            1 for row in problematic_rows if "conversão" in row["reason"].lower()
        ),
        "type_errors": sum(
            1 for row in problematic_rows if "tipo" in row["reason"].lower()
        ),
        "range_errors": sum(
            1 for row in problematic_rows if "intervalo" in row["reason"].lower()
        ),
        "other_errors": sum(
            1
            for row in problematic_rows
            if not any(
                x in row["reason"].lower()
                for x in ["nulo", "conversão", "tipo", "intervalo"]
            )
        ),
    }

    return {
        "total_rows": len(df),
        "problematic_rows": problematic_rows,
        "error_count": len(problematic_rows),
        "error_details": error_types,
        "error_rate": (len(problematic_rows) / len(df) * 100) if len(df) > 0 else 0,
    }


def validate_date_value(date_value) -> Dict:
    """
    Valida um valor de data específico.

    Args:
        date_value: valor a ser validado

    Returns:
        Dict com resultado da validação
        {
            'is_valid': bool,
            'value': valor convertido ou None,
            'error': mensagem de erro se houver
        }
    """
    try:
        if pd.isna(date_value):
            return {"is_valid": False, "value": None, "error": "Valor nulo"}

        if isinstance(date_value, (pd.Timestamp, datetime)):
            return {"is_valid": True, "value": date_value, "error": None}

        # Tenta converter string para data
        if isinstance(date_value, str):
            try:
                # Primeiro tenta formato específico
                converted = pd.to_datetime(date_value, format="%d/%m/%Y %H:%M:%S")
                return {"is_valid": True, "value": converted, "error": None}
            except:
                # Se falhar, tenta formato flexível
                try:
                    converted = pd.to_datetime(date_value)
                    return {"is_valid": True, "value": converted, "error": None}
                except Exception as e:
                    return {
                        "is_valid": False,
                        "value": None,
                        "error": f"Formato inválido: {str(e)}",
                    }

        return {
            "is_valid": False,
            "value": None,
            "error": f"Tipo inválido: {type(date_value)}",
        }

    except Exception as e:
        return {
            "is_valid": False,
            "value": None,
            "error": f"Erro não esperado: {str(e)}",
        }


def fix_date_format(date_str: str) -> str:
    """
    Tenta corrigir formatos comuns de data.

    Args:
        date_str: string da data

    Returns:
        String da data formatada ou a original se não conseguir corrigir
    """
    if not isinstance(date_str, str):
        return date_str

    try:
        # Remove espaços extras
        date_str = date_str.strip()

        # Corrige separadores
        date_str = date_str.replace("-", "/")

        # Adiciona século se ano tiver 2 dígitos
        if len(date_str) == 8 and "/" in date_str:
            day, month, year = date_str.split("/")
            if len(year) == 2:
                year = "20" + year
                date_str = f"{day}/{month}/{year}"

        # Adiciona horário se não tiver
        if len(date_str) == 10:  # Só tem a data
            date_str += " 00:00:00"

        return date_str

    except:
        return date_str
