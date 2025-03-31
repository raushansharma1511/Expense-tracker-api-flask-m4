"""added index in the models

Revision ID: 22ebaaafa87a
Revises: 235928fc3565
Create Date: 2025-03-27 10:14:48.956692

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22ebaaafa87a'
down_revision = '235928fc3565'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('budgets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_budgets_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_budgets_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_categories_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('interwallet_transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interwallet_transactions_destination_wallet_id'), ['destination_wallet_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interwallet_transactions_source_wallet_id'), ['source_wallet_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interwallet_transactions_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('recurring_transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recurring_transactions_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_recurring_transactions_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_recurring_transactions_wallet_id'), ['wallet_id'], unique=False)

    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_wallets_user_id'), ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wallets_user_id'))

    with op.batch_alter_table('recurring_transactions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recurring_transactions_wallet_id'))
        batch_op.drop_index(batch_op.f('ix_recurring_transactions_user_id'))
        batch_op.drop_index(batch_op.f('ix_recurring_transactions_category_id'))

    with op.batch_alter_table('interwallet_transactions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interwallet_transactions_user_id'))
        batch_op.drop_index(batch_op.f('ix_interwallet_transactions_source_wallet_id'))
        batch_op.drop_index(batch_op.f('ix_interwallet_transactions_destination_wallet_id'))

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_categories_user_id'))

    with op.batch_alter_table('budgets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_budgets_user_id'))
        batch_op.drop_index(batch_op.f('ix_budgets_category_id'))

    # ### end Alembic commands ###
