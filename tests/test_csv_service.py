from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest

# テスト実行時のsys.path補正
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from csv_service import CsvEncodingError, CsvService, CsvServiceError


def test_load_csv_file_not_found_raises_error(tmp_path: Path) -> None:
    # Arrange
    non_existent = tmp_path / "not_found.csv"

    # Act & Assert
    with pytest.raises(CsvServiceError, match="指定されたファイルが存在しません"):
        CsvService.load_csv(non_existent)


def test_load_csv_empty_file_raises_error(tmp_path: Path) -> None:
    # Arrange
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    # Act & Assert
    with pytest.raises(CsvServiceError, match="ファイルが空です"):
        CsvService.load_csv(empty_file)


def test_load_csv_utf8_sig_success(tmp_path: Path) -> None:
    # Arrange
    csv_file = tmp_path / "sample_utf8.csv"
    content = "id,name,value\n1,Alice,100\n2,Bob,200\n"
    csv_file.write_bytes(content.encode("utf-8-sig"))

    # Act
    df = CsvService.load_csv(csv_file)

    # Assert
    assert list(df.columns) == ["id", "name", "value"]
    assert len(df) == 2
    assert df.iloc[0]["name"] == "Alice"
    assert df.iloc[1]["value"] == 200


def test_load_csv_cp932_fallback_success(tmp_path: Path) -> None:
    # Arrange: UTF-8ではデコードできないCP932固有文字を含むCSV
    csv_file = tmp_path / "sample_cp932.csv"
    content = "品番,品名,価格\n101,ネジ,50\n102,ボルト,120\n"
    csv_file.write_bytes(content.encode("cp932"))

    # Act
    df = CsvService.load_csv(csv_file)

    # Assert
    assert list(df.columns) == ["品番", "品名", "価格"]
    assert len(df) == 2
    assert df.iloc[0]["品名"] == "ネジ"
    assert df.iloc[1]["価格"] == 120


def test_load_csv_unsupported_encoding_raises_encoding_error(tmp_path: Path) -> None:
    # Arrange: どのエンコーディングでもパースできないバイナリ
    csv_file = tmp_path / "corrupt.csv"
    csv_file.write_bytes(b"\x80\xFF\xFE\xFD\xFC\xFB")

    # Act & Assert
    with pytest.raises(CsvEncodingError, match="サポート対象の文字コード"):
        CsvService.load_csv(csv_file)


def test_load_csv_unexpected_pandas_exception_raises_csv_service_error(
    tmp_path: Path,
) -> None:
    # Arrange
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("a,b\n1,2\n", encoding="utf-8")

    # Act & Assert
    with (
        patch("pandas.read_csv", side_effect=RuntimeError("Simulated parse error")),
        pytest.raises(CsvServiceError, match="CSV読み込み中にエラーが発生しました"),
    ):
        CsvService.load_csv(csv_file)


@pytest.mark.parametrize("empty_query", ["", "   ", "\t\n"])
def test_search_dataframe_empty_query_returns_copy(empty_query: str) -> None:
    # Arrange
    source_df = pd.DataFrame({"colA": [1, 2], "colB": ["foo", "bar"]})

    # Act
    result_df = CsvService.search_dataframe(source_df, empty_query)

    # Assert
    assert len(result_df) == 2
    assert list(result_df["colB"]) == ["foo", "bar"]
    # 返り値が独立したコピーであることの検証
    assert result_df is not source_df


def test_search_dataframe_empty_dataframe_returns_empty() -> None:
    # Arrange
    source_df = pd.DataFrame(columns=["colA", "colB"])

    # Act
    result_df = CsvService.search_dataframe(source_df, "test")

    # Assert
    assert result_df.empty
    assert list(result_df.columns) == ["colA", "colB"]


def test_search_dataframe_single_match() -> None:
    # Arrange
    source_df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "title": ["Report Alpha", "Beta Document", "Gamma Report"],
        }
    )

    # Act
    result_df = CsvService.search_dataframe(source_df, "Alpha")

    # Assert
    assert len(result_df) == 1
    assert result_df.iloc[0]["title"] == "Report Alpha"


