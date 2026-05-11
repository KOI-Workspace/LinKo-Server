import sqlalchemy as sa
from alembic import op

revision = "20260511_0005"
down_revision = "20260511_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("is_preview", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_lessons_is_preview", "lessons", ["is_preview"])


def downgrade() -> None:
    op.drop_index("ix_lessons_is_preview", table_name="lessons")
    op.drop_column("lessons", "is_preview")
