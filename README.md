# tabelogUserRestaurantScrap

食べログの店舗レビュー情報・レビュワー情報を収集するスクリプト群です。  
`Standard Flow` と `Seasonal Flow` の2系統があり、共通処理は `scraper_core/` 配下に集約しています。

## 前提

- Python 3.9+ 推奨
- 実行ディレクトリはリポジトリルート（この `README.md` がある場所）
- 入力CSVは同梱していないため、任意の場所に作成して `--input-csv` で指定
- 依存パッケージ:
  - `pandas`
  - `requests`
  - `beautifulsoup4`

例:

```bash
python3 -m pip install --user pandas requests beautifulsoup4
```

## 入力CSVフォーマット

収集スクリプトの`--input-csv`には、以下カラムを持つCSVを指定してください。

- `store_name`
- `tabelog_url`

最小例:

```csv
store_name,tabelog_url
チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
```

## ディレクトリ構成（主要）

- `standard_reviewer_flow/`
  - `collect_restaurant_reviewers.py`
  - `integrate_reviewers.py`
  - `collect_user_info.py`
  - `calculate_restaurant_local_user.py`
- `seasonal_reviewer_flow/`
  - `collect_seafood_restaurant_reviewers.py`
  - `integrate_seafood_reviewers.py`
  - `collect_user_reviews.py`
- `scraper_core/`
  - `reviewer_pipeline.py`（2系統共通ロジック）
  - `http_client.py`（リトライ付きHTTP取得）
  - `reviewer_stats_pipeline.py`（レビュワー全国/函館件数）
  - `local_user_rate_pipeline.py`（店舗ローカル率集計）
  - `visited_store_pipeline.py`（レビュワー訪問店舗詳細）

削除済み（リポジトリには含めない方針）:

- 旧フロー: `localuservalue_ver1/`, `local_uservalue_ver2/`
- 生成物: `output*/`, `seasonal_reviewer_flow/output*/`, `*.csv`（生成物）
- 同梱入力: `input/`

出力ディレクトリとCSVは、実行時に自動作成されます（`.gitignore` で除外）。

## 実行手順

### Standard Flow（通常店舗リスト）

0. 入力CSVを作成（例）
   ```bash
   cat > /tmp/restaurant_info.csv <<'CSV'
   store_name,tabelog_url
   チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
   CSV
   ```
1. 店舗ごとのレビュワー収集
   ```bash
   python3 standard_reviewer_flow/collect_restaurant_reviewers.py --input-csv /tmp/restaurant_info.csv
   ```
2. レビュワーCSV統合
   ```bash
   python3 standard_reviewer_flow/integrate_reviewers.py
   ```
   - 出力: `output_integrate/all_reviewer.csv`
3. （任意）レビュワーの全国/函館件数収集
   ```bash
   python3 standard_reviewer_flow/collect_user_info.py
   ```
   - 例（実行時間短縮）:
     ```bash
     python3 standard_reviewer_flow/collect_user_info.py --max-reviewers 10 --sleep-seconds 0.5
     ```
4. （任意）ローカルユーザー率算出
   ```bash
   python3 standard_reviewer_flow/calculate_restaurant_local_user.py
   ```

短時間で起動確認したい場合（1店舗・1ページのみ）:

```bash
python3 standard_reviewer_flow/collect_restaurant_reviewers.py \
  --input-csv /tmp/restaurant_info.csv \
  --max-stores 1 --max-pages 1 --sleep-seconds 0.2
```

### Seasonal Flow（seasonalリスト）

0. 入力CSVを作成（例）
   ```bash
   cat > /tmp/seasonal_restaurant_info.csv <<'CSV'
   store_name,tabelog_url
   チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
   CSV
   ```
1. 店舗ごとのレビュワー収集
   ```bash
   python3 seasonal_reviewer_flow/collect_seafood_restaurant_reviewers.py --input-csv /tmp/seasonal_restaurant_info.csv
   ```
2. レビュワーCSV統合
   ```bash
   python3 seasonal_reviewer_flow/integrate_seafood_reviewers.py
   ```
   - 出力: `seasonal_reviewer_flow/integrate_reviewer/all_reviewer.csv`
3. 統合レビュワーから訪問店舗詳細を収集
   ```bash
   python3 seasonal_reviewer_flow/collect_user_reviews.py
   ```
   - 例（検証用に1人・1ページ）:
     ```bash
     python3 seasonal_reviewer_flow/collect_user_reviews.py --max-reviewers 1 --end-page 1 --sleep-seconds 0.2
     ```

短時間で起動確認したい場合（1店舗・1ページのみ）:

```bash
python3 seasonal_reviewer_flow/collect_seafood_restaurant_reviewers.py \
  --input-csv /tmp/seasonal_restaurant_info.csv \
  --max-stores 1 --max-pages 1 --sleep-seconds 0.2
```

## リファクタリング内容

- `collect_restaurant_reviewers.py` と `collect_seafood_restaurant_reviewers.py` の重複処理を共通化
- `integrate_reviewers.py` と `integrate_seafood_reviewers.py` の重複処理を共通化
- 共通化先: `scraper_core/reviewer_pipeline.py`
- 共通CLI化: `scraper_core/cli.py`（`--max-stores` / `--max-pages` / `--request-timeout` / `--max-reviewers`対応）
- HTTP層を分離: `scraper_core/http_client.py`（リトライ・待機・タイムアウト統一）
- 後続処理を分離:
  - `scraper_core/reviewer_stats_pipeline.py`
  - `scraper_core/local_user_rate_pipeline.py`
  - `scraper_core/visited_store_pipeline.py`
- 命名統一: `reviewr_*` を `reviewer_*` に統一（旧列名は読み取り互換あり）

## 実行確認

2026-03-08時点で、以下を実行して実データ取得を確認済みです。

- Standard Flow: `--max-stores 1 --max-pages 1` で収集・統合し、`all_reviewer.csv`に20件出力
- Seasonal Flow: `--max-stores 1 --max-pages 1` で収集・統合し、`all_reviewer.csv`に20件出力
- Standard後続: `collect_user_info.py --max-reviewers 1` で全国/函館件数を取得
- Seasonal後続: `collect_user_reviews.py --max-reviewers 1 --end-page 1` で訪問店舗詳細20件を取得

## 既知の注意点

- 食べログ側のHTML変更により、レビュワー抽出セレクタが一致しない場合があります。
- その場合、CSVがヘッダのみで生成されることがあります。
- 出力系ディレクトリ/CSVは `.gitignore` で除外済みです。
