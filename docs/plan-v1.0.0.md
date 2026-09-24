# v1.0.0 開発プラン（地図表示まで）

- **期間**: 2026-09-23 〜 2026-10-21（4週間）
- **ゴール**: 地図表示を完成させ、`v1.0.0` タグを打つ
- **前提となる学習目標**: 要件定義 → 開発 → リリース → 次の要件、を1周回す

---

## 1. スコープ

### 確定事項

| 項目 | 決定 |
|---|---|
| 完成の定義 | AIが組んだルートが、左右分割画面の右側に番号付きピンで表示される |
| 地図の双方向性 | 読み取り専用。クリックでの地点追加・削除は次フェーズ |
| レイアウト | 左右分割（左：チャット／右：地図） |
| 移動手段 | 徒歩のみ |
| 認証 | 今回は触らない（現行のBasic認証＋アクセスキーのまま） |
| 永続化 | 今回は触らない（メモリ上のまま） |
| デプロイ先 | Render（バックエンド）＋ Vercel（フロント） |

### スコープ外（v1.0.0 では明確にやらない）

- 地図クリックでの地点操作
- 認証の作り替え
- しおりの永続化・履歴
- 車・公共交通機関のルート（`transit_jurnys.py` は実験のまま据え置き）
- `backend/sql/` `DB/` `scripts/` の復活
- `wrapped_tools.py` の分割（次フェーズ「おすすめ精度向上」の直前に、テストを書いてから行う）

---

## 2. v1.0.0 受け入れ条件

### Must（これが揃わなければリリースしない）

| # | 条件 | 判定方法 |
|---|---|---|
| 1 | 従来どおり会話でルートが組める（退行なし） | 手動での通し確認 |
| 2 | 左右分割画面で、右側に地図が表示される | 目視 |
| 3 | ルート確定時、全地点に訪問順の番号付きピンが立つ | ピン数 == `jq '.plan.stops \| length'` |
| 4 | 全ピンが収まるよう表示範囲が自動調整される | 目視 |
| 5 | `pytest -q` が通る | exit 0 |
| 6 | `npm run build` が通る | exit 0 |
| 7 | README に起動手順と v1.0.0 の機能が書かれている | ファイル確認 |

### Should（間に合わなければ v1.1.0 送り）

- 徒歩経路の線（polyline）描画
- ピンをクリックして名前・到着時刻を表示

---

## 3. 週ごとのタスク

### Week 1（9/23〜9/29）土台を固める

**目的**: これから4週間、安心して変更できる状態を作る

| # | タスク | 分類 | ブランチ |
|---|---|---|---|
| 1-1 | ~~Google Cloud の予算アラート＋APIキーの quota 設定~~ **✅ 完了 2026-09-23** | 片付け | （コード変更なし） |
| 1-2 | **uv へ移行**（`pyproject.toml` + `uv.lock`、Python 3.13 固定、`protobuf`/`asyncpg` 除去、Render のビルド設定切り替え）→ 詳細は付録D | 片付け | `main`（段階ごとに直接コミット・付録D参照） |
| 1-3 | `timeline.py`・`timeline.py.bak` の処分、スパイク2本の扱い決定、fork由来の `deploy.yml` 削除、マージ済みブランチ整理 | 片付け | `chore/housekeeping` |
| 1-3b | **フロントの lock ファイル二重問題を解消**（npm / yarn のどちらを正とするか決め、負けた方の lock を削除）→ 詳細は付録C | 片付け | `chore/housekeeping` |
| 1-4 | pytest 導入＋純粋関数テスト3本 | テスト | `test/pure-functions` |
| 1-5 | レスポンスに `plan` を追加（バックエンド→フロント、store に入れるまで） | 実装 | `feature/plan-payload` |
| 1-6 | ADR-0001 を書く（しおりデータをチャットレスポンスに同梱する決定と理由） | 記録 | 1-5 と同じ |
| 1-7 | CLAUDE.md・要件定義書 v2.0 を実態に合わせる | 記録 | `docs/update-v2` |

**テスト3本の対象**（いずれも外部APIを呼ばない純粋関数）

