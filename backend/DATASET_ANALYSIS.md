# Cloned UPI-Fraud-Detection-System dataset analysis

Dataset search location: `data`

## Repository inventory (`data/UPI-Fraud-Detection-System`)

- `data/UPI-Fraud-Detection-System/app.py`
- `data/UPI-Fraud-Detection-System/data_dictionary.csv`
- `data/UPI-Fraud-Detection-System/fraud_labels.csv`
- `data/UPI-Fraud-Detection-System/merchants.csv`
- `data/UPI-Fraud-Detection-System/README.md`
- `data/UPI-Fraud-Detection-System/requirements.txt`
- `data/UPI-Fraud-Detection-System/transactions.csv`
- `data/UPI-Fraud-Detection-System/UPI Fraud Detection Engine.ipynb`
- `data/UPI-Fraud-Detection-System/UPI_Fraud_Detection_Engine_using_DL.pdf`
- `data/UPI-Fraud-Detection-System/users.csv`

CSV files are profiled below. No Excel or Parquet dataset files were found.

## Dataset profiles

### `data/UPI-Fraud-Detection-System/data_dictionary.csv` (data_dictionary)

- Format: CSV; rows: 63; columns: 6
- Exact duplicate rows: 0

| Column | Inferred type | Missing |
|---|---|---:|
| `file` | string/category | 0 (0.00%) |
| `column` | string/category | 0 (0.00%) |
| `description` | string/category | 0 (0.00%) |
| `dtype` | string/category | 0 (0.00%) |
| `example_values` | string/category | 0 (0.00%) |
| `notes` | string/category | 15 (23.81%) |

Redacted sample (identifier/name/contact fields are omitted):

```json
[
  {
    "file": "transactions.csv",
    "column": "transaction_id",
    "dtype": "string"
  },
  {
    "file": "transactions.csv",
    "column": "user_id",
    "dtype": "string"
  },
  {
    "file": "transactions.csv",
    "column": "receiver_id",
    "dtype": "string"
  }
]
```

- Numeric/boolean columns: none
- Categorical/date/text columns: `file`, `column`, `description`, `dtype`, `example_values`, `notes`

### `data/UPI-Fraud-Detection-System/fraud_labels.csv` (fraud_labels)

- Format: CSV; rows: 20,000; columns: 11
- Exact duplicate rows: 0

| Column | Inferred type | Missing |
|---|---|---:|
| `transaction_id` | string/category | 0 (0.00%) |
| `user_id` | string/category | 0 (0.00%) |
| `receiver_id` | string/category | 0 (0.00%) |
| `amount` | number | 0 (0.00%) |
| `timestamp` | datetime/date | 0 (0.00%) |
| `is_fraud` | integer | 0 (0.00%) |
| `new_device_flag` | integer | 0 (0.00%) |
| `ip_location_mismatch` | integer | 0 (0.00%) |
| `failed_attempts_last_24h` | integer | 0 (0.00%) |
| `transaction_velocity` | number | 393 (1.97%) |
| `amount_deviation_score` | number | 367 (1.84%) |

Label distribution for `is_fraud`: `0` = 19,237, `1` = 763

Redacted sample (identifier/name/contact fields are omitted):

```json
[
  {
    "amount": "1650.84",
    "timestamp": "2024-12-26 14:52:00",
    "is_fraud": "0",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "0",
    "transaction_velocity": "0.0",
    "amount_deviation_score": "0.5146"
  },
  {
    "amount": "599.2",
    "timestamp": "2024-06-29 00:09:24",
    "is_fraud": "0",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "1",
    "transaction_velocity": "0.0",
    "amount_deviation_score": "0.7026"
  },
  {
    "amount": "261.36",
    "timestamp": "2024-02-21 05:08:33",
    "is_fraud": "0",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "0",
    "transaction_velocity": "0.0",
    "amount_deviation_score": "0.1547"
  }
]
```

- Numeric/boolean columns: `amount`, `is_fraud`, `new_device_flag`, `ip_location_mismatch`, `failed_attempts_last_24h`, `transaction_velocity`, `amount_deviation_score`
- Categorical/date/text columns: `transaction_id`, `user_id`, `receiver_id`, `timestamp`