def test_search_dataframe_case_insensitive_and_cross_column() -> None:
    # Arrange
    source_df = pd.DataFrame(
        {
            "category": ["FRUIT", "Vegetable", "Meat"],
            "name": ["apple", "Tomato", "beef"],
            "code": ["F01", "V02", "M03"],
        }
    )

    # Act: 小文字 "fruit" で検索 -> 大文字 "FRUIT" の列に合致
    result_df = CsvService.search_dataframe(source_df, "fruit")

    # Assert
    assert len(result_df) == 1
    assert result_df.iloc[0]["name"] == "apple"

    # Act: "02" で数値・コード列検索
    code_result = CsvService.search_dataframe(source_df, "02")
    assert len(code_result) == 1
    assert code_result.iloc[0]["name"] == "Tomato"


def test_search_dataframe_literal_regex_characters() -> None:
    # Arrange: 正規表現メタ文字を含む文字列
    source_df = pd.DataFrame(
        {
            "pattern": ["value[0]", "value.*", "normal_value"],
        }
    )

    # Act: "[0]" を検索 -> 正規表現としてではなくリテラル一致
    result_df = CsvService.search_dataframe(source_df, "[0]")

    # Assert
    assert len(result_df) == 1
    assert result_df.iloc[0]["pattern"] == "value[0]"

    # Act: ".*" を検索 -> "value.*" のみ抽出されること
    regex_literal_df = CsvService.search_dataframe(source_df, ".*")
    assert len(regex_literal_df) == 1
    assert regex_literal_df.iloc[0]["pattern"] == "value.*"


def test_search_dataframe_no_match_returns_empty() -> None:
    # Arrange
    source_df = pd.DataFrame({"name": ["Alice", "Bob"]})

    # Act
    result_df = CsvService.search_dataframe(source_df, "Charlie")

    # Assert
    assert result_df.empty
    assert list(result_df.columns) == ["name"]


def test_export_to_xlsx_success(tmp_path: Path) -> None:
    # Arrange
    target_xlsx = tmp_path / "output.xlsx"
    df = pd.DataFrame({"x": [10, 20], "y": ["A", "B"]})

    # Act
    exported_path = CsvService.export_to_xlsx(df, target_xlsx)

    # Assert
    assert exported_path == target_xlsx.resolve()
    assert target_xlsx.is_file()

    # 再読み込みでデータ整合性を検証
    loaded_df = pd.read_excel(target_xlsx, engine="openpyxl")
    assert list(loaded_df.columns) == ["x", "y"]
    assert len(loaded_df) == 2
    assert loaded_df.iloc[0]["x"] == 10
    assert loaded_df.iloc[1]["y"] == "B"


def test_export_to_xlsx_creates_parent_directory(tmp_path: Path) -> None:
    # Arrange: 存在しないサブディレクトリへのパス
    nested_target = tmp_path / "deep" / "nested" / "dir" / "report.xlsx"
    df = pd.DataFrame({"col": [1]})

    # Act
    exported_path = CsvService.export_to_xlsx(df, nested_target)

    # Assert
    assert exported_path == nested_target.resolve()
    assert nested_target.is_file()


def test_export_to_xlsx_os_error_raises_csv_service_error(tmp_path: Path) -> None:
    # Arrange
    df = pd.DataFrame({"col": [1]})
    target = tmp_path / "blocked.xlsx"

    # Act & Assert
    with (
        patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")),
        pytest.raises(CsvServiceError, match="ファイル書き込み権限エラーまたはパスが無効です"),
    ):
        CsvService.export_to_xlsx(df, target)


def test_export_to_xlsx_unexpected_exception_raises_csv_service_error(
    tmp_path: Path,
) -> None:
    # Arrange
    df = pd.DataFrame({"col": [1]})
    target = tmp_path / "error.xlsx"

    # Act & Assert
    with (
        patch.object(pd.DataFrame, "to_excel", side_effect=RuntimeError("Excel crash")),
        pytest.raises(CsvServiceError, match="XLSX書き出し中に予期しないエラーが発生しました"),
    ):
        CsvService.export_to_xlsx(df, target)