| 対象 | 何を確かめるか |
|---|---|
| `_add_minutes`（wrapped_tools.py:208） | `"23:30"` + 45分 → `"00:15"`。日付跨ぎ |
| `_distance_km`（wrapped_tools.py:189） | 既知の2地点で妥当な値。同一地点なら 0 |
| `_dedupe_by_area`（wrapped_tools.py:242） | 近接候補が1件に集約され、離れた候補は残る |

**達成条件**

```bash
grep -c "==" backend/requirements.txt           # 依存数と一致（全て固定）
cd backend && pytest -q                          # → "3 passed"
curl -s -X POST localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $ACCESS_KEY_OWNER" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"鎌倉を3時間観光したい"}]}' \
  | jq '.plan.stops | length'                    # → 2 以上
ls docs/adr/                                     # → 0001-*.md が存在
```

**週末時点の状態**: 画面は従来どおり。裏で座標がフロントに届いている。

---

### Week 2（9/30〜10/6）レイアウトとCI

**目的**: 地図を置く「場所」と、壊れたら気づく「仕組み」を作る

| # | タスク | ブランチ |
|---|---|---|
| 2-1 | `App.tsx` を flex row 化、`MapPanel` コンポーネント新規作成 | `feature/split-layout` |
| 2-2 | 右パネルに `plan.stops` の名前を訪問順に並べる（地図はまだ無し） | 同上 |
| 2-3 | GitHub Actions：push で `pytest -q` と `npm run build` を実行 | `chore/ci` |

`App.tsx:77-84` の外側 div を flex row にして `<Chat />` の横に `<MapPanel />` を並べる。`Chat` は既に `flex-1` なので、`Chat.tsx` と `ChatContent.tsx` は触らずに済む見込み。

**達成条件**

```bash
cd frontend && npm run build                     # exit 0
gh run list --limit 1                            # → success
```

＋ 画面右に訪問順の名前リストが出る／チャットが従来どおり動く（退行チェック）

**週末時点の状態**: 左右分割が完成。右は地図の代わりに名前リスト。ここで止めても成果物として成立する。

**メモ**: 4週間で最も軽い週。余力があれば 3-1 を前倒しする。

---

### Week 3（10/7〜10/13）地図とピン ← 山場

| # | タスク | ブランチ |
|---|---|---|
| 3-1 | フロント用 Google Maps APIキーを新規発行＋HTTPリファラ制限 | （設定のみ） |
| 3-2 | `@vis.gl/react-google-maps` 導入、地図描画 | `feature/map-panel` |
| 3-3 | `stops` を訪問順の番号付きマーカーで配置 | 同上 |
| 3-4 | 全ピンが収まるよう表示範囲を自動調整 | 同上 |
| 3-5 | ADR-0002 を書く（地図ライブラリの選定理由、Leaflet を採らなかった理由） | 同上 |

**3-1 は必須**。バックエンドの `GOOGLE_MAPS_API_KEY` を流用してはいけない。Vite の `VITE_` 環境変数はビルド成果物に埋め込まれて誰でも読めるため、Places/Routes を叩き放題にされる。必ず別キー＋リファラ制限で。

**達成条件**

```bash
cd frontend && npm run build                     # exit 0
cd backend && pytest -q                          # 退行なし
```

＋ ピンの数が `jq '.plan.stops | length'` と一致

---

### Week 4（10/14〜10/21）仕上げとリリース

| # | タスク | 分類 |
|---|---|---|
| 4-1 | `plan` 未確定時・エラー時の表示（地図が空のときの見え方） | Must |
| 4-2 | 通し動作確認（受け入れ条件1〜7を上から順に） | Must |
| 4-3 | README 更新（起動手順・v1.0.0 の機能・スクリーンショット） | Must |
| 4-4 | CHANGELOG.md 作成 | Must |
| 4-5 | `v1.0.0` タグを打つ | Must |
| 4-6 | 経路線（polyline）／ピンクリックで詳細 | Should |

