# Ultima Online Asset Viewer

A comprehensive web-based asset viewer for Ultima Online game assets, built with Flask and the ultima_sdk Python library. This application provides an interactive browser interface similar to UOFiddler for exploring game assets.

## Features

- **Art Tiles**: Browse static art tiles with search and range loading
- **Gumps**: View UI elements and graphics
- **Textures**: Explore texture assets
- **Hues**: Browse color palettes with visual previews
- **TileData**: View land and static tile definitions
- **Animations**: Browse character and object animations
- **Skills**: View skill definitions
- **Radar Colors**: Explore minimap color palette
- **String Lists**: Browse localized text strings
- **Interactive Interface**: Search, filter, and download assets
- **Real-time Loading**: Assets are loaded on-demand from the client files

## Requirements

- Python 3.8+
- Ultima Online client directory
- Flask and Pillow (installed via requirements.txt)

## Installation

1. Install dependencies:
```bash
cd examples/asset_viewer
pip install -r requirements.txt
```

## Usage

Run the web application:

```bash
python app.py --uo-root /path/to/ultima_online
```

Or with custom host/port:

```bash
python app.py --uo-root /path/to/ultima_online --host 0.0.0.0 --port 8080
```

Then open your browser to `http://localhost:5000`

## Command Line Options

- `--uo-root PATH`: Path to Ultima Online client directory (required for most assets)
- `--host HOST`: Host to bind to (default: 127.0.0.1)
- `--port PORT`: Port to bind to (default: 5000)
- `--debug`: Enable Flask debug mode

## Asset Types

### Art Viewer
- Load specific art tiles by ID
- Load ranges of art tiles
- View tile dimensions
- Download PNG images

### Gumps Viewer
- Browse UI elements
- Search by ID or load ranges
- View gump dimensions

### Hues Viewer
- Visual color palette previews
- View hue ranges and names
- Color picker interface

### TileData Viewer
- Land tiles with flags and texture IDs
- Static tiles with properties (weight, quality, etc.)
- Detailed tile information

### Animations Viewer
- Character and object animations
- Frame-by-frame viewing
- Body ID, action, and direction controls

### Skills Viewer
- Skill definitions and properties
- Action types and button usage

### Radar Colors
- Minimap color palette
- Hex and RGB color values

### String Lists
- Localized text strings
- Multiple language support

## Interface

The web interface provides:

- **Navigation**: Easy switching between asset types
- **Search**: Find specific assets by ID
- **Range Loading**: Load batches of assets efficiently
- **Modal Details**: Detailed views with download options
- **Responsive Design**: Works on desktop and mobile browsers
- **Status Indicators**: Shows which asset types are available

## Technical Details

- Built with Flask web framework
- Bootstrap 5 for responsive UI
- Real-time asset loading via AJAX
- Base64-encoded images for instant viewing
- Error handling for missing assets
- Graceful degradation when client files unavailable

## Similar to UOFiddler

This webapp provides similar functionality to UOFiddler:

- Asset browsing and searching
- Image export capabilities
- Detailed asset information
- Multiple asset type support
- User-friendly interface

But with the advantages of:
- Web-based (no installation required for users)
- Cross-platform compatibility
- Real-time updates
- Modern web interface