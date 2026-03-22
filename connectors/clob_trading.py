class ClobTrading:
    """Live trading scaffold intentionally minimal for v1."""

    def place_limit(self, *args, **kwargs):
        raise NotImplementedError("Live trading not implemented in v1; use MODE=paper")