- Observed bounds: `amount` = 13.7 to 32259.72; `timestamp` = 2024-01-01 00:21:17 to 2024-12-30 22:31:52

### `data/UPI-Fraud-Detection-System/merchants.csv` (merchants)

- Format: CSV; rows: 400; columns: 9
- Exact duplicate rows: 0

| Column | Inferred type | Missing |
|---|---|---:|
| `merchant_id` | string/category | 0 (0.00%) |
| `merchant_name` | string/category | 0 (0.00%) |
| `merchant_category` | string/category | 0 (0.00%) |
| `merchant_size` | string/category | 0 (0.00%) |
| `city` | string/category | 0 (0.00%) |
| `city_tier` | string/category | 0 (0.00%) |
| `avg_daily_transactions` | integer | 0 (0.00%) |
| `is_registered` | integer | 0 (0.00%) |
| `rating` | number | 0 (0.00%) |

Redacted sample (identifier/name/contact fields are omitted):

```json
[
  {
    "merchant_category": "Insurance",
    "merchant_size": "Medium",
    "city_tier": "Tier 2",
    "avg_daily_transactions": "60",
    "is_registered": "1",
    "rating": "4.2"
  },
  {
    "merchant_category": "Travel",
    "merchant_size": "Small",
    "city_tier": "Tier 2",
    "avg_daily_transactions": "7",
    "is_registered": "1",
    "rating": "4.7"
  },
  {
    "merchant_category": "Utilities",
    "merchant_size": "Small",
    "city_tier": "Tier 1",
    "avg_daily_transactions": "4",
    "is_registered": "1",
    "rating": "4.1"
  }
]
```

- Numeric/boolean columns: `avg_daily_transactions`, `is_registered`, `rating`
- Categorical/date/text columns: `merchant_id`, `merchant_name`, `merchant_category`, `merchant_size`, `city`, `city_tier`

### `data/UPI-Fraud-Detection-System/transactions.csv` (transactions)

- Format: CSV; rows: 20,000; columns: 30
- Exact duplicate rows: 0

| Column | Inferred type | Missing |
|---|---|---:|
| `transaction_id` | string/category | 0 (0.00%) |
| `user_id` | string/category | 0 (0.00%) |
| `receiver_id` | string/category | 0 (0.00%) |
| `receiver_type` | string/category | 0 (0.00%) |
| `amount` | number | 0 (0.00%) |
| `timestamp` | datetime/date | 0 (0.00%) |
| `date` | datetime/date | 0 (0.00%) |
| `hour_of_day` | integer | 0 (0.00%) |
| `day_of_week` | string/category | 0 (0.00%) |
| `is_weekend` | integer | 0 (0.00%) |
| `is_night_transaction` | integer | 0 (0.00%) |
| `time_since_last_txn_min` | number | 2,335 (11.68%) |
| `transaction_type` | string/category | 0 (0.00%) |
| `payment_app` | string/category | 0 (0.00%) |
| `device_type` | string/category | 0 (0.00%) |
| `status` | string/category | 0 (0.00%) |
| `user_city_tier` | string/category | 0 (0.00%) |
| `user_kyc_status` | string/category | 0 (0.00%) |
| `user_avg_monthly_txn` | integer | 0 (0.00%) |
| `user_avg_txn_value` | number | 0 (0.00%) |
| `user_loyalty_score` | number | 0 (0.00%) |
| `new_device_flag` | integer | 0 (0.00%) |
| `ip_location_mismatch` | integer | 0 (0.00%) |
| `failed_attempts_last_24h` | integer | 0 (0.00%) |
| `transaction_velocity` | number | 393 (1.97%) |
| `amount_deviation_score` | number | 367 (1.84%) |
| `is_fraud` | integer | 0 (0.00%) |
| `recurring_payment_flag` | integer | 0 (0.00%) |
| `balance_after_transaction` | number | 0 (0.00%) |
| `transaction_frequency_score` | number | 0 (0.00%) |

Label distribution for `is_fraud`: `0` = 19,237, `1` = 763

Redacted sample (identifier/name/contact fields are omitted):

