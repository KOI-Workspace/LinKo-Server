import sqlalchemy as sa
from alembic import op

revision = "20260511_0004"
down_revision = "20260511_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("picture", sa.String(length=2048), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_waitlist_entries_id", "waitlist_entries", ["id"])
    op.create_index("ix_waitlist_entries_user_id", "waitlist_entries", ["user_id"])
    op.create_index("ix_waitlist_entries_email", "waitlist_entries", ["email"])


def downgrade() -> None:
    op.drop_index("ix_waitlist_entries_email", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_user_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_id", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")
