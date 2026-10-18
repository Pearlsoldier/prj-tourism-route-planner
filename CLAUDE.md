# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

AIとの対話で観光地を探し、徒歩ルートを組み立てるWebアプリ（SPA）。フロントエンドはBetterChatGPTのForkで、バックエンドはFastAPI + Gemini APIのFunction Callingを使う。

## ドキュメントの所在

作業を始める前に次の2つを読む。

| ファイル | 内容 |
|---|---|
| `docs/plan-v1.0.0.md` | v1.0.0 までの4週計画。タスク一覧・進捗・付録（調査結果と手順） |
| `docs/adr/` | 設計判断の記録（なぜそう決めたか、何を諦めたか） |

`notes/` は個人的な学習メモ（gitignore 済み）。読む必要はない。

## 開発コマンド

### バックエンド（`backend/` ディレクトリ）

```bash
cd backend
uv run uvicorn main:app --reload
```

起動後、`http://localhost:8000` で動作。`uv run` が `.venv` を自動で有効化するので
`activate` は不要（2026-09-27 に uv へ移行、ADR-0002）。

依存の追加は `uv add <パッケージ>`（開発用は `uv add --dev`）。`pyproject.toml` と
`uv.lock` の両方が更新される。**`pip install` は使わない**（`uv.lock` に反映されず、
本番と差が出る）。

### フロントエンド（`frontend/` ディレクトリ）

```bash
cd frontend
npm run dev    # 開発サーバー（http://localhost:5173）
npm run build  # 本番ビルド
```

**⚠️ `npm install` / `yarn install` を実行してはいけない。**
`package-lock.json` と `yarn.lock` が両方存在する未解決の問題がある（タスク 1-3b）。
どちらを実行しても対応する lock ファイルが書き換わり、「実際にどちらのパッケージ
マネージャが使われてきたか」を示す証拠（ファイルの更新時刻）が失われる。これは
復元できない。判断が済むまで実行前に必ず確認を取る。詳細は
`docs/plan-v1.0.0.md` の付録C。


テストスクリプト（`backend/test.py` など）は単体で `python test.py` で実行できる探索的なスクリプト。正式なテストスイートはない。

## アーキテクチャ

### データフロー

```
フロントエンド（BetterChatGPT fork）
  └─ POST /v1/chat/completions
       └─ FastAPI（main.py）
            ├─ Gemini API（Function Calling）
            │    └─ tools.py の関数を呼び出す
            ├─ Guidebook（セッション状態）
            └─ timeline.py でプラン完成時にMarkdown表を生成して応答に追記
```

### セッション管理（`backend/main.py`）

- `sessions` 辞書にセッションを保持。ユーザーの**第一声のSHA-256ハッシュ**をキーにする（フロントから会話IDを渡さない現在の設計上の制約）。
- 各セッションは `Guidebook` インスタンス。

### Guidebook（`backend/models/guidebook.py`）

AIが情報を集めながら埋めていく「旅のしおり」のデータクラス。

| フィールド | 説明 |
|---|---|
| `origin` | 出発地（geocode_place の結果） |
| `selected` | 巡る地点のリスト（name と stay_minutes を持つ辞書） |
| `legs` | 区間データ（get_walking_leg の結果を append） |
| `start_time` | 観光の開始時刻（"HH:MM" 形式、任意） |

`is_ready()` が True になったタイミングで timeline.py がプランのMarkdown表を生成し、Geminiの応答に付加する。

### しおりの3つの役割（ADR-0001）

しおりに関わるコードは、**誰の都合で変わるか**で置き場所を分ける。

```
AI がしおりを作る          → Guidebook       （backend/models/guidebook.py）
地図に出せる形に詰め替える → to_plan         （backend/functions/plan_payload.py）
地図を描く                 → フロントの部品  （Week 3）
```

- `Guidebook` に置くのは AI のためのものだけ（`missing_fields`・`is_ready` など）。地図やブラウザのための変換を `Guidebook` のメソッドにしない
- `to_plan` は計算をしない。`build_route` が計算した値を選んで詰め替えるだけ
- 詰め替えた形（`plan`）と、その理由は `docs/adr/0001-plan-payload.md`

