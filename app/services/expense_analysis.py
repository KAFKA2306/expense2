"""
Expense Analysis Service

Provides analysis functions for expense data, excluding transfers and income.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional


class ExpenseAnalysisService:
    """Service for analyzing expense data."""

    # Tags to exclude from expense analysis
    EXCLUDED_TAGS = ["transfer", "income"]

    # Fixed cost categories (subscriptions, regular payments)
    FIXED_COST_TAGS = ["subscription"]

    # Reducible expense categories (discretionary spending)
    REDUCIBLE_CATEGORIES = ["外食", "趣味・娯楽", "ショッピング"]

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = (
                Path(__file__).parent.parent.parent / "data" / "transactions.csv"
            )
        self.data_path = data_path
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        """Load and cache transaction data."""
        if self._df is None:
            if not self.data_path.exists():
                return pd.DataFrame()
            self._df = pd.read_csv(self.data_path)
            self._df["date"] = pd.to_datetime(self._df["date"])
            self._df["year_month"] = self._df["date"].dt.to_period("M")
        return self._df.copy()

    def filter_expenses(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Filter out transfers and income, keeping only actual expenses."""
        if df is None:
            df = self._load_data()
        if df.empty:
            return df
        # Exclude transfers and income based on tags
        mask = ~df["tags"].isin(self.EXCLUDED_TAGS)
        # Also ensure we only get expenses (negative amounts)
        mask &= df["amount"] < 0
        return df[mask].copy()

    def get_monthly_trend(self) -> list[dict]:
        """Get monthly expense trend."""
        df = self.filter_expenses()
        if df.empty:
            return []

        monthly = df.groupby("year_month")["amount"].sum().abs().reset_index()
        monthly["year_month"] = monthly["year_month"].astype(str)
        return monthly.rename(
            columns={"year_month": "month", "amount": "total"}
        ).to_dict("records")

    def get_category_breakdown(self, year_month: Optional[str] = None) -> list[dict]:
        """Get expense breakdown by category."""
        df = self.filter_expenses()
        if df.empty:
            return []

        if year_month:
            df = df[df["year_month"].astype(str) == year_month]

        breakdown = (
            df.groupby("category")["amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
            .reset_index()
        )
        total = breakdown["amount"].sum()
        breakdown["percentage"] = (breakdown["amount"] / total * 100).round(1)
        return breakdown.to_dict("records")

    def get_fixed_vs_variable(self) -> dict:
        """Separate fixed costs (subscriptions) from variable costs."""
        df = self.filter_expenses()
        if df.empty:
            return {"fixed": 0, "variable": 0, "fixed_items": []}

        fixed_mask = df["tags"].isin(self.FIXED_COST_TAGS)
        fixed_total = abs(df[fixed_mask]["amount"].sum())
        variable_total = abs(df[~fixed_mask]["amount"].sum())

        # Get unique fixed cost items
        fixed_items = (
            df[fixed_mask]
            .groupby("description")["amount"]
            .mean()
            .abs()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
            .to_dict("records")
        )

        return {
            "fixed": round(fixed_total, 0),
            "variable": round(variable_total, 0),
            "fixed_items": fixed_items,
        }

    def get_reducible_expenses(self) -> list[dict]:
        """Identify potentially reducible expenses."""
        df = self.filter_expenses()
        if df.empty:
            return []

        reducible = df[df["category"].isin(self.REDUCIBLE_CATEGORIES)]
        monthly = (
            reducible.groupby(["year_month", "category"])["amount"]
            .sum()
            .abs()
            .reset_index()
        )
        monthly["year_month"] = monthly["year_month"].astype(str)

        # Calculate monthly average per category
        avg_by_category = (
            (
                reducible.groupby("category")["amount"].sum().abs()
                / reducible["year_month"].nunique()
            )
            .round(0)
            .reset_index()
        )
        avg_by_category.columns = ["category", "monthly_avg"]

        return avg_by_category.to_dict("records")

    def get_merchant_ranking(self, top_n: int = 10) -> list[dict]:
        """Get top merchants by spending."""
        df = self.filter_expenses()
        if df.empty:
            return []

        ranking = (
            df.groupby("description")
            .agg({"amount": ["sum", "count"]})
            .droplevel(0, axis=1)
            .reset_index()
        )
        ranking.columns = ["merchant", "total", "count"]
        ranking["total"] = ranking["total"].abs()
        ranking = ranking.sort_values("total", ascending=False).head(top_n)
        return ranking.to_dict("records")

    def get_mom_yoy_comparison(self) -> dict:
        """Get month-over-month and year-over-year comparison by category."""
        df = self.filter_expenses()
        if df.empty:
            return {"mom": [], "yoy": []}

        today = datetime.now()
        current_month = today.replace(day=1)
        last_month = (current_month - pd.DateOffset(months=1)).to_period("M")
        prev_month = (current_month - pd.DateOffset(months=2)).to_period("M")
        last_year_month = (current_month - pd.DateOffset(months=12)).to_period("M")

        def get_category_totals(period):
            period_df = df[df["year_month"] == period]
            return period_df.groupby("category")["amount"].sum().abs()

        last_m = get_category_totals(last_month)
        prev_m = get_category_totals(prev_month)
        last_y = get_category_totals(last_year_month)

        # MoM comparison
        mom = []
        for cat in last_m.index:
            current = last_m.get(cat, 0)
            previous = prev_m.get(cat, 0)
            change = ((current - previous) / previous * 100) if previous > 0 else 0
            mom.append(
                {
                    "category": cat,
                    "current": current,
                    "previous": previous,
                    "change": round(change, 1),
                }
            )

        # YoY comparison
        yoy = []
        for cat in last_m.index:
            current = last_m.get(cat, 0)
            previous = last_y.get(cat, 0)
            change = ((current - previous) / previous * 100) if previous > 0 else 0
            yoy.append(
                {
                    "category": cat,
                    "current": current,
                    "previous": previous,
                    "change": round(change, 1),
                }
            )

        return {"mom": mom, "yoy": yoy}

    def get_moving_average_12m(self) -> list[dict]:
        """Calculate 12-month moving average of expenses."""
        df = self.filter_expenses()
        if df.empty:
            return []

        monthly = df.groupby("year_month")["amount"].sum().abs().sort_index()

        ma12 = monthly.rolling(window=12, min_periods=1).mean()

        result = pd.DataFrame(
            {
                "month": monthly.index.astype(str),
                "actual": monthly.values,
                "ma12": ma12.values.round(0),
            }
        )
        return result.to_dict("records")

    def get_annual_forecast(self) -> dict:
        """Forecast annual expenses based on historical data."""
        df = self.filter_expenses()
        if df.empty:
            return {"forecast": 0, "method": "no_data"}

        today = datetime.now()
        current_year = today.year

        # Get current year data
        ytd = abs(df[df["date"].dt.year == current_year]["amount"].sum())
        months_elapsed = today.month

        # Get last 12 months average
        last_12m = abs(
            df[df["date"] >= (today - pd.DateOffset(months=12))]["amount"].sum()
        )
        monthly_avg = last_12m / 12

        # Forecast methods
        # 1. Simple projection based on YTD
        ytd_projection = (ytd / months_elapsed) * 12 if months_elapsed > 0 else 0

        # 2. Based on 12-month average
        ma_projection = monthly_avg * 12

        # Use weighted average (more weight to recent trend)
        forecast = ytd_projection * 0.6 + ma_projection * 0.4

        return {
            "ytd": round(ytd, 0),
            "ytd_projection": round(ytd_projection, 0),
            "ma_projection": round(ma_projection, 0),
            "forecast": round(forecast, 0),
            "monthly_avg": round(monthly_avg, 0),
            "months_elapsed": months_elapsed,
        }

    def get_summary(self) -> dict:
        """Get all analysis data in one call."""
        return {
            "monthly_trend": self.get_monthly_trend(),
            "category_breakdown": self.get_category_breakdown(),
            "fixed_vs_variable": self.get_fixed_vs_variable(),
            "reducible_expenses": self.get_reducible_expenses(),
            "merchant_ranking": self.get_merchant_ranking(),
            "comparison": self.get_mom_yoy_comparison(),
            "moving_average": self.get_moving_average_12m(),
            "annual_forecast": self.get_annual_forecast(),
        }
