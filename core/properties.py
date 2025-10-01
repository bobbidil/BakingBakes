"""
Property definitions for BakingBakes addon
"""

import bpy

class BakeObjectItem(bpy.types.PropertyGroup):
    """Individual bake object item"""
    object: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to include in baking"
    )

class BakeObjectsList(bpy.types.PropertyGroup):
    """Collection of bake objects"""
    objects: bpy.props.CollectionProperty(type=BakeObjectItem)
    active_index: bpy.props.IntProperty(default=0)
    bake_selected_to_targets: bpy.props.BoolProperty(
        name="Bake Selected Object to Target Objects",
        description="Bake the selected high-poly object to all target low-poly objects in the list",
        default=False
    )

class BakeSettings(bpy.types.PropertyGroup):
    """Bake settings with comprehensive PBR bake type toggles"""
    # Left Column
    bake_diffuse: bpy.props.BoolProperty(name="Diffuse", default=True)
    bake_sss: bpy.props.BoolProperty(name="SSS", default=False)
    bake_roughness_glossy: bpy.props.BoolProperty(name="Roughness/Glossy", default=True)
    bake_transmission: bpy.props.BoolProperty(name="Transmission", default=False)
    bake_clearcoat: bpy.props.BoolProperty(name="Clearcoat", default=False)
    bake_emission: bpy.props.BoolProperty(name="Emission", default=False)
    bake_specular: bpy.props.BoolProperty(name="Specular", default=True)
    bake_bump: bpy.props.BoolProperty(name="Bump", default=False)

    # Right Column
    bake_metalness: bpy.props.BoolProperty(name="Metalness", default=False)
    bake_sss_colour: bpy.props.BoolProperty(name="SSS Colour", default=False)
    bake_normal: bpy.props.BoolProperty(name="Normal", default=True)
    bake_transmission_rough: bpy.props.BoolProperty(name="Transmission Rough...", default=False)
    bake_clearcoat_roughness: bpy.props.BoolProperty(name="Clearcoat Roughness", default=False)
    bake_emission_strength: bpy.props.BoolProperty(name="Emission Strength", default=False)
    bake_alpha: bpy.props.BoolProperty(name="Alpha", default=False)

    # Dropdown settings
    roughness_mode: bpy.props.EnumProperty(
        name="Rough",
        items=[
            ('ROUGHNESS', 'Roughness', ''),
            ('GLOSSY', 'Glossy', ''),
        ],
        default='ROUGHNESS'
    )

    normal_mode: bpy.props.EnumProperty(
        name="Normal",
        items=[
            ('OPENGL', 'OpenGL', ''),
            ('DIRECTX', 'DirectX', ''),
        ],
        default='OPENGL'
    )

    # Baking options
    auto_uv_bake_map: bpy.props.BoolProperty(
        name="Bake to UV Maps named 'Bake'",
        description="Require UV map named 'Bake' for baking (will error if not found)",
        default=False
    )

def register_props():
    """Register scene properties"""
    bpy.types.Scene.bb_show_bake_objects = bpy.props.BoolProperty(
        name="Bake Objects",
        description="Show Bake Objects settings",
        default=False,
    )
    bpy.types.Scene.bb_show_bake_settings = bpy.props.BoolProperty(
        name="Bake Settings",
        description="Show Bake Settings",
        default=False,
    )
    bpy.types.Scene.bb_show_bake_panel = bpy.props.BoolProperty(
        name="Bake",
        description="Show Bake panel",
        default=False,
    )

def unregister_props():
    """Unregister scene properties"""
    if hasattr(bpy.types.Scene, "bb_show_bake_objects"):
        del bpy.types.Scene.bb_show_bake_objects
    if hasattr(bpy.types.Scene, "bb_show_bake_settings"):
        del bpy.types.Scene.bb_show_bake_settings
    if hasattr(bpy.types.Scene, "bb_show_bake_panel"):
        del bpy.types.Scene.bb_show_bake_panel
