# v1.0.0 開発プラン（地図表示まで）

- **期間**: 2026-09-23 〜 2026-11-01（当初は 10/21 まで。2026-10-11 の再計画で延長。下記「再計画」参照）
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
| 3 | ルート確定時、全訪問先に訪問順の番号付きピンが立ち、起点には別の印が立つ | 番号付きピン数 == `jq '.plan.visits \| length'`（形は ADR-0001） |
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
| 1-2 | ~~**uv へ移行**（`pyproject.toml` + `uv.lock`、Python 3.13 固定、`protobuf`/`asyncpg` 除去、Render のビルド設定切り替え）→ 詳細は付録D~~ **✅ 完了 2026-09-27**（達成条件 8/8） | 片付け | `main`（段階ごとに直接コミット） |
| 1-3 | `timeline.py`・`timeline.py.bak` の処分、スパイク2本の扱い決定、fork由来の `deploy.yml` 削除、マージ済みブランチ整理 | 片付け | `chore/housekeeping` |
| 1-3b | ~~**フロントの lock ファイル二重問題を解消**（npm / yarn のどちらを正とするか決め、負けた方の lock を削除）~~ **✅ 完了 2026-10-26**（yarn を採用。Vercel のビルドログで `yarn install v1.22.19` を確認し `package-lock.json` を削除。結果は付録C末尾） | 片付け | `chore/housekeeping` |
| 1-4 | ~~pytest 導入＋純粋関数テスト3本~~ **✅ 完了 2026-10-11**（3関数に対しテスト関数5本、`9 passed`。`_distance_km` の「同一地点なら 0」は未テスト） | テスト | `test/pure-functions` |
| 1-5 | ~~レスポンスに `plan` を追加（バックエンド→フロント、store に入れるまで）~~ **✅ 完了 2026-10-22**（バックエンド：`b72b314` `to_plan`＋テスト3本・`12 passed`／`c4f6b89` 応答に同梱。フロント：`57261b6` `plan-slice`（チャット `id` → `Plan \| null`、永続化しない）。ローカルで1往復し、未完成時 `null`→完成時に同じ `id` へ中身が入ることをコンソールで確認） | 実装 | `feature/plan-payload` |
| 1-6 | ~~ADR-0001 を書く（しおりデータをチャットレスポンスに同梱する決定と理由）~~ **✅ 完了 2026-10-11**（Accepted。1-5 の設計と並行して記録、`59efc42`・`72cdfb1`） | 記録 | 1-5 と同じ |
| 1-7 | CLAUDE.md・要件定義書 v2.0 を実態に合わせる | 記録 | `docs/update-v2` |

#### Week 1 の棚卸し（2026-09-27）

1-1・1-2 が完了し、残り6タスク・約6時間。**Week 1 は残り3日**（9/27・28・29）。

**推奨する着手順序（上の表の並びとは異なる）**

| 順 | # | 見積 | この順にする理由 |
|---|---|---|---|
| 1 | **1-4** | 90分 | **1-2 の投資を回収するタスク。** ADR-0002 が uv 移行を正当化した理由そのものが「テストの失敗原因を自分の変更だけに絞る」だった。依存が完全に固定された今、テストが落ちたら原因は100%自分のコード |
| 2 | 1-5 | 120分 | Week 1 唯一の実装。1-4 のテストが安全網になる |
| 3 | 1-6 | 40分 | 1-5 で下した決定を記録するので、1-5 の後でなければ書けない |
| 4 | 1-3b | 20分 | 証拠3点が揃い判断はほぼ確定。実質的な期限は **Week 3 の地図**（フロントで初めて依存を追加するとき） |
| 5 | 1-3 | 40分 | 判断基準「その片付けは、次にやる作業の前提になっているか？」が **No**。1-4・1-5 は `timeline.py` に触らない |
| 6 | 1-7 | 60分 | 最終状態を記録するので最後。**溢れた場合はこれを Week 2 に送るのが最も影響が小さい**（他の作業を止めない） |

**根拠の出どころ**：1-4 を先頭にしたのは ADR-0002 の文脈「Week 1 でテストを導入する予定がある。テストの失敗原因が2つあると警報として機能しない」。1-3 を後ろに回したのは上記の片付け判断基準の再適用。

