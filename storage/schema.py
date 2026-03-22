DDL = [
    """
    CREATE TABLE IF NOT EXISTS markets (
      market_id TEXT PRIMARY KEY,
      asset TEXT NOT NULL,
      horizon TEXT NOT NULL,
      yes_token_id TEXT NOT NULL,
      no_token_id TEXT NOT NULL,
      end_time TEXT NOT NULL,
      is_active INTEGER NOT NULL,
      updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS book_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      market_id TEXT NOT NULL,
      ts_epoch_ms INTEGER NOT NULL,
      yes_bid REAL, yes_ask REAL, no_bid REAL, no_ask REAL,
      yes_bid_size REAL, yes_ask_size REAL, no_bid_size REAL, no_ask_size REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS signals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT NOT NULL,
      market_id TEXT NOT NULL,
      asset TEXT NOT NULL,
      horizon TEXT NOT NULL,
      side TEXT NOT NULL,
      mid REAL NOT NULL,
      best_bid REAL NOT NULL,
      best_ask REAL NOT NULL,
      spread REAL NOT NULL,
      seconds_left INTEGER NOT NULL,
      score REAL NOT NULL,
      accepted INTEGER NOT NULL,
      reason TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
      order_id TEXT PRIMARY KEY,
      ts TEXT NOT NULL,
      market_id TEXT NOT NULL,
      is_entry INTEGER NOT NULL,
      status TEXT NOT NULL,
      reason TEXT NOT NULL,
      size REAL NOT NULL,
      limit_price REAL NOT NULL,
      fill_price REAL,
      fill_size REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
      position_id TEXT PRIMARY KEY,
      market_id TEXT NOT NULL,
      asset TEXT NOT NULL,
      horizon TEXT NOT NULL,
      side TEXT NOT NULL,
      entry_price REAL NOT NULL,
      entry_size REAL NOT NULL,
      target_price REAL NOT NULL,
      stop_price REAL NOT NULL,
      status TEXT NOT NULL,
      realized_pnl REAL NOT NULL,
      entry_time TEXT NOT NULL,
      exit_time TEXT,
      exit_reason TEXT
    )
    """,
]
