# tabelogUserRestaurantScrap

食べログの店舗レビュー情報・レビュワー情報を収集するスクリプト群です。  
`Standard Flow` と `Seasonal Flow` の2系統があり、共通処理は `scraper_core/` に集約しています。

## 前提

- Python 3.9+ 推奨
- 実行ディレクトリはリポジトリルート
- 入力CSVは同梱していないため、任意の場所に作成して `--input-csv` で指定
- 依存パッケージ:
  - `pandas`
  - `requests`
  - `beautifulsoup4`

```bash
python3 -m pip install --user pandas requests beautifulsoup4
```

## 入力CSVフォーマット

`--input-csv` は以下カラムを持つCSVを指定してください。

- `store_name`
- `tabelog_url`

```csv
store_name,tabelog_url
チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
```

## クイックスタート（Standard）

```bash
cat > /tmp/restaurant_info.csv <<'CSV'
store_name,tabelog_url
チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
CSV

python3 standard_reviewer_flow/collect_restaurant_reviewers.py \
  --input-csv /tmp/restaurant_info.csv \
  --max-stores 1 --max-pages 1 --sleep-seconds 0.2

python3 standard_reviewer_flow/integrate_reviewers.py
```

統合結果は `output_integrate/all_reviewer.csv` に出力されます。

## Standard Flow（詳細）

1. 店舗ごとのレビュワー収集
   ```bash
   python3 standard_reviewer_flow/collect_restaurant_reviewers.py --input-csv /tmp/restaurant_info.csv
   ```
   - 既定出力: `output/*.csv`
2. レビュワーCSV統合
   ```bash
   python3 standard_reviewer_flow/integrate_reviewers.py
   ```
   - 既定出力: `output_integrate/all_reviewer.csv`
3. （任意）レビュワーの全国/函館件数収集
   ```bash
   python3 standard_reviewer_flow/collect_user_info.py
   ```
   - 既定出力: `output_user_info/reviewer_stats.csv`
4. （任意）ローカルユーザー率算出
   ```bash
   python3 standard_reviewer_flow/calculate_restaurant_local_user.py
   ```
   - 既定出力: `output_restaurant_local_rate/local_rate.csv` と店舗別CSV

## Seasonal Flow（詳細）

1. 入力CSV作成（例）
   ```bash
   cat > /tmp/seasonal_restaurant_info.csv <<'CSV'
   store_name,tabelog_url
   チャイナダイニング鳳凰,https://tabelog.com/hokkaido/A0105/A010501/1040561/
   CSV
   ```
2. 店舗ごとのレビュワー収集
   ```bash
   python3 seasonal_reviewer_flow/collect_seafood_restaurant_reviewers.py --input-csv /tmp/seasonal_restaurant_info.csv
   ```
   - 既定出力: `seasonal_reviewer_flow/output_restaurant_review/*.csv`
3. レビュワーCSV統合
   ```bash
   python3 seasonal_reviewer_flow/integrate_seafood_reviewers.py
   ```
   - 既定出力: `seasonal_reviewer_flow/integrate_reviewer/all_reviewer.csv`
4. 統合レビュワーから訪問店舗詳細を収集
   ```bash
   python3 seasonal_reviewer_flow/collect_user_reviews.py
   ```
   - 既定出力: `seasonal_reviewer_flow/output_user_visited_store/*.csv`

初回で先頭から収集したい場合は `start-index` を明示してください。

```bash
python3 seasonal_reviewer_flow/collect_user_reviews.py --start-index 0
```

## 主要オプション

- `collect_restaurant_reviewers.py` / `collect_seafood_restaurant_reviewers.py`
  - `--max-stores`, `--max-pages`, `--sleep-seconds`, `--request-timeout`
- `collect_user_info.py`
  - `--max-reviewers`, `--sleep-seconds`, `--request-timeout`
- `collect_user_reviews.py`
  - `--max-reviewers`, `--begin-page`, `--end-page`, `--start-index`, `--sleep-seconds`

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
  - `reviewer_pipeline.py`
  - `http_client.py`
  - `reviewer_stats_pipeline.py`
  - `local_user_rate_pipeline.py`
  - `visited_store_pipeline.py`

## 生成物の扱い

- 出力ディレクトリ・CSVは実行時に作成されます。
- 生成物は `.gitignore` で除外済みです。
- 旧構成（`localuservalue_ver1/`, `local_uservalue_ver2/`, 同梱 `input/`）は削除済みです。

## 実行確認

2026-03-08 時点で、以下の実行を確認済みです。

- Standard: `--max-stores 1 --max-pages 1` で収集・統合し `all_reviewer.csv` に20件出力
- Seasonal: `--max-stores 1 --max-pages 1` で収集・統合し `all_reviewer.csv` に20件出力
- Standard後続: `collect_user_info.py --max-reviewers 1` で全国/函館件数を取得
- Seasonal後続: `collect_user_reviews.py --max-reviewers 1 --end-page 1` で訪問店舗詳細20件を取得

## 注意点

- 食べログ側HTML変更により、レビュワー抽出セレクタが一致しない場合があります。
- その場合、CSVがヘッダのみで生成されることがあります。
