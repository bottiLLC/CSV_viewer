[![CI](https://github.com/bottiLLC/CSV_viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/bottiLLC/CSV_viewer/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/Python-3.14%20%7C%203.13-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


## Overview
Tkinterとpandasで構築された、文字コード自動判別・高速リテラル文字列検索・XLSX任意パス直接書き出しに対応した軽量デスクトップCSVビューア治具。

## Quick Start (TL;DR)
```bash
# 1. 依存関係の同期
uv sync --all-extras --dev

# 2. 単体テスト実行
uv run pytest

# 3. アプリケーション起動（または run.bat をダブルクリック）
uv run python app.py
```

## Architecture & Features
- **SRP分離アーキテクチャ**: UI層（`app.py`）と純粋ドメイン処理層（`csv_service.py`）を完全分離し、ヘッドレス単体テスト容易性を担保。
- **多段エンコーディングフォールバック**: `utf-8-sig`（BOM付き/無し）から `cp932`（Windows日本語 Shift-JIS）への自動フォールバックにより文字化けを防止。
- **全列横断リテラル検索**: 正規表現メタ文字によるクラッシュを回避する `regex=False` 完全リテラル部分一致検索（大文字・小文字不問）を搭載。
- **直接XLSXエクスポート**: 表示中（絞り込み後）のデータをOS標準ファイルダイアログ経由で任意の保存先へ直接書き出し。

## Environment Variables
| Variable | Default | Description |
| :--- | :--- | :--- |
| `UV_PYTHON_PREFERENCE` | `only-system` | ローカルシステムPythonの利用を強制するフラグ（`run.bat` / `run.command` 内で設定） |

## Limits & Known Trade-offs
- **Treeview描画リミット**: 描画負荷とUI応答性維持のため、Treeview上の初期描画件数を最大1,000行に制限（検索・出力はバックエンドの全件DataFrameに対して実行）。
- **ステートレス運用**: 本ツールはセッションや履歴の永続化を行わず、ファイルを開くたびにメモリ上で展開する仕様（ローカルルール `AGENTS.md` にて `./data` 隔離対象外に設定）。

---
Copyright (c) 2026 LLC Bocchi. Released under the [MIT License](LICENSE).