**週10時間という前提の検証**：タスク 1-2 は 9/23 着手 → 9/27 完了（4日）。ただしこれは学習に大半を使った結果（TOML/lock の仕組み、ADR の書き方、Render の uv 対応調査、段階的移行の設計）。残り6タスクに同じ密度の学習は含まれないため6時間の見積は妥当と判断する。

**テスト3本の対象**（いずれも外部APIを呼ばない純粋関数）

| 対象 | 何を確かめるか |
|---|---|
| `_add_minutes`（wrapped_tools.py:208） | `"23:30"` + 45分 → `"00:15"`。日付跨ぎ |
| `_distance_km`（wrapped_tools.py:189） | 既知の2地点で妥当な値。同一地点なら 0 |
| `_dedupe_by_area`（wrapped_tools.py:242） | 近接候補が1件に集約され、離れた候補は残る |

**達成条件**

```bash
test ! -f backend/requirements.txt               # → 終了コード 0（uv へ移行済み）
grep -c '^name = ' backend/uv.lock                # → 32（31依存 + backend 自身）
cd backend && uv run pytest -q                   # → failed 0（2026-10-11 時点で "9 passed"）
grep -c '^def test_' backend/tests/test_wrapped_tools.py   # → 5（3関数を対象にテスト関数5本）
cd backend && uv run pytest --collect-only | grep -c 'test_gemini\|test_plases'   # → 0（実APIを叩く探索スクリプトを収集しない）
cd backend && uv run pytest --collect-only | grep 'testpaths'   # → "testpaths: tests"
uv run --project backend python -c "import tomllib;print(sum('pytest' in x for x in tomllib.load(open('backend/pyproject.toml','rb'))['project']['dependencies']))"   # → 0（pytest は dev グループのみ）
curl -s -X POST localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $ACCESS_KEY_OWNER" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"鎌倉を3時間観光したい"}]}' \
  | jq '.plan.visits | length'                   # → 1 以上（課金あり。実行前に確認）
ls docs/adr/                                     # → 0001-*.md が存在
```

**週末時点の状態**: 画面は従来どおり。裏で座標がフロントに届いている。

---

### 再計画（2026-10-11）：リリース日を 10/21 → 11/1 に移す。Must は維持

**経緯**：Week 1 の残り5タスクが約10日の中断で未着手のまま、暦は Week 3 に入った。10/11 時点で 1-1・1-2・1-4 が完了。残りの Must（1-5 の `plan` 追加 → 左右分割 → 地図とピン → 仕上げ）を 10/21 までの10日間に収めるのは現実的でないと判断した。

**決定**：Must（受け入れ条件1〜7）は削らずリリース日を動かす。地図とピンが v1.0.0 の中心であり、削ると v1.0.0 の意味がなくなるため。

**以降の割り当て（このあとの Week 2〜4 の見出しの日付は当初のもの。割り当ては本表を正とする）**

| 期間 | タスク | 週末時点の状態 |
|---|---|---|
| 10/12〜10/18 | 1-5 → 1-6 → 1-3b → 3-1 → 2-1・2-2 → 2-3 | 左右分割が完成。右は名前リスト。`plan` がフロントに届く |
| 10/19〜10/25 | 3-2 → 3-3 → 3-4 → 3-5 | 地図に番号付きピンが立ち、表示範囲が自動調整される |
| 10/26〜11/1 | 4-1 → 4-2 → 4-3 → 4-4 → 4-5、余力で 1-3、1-7、4-6（Should） | `v1.0.0` タグ |

- 1-3（`timeline.py` 等の処分）と 1-7（CLAUDE.md・要件定義書 v2.0）は、次にやる作業の前提になっていないため最終週に回す。溢れる場合は 1-7 を `v1.0.0` タグの後に送る（受け入れ条件には含まれない）。
- 週10時間という前提は引き続き**未確認**。違う場合は 10/12 週の実績で割り当てを引き直す。
- 来週の見積のうち 2-1・2-2（約3時間）、2-3（約1時間）、3-1（約20分）は計画書に元の見積がなく、目安（推測）である。

### Week 2（9/30〜10/6）レイアウトとCI

**目的**: 地図を置く「場所」と、壊れたら気づく「仕組み」を作る

