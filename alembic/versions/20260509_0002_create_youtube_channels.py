import sqlalchemy as sa
from alembic import op

revision = "20260509_0002"
down_revision = "20260508_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "youtube_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("youtube_channel_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("country", sa.String(length=16), nullable=True),
        sa.Column("default_language", sa.String(length=32), nullable=True),
        sa.Column("raw_youtube_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_youtube_channels_id", "youtube_channels", ["id"])
    op.create_index(
        "ix_youtube_channels_youtube_channel_id",
        "youtube_channels",
        ["youtube_channel_id"],
        unique=True,
    )

    op.create_table(
        "user_youtube_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "youtube_channel_id",
            sa.Integer(),
            sa.ForeignKey("youtube_channels.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "youtube_channel_id", name="uq_user_youtube_channel"),
    )
    op.create_index("ix_user_youtube_channels_id", "user_youtube_channels", ["id"])
    op.create_index("ix_user_youtube_channels_user_id", "user_youtube_channels", ["user_id"])
    op.create_index(
        "ix_user_youtube_channels_youtube_channel_id",
        "user_youtube_channels",
        ["youtube_channel_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_youtube_channels_youtube_channel_id", table_name="user_youtube_channels")
    op.drop_index("ix_user_youtube_channels_user_id", table_name="user_youtube_channels")
    op.drop_index("ix_user_youtube_channels_id", table_name="user_youtube_channels")
    op.drop_table("user_youtube_channels")
    op.drop_index("ix_youtube_channels_youtube_channel_id", table_name="youtube_channels")
    op.drop_index("ix_youtube_channels_id", table_name="youtube_channels")
    op.drop_table("youtube_channels")