**polyline について**: `get_walking_leg`（tools.py:130-133）の FieldMask が `routes.duration,routes.distanceMeters` だけで、経路の形状を取得していない。線を描くには `routes.polyline.encodedPolyline` を追加し、`legs` に保存する必要がある。変更は数行だが、Routes API の課金ティアが変わらないか事前に確認すること。

**達成条件**

```bash
git tag                                          # → v1.0.0 が存在
cd backend && pytest -q                          # exit 0
cd frontend && npm run build                     # exit 0
cat CHANGELOG.md                                 # v1.0.0 の内容が記載されている
```

---

## 4. 運用ルール（4週間を通じて）

### Definition of Done（1タスクの完了条件）

以下が全部揃って初めて「終わった」とする。

1. ブランチを main にマージした
2. マージ済みブランチをローカル・リモート両方で削除した
3. CI が通っている
4. 設計判断があったなら ADR を書いた
5. 作業中の一時ファイル・`.bak` を残していない

### ADR の運用

- 置き場所: `docs/adr/NNNN-短い題名.md`
- 遡って過去の決定を起こさない。既存のコードコメント7箇所はそのまま残す
- 書くのはこれから下す決定だけ。4週間で2本（ADR-0001, 0002）が発生する想定
- 書く基準: 「なぜそうしなかったのか」を後から聞かれそうな決定。実装の細部は書かない

### コミット

- Conventional Commits を継続
- 「〜改修中」のような WIP コミットを main に入れない。ブランチ内なら可、マージ前に整理する
- 1コミット＝そのコミットに巻き戻してアプリが動く単位

---

## 5. 前提と未確定事項

| # | 前提 | 違う場合の影響 |
|---|---|---|
| 1 | 週あたり10時間程度（平日夜2h×3＋週末4h）**※未確認** | 少ない場合、Week 4 の Should を全部落として v1.1.0 へ回す |
| 2 | pytest 未経験。Week 1 に2〜3時間の学習コストを見込む | 経験があれば Week 1 に余裕が生まれる |
| 3 | Week 1 の片付け（1-1〜1-3）は数時間で終わる | 予算アラート設定に詰まると Week 1 が押す |

---

## 6. 次フェーズ以降（v1.0.0 の後）

| バージョン | 内容 |
|---|---|
| v1.1.0 | おすすめ精度の向上。**`build_route` のモックテストを書くところから始める**（7連続 `fix:` の再発防止） |
| v1.2.0 想定 | 認証の作り替え（Google OAuth の自作 → 余力があればパスキー） |
| 未定 | しおりの永続化、地図の双方向操作、車・公共交通機関 |

---

## 7. 更新履歴

| 日付 | 版 | 変更内容 | 理由 |
|---|---|---|---|
| 2026-09-23 | v1.0 | 初版作成 | 要件定義書 v1.1 と実装のズレを整理し、4週間のスコープと受け入れ条件を確定 |
| 2026-09-23 | v1.1 | 1-1 完了を記録／付録A（CLAUDE.md の修正箇所）を追加 | 会話のコンパクト化で失われないよう、具体的な修正内容をファイルに固定 |
| 2026-09-23 | v1.2 | タスク 1-3b（lock ファイル二重問題）と付録C を追加 | 依存管理の学習中に発見。ファイル更新日時が証拠になっており、`install` を一度でも実行すると失われるため即座に記録 |
| 2026-09-24 | v1.3 | タスク 1-2 を「`requirements.txt` の `==` 固定」から「uv 移行」に変更／付録D を追加／`.gitignore` から `docs/` を外し個人メモを `notes/` へ分離 | Render が uv をネイティブサポートしていると判明し、ADR-0002 の却下理由が事実として成立しなくなった。併せて Python 3.10 の EOL が 2026-10-31（37日後）と判明し、バージョン固定の緊急度が上がった |

---

## 付録A. CLAUDE.md の修正箇所（タスク 1-7 用）

ルート `CLAUDE.md` の記述が現在のコードと食い違っている。1-7 で以下を修正する。