| # | タスク | ブランチ |
|---|---|---|
| 2-1 | ~~`App.tsx` を flex row 化、`MapPanel` コンポーネント新規作成~~ **✅ 完了 2026-10-27**（右パネル幅 40%、md 未満では非表示。HTML モックで見た目を確認してから実装） | `feature/split-layout` |
| 2-2 | ~~右パネルに `plan.origin` と `plan.visits` の名前を訪問順に並べる（地図はまだ無し）~~ **✅ 完了 2026-10-27**（S＋番号の印、時刻・徒歩の時間と距離も表示。ローカルで1往復し5か所のリストを確認） | 同上 |
| 2-3 | ~~GitHub Actions：push で `pytest -q` と `npm run build` を実行~~ **✅ 完了 2026-10-27**（`.github/workflows/ci.yml`。backend は `uv sync --locked` → `uv run pytest -q`、frontend は `yarn install --frozen-lockfile` → `yarn build`。lock がずれていたら書き換えずに失敗させる。secrets なし。部品は Node.js 24 対応の checkout v7・setup-node v7・setup-uv v10.3.0（setup-uv は `@v10` の印がなく、細かい番号まで書かないと `unable to find version` で失敗する）。`gh` が入っていないため、結果は GitHub API の `actions/runs` の `conclusion: success` で確認） | `chore/ci` |

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
| 3-1 | ~~フロント用 Google Maps APIキーを新規発行＋HTTPリファラ制限~~ **✅ 完了 2026-10-26**（Maps JavaScript API を有効化。リファラは `http://localhost:5173/*` と `https://prj-tourism-route-planner.vercel.app/*`、API は Maps JavaScript API のみ。変数名 `VITE_GOOGLE_MAPS_API_KEY` を `frontend/.env` と Vercel（Production、Config 型）に登録。このキーで Geocoding を叩くと `REQUEST_DENIED` になることを curl で確認） | （設定のみ） |
| 3-2 | ~~`@vis.gl/react-google-maps` 導入、地図描画~~ **✅ 完了 2026-10-27**（**1.6.1 に固定**：1.7.0 以降は `JSX.IntrinsicElements` に `gmp-*` タグを足し、`react-markdown` 8系の型が壊れて `yarn build` が失敗する。上げるときは `react-markdown` の更新が先。右パネル上半分に出発地中心の地図。ビルド成果物のキーは1種類のみ） | `feature/map-panel` |
| 3-3 | ~~`visits` を訪問順の番号付きマーカーで、`origin` を別の印で配置~~ **✅ 完了 2026-10-28**（`799235d`。出発地は青の S、訪問先は赤の番号。右のリストと同じ色。`AdvancedMarker` に要るマップ ID は、未設定なら開発用の `DEMO_MAP_ID` を使う。ダークテーマでは地図も暗い配色にする） | 同上 |
| 3-4 | ~~全ピンが収まるよう表示範囲を自動調整~~ **✅ 完了 2026-10-28**（`1578739`。`FitToPlan` で `fitBounds`、余白 48px。地点が1つだけのときはズーム 15 に固定。3-3 と合わせてローカルで1往復し、画面で確認） | 同上 |
| 3-5 | ADR-0002 を書く（地図ライブラリの選定理由、Leaflet を採らなかった理由） | 同上 |

**3-1 は必須**。バックエンドの `GOOGLE_MAPS_API_KEY` を流用してはいけない。Vite の `VITE_` 環境変数はビルド成果物に埋め込まれて誰でも読めるため、Places/Routes を叩き放題にされる。必ず別キー＋リファラ制限で。

**達成条件**

```bash
cd frontend && npm run build                     # exit 0
cd backend && pytest -q                          # 退行なし
```

＋ 番号付きピンの数が `jq '.plan.visits | length'` と一致

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

**4-6 の途中経過（2026-10-28）**：経路線は「ピンどうしを訪問順に直線（点線）で結ぶ」形で先に入れた（`RouteLine`、フロントのみ・追加課金なし）。実際に歩く道に沿った線は、バックエンドで道の形を取得し `plan` の形（ADR-0001）を変える必要があるため v1.1.0 に送る。ピンクリックで詳細は未着手。

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
| 未定 | **Gemini 呼び出しを `Models.generate_content` から `Chat.send_message` に移す**（下記参照。ADR が必要） |
| 未定 | **`Guidebook` の `selected`・`legs` の1件をクラス（`Stop`・`Leg`）にする**（下記参照。ADR-0001 の改訂が必要） |

