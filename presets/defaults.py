"""
Default settings and presets for BakingBakes addon
"""

# Default bake settings that users can reset to
DEFAULT_BAKE_SETTINGS = {
    'bake_diffuse': True,
    'bake_normal': True,
    'bake_roughness_glossy': True,
    'bake_metalness': False,
    'bake_sss': False,
    'bake_sss_colour': False,
    'bake_transmission': False,
    'bake_transmission_rough': False,
    'bake_clearcoat': False,
    'bake_clearcoat_roughness': False,
    'bake_emission': False,
    'bake_emission_strength': False,
    'bake_specular': True,
    'bake_alpha': False,
    'bake_bump': False,
    'bake_ao': False,
    'bake_shadow': False,
    'bake_uv': False,
    'bake_environment': False,
    'bake_glossy': False,
}

# Preset configurations for different use cases
PRESETS = {
    'GAME_ASSETS': {
        'name': 'Game Assets',
        'description': 'Standard game-ready PBR maps',
        'settings': {
            'bake_diffuse': True,
            'bake_normal': True,
            'bake_roughness_glossy': True,
            'bake_metalness': True,
            'bake_ao': True,
        }
    },
    'VFX_FILM': {
        'name': 'VFX/Film',
        'description': 'High-quality maps for visual effects',
        'settings': {
            'bake_diffuse': True,
            'bake_normal': True,
            'bake_roughness_glossy': True,
            'bake_specular': True,
            'bake_emission': True,
            'bake_alpha': True,
        }
    },
    'ARCHITECTURAL': {
        'name': 'Architectural',
        'description': 'Maps for architectural visualization',
        'settings': {
            'bake_diffuse': True,
            'bake_normal': True,
            'bake_roughness_glossy': True,
            'bake_ao': True,
            'bake_bump': True,
        }
    }
}