```json
[
  {
    "amount": "1533.88",
    "timestamp": "2024-01-01 00:21:17",
    "transaction_type": "EMI",
    "receiver_type": "Merchant",
    "hour_of_day": "0",
    "is_night_transaction": "1",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "2",
    "transaction_velocity": "0.0",
    "amount_deviation_score": "2.2467",
    "is_fraud": "0"
  },
  {
    "amount": "1371.57",
    "timestamp": "2024-01-01 00:36:29",
    "transaction_type": "P2M",
    "receiver_type": "Merchant",
    "hour_of_day": "0",
    "is_night_transaction": "1",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "0",
    "transaction_velocity": "4.0",
    "amount_deviation_score": "1.1773",
    "is_fraud": "0"
  },
  {
    "amount": "500.5",
    "timestamp": "2024-01-01 00:47:46",
    "transaction_type": "Subscription",
    "receiver_type": "Merchant",
    "hour_of_day": "0",
    "is_night_transaction": "1",
    "new_device_flag": "0",
    "ip_location_mismatch": "0",
    "failed_attempts_last_24h": "0",
    "transaction_velocity": "1.0",
    "amount_deviation_score": "0.1471",
    "is_fraud": "0"
  }
]
```

- Numeric/boolean columns: `amount`, `hour_of_day`, `is_weekend`, `is_night_transaction`, `time_since_last_txn_min`, `user_avg_monthly_txn`, `user_avg_txn_value`, `user_loyalty_score`, `new_device_flag`, `ip_location_mismatch`, `failed_attempts_last_24h`, `transaction_velocity`, `amount_deviation_score`, `is_fraud`, `recurring_payment_flag`, `balance_after_transaction`, `transaction_frequency_score`
- Categorical/date/text columns: `transaction_id`, `user_id`, `receiver_id`, `receiver_type`, `timestamp`, `date`, `day_of_week`, `transaction_type`, `payment_app`, `device_type`, `status`, `user_city_tier`, `user_kyc_status`

- Observed bounds: `amount` = 13.7 to 32259.72; `timestamp` = 2024-01-01 00:21:17 to 2024-12-30 22:31:52; `date` = 2024-01-01 to 2024-12-30

### `data/UPI-Fraud-Detection-System/users.csv` (users)

- Format: CSV; rows: 2,000; columns: 13
- Exact duplicate rows: 0

| Column | Inferred type | Missing |
|---|---|---:|
| `user_id` | string/category | 0 (0.00%) |
| `age_group` | string/category | 0 (0.00%) |
| `city` | string/category | 0 (0.00%) |
| `city_tier` | string/category | 0 (0.00%) |
| `kyc_status` | string/category | 0 (0.00%) |
| `account_age_days` | integer | 0 (0.00%) |
| `linked_bank_count` | integer | 0 (0.00%) |
| `avg_monthly_transactions` | integer | 0 (0.00%) |
| `avg_transaction_value` | number | 0 (0.00%) |
| `preferred_app` | string/category | 0 (0.00%) |
| `preferred_device` | string/category | 0 (0.00%) |
| `user_loyalty_score` | number | 0 (0.00%) |
| `is_high_risk_user` | integer | 0 (0.00%) |

Redacted sample (identifier/name/contact fields are omitted):

```json
[
  {
    "age_group": "55+",
    "city_tier": "Tier 2",
    "kyc_status": "Verified",
    "account_age_days": "486",
    "linked_bank_count": "1",
    "avg_monthly_transactions": "19",
    "avg_transaction_value": "629.65",
    "is_high_risk_user": "0"
  },
  {
    "age_group": "35-44",
    "city_tier": "Tier 3",
    "kyc_status": "Verified",
    "account_age_days": "449",
    "linked_bank_count": "2",
    "avg_monthly_transactions": "15",
    "avg_transaction_value": "429.28",
    "is_high_risk_user": "0"
  },
  {
    "age_group": "25-34",
    "city_tier": "Tier 1",
    "kyc_status": "Verified",
    "account_age_days": "160",
    "linked_bank_count": "1",
    "avg_monthly_transactions": "56",
    "avg_transaction_value": "340.67",
    "is_high_risk_user": "0"
  }
]
```

- Numeric/boolean columns: `account_age_days`, `linked_bank_count`, `avg_monthly_transactions`, `avg_transaction_value`, `user_loyalty_score`, `is_high_risk_user`
- Categorical/date/text columns: `user_id`, `age_group`, `city`, `city_tier`, `kyc_status`, `preferred_app`, `preferred_device`

