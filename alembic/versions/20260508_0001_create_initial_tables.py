import sqlalchemy as sa
from alembic import op

revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("picture", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("youtube_video_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("channel_title", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_youtube_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_videos_id", "videos", ["id"])
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)

    op.create_table(
        "video_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("requested_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_video_queries_id", "video_queries", ["id"])
    op.create_index("ix_video_queries_user_id", "video_queries", ["user_id"])
    op.create_index("ix_video_queries_video_id", "video_queries", ["video_id"])


def downgrade() -> None:
    op.drop_index("ix_video_queries_video_id", table_name="video_queries")
    op.drop_index("ix_video_queries_user_id", table_name="video_queries")
    op.drop_index("ix_video_queries_id", table_name="video_queries")
    op.drop_table("video_queries")
    op.drop_index("ix_videos_youtube_video_id", table_name="videos")
    op.drop_index("ix_videos_id", table_name="videos")
    op.drop_table("videos")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
