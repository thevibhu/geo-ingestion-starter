# Complete PostGIS implementation using raw SQL for spatial operations
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
from typing import Optional, List, Dict, Any

def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    """Insert a named point into features table with PostGIS geometry"""
    feature_id = uuid.uuid4()
    
    # Use PostGIS to create a geography point from lon/lat
    # ST_SetSRID + ST_MakePoint creates the geometry, ::geography converts to geography type
    query = text("""
        INSERT INTO features (id, name, status, attempts, created_at, geom)
        VALUES (
            :feature_id,
            :name,
            'queued',
            0,
            NOW(),
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        )
    """)
    
    db.execute(query, {
        "feature_id": feature_id,
        "name": name,
        "lat": lat,
        "lon": lon
    })
    db.commit()
    
    return feature_id

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    """Buffer the point geometry, compute area, and store in footprints table"""
    try:
        feature_uuid = uuid.UUID(feature_id)
    except ValueError:
        return False
    
    # First check if feature exists and is in queued status
    check_query = text("""
        SELECT id, geom FROM features 
        WHERE id = :feature_id AND status = 'queued' AND geom IS NOT NULL
    """)
    
    result = db.execute(check_query, {"feature_id": feature_uuid}).fetchone()
    if not result:
        return False
    
    # Buffer the geometry and compute area in one query
    # ST_Buffer creates a 500m buffer, ST_Area computes the area in square meters
    process_query = text("""
        WITH buffered AS (
            SELECT 
                :feature_id as feature_id,
                ST_Buffer(f.geom, :buffer_m) as buffered_geom
            FROM features f 
            WHERE f.id = :feature_id
        ),
        area_calc AS (
            SELECT 
                feature_id,
                buffered_geom,
                ST_Area(buffered_geom) as area_m2
            FROM buffered
        )
        INSERT INTO footprints (feature_id, geom, buffer_area_m2)
        SELECT feature_id, buffered_geom, area_m2
        FROM area_calc
        ON CONFLICT (feature_id) DO UPDATE SET
            geom = EXCLUDED.geom,
            buffer_area_m2 = EXCLUDED.buffer_area_m2
    """)
    
    db.execute(process_query, {
        "feature_id": feature_uuid,
        "buffer_m": buffer_m
    })
    
    # Update feature status to 'done'
    update_query = text("""
        UPDATE features 
        SET status = 'done', updated_at = NOW(), attempts = attempts + 1
        WHERE id = :feature_id
    """)
    
    db.execute(update_query, {"feature_id": feature_uuid})
    db.commit()
    
    return True

def get_feature(db: Session, feature_id: str) -> Optional[Dict[str, Any]]:
    """Get feature details with buffer area if available"""
    try:
        feature_uuid = uuid.UUID(feature_id)
    except ValueError:
        return None
    
    query = text("""
        SELECT 
            f.id,
            f.name,
            f.status,
            f.attempts,
            f.created_at,
            f.updated_at,
            fp.buffer_area_m2
        FROM features f
        LEFT JOIN footprints fp ON f.id = fp.feature_id
        WHERE f.id = :feature_id
    """)
    
    result = db.execute(query, {"feature_id": feature_uuid}).fetchone()
    if not result:
        return None
    
    return {
        "id": str(result.id),
        "name": result.name,
        "status": result.status,
        "attempts": result.attempts,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        "buffer_area_m2": result.buffer_area_m2
    }

def features_near(db: Session, lat: float, lon: float, radius_m: int) -> List[Dict[str, Any]]:
    """Find features within specified radius using PostGIS ST_DWithin"""
    # Create a reference point and find features within radius
    # ST_DWithin is optimized for geography types and uses spatial indexes
    query = text("""
        SELECT 
            f.id,
            f.name,
            f.status,
            f.attempts,
            f.created_at,
            f.updated_at,
            fp.buffer_area_m2,
            ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) as distance_m
        FROM features f
        LEFT JOIN footprints fp ON f.id = fp.feature_id
        WHERE f.geom IS NOT NULL
        AND ST_DWithin(
            f.geom, 
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
            :radius_m
        )
        ORDER BY distance_m
    """)
    
    results = db.execute(query, {
        "lat": lat,
        "lon": lon,
        "radius_m": radius_m
    }).fetchall()
    
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "status": row.status,
            "attempts": row.attempts,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "buffer_area_m2": row.buffer_area_m2,
            "distance_m": float(row.distance_m) if row.distance_m else None
        }
        for row in results
    ]