### 保留中の技術的負債：AFC 非推奨警告（2026-09-24 発見）

uv 移行で `google-genai` が 2.10.0 → 2.25.0 に上がった際、本番ログに以下が出るようになった。

```
Direct use of automatic function calling (AFC) in Models.generate_content is not recommended.
Instead, we recommend to use AFC in Chat.send_message.
```

動作には影響していない（`200 OK`、会話も成立）。ただし2つの意味を持つ。

1. **書き方が SDK の推奨から外れている。** 将来のメジャー更新で壊れる可能性がある
2. **自作したセッション管理が不要かもしれない。** 現在 `main.py` は「第一声の SHA-256 ハッシュ」をキーに `sessions` 辞書でセッションを自作している（フロントが会話IDを送らないため）。`Chat` API はセッションを SDK 側で保持するため、この自作部分が置き換えられる可能性がある

**v1.0.0 では手を付けない。** 理由：

- 動いているものを移行の途中で触らない
- `generate_content` → `Chat` はリクエスト処理の構造変更であり、タスク 1-2（依存管理）のスコープ外
- セッション管理の設計判断を含むため、**ADR を書くべき変更**。勢いでやる作業ではない

着手する際の前提：`build_route` のモックテスト（v1.1.0 の先頭項目）が先に必要。テストなしでリクエスト処理の構造を変えると、壊れたことに気づけない。

### 保留中のリファクタリング：`Guidebook` の中身をクラスにする（2026-10-12 メモ）

**きっかけ：** 1-5 で `to_plan` の入力を調べたとき、`selected`・`legs` の1件にどんなキーがあるかが、`build_route` の中の辞書リテラル（`stops = [{...}]`・`stops.append({...})`・`legs.append({...})`）を読まないと分からなかった。`Guidebook` には `selected: list[dict]` としか書かれておらず、中身の形がどこにも宣言されていない。

**やりたいこと（ユーザーの希望。`to_plan` が動くのを確認した後、Claude が修正する）：**
`Stop`・`Leg` をクラス（dataclass）にし、`stop["name"]` を `stop.name` で読めるようにする。`models/guidebook.py` を見ればキーが分かる状態にする。

**検討した3案（2026-10-12）：**

| 案 | 内容 | 規模 |
|---|---|---|
| A | 変えない。`to_plan` の docstring にキーを書く | 数行 |
| B | `TypedDict` で `Stop`・`Leg` の型を宣言する。動作は変わらない | 20〜30行 |
| **C（希望）** | `Stop`・`Leg` をクラスにする | `build_route`・`reorder_places`・`prompts.py`（`asdict`）・`to_plan` に波及 |

**着手前に確認すること：**

- ADR-0001 の「実装の方針」に「`Guidebook` の形は v1.0.0 では変えない」とある。C はこれに反するので、ADR-0001 を改訂するか、新しい ADR を書く
- `build_route` にはテストがない（モックテストは v1.1.0 の先頭項目）。辞書をクラスに変えると、`stop["name"]` の書き換え漏れは `build_route` が Gemini から呼ばれた瞬間にしか分からない。`uvx ruff check` では検出できない（辞書の添字アクセスは型を見ないため）
- `prompts.py` は `asdict(guidebook)` でプロンプトに JSON を埋め込んでいる。中身を dataclass にしても `asdict` は入れ子を辞書に変換するので、AI に見える形は変わらないはず。着手時に確かめる
- `to_plan` の小さな関数（`_place`・`_travel`・`_visit`）は、引数の読み方が `stop["name"]` → `stop.name` に変わるだけで済むはず

---

## 7. 更新履歴

