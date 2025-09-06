"""Enable PostGIS and create geography columns with spatial indexes

Revision ID: 0001_init
Revises:
Create Date: 2025-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from geoalchemy2 import Geography

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # Create features table
    op.create_table(
        'features',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='queued'),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('geom', Geography('POINT', srid=4326), nullable=True)
    )
    
    # Create footprints table
    op.create_table(
        'footprints',
        sa.Column('feature_id', PG_UUID(as_uuid=True), sa.ForeignKey('features.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('geom', Geography('POLYGON', srid=4326), nullable=True),
        sa.Column('buffer_area_m2', sa.Float, nullable=True)
    )
    
    # Drop and recreate index on features.geom
    op.execute("DROP INDEX IF EXISTS idx_features_geom;")
    op.create_index(
        'idx_features_geom',
        'features',
        ['geom'],
        postgresql_using='gist'
    )

    # Drop and recreate index on footprints.geom
    op.execute("DROP INDEX IF EXISTS idx_footprints_geom;")
    op.create_index(
        'idx_footprints_geom',
        'footprints',
        ['geom'],
        postgresql_using='gist'
    )


def downgrade():
    # Drop tables and indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_footprints_geom;")
    op.execute("DROP INDEX IF EXISTS idx_features_geom;")
    op.drop_table('footprints')
    op.drop_table('features')
    op.execute("DROP EXTENSION IF EXISTS postgis;")