# Local Project Rules (CSV Viewer)

## 1. Exemption: Persistent Data Isolation & Backup Invariant
- **No `./data` Isolation Requirement**:
  本アプリケーションはステートレスなデスクトップビューア治具であり、ローカルDBや永続アプリケーション状態を内部管理しないため、`@[user_global]` における「`./data` ディレクトリへの永続データ隔離」および「`backup_manager.py` による自動整合性検証バックアップ連携」の適用を明示的に除外する。
- **Direct File Export**:
  XLSX形式の書き出しは、`filedialog.asksaveasfilename` を介してユーザーが指定した任意のファイルパスへ直接保存する設計とする。

## 2. Invariant Adherence
- 高凝集・単一責任の原則 (SRP): UI（Tkinter）とドメインロジック（CSV読込・文字列検索・Excel出力）の分離を維持する。
- 厳格な型安全性 (`mypy --strict`)、決定論的パス解決、および単体テスト (`pytest`) による品質保証を徹底する。
- 出力プロトコルおよびコーディング標準はグローバルルールに完全準拠する。