| 日付 | 版 | 変更内容 | 理由 |
|---|---|---|---|
| 2026-09-23 | v1.0 | 初版作成 | 要件定義書 v1.1 と実装のズレを整理し、4週間のスコープと受け入れ条件を確定 |
| 2026-09-23 | v1.1 | 1-1 完了を記録／付録A（CLAUDE.md の修正箇所）を追加 | 会話のコンパクト化で失われないよう、具体的な修正内容をファイルに固定 |
| 2026-09-23 | v1.2 | タスク 1-3b（lock ファイル二重問題）と付録C を追加 | 依存管理の学習中に発見。ファイル更新日時が証拠になっており、`install` を一度でも実行すると失われるため即座に記録 |
| 2026-09-24 | v1.3 | タスク 1-2 を「`requirements.txt` の `==` 固定」から「uv 移行」に変更／付録D を追加／`.gitignore` から `docs/` を外し個人メモを `notes/` へ分離 | Render が uv をネイティブサポートしていると判明し、ADR-0002 の却下理由が事実として成立しなくなった。併せて Python 3.10 の EOL が 2026-10-31（37日後）と判明し、バージョン固定の緊急度が上がった |
| 2026-09-27 | v1.4 | タスク 1-2 完了を記録／付録D に関門②③の実測結果と発見2件を追加 | uv 移行を段階1〜5すべて完了。ローカル `.venv`・`uv.lock`・本番の三者が31パッケージで完全一致し、`asyncpg`/`protobuf` が全環境から消滅した |
| 2026-09-27 | v1.5 | Week 1 の棚卸し（推奨着手順序と根拠）を追加／達成条件から削除済み `requirements.txt` への参照を除去／CLAUDE.md の起動手順・`npm install` 禁止・ドキュメント所在を先行修正 | セッションを跨ぐ引き継ぎの整理。`CLAUDE.md` は毎セッション自動で読まれるため、`source venv/bin/activate` を残すと新しいセッションが存在しない venv を案内してしまう。棚卸し結果は会話にしか無かったため記録した |
| 2026-10-11 | v1.6 | タスク 1-4 完了を記録（達成条件を `"3 passed"` からコマンドで判定できる5本に書き換え）／再計画（リリース日を 10/21 → 11/1 に移し、Must は維持。以降の割り当てを追加） | 約10日の中断で Week 1 の残り5タスクが未着手のまま暦が Week 3 に入り、10/21 までに Must を収めるのは現実的でなくなった。受け入れ条件の2〜4（地図・ピン・範囲調整）は v1.0.0 の中心のため、削らず日付を動かした |
| 2026-10-11 | v1.7 | `plan` の形を ADR-0001 で決定し、受け入れ条件3・1-5 の達成条件・2-2・3-3 の `plan.stops` を `plan.visits`／`plan.origin` に書き換え | 起点は訪問先ではない（集まって出発する場所）ため `visits` から分けた。起点と訪問先が同じ場所でも表せるよう、場所と役割を別のオブジェクトにした |
| 2026-10-22 | v1.8 | タスク 1-5 完了を記録（フロントの `plan-slice` を追加） | 1-5 が終わったら再計画する合意（10/18）の起点にするため |
| 2026-10-26 | v1.9 | タスク 1-3b 完了を記録（yarn を採用、付録Cに結果を追加） | Vercel のビルドログで本番が yarn と確認でき、判断材料が揃った |
| 2026-10-26 | v1.10 | タスク 3-1 完了を記録 | フロント用キーの発行と制限が済み、3-2 の前提が揃った |
| 2026-10-27 | v1.11 | タスク 2-1・2-2 完了を記録 | 左右分割と名前リストが動いた |
| 2026-10-27 | v1.12 | タスク 2-3 完了を記録 | CI が push ごとに動き、成功を確認した |
| 2026-10-27 | v1.13 | タスク 3-2 完了を記録 | 地図が右パネルに出た。ライブラリを 1.6.1 に固定した理由も残す |

---

## 付録A. CLAUDE.md の修正箇所（タスク 1-7 用）

ルート `CLAUDE.md` の記述が現在のコードと食い違っている。1-7 で以下を修正する。

> **✅ 2026-09-27 に先行修正した項目**（壊れた状態を次のセッションに引き継がないため）
> - 起動手順を `source venv/bin/activate` → `uv run uvicorn main:app --reload` に変更（旧 venv は削除済みで、そのままでは動かない）
> - 依存追加を `uv add` に統一し `pip install` を禁止する記述を追加
> - `npm install` / `yarn install` の禁止を明記（付録C への参照つき）
> - 冒頭に「ドキュメントの所在」（`docs/plan-v1.0.0.md` と `docs/adr/`）を追加
>
> 下の表の項目（ツール構成・`timeline.py`・綴りミス）は 1-7 で対応する。

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
| 2 | `git ls-files frontend/ \| grep -cE 'yarn\.lock$\|package-lock\.json$'` | `1`（単に `grep -c lock` だと `CodeBlock.tsx` にも当たって `2` になる） |
| 3 | `cd frontend && npm run build`（採用した方で） | 成功 |
| 4 | `grep -c "npm\|yarn" CLAUDE.md` | 1以上（使用するものが明記されている） |

