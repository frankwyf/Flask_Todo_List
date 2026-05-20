# 詳細ドキュメント（日本語）

## 1. プロジェクト概要
本プロジェクトは Flask ベースのタスク管理アプリです。ポートフォリオ公開向けに再構成し、次の機能を提供します。
- ユーザー登録・ログイン
- タスクの作成/編集/完了/削除
- 状態・モジュール・タイトルによる検索
- ECharts による可視化
- 任意のメール通知と天気ウィジェット

## 2. 技術構成
- Backend: Flask, SQLAlchemy, Flask-Migrate
- Security: Flask-Bcrypt
- Frontend: Jinja2, Bootstrap, jQuery, ECharts
- Database: デフォルトは SQLite（環境変数で変更可能）

## 3. 実行構造
- エントリポイント: run.py
- アプリ初期化: app/__init__.py
- 設定管理: app/config.py
- モデル: app/model.py
- ルーティング: app/view.py
- テンプレート/静的資産: app/templates, app/static

処理フロー:
1. ブラウザ要求が app/view.py のルートに到達
2. ルートで SQLAlchemy を使ってデータを操作
3. Jinja テンプレートへデータを渡してレンダリング
4. JS/CSS で UI と操作性を補完

## 4. 脱機密化（サニタイズ）方針
機密情報をソースコードから除去し、環境変数に統一しました。

主な環境変数:
- SECRET_KEY
- DATABASE_URL
- MAIL_SERVER / MAIL_PORT / MAIL_USERNAME / MAIL_PASSWORD / MAIL_DEFAULT_SENDER
- WEATHER_WIDGET_KEY

デフォルト動作:
- DATABASE_URL 未設定時は SQLite（instance/app.db）
- MAIL 設定が空の場合、メール通知は無効
- WEATHER_WIDGET_KEY が空の場合、天気表示は無効

## 5. 技術説明で使える要点
- App Factory を導入し、初期化順序と設定管理を明確化
- ハードコードされた認証情報を削除し、公開可能な構成へ変更
- SQLite デフォルト化で初期セットアップを簡略化

## 6. 今後の改善案
- Blueprint によるルート分割
- pytest による自動テスト導入
- Flask-WTF でフォームバリデーション強化
- Docker / CI の追加