| CLAUDE.md の記載 | 実際 |
|---|---|
| Gemini に6つのツールを登録（`geocode_place` / `search_nearby_location` / `get_walking_leg` / `select_places` / `set_start_time` / `reorder_places`） | **`build_route` ただ1つだけ**（main.py:104） |
| `timeline.py` がMarkdown表を生成して応答に追記 | **追記していない**。2026-09-05 に廃止（main.py:133-135）。`timeline.py` 114行は死蔵の可能性 → 1-3 で処分を判断 |
| ラッパーは `make_select_places` / `make_set_start_time` / `make_reorder_places` | main.py が import しているのは `make_build_route` |
| ファイル名 `wraped_tools.py` | 実際は `wrapped_tools.py`（綴りミス） |

要件定義書（`観光地巡りアプリ_要件定義書.md`）側の修正点：

| 記載 | 実際 |
|---|---|
| デプロイ先：AWS App Runner | Render（バックエンド）＋ Vercel（フロント） |
| 地図・しおりパネルを自作して1画面に配置 | 未着手。v1.0.0 で地図のみ実装、しおりはチャット本文のまま |
| 移動手段：徒歩・車・公共交通機関 | 徒歩のみ。車・公共交通は v1.0.0 スコープ外 |
| ルート変更：スポットを別の場所に差し替え | `reorder_places`（順序変更）のみ実装 |
| 認証・ログイン機能はスコープ外 | Basic認証＋アクセスキーを実装済み |
| 観光地データは PostgreSQL | Google Places API に移行済み。`sql/` `DB/` `scripts/` は死蔵 |
| ローカル開発は Docker Compose | 使っていない |

---

## 付録B. 「リファクタリング」の3分類

作業を分類してから着手する。混同すると終わりが無くなる。

| | 定義 | テスト必須？ | いつやるか |
|---|---|---|---|
| ① 片付け（衛生作業） | 死蔵コード削除、依存固定、設定整理 | 不要（構造を変えないため） | いつでも |
| ② 準備リファクタリング | ある機能を載せやすくするための構造変更 | **必須** | その機能の直前 |
| ③ 大掃除リファクタリング | 目的を伴わない全体整理 | 必須 | **やらない**（終わりが無い） |

`wrapped_tools.py` の分割は現時点では③に当たるため行わない。v1.1.0（おすすめ精度向上）の直前に、テストを書いた上で②として実施する。

---

## 付録C. フロントエンドの lock ファイル二重問題（タスク 1-3b 用）

**発見日**: 2026-09-23（依存管理の学習中に判明。当初のタスク一覧には無かった項目）

### 観測された事実（2026-09-23 時点・未操作の状態）

```
frontend/package-lock.json   286,855 bytes   Jul  6 22:24   ← npm が生成
frontend/yarn.lock           172,118 bytes   Aug 25 22:55   ← yarn が生成
frontend/package.json          2,737 bytes   Aug 25 22:55
```

| 項目 | 値 |
|---|---|
| git の追跡状況 | **両方とも追跡されている**（`git ls-files frontend/ \| grep -i lock` で確認） |
| `package.json` の直接依存 | dependencies 26 / devDependencies 19 = **45個** |
| `yarn.lock` に記録されたパッケージ | **597個**（差の552個は推移的依存） |
| `vercel.json` | **存在しない** → Vercel はダッシュボード設定でビルドしている |
| `.npmrc` / `.yarnrc` | **存在しない** → パッケージマネージャの明示的な指定が無い |
| `package.json` 内の yarn 参照 | `electron` / `pack` / `make` スクリプトのみ（fork元由来、本プロジェクトでは未使用） |
| CLAUDE.md の記載 | `npm run dev` / `npm run build` |

### 追加証拠（2026-09-24 判明）

`node_modules/` の最終更新時刻が `yarn.lock` と `package.json` と完全に一致する。

```
2026-08-25 22:55   node_modules/        （476 パッケージ）
2026-08-25 22:55   yarn.lock
2026-08-25 22:55   package.json
2026-07-06 22:24   package-lock.json    ← fork 時点で凍結、以後未更新
```

