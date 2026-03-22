from models.portfolio import PortfolioState


def deployed_fraction(portfolio: PortfolioState) -> float:
    if portfolio.bankroll <= 0:
        return 1.0
    return portfolio.deployed_capital / portfolio.bankroll
