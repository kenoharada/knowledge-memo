# knowledge-memo

このアプリケーションは、ユーザーが YouTube の URL を入力すると、対応する動画を表示し、動画の要約を生成します。また、ユーザーはテキストエリアでメモを記述し、そのメモはサーバーに保存されます。

## 構成

プロジェクトのフォルダ構成は以下の通りです：

```
/myapp/
│
├── static/
│ ├── script.js # フロントエンドのJavaScriptファイル
│ └── styles.css # フロントエンドのCSSファイル
│
├── templates/
│ └── index.html # フロントエンドのHTMLファイル
│
├── app.py # Flaskのメインアプリケーションファイル
└── README.md # プロジェクトの説明ファイル
```

## ローカルでの実行

1. 必要な依存関係をインストールします。これには Flask とその他の必要なライブラリが含まれます。
   `pip install -r requirements.txt`
2. OpenAI の API キーを設定します。
   `export OPENAI_API_KEY=<your-api-key>`
3. `app.py`を実行してサーバーを起動します。
   `python app.py`
4. ブラウザで`localhost:5000`を開きます。

## 機能

- ユーザーは YouTube の動画 URL を入力できます。
- 入力された URL に基づいて動画が表示されます。
- ユーザーはテキストエリアにメモを記述し、メモは自動的にサーバーに保存されます。
