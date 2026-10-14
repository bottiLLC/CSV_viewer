from __future__ import annotations

from pathlib import Path
from typing import Final
import pandas as pd

DEFAULT_ENCODINGS: Final[tuple[str, ...]] = ("utf-8-sig", "cp932", "utf-8")


class CsvServiceError(Exception):
    """CSV操作全般の基本ドメイン例外。"""


class CsvEncodingError(CsvServiceError):
    """サポート対象エンコーディングでのデコード失敗例外。"""


class CsvService:
    """CSV読み込み、全カラム部分一致検索、およびXLSXエクスポートを管轄するドメインサービス。

    UI層から完全に分離され、副作用のない純粋なデータ変換およびファイルI/Oを提供する。
    """

    @staticmethod
    def load_csv(file_path: Path) -> pd.DataFrame:
        """指定パスのCSVファイルをフォールバック付きで読み込みDataFrameとして取得する。

        Args:
            file_path: 読み込み対象のCSVファイルパス。

        Returns:
            読み込まれたCSVデータを含むpandas DataFrame。

        Raises:
            CsvServiceError: ファイルが存在しない、または空ファイルの場合。
            CsvEncodingError: サポート対象の文字コードでデコードできない場合。
        """
        resolved_path = file_path.resolve()
        if not resolved_path.is_file():
            raise CsvServiceError(f"指定されたファイルが存在しません: {resolved_path}")

        for encoding in DEFAULT_ENCODINGS:
            try:
                df = pd.read_csv(resolved_path, encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError as err:
                raise CsvServiceError(f"ファイルが空です: {resolved_path}") from err
            except Exception as err:
                raise CsvServiceError(f"CSV読み込み中にエラーが発生しました: {err!s}") from err

        raise CsvEncodingError(
            f"サポート対象の文字コード（{', '.join(DEFAULT_ENCODINGS)}）でデコードできませんでした: {resolved_path}"
        )

    @staticmethod
    def search_dataframe(df: pd.DataFrame, query: str) -> pd.DataFrame:
        """全列を対象に指定クエリの部分一致検索（大文字・小文字不問）を実行する。

        Args:
            df: 検索対象の元のDataFrame。
            query: 検索対象文字列。空文字列の場合は元のDataFrameをそのまま返す。

        Returns:
            検索条件に一致する行のみで構成された新しいDataFrame。
        """
        normalized_query = query.strip()
        if not normalized_query or df.empty:
            return df.copy()

        # 正規表現インジェクションを回避し、リテラル文字列として全カラム走査
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            column_matches = (
                df[col]
                .astype(str)
                .str.contains(normalized_query, case=False, na=False, regex=False)
            )
            mask |= column_matches

        return df.loc[mask].copy()

    @staticmethod
    def export_to_xlsx(df: pd.DataFrame, target_path: Path) -> Path:
        """DataFrameをExcel（.xlsx）形式で出力・保存する。

        Args:
            df: エクスポート対象のDataFrame。
            target_path: 出力先ファイルパス。

        Returns:
            実際に保存された確定絶対パス。

        Raises:
            CsvServiceError: ディレクトリ作成失敗や権限不足等で書き込みに失敗した場合。
        """
        resolved_target = target_path.resolve()
        try:
            resolved_target.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(resolved_target, index=False, engine="openpyxl")
            return resolved_target
        except OSError as err:
            raise CsvServiceError(f"ファイル書き込み権限エラーまたはパスが無効です: {err!s}") from err
        except Exception as err:
            raise CsvServiceError(f"XLSX書き出し中に予期しないエラーが発生しました: {err!s}") from err