## Cross-file integrity

- Transaction IDs are unique: True.
- Label IDs are unique: True; transaction and label ID sets match: True; label mismatches: 0.
- Sender IDs resolve to users: 20,000/20,000.
- Merchant receiver IDs resolve: 15,119/15,119; user receiver IDs resolve: 4,881/4,881.

## Suitability and interpretation

- The transaction table has a binary `is_fraud` target: 763 positive, 19,237 negative (3.82% positive).
- The repository README documents the records as synthetically generated and describes labels derived from a hand-authored risk-signal formula. The labels are not confirmed, adjudicated real-world fraud outcomes.
- Appropriate use: preprocessing, feature engineering, pipeline smoke tests, and experiments that explicitly target agreement with the synthetic label generator. Not appropriate for claims about live UPI fraud accuracy, external validation, or operational decisions.
- Present transaction, sender/receiver, and behavioral fields include: `amount`, `receiver_type`, `transaction_type`, `user_id`, `receiver_id`, `timestamp`, `hour_of_day`, `time_since_last_txn_min`, `transaction_velocity`, `new_device_flag`, `ip_location_mismatch`, `failed_attempts_last_24h`, `amount_deviation_score`. Sender/receiver IDs and linked user/merchant tables support synthetic relational and temporal experiments; IDs themselves should not be model features.
- Directly available suspicious-pattern signals include new device, IP/location mismatch, failed attempts, transaction velocity, amount deviation, night-time, KYC status, and a linked high-risk-user flag.
- `users.csv` supplies anonymized sender profile fields such as age bracket, city tier, KYC status, account age, linked-bank count, transaction averages, preferred app/device, loyalty score, and high-risk flag. `receiver_id` and `receiver_type` distinguish user/merchant receivers; merchant records include category, size, city tier, registration, and rating.
- Not present: real VPA/account numbers, phone numbers, device IDs, IP addresses, bank/provider identity, collect-request text, or confirmed payment-network events. Do not infer these from the UPI repository name.
- Exclude the target `is_fraud` from predictors. Treat post-transaction `status` and `balance_after_transaction` as potential outcome leakage; exclude unless their time-of-decision availability is proven.
- Transactions repeat by sender. Use a user-grouped or forward-in-time evaluation split to reduce identity/history leakage; do not randomly split rows and call the result independent-user validation.
- The separate fraud-labels CSV repeats target and transaction fields. Do not treat its duplicate label/signal columns as additional independent observations.
- The existing PayShield backend has its own heuristic assessment and a separate synthetic-trained seven-feature RF package. This external schema/label source does not establish compatibility or justify replacing that model. No model training, artifact overwrite, or API-contract change is performed by this inspector.
- Feature compatibility is partial: `amount`, `hour_of_day`, failed-attempts, and average-amount proxies exist. In the existing backend, failed attempts are currently assumed to be zero and are not accepted/stored by its analysis request. Its 24-hour transaction count is not equivalent to this dataset's `transaction_velocity`; receiver novelty must be derived strictly from past sender history, and its relative amount-deviation calculation must be reconciled with this dataset's normalized `amount_deviation_score` before retraining or inference integration.

## Local analysis environment

- Python: 3.14.7
- Package versions: `pandas` 3.1.0; `numpy` 2.5.4; `scikit-learn` 1.9.1; `torch` not installed; `fastapi` 0.162.0; `sqlalchemy` 2.1.6; `pyarrow` not installed; `openpyxl` not installed; `joblib` 1.6.0

The cloned repository contains an `app.py`, a notebook, and a PDF presentation. Its Streamlit app fits preprocessing on the full transaction table and trains a neural network during app initialization; it does not load a checked-in trained-model checkpoint. The notebook has a row-random holdout split but does not group by user, so repeated senders can cross the split.

For a meaningful PayShield evaluation, obtain legally usable, de-identified transactions with adjudicated outcomes and event times; use time-forward and user-aware validation. Until then, keep results labeled synthetic and use this dataset only for controlled pipeline experiments.

Observed positive target count: 763 of 20,000 (the count above comes from the CSV; no model metrics are reported).
