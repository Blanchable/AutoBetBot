from models.portfolio import PortfolioState


def render_dashboard(mode: str, enabled_lanes: list[str], portfolio: PortfolioState, candidate_count: int, recent_rejections: list[str]) -> str:
    lines = [
        "==== AutoBetBot Dashboard ====",
        f"mode={mode}",
        f"bankroll={portfolio.bankroll:.2f}",
        f"deployed={portfolio.deployed_capital:.2f}",
        f"open_positions={len(portfolio.open_positions)}",
        f"candidates={candidate_count}",
        f"realized_pnl={portfolio.realized_pnl:.2f}",
        f"enabled_lanes={', '.join(enabled_lanes)}",
    ]
    if recent_rejections:
        lines.append(f"recent_rejections={'; '.join(recent_rejections[-5:])}")
    return "\n".join(lines)