### 結果（2026-10-26）：yarn を採用

**4点目の裏取り（Vercel のビルドログ）**

```
yarn install v1.22.19
warning package-lock.json found. Your project contains lock files generated by tools other than Yarn. ...
...
success Saved lockfile.
Running "yarn run build"
```

本番は yarn で install・ビルドしていた。yarn 自身も `package-lock.json` の混在を警告していた。

**追加で分かったこと**

| 確認 | 結果 |
|---|---|
| `node_modules/.yarn-integrity` | ある（npm の `node_modules/.package-lock.json` はない）→ ローカルの `node_modules` も yarn が作った |
| 8/25 に足した `@vercel/functions`（`middleware.ts` が使う） | `yarn.lock` には載っている、`package-lock.json` には載っていない |
| `package.json` と `yarn.lock` だけを別ディレクトリに置き、`yarn install --frozen-lockfile` | `exit=0`、`yarn.lock` は変化なし → 2つは揃っている |

Vercel のログの `success Saved lockfile.` は、`yarn.lock` がずれていたせいではない（上の3行目で確認）。原因は未確定。`package-lock.json` を消した後のデプロイでこの行と警告が消えるかを見る。

**達成条件**

| # | 結果 |
|---|---|
| 1 | `ls frontend/ \| grep -c lock` → `1` ✅ |
| 2 | `git ls-files frontend/ \| grep -cE 'yarn\.lock$\|package-lock\.json$'` → `1` ✅ |
| 3 | `yarn build` → `1475 modules transformed`、`exit=0` ✅ |
| 4 | CLAUDE.md にパッケージマネージャを yarn と明記し、依存の追加は `yarn add` と書いた ✅ |

ADR にはしない。理由は、本番の実績に揃えただけで、選択肢を比べて決めたわけではないから。
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

### 関門②の実測結果（2026-09-24）

`.python-version` を push した後の Render のビルドログ（`pip install` の出力）と、手元の `uv.lock` を突き合わせた結果。

```
本番(pip) 33個  /  uv.lock 31個

本番だけにある      : asyncpg, protobuf
uv.lock だけにある  : （なし）
バージョン相違      : （なし）← 31個すべて完全一致
```

**段階4 の切り替えで環境は変わらない。** 不要な2個（`asyncpg`, `protobuf`）が消えるだけであることが実測で確定した。「uv にしたら依存が変わって壊れる」懸念はこの時点で解消。

また ADR の文脈に書いた「本番にだけ入っている2個」が名指しで確認された。

Python 3.13 化の直接証拠：ビルドログに以下が出力された。

```
==> Using Python version 3.13.15 via /opt/render/project/src/backend/.python-version
```

- **ローカルの `.venv` と同一のパッチバージョン（3.13.15）**になった
- パスが `.../src/backend/.python-version` であることから、Render の Root Directory が `backend` として機能していることが裏付けられた（段階4で `uv sync --frozen` が `backend/uv.lock` を見つけられる根拠）

間接証拠：ログに `exceptiongroup` が無い。Python 3.10 では `anyio` がこれを必要としたが、3.11 で標準ライブラリに入ったため不要になった。**推移的依存の集合が Python のバージョンで変わる**ことの実例であり、`requirements.txt` の `==` では原理的に捉えられない差分でもある。

### ローカルと本番の差分の推移

| | 移行前 | 段階2 完了時 | 段階5 完了後（予定） |
|---|---|---|---|
| Python | ローカル 3.10.3 / 本番 不明 | **両方 3.13.15** | 同 |
| 依存のバージョン | 固定なし | **31個すべて一致** | 同 |
| 余分なパッケージ | 本番のみ `asyncpg`, `protobuf` | 同（未撤去） | **なし** |

段階5 の完了で「ローカル ≡ 本番」が成立する。これがタスク 1-2 の達成をもって示したい状態。

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

### 関門③の実測結果（2026-09-24）

