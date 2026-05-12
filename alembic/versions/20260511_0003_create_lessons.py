import sqlalchemy as sa
from alembic import op

revision = "20260511_0003"
down_revision = "20260509_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("youtube_url", sa.Text(), nullable=False),
        sa.Column("youtube_video_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("channel_title", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("generation_status", sa.String(length=32), nullable=False),
        sa.Column("transcript_status", sa.String(length=32), nullable=False),
        sa.Column("transcript_source", sa.String(length=32), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("caption_segments_json", sa.JSON(), nullable=True),
        sa.Column("flashcards_json", sa.JSON(), nullable=True),
        sa.Column("subtitles_json", sa.JSON(), nullable=True),
        sa.Column("watch_vocab_json", sa.JSON(), nullable=True),
        sa.Column("cultural_notes_json", sa.JSON(), nullable=True),
        sa.Column("raw_youtube_metadata", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcript_error_code", sa.String(length=64), nullable=True),
        sa.Column("transcript_error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lessons_id", "lessons", ["id"])
    op.create_index("ix_lessons_user_id", "lessons", ["user_id"])
    op.create_index("ix_lessons_youtube_video_id", "lessons", ["youtube_video_id"])
    op.create_index("ix_lessons_generation_status", "lessons", ["generation_status"])


def downgrade() -> None:
    op.drop_index("ix_lessons_generation_status", table_name="lessons")
    op.drop_index("ix_lessons_youtube_video_id", table_name="lessons")
    op.drop_index("ix_lessons_user_id", table_name="lessons")
    op.drop_index("ix_lessons_id", table_name="lessons")
    op.drop_table("lessons")
