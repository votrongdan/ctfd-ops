import sqlalchemy as sa
revision = "ssm_lifecycle_1"
down_revision = None


def upgrade(op):
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('ssm_sessions')}
    for column in (sa.Column('lifecycle', sa.String(64), nullable=True),
                   sa.Column('pending_until', sa.DateTime(), nullable=True)):
        if column.name not in columns:
            op.add_column('ssm_sessions', column)
