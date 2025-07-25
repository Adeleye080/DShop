"""propagate tables and indexes

Revision ID: 02c62822be5f
Revises: b833f2758b40
Create Date: 2025-07-23 17:45:45.289323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02c62822be5f'
down_revision: Union[str, None] = 'b833f2758b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('shipping_address_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'orders', 'addresses', ['shipping_address_id'], ['id'])
    op.create_index('idx_product_created_deleted', 'products', ['created_at', 'is_deleted'], unique=False)
    op.create_index('idx_product_name_deleted', 'products', ['name', 'is_deleted'], unique=False)
    op.create_index('idx_product_price_stock', 'products', ['price', 'stock'], unique=False)
    op.create_index(op.f('ix_products_created_at'), 'products', ['created_at'], unique=False)
    op.create_index(op.f('ix_products_description'), 'products', ['description'], unique=False)
    op.create_index(op.f('ix_products_is_deleted'), 'products', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_price'), 'products', ['price'], unique=False)
    op.create_index(op.f('ix_products_stock'), 'products', ['stock'], unique=False)
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))
    op.create_index('idx_user_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('idx_user_role_active', 'users', ['role', 'is_active'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email_verified'), 'users', ['email_verified'], unique=False)
    op.create_index(op.f('ix_users_full_name'), 'users', ['full_name'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_is_admin'), 'users', ['is_admin'], unique=False)
    op.create_index(op.f('ix_users_is_deleted'), 'users', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_users_password_reset_token'), 'users', ['password_reset_token'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_verification_token'), 'users', ['verification_token'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_verification_token'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_password_reset_token'), table_name='users')
    op.drop_index(op.f('ix_users_is_deleted'), table_name='users')
    op.drop_index(op.f('ix_users_is_admin'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_full_name'), table_name='users')
    op.drop_index(op.f('ix_users_email_verified'), table_name='users')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index('idx_user_role_active', table_name='users')
    op.drop_index('idx_user_email_active', table_name='users')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'phone')
    op.drop_index(op.f('ix_products_stock'), table_name='products')
    op.drop_index(op.f('ix_products_price'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_is_deleted'), table_name='products')
    op.drop_index(op.f('ix_products_description'), table_name='products')
    op.drop_index(op.f('ix_products_created_at'), table_name='products')
    op.drop_index('idx_product_price_stock', table_name='products')
    op.drop_index('idx_product_name_deleted', table_name='products')
    op.drop_index('idx_product_created_deleted', table_name='products')
    op.drop_constraint(None, 'orders', type_='foreignkey')
    op.drop_column('orders', 'shipping_address_id')
    # ### end Alembic commands ###
