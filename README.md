[![CI](https://github.com/bottiLLC/CSV_viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/bottiLLC/CSV_viewer/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/Python-3.14%20%7C%203.13-blue.svg)](https://www.python.org/) [![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


## Overview
Streamlitとpandasで構築された、長文セルの全文閲覧・文字コード自動判別・高速リテラル検索・XLSX直接エクスポートに対応した高機能CSVビューア治具。

## Quick Start (TL;DR)
```bash
# 1. 依存関係の同期
uv sync --all-extras --dev

# 2. 単体テスト実行
uv run pytest

# 3. アプリケーション起動（または run.bat をダブルクリック）
uv run streamlit run app.py
```

## Architecture & Features
- **SRP分離アーキテクチャ**: UI層（`app.py`）と純粋ドメイン処理層（`csv_service.py`）を完全分離し、100% C1ブランチカバレッジのヘッドレス単体テスト容易性を担保。
- **長文セル全文インスペクタ**: Tkinter等のGUIで発生するセル文字列の表示切れ・省略を排除し、Glide Data Gridベースの列幅調整および選択行の全列全文展開ビューを提供。
- **多段エンコーディングフォールバック**: `utf-8-sig`（BOM付き/無し）から `cp932`（Windows日本語 Shift-JIS）への自動フォールバックにより文字化けを防止。
- **全列横断リテラル検索**: 正規表現メタ文字によるクラッシュを回避する `regex=False` 完全リテラル部分一致検索（大文字・小文字不問）を搭載。
- **直接XLSXエクスポート**: 表示中（絞り込み後）のデータをブラウザ経由で任意の保存先へExcel形式（.xlsx）として即座にダウンロード可能。

## Environment Variables
| Variable | Default | Description |
| :--- | :--- | :--- |
| `UV_PYTHON_PREFERENCE` | `only-system` | ローカルシステムPythonの利用を強制するフラグ（`run.bat` / `run.command` 内で設定） |

## Limits & Known Trade-offs
- **ブラウザメモリ消費**: 数百万行を超える極大CSVファイルの場合、ブラウザフロントエンド側のメモリ消費が増加する可能性があるため、大容量ファイルは事前に分割またはサンプリングを推奨。
- **ステートレス運用**: 本ツールはセッションや履歴の永続化を行わず、ファイルを開くたびにメモリ上で展開する仕様（ローカルルール `AGENTS.md` にて `./data` 隔離対象外に設定）。

---
Copyright (c) 2026 LLC Bocchi. Released under the [MIT License](LICENSE).
