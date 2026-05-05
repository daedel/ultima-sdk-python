"""Ultima Online Asset Viewer Webapp.

A web-based asset viewer similar to UOFiddler, showcasing all major
Ultima Online asset types through the ultima_sdk.
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, jsonify, send_file

from ultima_sdk import (
    Art,
    Files,
    Gumps,
    Hues,
    Light,
    Map,
    Multis,
    RadarCol,
    Skills,
    SkillGroups,
    Sound,
    StringList,
    Textures,
    TileData,
    Animations,
)

from .._common import (
    add_uo_root_arg,
    resolve_uo_root,
    init_files,
)

app = Flask(__name__)

# Global asset managers
asset_managers = {}

def initialize_assets(uo_root: str | None = None) -> bool:
    """Initialize all asset managers."""
    global asset_managers

    try:
        # Initialize file system
        init_files(uo_root, require=False)

        # Initialize all asset types
        managers = [
            ('art', Art, 'Static Art Tiles'),
            ('gumps', Gumps, 'UI Elements'),
            ('textures', Textures, 'Textures'),
            ('light', Light, 'Lighting Data'),
            ('map', Map, 'Map Data'),
            ('multis', Multis, 'Multi-Tile Structures'),
            ('sound', Sound, 'Sound Effects'),
            ('string_list', StringList, 'String Lists'),
            ('skills', Skills, 'Skills'),
            ('skill_groups', SkillGroups, 'Skill Groups'),
            ('animations', Animations, 'Animations'),
            ('hues', Hues, 'Color Palettes'),
            ('radar_col', RadarCol, 'Radar Colors'),
            ('tiledata', TileData, 'Tile Data'),
        ]

        for key, manager_class, description in managers:
            try:
                if hasattr(manager_class, 'initialize'):
                    manager_class.initialize()
                    asset_managers[key] = {
                        'manager': manager_class,
                        'description': description,
                        'initialized': True
                    }
                    print(f"✓ Initialized {description}")
                else:
                    asset_managers[key] = {
                        'manager': manager_class,
                        'description': description,
                        'initialized': False,
                        'error': 'No initialize method'
                    }
                    print(f"⚠ {description} has no initialize method")
            except Exception as e:
                asset_managers[key] = {
                    'manager': None,
                    'description': description,
                    'initialized': False,
                    'error': str(e)
                }
                print(f"✗ Failed to initialize {description}: {e}")

        return True
    except Exception as e:
        print(f"Failed to initialize assets: {e}")
        return False

@app.route('/')
def index():
    """Main index page with navigation to all asset types."""
    return render_template('index.html', asset_managers=asset_managers)

@app.route('/art')
def art_viewer():
    """Static art tiles viewer."""
    return render_template('art_viewer.html')

@app.route('/api/art/<int:art_id>')
def get_art(art_id: int):
    """Get art tile as base64 image."""
    try:
        if not asset_managers.get('art', {}).get('initialized'):
            return jsonify({'error': 'Art not initialized'}), 500

        # Try to get the art
        art_tile = Art.get_art(art_id)
        if not art_tile:
            return jsonify({'error': f'Art {art_id} not found'}), 404

        # Convert to image
        image = art_tile.to_image()
        if not image:
            return jsonify({'error': f'Failed to convert art {art_id} to image'}), 500

        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'id': art_id,
            'image': f'data:image/png;base64,{img_str}',
            'width': image.width,
            'height': image.height
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/gumps')
def gumps_viewer():
    """Gumps viewer."""
    return render_template('gumps_viewer.html')

@app.route('/api/gumps/<int:gump_id>')
def get_gump(gump_id: int):
    """Get gump as base64 image."""
    try:
        if not asset_managers.get('gumps', {}).get('initialized'):
            return jsonify({'error': 'Gumps not initialized'}), 500

        gump = Gumps.get_gump(gump_id)
        if not gump:
            return jsonify({'error': f'Gump {gump_id} not found'}), 404

        image = gump.to_image()
        if not image:
            return jsonify({'error': f'Failed to convert gump {gump_id} to image'}), 500

        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'id': gump_id,
            'image': f'data:image/png;base64,{img_str}',
            'width': image.width,
            'height': image.height
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/textures')
def textures_viewer():
    """Textures viewer."""
    return render_template('textures_viewer.html')

@app.route('/api/textures/<int:texture_id>')
def get_texture(texture_id: int):
    """Get texture as base64 image."""
    try:
        if not asset_managers.get('textures', {}).get('initialized'):
            return jsonify({'error': 'Textures not initialized'}), 500

        texture = Textures.get_texture(texture_id)
        if not texture:
            return jsonify({'error': f'Texture {texture_id} not found'}), 404

        image = texture.to_image()
        if not image:
            return jsonify({'error': f'Failed to convert texture {texture_id} to image'}), 500

        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'id': texture_id,
            'image': f'data:image/png;base64,{img_str}',
            'width': image.width,
            'height': image.height
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hues')
def hues_viewer():
    """Hues viewer."""
    return render_template('hues_viewer.html')

@app.route('/api/hues')
def get_hues():
    """Get all hues data."""
    try:
        if not asset_managers.get('hues', {}).get('initialized'):
            return jsonify({'error': 'Hues not initialized'}), 500

        hues = []
        for i in range(3000):  # Reasonable range for hues
            try:
                hue = Hues.get_hue(i)
                if hue:
                    hues.append({
                        'id': i,
                        'name': hue.get('name', f'Hue {i}'),
                        'colors': hue.get('colors', [])[:32],  # First 32 colors
                        'tableStart': hue.get('tableStart', 0),
                        'tableEnd': hue.get('tableEnd', 0)
                    })
            except:
                break

        return jsonify({'hues': hues})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tiledata')
def tiledata_viewer():
    """TileData viewer."""
    return render_template('tiledata_viewer.html')

@app.route('/api/tiledata/land')
def get_land_tiles():
    """Get land tile data."""
    try:
        if not asset_managers.get('tiledata', {}).get('initialized'):
            return jsonify({'error': 'TileData not initialized'}), 500

        tiles = []
        for i in range(100):  # First 100 land tiles
            try:
                tile = TileData.get_land_tile(i)
                if tile:
                    tiles.append({
                        'id': i,
                        'name': tile.get('name', f'Land {i}'),
                        'flags': tile.get('flags', 0),
                        'texture_id': tile.get('texture_id', 0)
                    })
            except:
                break

        return jsonify({'tiles': tiles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tiledata/static')
def get_static_tiles():
    """Get static tile data."""
    try:
        if not asset_managers.get('tiledata', {}).get('initialized'):
            return jsonify({'error': 'TileData not initialized'}), 500

        tiles = []
        for i in range(100):  # First 100 static tiles
            try:
                tile = TileData.get_static_tile(i)
                if tile:
                    tiles.append({
                        'id': i,
                        'name': tile.get('name', f'Static {i}'),
                        'flags': tile.get('flags', 0),
                        'weight': tile.get('weight', 0),
                        'quality': tile.get('quality', 0),
                        'quantity': tile.get('quantity', 0),
                        'hue': tile.get('hue', 0),
                        'stacking_offset': tile.get('stacking_offset', 0)
                    })
            except:
                break

        return jsonify({'tiles': tiles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/animations')
def animations_viewer():
    """Animations viewer."""
    return render_template('animations_viewer.html')

@app.route('/api/animations/<int:body_id>')
def get_animation(body_id: int):
    """Get animation frames for a body."""
    try:
        if not asset_managers.get('animations', {}).get('initialized'):
            return jsonify({'error': 'Animations not initialized'}), 500

        # Get animation for body
        animation = Animations.get_animation(body_id, action=0, direction=0)
        if not animation:
            return jsonify({'error': f'Animation for body {body_id} not found'}), 404

        frames = []
        for i, frame in enumerate(animation.frames):
            if frame:
                image = frame.to_image()
                if image:
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    frames.append({
                        'frame': i,
                        'image': f'data:image/png;base64,{img_str}',
                        'width': image.width,
                        'height': image.height
                    })

        return jsonify({
            'body_id': body_id,
            'frames': frames
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/skills')
def skills_viewer():
    """Skills viewer."""
    return render_template('skills_viewer.html')

@app.route('/api/skills')
def get_skills():
    """Get all skills data."""
    try:
        if not asset_managers.get('skills', {}).get('initialized'):
            return jsonify({'error': 'Skills not initialized'}), 500

        skills = []
        for i in range(100):  # Reasonable range
            try:
                skill = Skills.get_skill(i)
                if skill:
                    skills.append({
                        'id': i,
                        'name': skill.get('name', f'Skill {i}'),
                        'action': skill.get('action', 0),
                        'use_button': skill.get('use_button', False)
                    })
            except:
                break

        return jsonify({'skills': skills})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/radar')
def radar_viewer():
    """Radar colors viewer."""
    return render_template('radar_viewer.html')

@app.route('/api/radar')
def get_radar_colors():
    """Get radar color data."""
    try:
        if not asset_managers.get('radar_col', {}).get('initialized'):
            return jsonify({'error': 'RadarCol not initialized'}), 500

        colors = []
        for i in range(1000):  # Reasonable range
            try:
                color = RadarCol.get_color(i)
                if color is not None:
                    colors.append({
                        'id': i,
                        'color': f'#{color:06X}'
                    })
            except:
                break

        return jsonify({'colors': colors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/strings')
def strings_viewer():
    """String list viewer."""
    return render_template('strings_viewer.html')

@app.route('/api/strings/<int:language>')
def get_strings(language: int):
    """Get string list for a language."""
    try:
        if not asset_managers.get('string_list', {}).get('initialized'):
            return jsonify({'error': 'StringList not initialized'}), 500

        strings = []
        for i in range(100):  # First 100 strings
            try:
                string = StringList.get_string(language, i)
                if string:
                    strings.append({
                        'id': i,
                        'text': string
                    })
            except:
                break

        return jsonify({'language': language, 'strings': strings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    uo_root = resolve_uo_root(args.uo_root)

    print("Initializing Ultima Online Asset Viewer...")
    print(f"UO Root: {uo_root}")

    if not initialize_assets(uo_root):
        print("Failed to initialize assets. Some features may not work.")
    else:
        print("Asset initialization complete!")

    print(f"Starting web server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()