# tourism-route-planner

観光地周遊アプリ。AIとの対話で観光地を探し、ルートナビゲーションまで行えるWebアプリ（SPA）。

## ドキュメント

- [要件定義書](./docs/観光地巡りアプリ_要件定義書.md)

## 技術スタック（暫定）

- フロントエンド: オープンソースチャットUI（BetterChatGPT）をFork + 地図・しおりパネル自作
- バックエンド: Python / FastAPI
- AI対話: Gemini API（Function Calling）
- 地図・ルート: 検討中（Google Maps Platform軸）
- ローカル開発: Docker Compose
- デプロイ先: AWS

## セットアップ

```bash
# バックエンド
cd backend
python -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install -r requirements.txt

# フロントエンド
cd frontend
npm install
npm run dev
```

## 開発状況

進行中（1週目：要件定義）