### Geminiへ渡すツール

Geminiに登録されるツール（Function Calling で呼ばれる）:

| 関数 | 役割 |
|---|---|
| `geocode_place` | 地名→緯度経度（Google Geocoding API） |
| `search_nearby_location` | 周辺施設検索（Google Places API） |
| `get_walking_leg` | 徒歩区間の距離・所要時間（Google Routes API） |
| `select_places` | 巡る地点を確定してGuidebookに記録 |
| `set_start_time` | 開始時刻をGuidebookに記録 |
| `reorder_places` | 巡り順の変更（legs をリセットして再計算） |

`get_place_details`（口コミ・要約取得）は Gemini に登録しない。`with_details` デコレータが `search_nearby_location` の結果に自動で付加する。

### ラッパー（`backend/functions/wraped_tools.py`）

- `record_to_guidebook(plan, field, mode)`: ツールの戻り値をGuidebookに自動記録するデコレータファクトリ。`mode="once"` なら初回のみ、`mode="append"` なら追記。
- `make_select_places`, `make_set_start_time`, `make_reorder_places`: それぞれ `plan` を閉じ込めたクロージャを返す。

### プロンプト（`backend/prompts.py`）

`BASE` 定数（会話の進め方と厳守事項）＋ 毎リクエストごとに現在の `Guidebook` の状態を JSON で埋め込む。AIには「不足している欄」も明示して渡す。

### フロントエンド（`frontend/`）

BetterChatGPT の Fork。エンドポイント設定画面（SettingsMenu）でバックエンドURL（`http://localhost:8000/v1/chat/completions`）とアクセスキーを入力して使う。APIキーフィールドがアクセスキーとして機能し、`Authorization: Bearer <key>` ヘッダーで送信される。

パスエイリアスは `vite.config.ts` で定義（`@components/`, `@store/`, `@hooks/` など）。

フロントエンドはVercel（Static）でホスティング、バックエンドはRenderでホスティング。`frontend/middleware.ts`（Vercel Routing Middleware）でサイト全体にBasic認証をかけている。資格情報はVercelプロジェクトの環境変数 `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` に設定する（未設定だと全リクエストが500になる、fail-close）。ローカルの `npm run dev` / `vite build` では実行されず、Vercel上でのみ動作する。

## 主要な設計上の注意点

- **Place Details のキャッシュ**: `place_cache` はプロセスのメモリ上のみ。再起動でリセットされる。
- **legs の再計算**: `reorder_places` 呼び出し後は `legs` が空になる。応答生成時に `selected` が2件以上あり `legs` が空なら自動で再計算する（`main.py` 末尾）。
- **Geminiのモデル**: `gemini-3.5-flash-lite` を使用（`main.py` の `generate_content` 呼び出し）。
- **DB関連ファイル**: `backend/sql/`, `backend/DB/`, `backend/scripts/` にPostgreSQL関連のコードがあるが、現在のメイン処理（観光地検索）では使われていない。Google Places APIに移行済み。

## 作業の進め方

- いきなり実装しない。まず原因の候補と読むべき箇所を、ファイル名と行番号つきで示す
- 達成条件はコマンドの出力で判定できる形にする
  （例：「マージした」ではなく「git log --oneline -1 の先頭が一致する」）
- 1コミット＝そのコミットに巻き戻してアプリが動く単位
- main への push は Render の自動デプロイが走る。push は必ず確認を取る
- Google Maps API を実際に叩くスクリプトは課金が発生する。実行前に確認を取る
- `frontend/` で `npm install` / `yarn install` は実行しない（証拠が不可逆に消える。タスク 1-3b が済むまで）

## ハマりどころ

- `.env` は `backend/` 直下。`load_dotenv()` は上へしか遡らないので、
  リポジトリのルートから実行すると読めない
- `uvicorn --reload` は親子2プロセスになる。`lsof -i :8000` で両方の PID を確認して落とす。
  `kill` が無視されることがあり、`Errno 48` はコードの問題ではない
- ツールの戻り値の型が統一されていない。`search_nearby_location` だけリストを返すため
  `"error" in result` が効かない