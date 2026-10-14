from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Final

# 決定論的モジュール解決のためのsys.path事前設定
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from csv_service import CsvEncodingError, CsvService, CsvServiceError

MAX_PREVIEW_ROWS: Final[int] = 1000


class CsvViewerApp:
    """CSV閲覧・検索・XLSX出力を担当するTkinter GUIプレゼンテーション層。

    ビジネスロジックは CsvService に完全委譲し、UIイベントと描画管理に専任する。
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("CSVビューア")
        self.root.geometry("960x600")
        self.root.minsize(720, 480)

        self.current_file_path: Path | None = None
        self.raw_df: pd.DataFrame | None = None
        self.display_df: pd.DataFrame | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """GUIコンポーネント（ツールバー、テーブル、ステータスバー）を構築する。"""
        # 操作ツールバー（上部）
        toolbar = ttk.Frame(self.root, padding=6)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        btn_open = ttk.Button(toolbar, text="CSVを開く", command=self.on_load_csv)
        btn_open.pack(side=tk.LEFT, padx=4)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=8, pady=2
        )

        ttk.Label(toolbar, text="検索:").pack(side=tk.LEFT, padx=2)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            toolbar, textvariable=self.search_var, width=24, state=tk.DISABLED
        )
        self.search_entry.pack(side=tk.LEFT, padx=4)
        self.search_entry.bind("<Return>", lambda _event: self.on_search())

        self.btn_search = ttk.Button(
            toolbar, text="検索", command=self.on_search, state=tk.DISABLED
        )
        self.btn_search.pack(side=tk.LEFT, padx=2)

        self.btn_clear = ttk.Button(
            toolbar, text="解除", command=self.on_clear_search, state=tk.DISABLED
        )
        self.btn_clear.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=8, pady=2
        )

        self.btn_export = ttk.Button(
            toolbar,
            text="xlsxで書き出し",
            command=self.on_export_xlsx,
            state=tk.DISABLED,
        )
        self.btn_export.pack(side=tk.LEFT, padx=4)

        # ステータスバー（下部）
        self.lbl_status = ttk.Label(
            self.root,
            text="CSVファイルを読み込んでください",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=4,
        )
        self.lbl_status.pack(fill=tk.X, side=tk.BOTTOM)

        # テーブル表示領域（中央）
        table_container = ttk.Frame(self.root)
        table_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.tree = ttk.Treeview(
            table_container, show="headings", selectmode="extended"
        )
        v_scroll = ttk.Scrollbar(
            table_container, orient=tk.VERTICAL, command=self.tree.yview
        )
        h_scroll = ttk.Scrollbar(
            table_container, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

    def on_load_csv(self) -> None:
        """ファイルダイアログからCSVを選択し、データをロードして描画する。"""
        selected = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not selected:
            return

        file_path = Path(selected)
        try:
            self.raw_df = CsvService.load_csv(file_path)
            self.current_file_path = file_path
            self.display_df = self.raw_df.copy()
            self.search_var.set("")

            self._set_controls_state(tk.NORMAL)
            self._render_treeview()
            self._update_status(f"読込完了: {file_path.name}")
        except (CsvEncodingError, CsvServiceError) as err:
            messagebox.showerror("読込エラー", str(err))

    def on_search(self) -> None:
        """入力されたクエリでDataFrameを走査し、結果テーブルを更新する。"""
        if self.raw_df is None:
            return

        query = self.search_var.get()
        self.display_df = CsvService.search_dataframe(self.raw_df, query)
        self._render_treeview()

        match_count = len(self.display_df)
        total_count = len(self.raw_df)
        if query.strip():
            self._update_status(
                f"検索実行: '{query}' ({match_count}/{total_count} 件一致)"
            )
        else:
            self._update_status(f"全件表示中 ({total_count} 件)")

    def on_clear_search(self) -> None:
        """検索条件をリセットして全行表示に復帰する。"""
        if self.raw_df is None:
            return

        self.search_var.set("")
        self.display_df = self.raw_df.copy()
        self._render_treeview()
        self._update_status(f"検索解除 (全 {len(self.raw_df)} 件)")

    def on_export_xlsx(self) -> None:
        """表示中（検索フィルタ反映済）のデータをユーザー指定パスへXLSX出力する。"""
        if self.display_df is None or self.current_file_path is None:
            return

        default_stem = self.current_file_path.stem
        suggested_name = f"{default_stem}_export.xlsx"

        save_target = filedialog.asksaveasfilename(
            title="Excelファイルとして保存",
            initialfile=suggested_name,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
        )
        if not save_target:
            return

        try:
            confirmed_path = CsvService.export_to_xlsx(
                self.display_df, Path(save_target)
            )
            messagebox.showinfo(
                "出力完了", f"正常に出力されました:\n{confirmed_path}"
            )
        except CsvServiceError as err:
            messagebox.showerror("エクスポート失敗", str(err))

    def _render_treeview(self) -> None:
        """Treeviewの列見出しとデータ行を再構築する（描画負荷防止リミット適用）。"""
        self.tree.delete(*self.tree.get_children())
        if self.display_df is None:
            return

        columns = list(self.display_df.columns)
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=120, minwidth=60, anchor=tk.W)

        # UIフリーズ防止のための最大プレビュー件数制御
        preview_data = self.display_df.head(MAX_PREVIEW_ROWS).values.tolist()
        for row in preview_data:
            self.tree.insert("", tk.END, values=row)

    def _set_controls_state(self, state: str) -> None:
        """検索・出力関連ウィジェットの活性/非活性を一括制御する。"""
        self.search_entry.config(state=state)
        self.btn_search.config(state=state)
        self.btn_clear.config(state=state)
        self.btn_export.config(state=state)

    def _update_status(self, message: str) -> None:
        """ステータスバーのメッセージを更新する。"""
        if self.display_df is not None and self.raw_df is not None:
            total = len(self.raw_df)
            current = len(self.display_df)
            rendered = min(current, MAX_PREVIEW_ROWS)
            self.lbl_status.config(
                text=f"{message} | 表示: {rendered}/{current}件 (元データ: {total}件)"
            )
        else:
            self.lbl_status.config(text=message)


if __name__ == "__main__":
    root_window = tk.Tk()
    app = CsvViewerApp(root_window)
    root_window.mainloop()
