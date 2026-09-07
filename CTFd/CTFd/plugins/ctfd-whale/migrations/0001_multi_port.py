"""Add multi-port columns without changing existing routes or allocations."""
import sqlalchemy as sa
revision = "whale_multi_port_1"
down_revision = None


def upgrade(op):
    for table, column in (
        ("dynamic_docker_challenge", sa.Column("redirect_rules", sa.Text(), nullable=True)),
        ("whale_container", sa.Column("ports", sa.JSON(), nullable=True)),
    ):
        existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
        if column.name not in existing:
            op.add_column(table, column)
    # NULL remains compatible with the original single-port code path.