3ファイルが同一時刻であることは、**同じ `yarn install` が3つすべてを書いた**ことを意味する。`package-lock.json` だけが2か月半前で止まっている。**yarn が実際に使われているパッケージマネージャと判断してよい根拠がこれで3点揃った**（git 追跡状況・ファイル更新日時・node_modules の同期）。

この証拠も `install` を一度実行すれば失われる。1-3b の判断時は、まず Vercel ダッシュボードの Install Command を確認して4点目の裏取りをすること。

### なぜ問題か

`yarn.lock` は `package.json` と**同一時刻**に更新されている一方、`package-lock.json` は fork した 7/6 から**停止している**。
つまり2つの lock は**異なる依存解決結果**を保持している可能性が高い。

- `npm install` → 7/6 時点の古い解決結果が入る
- `yarn install` → 8/25 時点の解決結果が入る
- Vercel はビルド時に lock ファイルからパッケージマネージャを推定するため、**両方あるとどちらが選ばれるか確定できない**

backend の `asyncpg` 問題（requirements.txt に記載があるが venv には無い＝ローカルと本番で中身が違う）と**同じ構図**。

### ⚠️ 判断するまでの禁止事項

**`npm install` / `yarn install` を実行しないこと。**
実行した側の lock が更新され、上の「更新日時の差」という証拠が消える。この差が、どちらが実際に使われてきたかを示す唯一の手がかり。

### 判断手順（1-3b でやること）

1. **Vercel のダッシュボードで Install Command / ビルドログを確認する**
   → 本番が実際にどちらで入れているかが分かる。**ここが最優先の判断材料**
2. npm / yarn のどちらを正とするか決める
   - 判断材料: 本番の実績（手順1）、CLAUDE.md の記載（npm）、lock の更新日時（yarn が新しい）
   - 参考: Vercel は Node 標準の npm で動かすのが最も素直
3. 負けた方の lock を `git rm` する
4. 採用した方で `install` し直し、`npm run build` / `npm run dev` が通ることを確認
5. CLAUDE.md にパッケージマネージャを明記する（どちらに決めても、**書いていないことが再発原因**になる）
6. 判断理由を ADR に残すか検討（軽微なら CLAUDE.md への追記で十分）

### 達成条件

| # | コマンド | 期待する出力 |
|---|---|---|
| 1 | `ls frontend/ \| grep -c lock` | `1` |
| 2 | `git ls-files frontend/ \| grep -c lock` | `1` |
| 3 | `cd frontend && npm run build`（採用した方で） | 成功 |
| 4 | `grep -c "npm\|yarn" CLAUDE.md` | 1以上（使用するものが明記されている） |
---

## 付録D. uv 移行手順（タスク 1-2 用）

決定内容とその理由は `docs/adr/0002-dependency-pinning.md` を参照。ここには手順と達成条件だけを書く。

### 原則：新しい経路を用意 → 切り替え → 古い経路を撤去

本番に触る変更では常にこの3段階を取る。逆順にすると、切り替え先が無い状態で古い経路を壊すことになる。

さらにこの移行では **Python 3.13 化と uv 化という2つの変更が同時に起きる**ため、失敗したときに原因が切り分けられない。そこで両者を別の段階に分け、それぞれ単独で検証する。

| 段階 | 変えるもの | 本番への影響 | 検証されること |
|---|---|---|---|
| 1 | ローカルのみ | なし | uv と Python 3.13 でアプリが動くか |
| 2 | `.python-version` を push | **本番の Python が 3.13 になる**（依存は従来の pip） | **Python 3.13 単独** |
| 3 | `pyproject.toml` + `uv.lock` を push | なし（Build Command は未変更） | — |
| 4 | Render の Build / Start Command | **本番が uv 経由になる** | **uv 単独** |
| 5 | `requirements.txt` 削除 | なし | — |

段階2と段階4のあいだに段階3を挟むことで、片方が壊れたときにどちらが原因か確定できる。

---

### 段階1：ローカルで uv 環境を作る

```bash
# uv をインストール（未インストール）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version

cd backend

# ① pyproject.toml だけを作る
uv init --bare

# ② Python 3.13 を入れて固定する（.python-version が作られる）
uv python install 3.13
uv python pin 3.13
```

