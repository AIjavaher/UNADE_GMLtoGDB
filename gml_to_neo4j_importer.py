"""
Import GML UtilityNetwork ADE file back into Neo4j Database
Recreates the exact schema structure: Network, FeatureGraph, Node, InteriorFeatureLink_branch, etc.
"""
import xml.etree.ElementTree as ET
from neo4j import GraphDatabase
import re
from typing import Dict, List, Tuple, Optional

# Neo4j connection
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

class GMLToNeo4jImporter:
    def __init__(self, gml_file_path: str):
        self.gml_file_path = gml_file_path
        self.driver = GraphDatabase.driver(URI, auth=AUTH)
        
        # XML namespaces
        self.namespaces = {
            'gml': 'http://www.opengis.net/gml/3.2',
            'un': 'http://www.opengis.net/citygml/utility-network/2.0',
            'core': 'http://www.opengis.net/citygml/2.0',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        # Storage for parsed data
        self.networks = []
        self.feature_graphs = []
        self.nodes = []
        self.interior_links = []
        self.connections = []
        self.abstract_features = []
        
    def clear_database(self):
        """Clear existing database (optional - be careful!)"""
        with self.driver.session() as session:
            print("Clearing existing database...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared.")
    
    def parse_gml_file(self):
        """Parse the GML file and extract all network elements"""
        print(f"Parsing GML file: {self.gml_file_path}")
        
        tree = ET.parse(self.gml_file_path)
        root = tree.getroot()
        
        # Find all UtilityNetwork elements
        utility_networks = root.findall('.//un:UtilityNetwork', self.namespaces)
        
        for un_element in utility_networks:
            self.parse_utility_network(un_element)
        
        print(f"Parsed: {len(self.networks)} networks, {len(self.feature_graphs)} feature graphs, "
              f"{len(self.nodes)} nodes, {len(self.interior_links)} interior links, "
              f"{len(self.connections)} connections")
    
    def parse_utility_network(self, un_element):
        """Parse a single UtilityNetwork element"""
        network_id = un_element.get('{http://www.opengis.net/gml/3.2}id')
        
        # Extract network properties
        network_data = {
            'gml_id': network_id,
            'class': self.get_text_content(un_element, 'un:class'),
            'function': self.get_text_content(un_element, 'un:function'),
            'creation_date': self.get_text_content(un_element, 'core:creationDate')
        }
        self.networks.append(network_data)
        
        # Parse network features
        network_features = un_element.findall('.//un:networkFeature', self.namespaces)
        
        for feature in network_features:
            self.parse_network_feature(feature, network_id)
    
    def parse_network_feature(self, feature_element, parent_network_id):
        """Parse individual network features"""
        # Check what type of feature this is
        feature_graph = feature_element.find('un:FeatureGraph', self.namespaces)
        if feature_graph is not None:
            self.parse_feature_graph(feature_graph, parent_network_id)
            return
            
        abstract_feature = feature_element.find('un:AbstractNetworkFeature', self.namespaces)
        if abstract_feature is not None:
            self.parse_abstract_feature(abstract_feature, parent_network_id)
            return
            
        connection_node = feature_element.find('un:ConnectionNode', self.namespaces)
        if connection_node is not None:
            self.parse_node(connection_node, 'exterior', parent_network_id)
            return
            
        junction_node = feature_element.find('un:JunctionNode', self.namespaces)
        if junction_node is not None:
            self.parse_node(junction_node, 'interior', parent_network_id)
            return
            
        network_node = feature_element.find('un:NetworkNode', self.namespaces)
        if network_node is not None:
            self.parse_node(network_node, 'unknown', parent_network_id)
            return
            
        network_link = feature_element.find('un:NetworkLink', self.namespaces)
        if network_link is not None:
            self.parse_network_link(network_link, parent_network_id)
            return
    
    def parse_feature_graph(self, fg_element, parent_network_id):
        """Parse FeatureGraph elements"""
        fg_id = fg_element.get('{http://www.opengis.net/gml/3.2}id')
        
        fg_data = {
            'gml_id': fg_id,
            'parent_network': parent_network_id,
            'object_id': self.get_text_content(fg_element, 'un:objectId')
        }
        self.feature_graphs.append(fg_data)
    
    def parse_abstract_feature(self, af_element, parent_network_id):
        """Parse AbstractNetworkFeature elements"""
        af_id = af_element.get('{http://www.opengis.net/gml/3.2}id')
        
        af_data = {
            'gml_id': af_id,
            'parent_network': parent_network_id,
            'owner': self.get_text_content(af_element, 'un:owner'),
            'status': self.get_text_content(af_element, 'un:status')
        }
        self.abstract_features.append(af_data)
    
    def parse_node(self, node_element, node_type, parent_network_id):
        """Parse Node elements (ConnectionNode, JunctionNode, NetworkNode)"""
        node_id = node_element.get('{http://www.opengis.net/gml/3.2}id')
        
        # Extract geometry
        geometry_data = self.extract_point_geometry(node_element)
        
        node_data = {
            'gml_id': node_id,
            'type': node_type,
            'parent_network': parent_network_id,
            'function': self.get_text_content(node_element, 'un:function'),
            'feature_graph_id': self.get_text_content(node_element, 'un:featureGraphId'),
            'geometry': geometry_data['wkt'] if geometry_data else None,
            'latitude': geometry_data['lat'] if geometry_data else None,
            'longitude': geometry_data['lon'] if geometry_data else None,
            'x_coordinate': geometry_data['x'] if geometry_data else None,
            'y_coordinate': geometry_data['y'] if geometry_data else None,
            'z_coordinate': geometry_data['z'] if geometry_data else None
        }
        self.nodes.append(node_data)
    
    def parse_network_link(self, link_element, parent_network_id):
        """Parse NetworkLink elements (pipes/connections)"""
        link_id = link_element.get('{http://www.opengis.net/gml/3.2}id')
        
        # Check if this is an interior feature link or a connection
        function = self.get_text_content(link_element, 'un:function')
        
        if function == 'interior_link':
            # This is an InteriorFeatureLink_branch
            link_data = {
                'gml_id': link_id,
                'parent_network': parent_network_id,
                'function': function,
                'diameter': self.get_text_content(link_element, 'un:diameter'),
                'material': self.get_text_content(link_element, 'un:material'),
                'length': self.get_text_content(link_element, 'un:length'),
                'owner': self.get_text_content(link_element, 'un:owner'),
                'status': self.get_text_content(link_element, 'un:status')
            }
            self.interior_links.append(link_data)
        else:
            # This is a connection between nodes
            start_ref = link_element.find('un:start', self.namespaces)
            end_ref = link_element.find('un:end', self.namespaces)
            
            connection_data = {
                'gml_id': link_id,
                'parent_network': parent_network_id,
                'function': function,
                'start_node_ref': start_ref.get('{http://www.w3.org/1999/xlink}href') if start_ref is not None else None,
                'end_node_ref': end_ref.get('{http://www.w3.org/1999/xlink}href') if end_ref is not None else None,
                'geometry': self.extract_line_geometry(link_element)
            }
            self.connections.append(connection_data)
    
    def extract_point_geometry(self, element):
        """Extract point geometry from GML element"""
        point = element.find('.//gml:Point', self.namespaces)
        if point is None:
            return None
            
        pos = point.find('gml:pos', self.namespaces)
        if pos is None or not pos.text:
            return None
            
        coords = pos.text.strip().split()
        if len(coords) >= 2:
            lon, lat = float(coords[0]), float(coords[1])
            z = float(coords[2]) if len(coords) > 2 else None
            
            # Create WKT format
            if z is not None:
                wkt = f"POINT Z ({lon} {lat} {z})"
            else:
                wkt = f"POINT ({lon} {lat})"
            
            return {
                'wkt': wkt,
                'lon': lon,
                'lat': lat,
                'x': lon,  # Assuming these are already in the right coordinate system
                'y': lat,
                'z': z
            }
        return None
    
    def extract_line_geometry(self, element):
        """Extract line geometry from GML element"""
        linestring = element.find('.//gml:LineString', self.namespaces)
        if linestring is None:
            return None
            
        pos_list = linestring.find('gml:posList', self.namespaces)
        if pos_list is None or not pos_list.text:
            return None
            
        coords = pos_list.text.strip().split()
        if len(coords) >= 4:  # At least 2 points
            points = []
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    points.append(f"{coords[i]} {coords[i+1]}")
            
            return f"LINESTRING ({', '.join(points)})"
        return None
    
    def get_text_content(self, element, xpath):
        """Get text content from element using xpath"""
        found = element.find(xpath, self.namespaces)
        return found.text if found is not None and found.text else None
    
    def create_neo4j_database(self):
        """Create the Neo4j database from parsed data"""
        print("Creating Neo4j database...")
        
        with self.driver.session() as session:
            # Create Networks
            for network in self.networks:
                session.run("""
                CREATE (n:Network {
                    gml_id: $gml_id,
                    class: $class,
                    function: $function,
                    creation_date: $creation_date
                })
                """, **network)
            print(f"Created {len(self.networks)} Network nodes")
            
            # Create FeatureGraphs
            for fg in self.feature_graphs:
                session.run("""
                CREATE (fg:FeatureGraph {
                    gml_id: $gml_id,
                    parent_network: $parent_network,
                    id_obj: $object_id
                })
                """, **fg)
            print(f"Created {len(self.feature_graphs)} FeatureGraph nodes")
            
            # Create AbstractNetworkFeatures
            for af in self.abstract_features:
                session.run("""
                CREATE (af:AbstractNetworkFeature {
                    gml_id: $gml_id,
                    parent_network: $parent_network,
                    owner: $owner,
                    status: $status
                })
                """, **af)
            print(f"Created {len(self.abstract_features)} AbstractNetworkFeature nodes")
            
            # Create Nodes
            for node in self.nodes:
                # Extract FeatureGraph_id from the node_id if available
                feature_graph_id = None
                if node['feature_graph_id']:
                    feature_graph_id = node['feature_graph_id']
                elif 'NODE_' in node['gml_id']:
                    # Extract from gml_id pattern NODE_<feature_graph_id>
                    feature_graph_id = node['gml_id'].replace('NODE_', '')
                
                session.run("""
                CREATE (n:Node {
                    gml_id: $gml_id,
                    type: $type,
                    parent_network: $parent_network,
                    function: $function,
                    FeatureGraph_id: $feature_graph_id,
                    geometry: $geometry,
                    latitude: $latitude,
                    longitude: $longitude,
                    x_coordinate: $x_coordinate,
                    y_coordinate: $y_coordinate,
                    z_coordinate: $z_coordinate
                })
                """, 
                gml_id=node['gml_id'],
                type=node['type'],
                parent_network=node['parent_network'],
                function=node['function'],
                feature_graph_id=feature_graph_id,
                geometry=node['geometry'],
                latitude=node['latitude'],
                longitude=node['longitude'],
                x_coordinate=node['x_coordinate'],
                y_coordinate=node['y_coordinate'],
                z_coordinate=node['z_coordinate']
                )
            print(f"Created {len(self.nodes)} Node entities")
            
            # Create InteriorFeatureLink_branch
            for link in self.interior_links:
                # Extract segment_id and FeatureGraph_id from gml_id
                segment_id = None
                feature_graph_id = None
                if 'IFL_' in link['gml_id']:
                    segment_id = link['gml_id'].replace('IFL_', '')
                
                session.run("""
                CREATE (ifl:InteriorFeatureLink_branch {
                    gml_id: $gml_id,
                    parent_network: $parent_network,
                    function: $function,
                    segment_id: $segment_id,
                    FeatureGraph_id: $feature_graph_id,
                    PIPE_SIZE: $diameter,
                    MATERIAL: $material,
                    PIPE_LENGT: $length,
                    ASSET_OWNE: $owner,
                    STATE: $status
                })
                """,
                gml_id=link['gml_id'],
                parent_network=link['parent_network'],
                function=link['function'],
                segment_id=segment_id,
                feature_graph_id=feature_graph_id,
                diameter=link['diameter'],
                material=link['material'],
                length=link['length'],
                owner=link['owner'],
                status=link['status']
                )
            print(f"Created {len(self.interior_links)} InteriorFeatureLink_branch entities")
            
            # Create relationships based on connections
            for conn in self.connections:
                if conn['start_node_ref'] and conn['end_node_ref']:
                    # Remove # from references
                    start_ref = conn['start_node_ref'].replace('#', '')
                    end_ref = conn['end_node_ref'].replace('#', '')
                    
                    # Determine relationship type based on function
                    rel_type = 'STARTNODE' if 'start' in conn['function'].lower() else 'CONNECTS_TO'
                    
                    session.run(f"""
                    MATCH (start {{gml_id: $start_ref}})
                    MATCH (end {{gml_id: $end_ref}})
                    CREATE (start)-[:{rel_type}]->(end)
                    """, start_ref=start_ref, end_ref=end_ref)
            print(f"Created {len(self.connections)} relationships")
    
    def import_gml_to_neo4j(self, clear_existing=False):
        """Main import function"""
        try:
            if clear_existing:
                self.clear_database()
            
            self.parse_gml_file()
            self.create_neo4j_database()
            
            print("✅ GML import completed successfully!")
            print(f"Imported:")
            print(f"  - {len(self.networks)} Networks")
            print(f"  - {len(self.feature_graphs)} FeatureGraphs") 
            print(f"  - {len(self.abstract_features)} AbstractNetworkFeatures")
            print(f"  - {len(self.nodes)} Nodes")
            print(f"  - {len(self.interior_links)} InteriorFeatureLink_branch")
            print(f"  - {len(self.connections)} Relationships")
            
        except Exception as e:
            print(f"❌ Error during import: {e}")
            raise
        finally:
            self.driver.close()

def main():
    """Import GML file to Neo4j"""
    gml_file = "water_network_utility_ade_complete.gml"
    
    print("GML to Neo4j Importer")
    print("=" * 50)
    
    # Ask user if they want to clear existing database
    clear_db = input("Clear existing database? (y/N): ").lower().strip() == 'y'
    
    importer = GMLToNeo4jImporter(gml_file)
    importer.import_gml_to_neo4j(clear_existing=clear_db)

if __name__ == "__main__":
    main() 