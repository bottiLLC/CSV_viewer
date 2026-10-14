from __future__ import annotations

import io
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
    def load_csv(source: Path | bytes) -> pd.DataFrame:
        """指定パスまたはバイト列のCSVデータをフォールバック付きで読み込みDataFrameとして取得する。

        Args:
            source: 読み込み対象のCSVファイルパスまたはバイト列。

        Returns:
            読み込まれたCSVデータを含むpandas DataFrame。

        Raises:
            CsvServiceError: ファイルが存在しない、または空ファイルの場合。
            CsvEncodingError: サポート対象の文字コードでデコードできない場合。
        """
        raw_bytes: bytes
        source_label: str
        if isinstance(source, Path):
            resolved_path = source.resolve()
            if not resolved_path.is_file():
                msg = f"指定されたファイルが存在しません: {resolved_path}"
                raise CsvServiceError(msg)
            source_label = str(resolved_path)
            try:
                raw_bytes = resolved_path.read_bytes()
            except OSError as err:
                msg = f"ファイル読み込み中にエラーが発生しました: {err!s}"
                raise CsvServiceError(msg) from err
        else:
            source_label = "アップロードデータ"
            raw_bytes = source

        if len(raw_bytes) == 0:
            raise CsvServiceError(f"ファイルが空です: {source_label}")

        for encoding in DEFAULT_ENCODINGS:
            try:
                buffer = io.BytesIO(raw_bytes)
                return pd.read_csv(buffer, encoding=encoding)
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError as err:
                raise CsvServiceError(f"ファイルが空です: {source_label}") from err
            except Exception as err:
                msg = f"CSV読み込み中にエラーが発生しました: {err!s}"
                raise CsvServiceError(msg) from err

        enc_list = ", ".join(DEFAULT_ENCODINGS)
        raise CsvEncodingError(
            f"サポート対象の文字コード（{enc_list}）で"
            f"デコードできませんでした: {source_label}"
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
    def export_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
        """DataFrameをExcel（.xlsx）形式のバイト列として生成する。

        Args:
            df: エクスポート対象のDataFrame。

        Returns:
            生成された.xlsxファイルのバイト列データ。

        Raises:
            CsvServiceError: XLSXバイナリ生成中に予期しないエラーが発生した場合。
        """
        buffer = io.BytesIO()
        try:
            df.to_excel(buffer, index=False, engine="openpyxl")
            return buffer.getvalue()
        except Exception as err:
            msg = f"XLSX書き出し中に予期しないエラーが発生しました: {err!s}"
            raise CsvServiceError(msg) from err

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
            xlsx_bytes = CsvService.export_to_xlsx_bytes(df)
            resolved_target.write_bytes(xlsx_bytes)
            return resolved_target
        except CsvServiceError:
            raise
        except OSError as err:
            msg = f"ファイル書き込み権限エラーまたはパスが無効です: {err!s}"
            raise CsvServiceError(msg) from err