`--bare` は必須。付けないと `main.py` や `README.md` を生成して既存ファイルと衝突する。

**順序も重要。** `uv init` は `.python-version` を自分で書くことがあるため、`pin` を先にやると上書きされうる。**init → pin の順**にして、最後に書いた値が残るようにする。

```bash
# 依存を追加（uv.lock が生成される）
uv add fastapi google-genai pydantic python-dotenv requests uvicorn
```

- `protobuf` と `asyncpg` は入れない（コード中で未使用／`main.py` の import グラフ外）
- バージョンは指定しない。uv が解決して `pyproject.toml` に `>=` を、`uv.lock` に `==` とハッシュを書く

### 関門①：ローカルで動くことを確認する（Render に触る前に必ず通す）

| # | コマンド | 期待する結果 |
|---|---|---|
| 1 | `uv run python --version` | `Python 3.13.x` |
| 2 | `uv run python -c "import main"` | エラーなし |
| 3 | `grep -c 'name = ' uv.lock` | 30 以上（推移的依存も記録されている） |
| 4 | `uv run uvicorn main:app --reload` | 起動して `http://localhost:8000` が応答する |
| 5 | フロントから会話を1往復し、ルートが出る | 出る |

**5 が最重要。** `import` が通っても、Gemini API と Google Maps API の呼び出しが 3.13 で動く保証はない。ここまで通して初めて段階2に進む。

`.env` は `backend/` 直下にあるので、`uv run` も `backend/` で実行する。

### ⚠️ pyenv との `.python-version` 衝突（2026-09-24 判明）

このマシンの `.zshrc` には Python のバージョン管理ツールが3つ入っている。

| 行 | ツール |
|---|---|
| `.zshrc:4` | conda（anaconda3） |
| `.zshrc:17` | pyenv |
| `.zshrc:26` | uv |

**pyenv と uv は同じファイル名 `.python-version` を読む。** `uv python pin 3.13` を実行すると、`backend/` で素の `python` / `python3` を叩いたときに pyenv が反応してこうなる。

```
pyenv: version `3.13' is not installed
```

uv が入れた Python 3.13 は `~/.local/share/uv/python/` にあり、pyenv はそこを見ないため。**これは故障ではなく、2つのツールが同じファイルを別の意味で解釈しているだけ。**

**対処：`uv run` 経由でしか Python を呼ばない。** `uv run python`, `uv run uvicorn main:app --reload` を使い、素の `python` を `backend/` で叩かない。uv の標準的な使い方そのままなので追加コストはない。

pyenv / conda の整理（uv 一本化）は筋が通っているが、**段階4の通過後に別タスクとして行う。** 移行中にやると「uv が動かない」のか「pyenv を消した副作用」なのか切り分けられなくなる。

**関門①で落ちた場合**：原因が Python 3.13 なら `uv python pin 3.12` に下げて再試行する。3.12 のサポート期限は 2028年なので、EOL 問題は解決したまま後退できる。

---

### 段階2：`.python-version` だけを push（Python 3.13 を単独で検証）

> **⚠️ 訂正（2026-09-24）：フィーチャーブランチは使わない。**
> Render は追跡ブランチ（`main`）しかデプロイしないため、ブランチに push しても
> 本番で検証できない。段階2の目的（Python 3.13 を本番で単独検証する）が
> 達成できないので、**`main` に段階ごとに直接コミットする**。
> ブランチの代わりに「1コミット＝1変更」が安全装置になる（`git revert` 1回で戻せる）。

```bash
git add backend/.python-version
git status --short          # このファイルだけが緑か確認
git commit -m "chore: Python のバージョンを 3.13 に固定"
git push origin main        # ← Render の自動デプロイが走る
```

Render の Root Directory が `backend` なので `backend/.python-version` がサービスのルートとして読まれる。**Build Command は `pip install -r requirements.txt` のままなので、依存の解決方法は変わらず、Python のバージョンだけが変わる。**

`.python-version` が効かない場合は、Render の環境変数 `PYTHON_VERSION` に `3.13` を設定する。

### 関門②：本番が 3.13 で動くことを確認する

| # | 確認場所 | 期待 |
|---|---|---|
| 1 | Render のビルドログ | Python 3.13.x が使われている |
| 2 | Render のビルドログ | `pip install` が成功している |
| 3 | 本番 URL で会話を1往復 | ルートが出る |

ここで落ちたら段階3以降に進まない。`.python-version` のコミットを revert すれば元に戻る（uv には一切触れていないため、切り戻しが1コミットで済む）。

---

### 段階3：`pyproject.toml` + `uv.lock` を push（本番は無変化）

```bash
git add backend/pyproject.toml backend/uv.lock
git status --short
git commit -m "chore: 依存管理を uv に移行（pyproject.toml + uv.lock を追加）"
```

Build Command はまだ `pip install -r requirements.txt` なので、**この push で本番の挙動は変わらない。** Render に `uv.lock` を配置し、次の段階の準備をするだけ。

`.venv/` は `.gitignore` 済みなのでコミットされない。`uv.lock` は**必ずコミットする**（これが「事実」ファイル本体）。

---

### 段階4：Render の設定を切り替える（uv を単独で検証）

Render ダッシュボード → 該当サービス → Settings で2箇所を変更する。

| 項目 | 変更前 | 変更後 |
|---|---|---|
| Build Command | `pip install -r requirements.txt` | `uv sync --frozen` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` | `uv run uvicorn main:app --host 0.0.0.0 --port $PORT` |

