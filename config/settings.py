"""Central project configuration."""
import os

# Do not store data-provider tokens in the repository.
# Set TUSHARE_TOKEN in the shell or OS environment before running downloads.
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

DATA_START = "20230101"
DATA_END = "20260512"

TRAIN_START = "2023-01-01"
TRAIN_END = "2024-06-30"
VAL_START = "2024-07-01"
VAL_END = "2025-06-30"
TEST_START = "2025-07-01"

DATA_DIR = "c:/Users/liuji/Desktop/claudets/data"
DAILY_PARQUET = "c:/Users/liuji/Desktop/claudets/data/daily_ohlcv.parquet"
WEEKLY_PARQUET = "c:/Users/liuji/Desktop/claudets/data/weekly_ohlcv.parquet"
DAILY_FEATURE_WEEKLY_PARQUET = "c:/Users/liuji/Desktop/claudets/data/weekly_daily_features.parquet"
PRICE_ADJUST = "qfq"

MAX_DRAWDOWN_THRESHOLD = 0.15
DRAWDOWN_MAX_ITERATIONS = 3
DRAWDOWN_WORSEN_STOP_ROUNDS = 2

GENERATION_SIZE_MIN = 12
GENERATION_SIZE_MAX = 20
MUTATION_NEW_FACTORS_MIN = 8
MAX_TREE_DEPTH = 5
MAX_WINDOW = 60
EVOLUTION_MAX_GENERATIONS = 3
EVOLUTION_MIN_IMPROVEMENT = 1e-4
EVOLUTION_STAGNATION_ROUNDS = 2
EVOLUTION_PARENT_SCORE_EPS = 1e-9

IC_OVERFIT_TRAIN_THRESHOLD = 0.10
IC_OVERFIT_VAL_THRESHOLD = 0.01

VOL_LOOKBACK = 4
VOL_HISTORY = 52
VOL_THRESHOLD_HIGH = 1.5
VOL_THRESHOLD_LOW = 0.5

WEIGHT_MIN = 0.025
WEIGHT_MAX = 0.40
