# UNADE GML to Graph Database Converter

A GUI application for converting CityGML files with Utility Network ADE (UNADE) extensions into Neo4j graph databases, supporting the transformation of utility network data into labeled property graph (LPG) models.

## Overview

This application facilitates the conversion of utility network data from CityGML format to graph database representation, enabling advanced network analysis and visualization. It specifically supports the Utility Network Application Domain Extension (UNADE) for CityGML.

## Features

- **GUI Interface**: User-friendly graphical interface for easy file conversion
- **CityGML UNADE Support**: Full support for Utility Network ADE extensions
- **Neo4j Integration**: Direct import into Neo4j graph database
- **Coordinate Transformation**: Built-in coordinate system transformation utilities
- **Sample Data**: Includes sample water network data for testing

## Requirements

- Python 3.8+
- Neo4j Database
- Required Python packages (see `pyproject.toml`)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/UNADE_GMLtoGDB.git
cd UNADE_GMLtoGDB
```

2. Install dependencies using Poetry:
```bash
poetry install
```

Or using pip:
```bash
pip install -r requirements.txt
```

## Usage

### Running the GUI Application

```bash
python run_gui.py
```

or

```bash
python gml_importer_gui.py
```

### Sample Data

The repository includes a sample CityGML file (`water_network_utility_ade_complete_3_citygml3.gml`) demonstrating the utility network structure that can be processed by the application.

## File Structure

- `gml_importer_gui.py` - Main GUI application
- `gml_to_neo4j_importer.py` - Core conversion engine
- `transform_coordinates.py` - Coordinate transformation utilities
- `run_gui.py` - GUI launcher script
- `water_network_utility_ade_complete_3_citygml3.gml` - Sample data file
- `pyproject.toml` - Python dependencies configuration

## Neo4j Database Setup

1. Install Neo4j Desktop or Neo4j Community Server
2. Create a new database
3. Configure connection parameters in the GUI application
4. Import your CityGML UNADE files

## Supported Data Types

- Utility Network features (pipes, nodes, connections)
- FeatureGraphs and InterFeatureLinks
- Interior and Exterior network nodes
- Branch connections and network topology

## Citation

If you use this software in your research, please cite:

```
-----
```

## License

---
## Acknowledgments

This work supports research in utility network modeling and graph database applications for smart city infrastructure.
