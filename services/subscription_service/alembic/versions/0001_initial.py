"""users and subscriptions

Revision ID: 0001
Revises:
Create Date: 2026-08-24

"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("tz", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("tier", sa.String(16), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fight_id", sa.String(64), nullable=False),
        sa.Column("lead_time_min", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("channel", sa.String(16), nullable=False, server_default="telegram"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_fight_id", "subscriptions", ["fight_id"])


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("users")