`--frozen` は必須。これを外すと `uv.lock` がビルド中に再解決され、固定した意味が失われる。

変更後、**Manual Deploy を実行する**（自動デプロイを待たない。いつ走ったか分からない状態で検証しないため）。

### 関門③：本番が uv 経由で動くことを確認する

| # | 確認場所 | 期待 |
|---|---|---|
| 1 | Render のビルドログ | `uv sync` が実行されている |
| 2 | 同 | ビルド時間が pip より短くなっている |
| 3 | 同 | `Resolved N packages` の N が 30 以上 |
| 4 | 本番 URL で会話を1往復 | ルートが出る |

**切り戻し手順**：Build / Start Command を変更前の値に戻して Manual Deploy。ファイルは触らないので git 操作は不要。

---

### 段階5：`requirements.txt` を削除する

関門③を通過してから実行する。

```bash
git rm backend/requirements.txt
git commit -m "chore: uv 移行に伴い requirements.txt を削除"
```

これを段階4より前にやるとビルドが失敗する（Build Command が存在しないファイルを参照する）。

---

### 達成条件（タスク 1-2 の完了判定）

| # | コマンド / 確認 | 期待 |
|---|---|---|
| 1 | `ls backend/pyproject.toml backend/uv.lock backend/.python-version` | 3つすべて存在する |
| 2 | `cat backend/.python-version` | `3.13` |
| 3 | `ls backend/requirements.txt` | `No such file` |
| 4 | `grep -ciE 'asyncpg\|protobuf' backend/uv.lock` | `0` |
| 5 | `git ls-files backend/ \| grep -c 'uv.lock'` | `1`（追跡されている） |
| 6 | `git ls-files backend/ \| grep -c '.venv'` | `0`（追跡されていない） |
| 7 | Render のビルドログ | `uv sync --frozen` が成功している |
| 8 | 本番 URL で会話を1往復 | ルートが出る |

### 移行後に更新が必要なファイル

| ファイル | 変更内容 |
|---|---|
| `CLAUDE.md` | 起動手順を `source venv/bin/activate && uvicorn ...` から `uv run uvicorn main:app --reload` に変更。タスク 1-7（付録A）と併せて実施 |
| `README.md` | 技術スタックに uv を追記 |

### 撤去するもの

- `backend/venv/`（古い Python 3.10 の仮想環境）。`.gitignore` 済みなので git 操作は不要。`rm -rf backend/venv` で削除する。**関門③を通過してから実行する**（切り戻し先として残しておく）
