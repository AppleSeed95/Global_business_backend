# バックエンド開発サーバーの実行方法

まず、Python -v3.12.3をインストールする必要があります。\
次に、バックエンド プロジェクトをダウンロードします。
### `git clone https://github.com/AppleSeed95/Global_business_backend.git`



## 手順

プロジェクト ディレクトリで、次のコマンドを実行できます。

### `python -m venv .venv`

プロジェクト ディレクトリに仮想環境を構成します。

### `.venv/scripts/activate`

仮想環境をアクティブにします。

### `pip install -r requirements.txt`

必要なライブラリをすべてインストールします。

### `python manage.py migrate`

データベースを移行します。

### `python manage.py runserver`

開発サーバーを起動する