`uv sync --frozen` でのビルドが成功。**三者完全一致**を達成した。

```
ローカル .venv (31個)  ≡  uv.lock (31個)  ≡  本番 (31個)
差分ゼロ。asyncpg / protobuf はすべてから消滅。
```

| | 移行前 | 移行後 |
|---|---|---|
| Python | ローカル 3.10.3 / 本番 不明 | **両方 3.13.15** |
| 依存のバージョン | 固定なし・推移的依存26個は記録すらされない | **31個すべて記録・完全一致** |
| 余分なパッケージ | 本番のみ `asyncpg`, `protobuf` | **なし** |

速度：`Prepared 31 packages in 221ms` / `Installed 31 packages in 20ms` / `Bytecode compiled 1463 files in 1.03s`。最後の行は uv がバイトコードを事前コンパイルしている（pip はデフォルトで行わない）ため、初回リクエストの応答が速くなる。

#### 🔴 発見①：uv 自体のバージョンが固定されていない（未対応）

```
Render:   Using uv version 0.10.2 (default)
ローカル:  uv 0.12.18
```

**依存を固定する道具が固定されていない。** 今回は 0.10.2 が 0.12.18 の書いた `uv.lock` を読めたため動作したが、`uv.lock` にはフォーマットのバージョンがあり、将来ローカルの uv を上げると Render 側が読めなくなる可能性がある。壊れるのは本番のビルド。

対処：Render の環境変数 `UV_VERSION` でローカルと同じ版に固定する（`render.com/docs/uv-version`）。

**段階5の完了後に、独立した小変更として行う。** 移行中に変更を積み増すと原因の切り分けができなくなるため。

#### 🟡 発見②：`VIRTUAL_ENV` の警告は `uv run` が必須である理由

```
warning: VIRTUAL_ENV=/opt/render/project/src/.venv does not match
         the project environment path `.venv` and will be ignored
```

Render はリポジトリルート（`src/`）の `.venv` を想定して環境変数を立てるが、プロジェクトは `src/backend/` にあるため uv は `backend/.venv` を作り、環境変数を無視した。

**Start Command を素の `uvicorn main:app ...` にしていた場合、存在しない `src/.venv` を探して失敗していた可能性がある。** `uv run` は作法ではなく、このズレを吸収する役割を担っている。

#### 注意：ビルド成功 ≠ 起動成功

ビルドログが `Build successful` で終わっても、Start Command の検証は済んでいない。サービスが Live になり、本番で会話が1往復できることを確認するまで関門③は通過ではない。

---

### タスク 1-2 完了記録（2026-09-27）

| # | 達成条件 | 結果 |
|---|---|---|
| 1 | `pyproject.toml` / `uv.lock` / `.python-version` が存在 | ✅ 3/3 |
| 2 | `.python-version` が `3.13` | ✅ |
| 3 | `requirements.txt` がファイルシステムに無い | ✅ |
| 4 | `requirements.txt` が git から消えている | ✅ 0件 |
| 5 | `uv.lock` に `asyncpg`/`protobuf` が無い | ✅ 0件 |
| 6 | `uv.lock` が git 追跡されている | ✅ |
| 7 | `.venv` が git 追跡されていない | ✅ 0件 |
| 8 | 本番が `uv sync --frozen` で動き、会話が成立する | ✅ |

**成果：ローカル ≡ `uv.lock` ≡ 本番（31パッケージ・バージョン完全一致）**

関連コミット：`68666d9`（Python 3.13 固定）→ `024d58e`（pyproject.toml + uv.lock）→ `8dc674a`（requirements.txt 削除）

`backend/venv`（旧 Python 3.10 環境）も撤去済み。

### 残タスク（タスク 1-2 から派生・いずれも独立した小作業）

| # | 内容 | 理由 | 扱い |
|---|---|---|---|
| 1 | Render に `UV_VERSION` を設定（ローカルと同じ 0.12.18） | 発見①。Render の既定は 0.10.2 で、将来ローカルの uv を上げると `uv.lock` が読めなくなる可能性がある | 未着手 |
| 2 | ~~CLAUDE.md の起動手順を `uv run uvicorn main:app --reload` に更新~~ | `source venv/bin/activate` は存在しない venv を参照している | **✅ 完了 2026-09-27**（引き継ぎのため先行実施） |

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
