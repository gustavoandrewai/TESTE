"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sector_taxonomy", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sector", sa.String(80), nullable=False, unique=True), sa.Column("subsector", sa.String(80), nullable=False), sa.Column("description", sa.String(255), nullable=False))
    op.create_table("fii_master", sa.Column("ticker", sa.String(12), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("sector", sa.String(80), nullable=False), sa.Column("subsector", sa.String(80), nullable=False), sa.Column("manager", sa.String(120), nullable=False), sa.Column("administrator", sa.String(120), nullable=False), sa.Column("is_ifix", sa.Boolean(), nullable=False))
    op.create_table("market_daily", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("ticker", sa.String(12), sa.ForeignKey("fii_master.ticker"), nullable=False), sa.Column("reference_date", sa.Date(), nullable=False), sa.Column("price", sa.Float(), nullable=False), sa.Column("vp_per_share", sa.Float(), nullable=False), sa.Column("pvp", sa.Float(), nullable=False), sa.Column("avg_daily_liquidity", sa.Float(), nullable=False), sa.Column("return_1m", sa.Float(), nullable=False), sa.Column("return_6m", sa.Float(), nullable=False), sa.Column("return_12m", sa.Float(), nullable=False), sa.Column("volatility", sa.Float(), nullable=False), sa.Column("drawdown", sa.Float(), nullable=False), sa.UniqueConstraint("ticker", "reference_date", name="uq_market_ticker_date"))
    op.create_table("fundamentals_monthly", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("ticker", sa.String(12), sa.ForeignKey("fii_master.ticker"), nullable=False), sa.Column("reference_date", sa.Date(), nullable=False), sa.Column("equity", sa.Float(), nullable=False), sa.Column("dy_monthly", sa.Float(), nullable=False), sa.Column("dy_12m", sa.Float(), nullable=False), sa.Column("physical_vacancy", sa.Float(), nullable=False), sa.Column("financial_vacancy", sa.Float(), nullable=False), sa.Column("asset_concentration", sa.Float(), nullable=False), sa.Column("tenant_concentration", sa.Float(), nullable=False), sa.Column("avg_contract_term", sa.Float(), nullable=False), sa.Column("leverage", sa.Float(), nullable=False), sa.Column("delinquency", sa.Float(), nullable=False), sa.Column("income_per_share", sa.Float(), nullable=False), sa.Column("income_stability", sa.Float(), nullable=False), sa.UniqueConstraint("ticker", "reference_date", name="uq_fund_ticker_date"))
    op.create_table("benchmarks_daily", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("reference_date", sa.Date(), nullable=False), sa.Column("ifix_return_1m", sa.Float(), nullable=False), sa.Column("ifix_return_12m", sa.Float(), nullable=False), sa.Column("cdi_annual", sa.Float(), nullable=False))
    op.create_table("scoring_daily", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("ticker", sa.String(12), sa.ForeignKey("fii_master.ticker"), nullable=False), sa.Column("reference_date", sa.Date(), nullable=False), sa.Column("pvp_score", sa.Float(), nullable=False), sa.Column("fundamental_score", sa.Float(), nullable=False), sa.Column("income_quality_score", sa.Float(), nullable=False), sa.Column("risk_liquidity_score", sa.Float(), nullable=False), sa.Column("relative_score", sa.Float(), nullable=False), sa.Column("total_score", sa.Float(), nullable=False), sa.Column("classification", sa.String(32), nullable=False), sa.UniqueConstraint("ticker", "reference_date", name="uq_scoring_ticker_date"))
    op.create_table("alerts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("ticker", sa.String(12), nullable=False), sa.Column("reference_date", sa.Date(), nullable=False), sa.Column("alert_type", sa.String(50), nullable=False), sa.Column("message", sa.String(255), nullable=False))
    op.create_table("job_runs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("job_name", sa.String(80), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("started_at", sa.DateTime(), nullable=False), sa.Column("finished_at", sa.DateTime(), nullable=True), sa.Column("details", sa.String(255), nullable=False))


def downgrade() -> None:
    op.drop_table("job_runs")
    op.drop_table("alerts")
    op.drop_table("scoring_daily")
    op.drop_table("benchmarks_daily")
    op.drop_table("fundamentals_monthly")
    op.drop_table("market_daily")
    op.drop_table("fii_master")
    op.drop_table("sector_taxonomy")
