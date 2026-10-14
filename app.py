from __future__ import annotations

import sys
from pathlib import Path

# 決定論的モジュール解決のためのsys.path事前設定
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Final

import pandas as pd
import streamlit as st

from csv_service import CsvEncodingError, CsvService, CsvServiceError

APP_TITLE: Final[str] = "CSV Viewer"
APP_ICON: Final[str] = "📊"
APP_VERSION: Final[str] = "v0.2.0"


def get_initial_file_from_args() -> Path | None:
    """コマンドライン引数から指定された初期CSVパスを取得する。

    Returns:
        有効な実在ファイルパス、または指定がない/存在しない場合はNone。
    """
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1])
        if candidate.is_file():
            return candidate.resolve()
    return None


@st.cache_data(show_spinner=False)
def cached_load_csv_from_path(file_path: Path) -> pd.DataFrame:
    """指定パスのCSVをキャッシュ化して読み込む。

    Args:
        file_path: 読み込み対象のPath。

    Returns:
        読み込まれたDataFrame。
    """
    return CsvService.load_csv(file_path)


@st.cache_data(show_spinner=False)
def cached_load_csv_from_bytes(data: bytes) -> pd.DataFrame:
    """バイト列のCSVをキャッシュ化して読み込む。

    Args:
        data: アップロードされたCSVバイト列。

    Returns:
        読み込まれたDataFrame。
    """
    return CsvService.load_csv(data)


def render_sidebar() -> tuple[pd.DataFrame | None, str]:
    """サイドバーの入力ウィジェット群を描画し、読み込まれたDataFrameと識別名を返す。

    Returns:
        (DataFrameまたは未ロード時None, ファイル名または未ロード時空文字)
    """
    with st.sidebar:
        st.header("⚙️ データソース")
        mode = st.radio(
            "読込方法",
            ["ファイルアップロード", "ローカルパス指定"],
            horizontal=True,
            help="CSVの指定方法を選択します。",
        )

        df: pd.DataFrame | None = None
        file_label: str = ""

        if mode == "ファイルアップロード":
            uploaded_file = st.file_uploader(
                "CSVファイルを選択",
                type=["csv"],
                help="UTF-8(BOM付き/無し)およびCP932(Shift-JIS)に自動対応",
            )
            if uploaded_file is not None:
                file_label = uploaded_file.name
                try:
                    df = cached_load_csv_from_bytes(uploaded_file.getvalue())
                except CsvEncodingError as err:
                    st.error(f"文字コード判定エラー: {err!s}")
                except CsvServiceError as err:
                    st.error(f"読み込みエラー: {err!s}")
        else:
            default_path_str = ""
            init_path = get_initial_file_from_args()
            if init_path is not None:
                default_path_str = str(init_path)

            path_input = st.text_input(
                "ローカルCSVパス",
                value=default_path_str,
                placeholder="C:/path/to/data.csv",
                help="読み込みたいCSVファイルの絶対パスまたは相対パスを入力します。",
            )
            if path_input.strip():
                target_path = Path(path_input.strip())
                file_label = target_path.name
                try:
                    df = cached_load_csv_from_path(target_path)
                except CsvEncodingError as err:
                    st.error(f"文字コード判定エラー: {err!s}")
                except CsvServiceError as err:
                    st.error(f"読み込みエラー: {err!s}")

        st.divider()
        st.caption(f"{APP_TITLE} {APP_VERSION} | MIT License")
        st.caption("Powered by Streamlit & Pandas")

    return df, file_label


def render_search_form(current_query: str) -> str:
    """検索キーワード入力フォームを描画し、確定されたクエリ文字列を返す。

    Args:
        current_query: 現在適用されている検索クエリ。

    Returns:
        確定された検索クエリ。
    """
    with st.form("search_form", clear_on_submit=False):
        st.subheader("1. 検索・絞り込み")
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            new_query = st.text_input(
                "検索キーワード",
                value=current_query,
                placeholder="全列横断リテラル部分一致検索（大文字・小文字不問）",
                help="正規表現メタ文字（[]、.*など）も安全に完全リテラルとして検索されます。",
            )
        with col_btn:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("検索実行", type="primary")

    if submitted:
        return new_query
    return current_query


def render_preview_and_export(
    raw_df: pd.DataFrame,
    display_df: pd.DataFrame,
    file_label: str,
) -> None:
    """統計メトリクス、XLSXエクスポートボタン、テーブルおよびセル詳細インスペクタを描画する。

    Args:
        raw_df: 全件の元DataFrame。
        display_df: 検索フィルタ後の表示対象DataFrame。
        file_label: 読み込み元ファイル名。
    """
    st.subheader("2. データプレビュー & エクスポート")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("総レコード数", f"{len(raw_df):,} 行")
    m2.metric("抽出件数", f"{len(display_df):,} 行")
    m3.metric("総列数", f"{len(display_df.columns):,} 列")

    stem = Path(file_label).stem if file_label else "export"
    with m4:
        st.write("")
        try:
            xlsx_bytes = CsvService.export_to_xlsx_bytes(display_df)
            st.download_button(
                label="📥 XLSXエクスポート",
                data=xlsx_bytes,
                file_name=f"{stem}_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                help="表示中の検索絞り込みデータをExcel（.xlsx）形式でダウンロードします。",
            )
        except CsvServiceError as err:
            st.error(f"XLSX生成失敗: {err!s}")

    st.caption(
        "💡 表内の列ヘッダーをドラッグして列幅を自由に調整できます。"
        "また、行をクリックして選択すると下部のインスペクタで長文セルの全文を確認できます。"
    )

    selection = st.dataframe(
        display_df,
        use_container_width=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
    )

    selected_rows = selection.selection.rows
    if selected_rows:
        selected_row_idx = selected_rows[0]
        row_series = display_df.iloc[selected_row_idx]
        st.subheader("🔍 選択行の長文・セル詳細インスペクタ")
        st.caption(f"選択行インデックス: {display_df.index[selected_row_idx]}")
        for col in display_df.columns:
            val_str = str(row_series[col])
            with st.expander(
                f"列: **{col}** ({len(val_str):,} 文字)",
                expanded=(len(val_str) > 40),
            ):
                st.text_area(
                    label=f"{col} の値",
                    value=val_str,
                    height=min(300, max(80, len(val_str.splitlines()) * 24)),
                    disabled=True,
                    label_visibility="collapsed",
                )


def main() -> None:
    """Streamlit アプリケーションのエントリーポイント。"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
    )

    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("長文セル全文閲覧・文字コード自動判別・リテラル検索・XLSX出力治具")

    df, file_label = render_sidebar()

    if df is None:
        st.info(
            "👈 サイドバーからCSVファイルをアップロードするか、"
            "ファイルパスを指定してください。"
        )
        st.stop()

    if "search_query" not in st.session_state:
        st.session_state["search_query"] = ""

    current_query: str = str(st.session_state["search_query"])
    new_query = render_search_form(current_query)

    if new_query != current_query:
        st.session_state["search_query"] = new_query
        current_query = new_query

    if current_query:
        col_clear, _ = st.columns([1, 6])
        with col_clear:
            if st.button("検索条件クリア", type="secondary"):
                st.session_state["search_query"] = ""
                st.rerun()

    display_df = CsvService.search_dataframe(df, current_query)
    render_preview_and_export(df, display_df, file_label)


if __name__ == "__main__":
    main()
