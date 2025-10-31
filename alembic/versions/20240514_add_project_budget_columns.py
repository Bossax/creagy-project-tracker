"""Add budget fields to projects table.

Revision ID: 20240514_add_project_budget
Revises: 
Create Date: 2024-05-14
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240514_add_project_budget"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add budget columns to the projects table."""
    op.add_column("projects", sa.Column("budget_allocated", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("budget_spent", sa.Float(), nullable=True))


def downgrade() -> None:
    """Drop the budget columns from the projects table."""
    op.drop_column("projects", "budget_spent")
    op.drop_column("projects", "budget_allocated")
