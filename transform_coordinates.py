"""
Transform projected coordinates to WGS-84 for yFiles mapping
"""
from neo4j import GraphDatabase
import re

# You'll need to install: pip install pyproj
try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    print("Install pyproj for coordinate transformation: pip install pyproj")
    PYPROJ_AVAILABLE = False

# Neo4j connection
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

def extract_coordinates_from_point_z(point_z_string):
    """Extract x, y, z from POINT Z (x y z) format"""
    match = re.search(r'POINT Z \(([0-9.-]+) ([0-9.-]+) ([0-9.-]+)\)', point_z_string)
    if match:
        x, y, z = match.groups()
        return float(x), float(y), float(z)
    return None, None, None

def transform_coordinates():
    """Transform coordinates and update Neo4j nodes"""
    if not PYPROJ_AVAILABLE:
        return
    
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    # You need to determine your source coordinate system
    # Common options for Australia/Melbourne area:
    # - EPSG:28355 (GDA94 / MGA Zone 55)
    # - EPSG:3857 (Web Mercator)
    # - EPSG:32755 (WGS 84 / UTM zone 55S)
    
    # Example for UTM Zone 55S (Melbourne area) to WGS84
    transformer = Transformer.from_crs("EPSG:32755", "EPSG:4326", always_xy=True)
    
    with driver.session() as session:
        # Get all nodes with geometry
        result = session.run("""
        MATCH (n:Node)
        WHERE n.geometry IS NOT NULL
        RETURN n.FeatureGraph_id as id, n.geometry as geometry
        """)
        
        updates = []
        for record in result:
            node_id = record['id']
            geometry = record['geometry']
            
            x, y, z = extract_coordinates_from_point_z(geometry)
            if x is not None and y is not None:
                try:
                    # Transform coordinates
                    lon, lat = transformer.transform(x, y)
                    updates.append({
                        'id': node_id,
                        'latitude': lat,
                        'longitude': lon,
                        'elevation': z,
                        'x': x,
                        'y': y
                    })
                    print(f"Node {node_id}: ({x}, {y}) -> ({lat:.6f}, {lon:.6f})")
                except Exception as e:
                    print(f"Error transforming {node_id}: {e}")
        
        # Update Neo4j with lat/lng
        for update in updates:
            session.run("""
            MATCH (n:Node {FeatureGraph_id: $id})
            SET n.latitude = $latitude,
                n.longitude = $longitude,
                n.elevation = $elevation,
                n.x_coordinate = $x,
                n.y_coordinate = $y
            """, update)
        
        print(f"Updated {len(updates)} nodes with lat/lng coordinates")
    
    driver.close()

def check_coordinate_system():
    """Check a sample of coordinates to help identify the coordinate system"""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    with driver.session() as session:
        result = session.run("""
        MATCH (n:Node)
        WHERE n.geometry IS NOT NULL
        RETURN n.geometry
        LIMIT 5
        """)
        
        print("Sample coordinates:")
        for record in result:
            geometry = record['geometry']
            x, y, z = extract_coordinates_from_point_z(geometry)
            print(f"X: {x}, Y: {y}, Z: {z}")
    
    driver.close()

if __name__ == "__main__":
    print("Checking coordinate system...")
    check_coordinate_system()
    
    if PYPROJ_AVAILABLE:
        print("\nTransforming coordinates...")
        transform_coordinates()
    else:
        print("\nTo transform coordinates, install pyproj and run again")
        print("pip install pyproj") 