# ADR-0003: 地図に Google マップを使い、React からは `@vis.gl/react-google-maps` で描く

## ステータス
Accepted（2026-10-28）

- 「Google マップを使う」「`@vis.gl/react-google-maps` を使う」（決定 1・2）は、計画書の作成時（2026-09-23）にタスク 3-2 として決めていた。理由をここで記録する
- 「1.6.1 に固定する」「`DEMO_MAP_ID`」「経路線は直線」（決定 3〜5）は、3-2〜3-4 を実装する中で決めた

## 文脈

- v1.0.0 の完成の定義は「AI が組んだルートが、左右分割画面の右側に番号付きピンで表示される」こと
- 地図に載せる場所は、すべて Google Maps Platform から来ている
  - 起点：`geocode_place`（Geocoding API）
  - 訪問先：`search_nearby_location`（Places API）
  - 区間の距離・時間：`get_walking_leg`（Routes API）
- フロントは React 18 + Vite の BetterChatGPT fork。チャットの描画に `react-markdown` 8 系を使っている
- 地図の操作は読み取り専用（計画書 1. スコープ）。ピンを立て、表示範囲を合わせられれば足りる

## 決定

### 1. 地図は Google マップを使う（Leaflet ＋ OpenStreetMap にしない）

| 候補 | 内容 | 結論 |
|---|---|---|
| (a) Google マップ（Maps JavaScript API） | バックエンドと同じ Google Maps Platform | **採用** |
| (b) Leaflet ＋ OpenStreetMap のタイル | オープンソース。API キー不要 | 不採用 |

理由：
- **利用規約**：Google Maps Platform の規約では、Places API などで得た内容を地図の上に出すときは、Google マップの上に出すことになっている。訪問先は Places API の結果なので、(b) の地図にピンを立てると規約に触れるおそれがある
- **位置のずれ**：地名・建物の位置は、地図の提供元ごとに少しずつ違う。Google の座標を Google の地図に載せれば、ピンと地図上の建物がずれない
- **管理するものが増えない**：キー・予算アラート・quota を、すでにある Google Cloud のプロジェクトでまとめて見られる（1-1）。(b) では、OpenStreetMap のタイルサーバーの利用方針（大量アクセスの禁止など）を別に確認することになる

### 2. React からは `@vis.gl/react-google-maps` で描く

- Google の Maps JavaScript API を React の部品（`<APIProvider>`・`<Map>`・`<AdvancedMarker>`）として扱える
- Google がスポンサーになり、vis.gl（deck.gl などを作っているチーム）が保守している。Google の開発者向けドキュメントでも React 向けとして案内されている
- 部品にないものは `useMap()` で地図の本体（`google.maps.Map`）を取り出して直接操作できる。表示範囲の調整（`FitToPlan`）と線（`RouteLine`）はこの方法で書いた

### 3. 版は 1.6.1 に固定する

`package.json` に `^` を付けずに `"1.6.1"` と書く。

- 1.7.0 以降は、TypeScript の `JSX.IntrinsicElements` に `gmp-*`（Google の Web Components）のタグを足す
- その結果、`react-markdown` 8 系の型（`node_modules/react-markdown/lib/complex-types.ts`）と、それを使う `ContentView.tsx` の `CodeProps` が壊れ、`yarn build` が失敗する（1.10.1 で確認）
- 1.6.1 には、v1.0.0 で使う部品（`APIProvider`・`Map`・`AdvancedMarker`・`Pin`・`useMap`）がそろっている
- 依存の版を固定して、本番と手元の差をなくす考え方は ADR-0002 と同じ

### 4. マップ ID は、未設定なら `DEMO_MAP_ID` を使う

- 番号付きのピン（`AdvancedMarker`）を使うには、地図にマップ ID が要る
- `VITE_GOOGLE_MAPS_MAP_ID` が設定されていればそれを使い、なければ Google が開発用に用意している `DEMO_MAP_ID` を使う
- v1.0.0 では地図の見た目（クラウドで管理するスタイル）を変えないので、本番用のマップ ID は作っていない

### 5. ピンどうしを結ぶ線は、訪問順の直線（点線）にとどめる

| 候補 | 内容 | 結論 |
|---|---|---|
| (a) ピンどうしを直線で結ぶ | `plan` にある座標だけで描ける。フロントだけの変更 | **採用**（v1.0.0） |
| (b) 実際に歩く道に沿った線 | Routes API で道の形（`routes.polyline.encodedPolyline`）を取り、`plan` に載せる | v1.1.0 で検討 |

理由：
- (a) は追加の課金も、バックエンドの変更もない。S → 1 → 2 の順番がひと目でわかる、という目的は果たせる
- (b) は `plan` の形（ADR-0001 の `travel`）を変える。Routes API の FieldMask を広げると料金のランクが変わらないかの確認も要る。リリース直前（期限 11/1）に入れるには大きい
- 実際の道ではないことがわかるよう、実線ではなく点線にした

## 結果

### 得たもの

- ピン・表示範囲・線を、`plan` だけから描ける。地図のために新しく API を叩くのは、地図の読み込み（Maps JavaScript API）だけ
- 地図・場所の検索・徒歩の区間が、すべて同じ Google の座標でそろう

### 諦めたもの

- **地図を表示するたびに、お金がかかりうる。** 地図の読み込みは Maps JavaScript API の課金対象（無料枠あり）。Leaflet ＋ OpenStreetMap ならかからない。予算アラート（1-1）とキーの quota で上限を見張る
- **フロント用の API キーが、誰でも読める場所に出る。** `VITE_` の環境変数はビルド成果物に埋め込まれる。HTTP リファラと API の種類（Maps JavaScript API のみ）でキーの使い道を制限している（3-1）
- **`@vis.gl/react-google-maps` を上げられない。** 先に `react-markdown` を 9 系以降に上げる必要がある。`react-markdown` はチャットの表示の中心なので、上げるなら単独の作業にする
- **`DEMO_MAP_ID` は開発用。** Google が提供を変えると、ピンが出なくなるおそれがある。そのときは本番用のマップ ID を作り、`VITE_GOOGLE_MAPS_MAP_ID` に入れる
- **線が建物や川の上を横切る。** 歩く道の形ではないので、見た目の距離と、リストに出る徒歩の距離が合わない

### 再検討のきっかけ

- `react-markdown` を 9 系以降に上げたとき（`@vis.gl/react-google-maps` の固定を外せるか確かめる）
- 地図の見た目を変えたくなったとき、または `DEMO_MAP_ID` で地図やピンが出なくなったとき（本番用のマップ ID を作る）
- 歩く道に沿った線を出したくなったとき（決定 5 の (b)。`plan` の形を変えるので ADR-0001 も見直す）
- 地図の利用が増えて、無料枠を超えそうになったとき（地図の読み込み方、または地図の提供元を見直す）
