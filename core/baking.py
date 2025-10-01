"""
Baking logic and operations for BakingBakes addon
"""

import bpy

def ensure_uv_map(obj, uv_name="Bake"):
    """Ensure object has UV map with specified name"""
    if obj.type != 'MESH':
        return None

    mesh = obj.data
    uv_maps = mesh.uv_layers

    # Check if UV map already exists
    if uv_name in uv_maps:
        return uv_maps[uv_name]

    # Create new UV map
    return uv_maps.new(name=uv_name)

def create_bake_image(material_name, suffix, resolution=1024):
    """Create new image for baking with proper naming"""
    image_name = f"{material_name}_{suffix}"
    image = bpy.data.images.new(
        name=image_name,
        width=resolution,
        height=resolution,
        alpha=(suffix in ['Normal', 'Alpha'])
    )
    return image

def setup_material_for_baking(material, bake_image):
    """Set up material nodes for baking - NON-DESTRUCTIVE"""
    if not material:
        return None

    # Get or create node tree
    if not material.node_tree:
        return None

    nodes = material.node_tree.nodes

    # Find existing output node
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
            break

    if not output_node:
        return None

    # Create image texture node for baking (unconnected)
    tex_node = nodes.new(type='ShaderNodeTexImage')
    tex_node.location = (-600, -300)  # Position below main material
    tex_node.image = bake_image
    tex_node.label = f"Baked {bake_image.name.split('_')[-1]}"

    # Don't connect to anything - keep it unconnected as requested
    # The bake operation will use this node as the bake target

    return tex_node

def get_bake_type_mapping():
    """Get mapping of bake type checkboxes to Blender bake types and suffixes"""
    return {
        'bake_diffuse': ('DIFFUSE', 'Albedo'),
        'bake_normal': ('NORMAL', 'Normal'),
        'bake_roughness_glossy': ('ROUGHNESS', 'Roughness'),
        'bake_emit': ('EMIT', 'Emission'),
        'bake_ao': ('AO', 'AmbientOcclusion'),
        'bake_shadow': ('SHADOW', 'Shadow'),
        'bake_uv': ('UV', 'UV'),
        'bake_environment': ('ENVIRONMENT', 'Environment'),
        'bake_glossy': ('GLOSSY', 'Glossy'),
        'bake_transmission': ('TRANSMISSION', 'Transmission'),
        'bake_sss': ('SUBSURFACE', 'SSS'),
        'bake_sss_colour': ('SUBSURFACE_COLOR', 'SSSColor'),
        'bake_metalness': ('METALNESS', 'Metalness'),
        'bake_specular': ('SPECULAR', 'Specular'),
        'bake_alpha': ('ALPHA', 'Alpha'),
        'bake_clearcoat': ('CLEARCOAT', 'Clearcoat'),
        'bake_clearcoat_roughness': ('CLEARCOAT_ROUGHNESS', 'ClearcoatRoughness'),
        'bake_transmission_rough': ('TRANSMISSION_ROUGHNESS', 'TransmissionRoughness'),
        'bake_emission_strength': ('EMISSION_STRENGTH', 'EmissionStrength'),
        'bake_bump': ('BUMP', 'Bump'),
    }

def check_uv_maps_for_objects(bake_objects, require_bake_uv=True):
    """Check if all objects have required UV maps"""
    if not require_bake_uv:
        return True, []

    missing_uv_objects = []

    for item in bake_objects.objects:
        obj = item.object
        if not obj or obj.type != 'MESH':
            continue

        # Check if "Bake" UV map exists
        if "Bake" not in obj.data.uv_layers:
            missing_uv_objects.append(obj.name)

    return len(missing_uv_objects) == 0, missing_uv_objects

# REFACTORED: Clean dictionary-based bake operations instead of ugly elif chain
BAKE_OPERATIONS = {
    'NORMAL': lambda: bpy.ops.object.bake(type='NORMAL', pass_filter={'COLOR'}),
    'ROUGHNESS': lambda: bpy.ops.object.bake(type='ROUGHNESS', pass_filter={'COLOR'}),
    'EMIT': lambda: bpy.ops.object.bake(type='EMIT', pass_filter={'COLOR'}),
    'AO': lambda: bpy.ops.object.bake(type='AO', pass_filter={'COLOR'}),
    'SHADOW': lambda: bpy.ops.object.bake(type='SHADOW', pass_filter={'COLOR'}),
    'UV': lambda: bpy.ops.object.bake(type='UV', pass_filter={'COLOR'}),
    'ENVIRONMENT': lambda: bpy.ops.object.bake(type='ENVIRONMENT', pass_filter={'COLOR'}),
    'GLOSSY': lambda: bpy.ops.object.bake(type='GLOSSY', pass_filter={'COLOR'}),
    'TRANSMISSION': lambda: bpy.ops.object.bake(type='TRANSMISSION', pass_filter={'COLOR'}),
    'DIFFUSE': lambda: bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}),
    'SUBSURFACE': lambda: bpy.ops.object.bake(type='SUBSURFACE', pass_filter={'COLOR'}),
    'SUBSURFACE_COLOR': lambda: bpy.ops.object.bake(type='SUBSURFACE_COLOR', pass_filter={'COLOR'}),
    'METALNESS': lambda: bpy.ops.object.bake(type='METALNESS', pass_filter={'COLOR'}),
    'SPECULAR': lambda: bpy.ops.object.bake(type='SPECULAR', pass_filter={'COLOR'}),
    'ALPHA': lambda: bpy.ops.object.bake(type='ALPHA', pass_filter={'COLOR'}),
    'CLEARCOAT': lambda: bpy.ops.object.bake(type='CLEARCOAT', pass_filter={'COLOR'}),
    'CLEARCOAT_ROUGHNESS': lambda: bpy.ops.object.bake(type='CLEARCOAT_ROUGHNESS', pass_filter={'COLOR'}),
    'TRANSMISSION_ROUGHNESS': lambda: bpy.ops.object.bake(type='TRANSMISSION_ROUGHNESS', pass_filter={'COLOR'}),
    'EMISSION_STRENGTH': lambda: bpy.ops.object.bake(type='EMISSION_STRENGTH', pass_filter={'COLOR'}),
    'BUMP': lambda: bpy.ops.object.bake(type='BUMP', pass_filter={'COLOR'}),
}

def perform_bake_operation(bake_type):
    """Perform bake operation using clean dictionary lookup"""
    if bake_type in BAKE_OPERATIONS:
        return BAKE_OPERATIONS[bake_type]()
    else:
        raise ValueError(f"Unsupported bake type: {bake_type}")

def perform_multi_baking(context, obj, bake_settings):
    """Perform baking for multiple selected bake types - REFACTORED"""
    scene = context.scene

    # Ensure UV map exists
    if bake_settings.auto_uv_bake_map:
        uv_map = ensure_uv_map(obj, "Bake")
        if not uv_map:
            return False, f"Failed to create UV map for {obj.name}"
    else:
        # Use first available UV map
        if obj.data.uv_layers:
            uv_map = obj.data.uv_layers[0]
        else:
            return False, f"No UV maps found for {obj.name}"

    # Make UV map active
    if obj.data.uv_layers:
        for i, uv_layer in enumerate(obj.data.uv_layers):
            uv_layer.active = (uv_layer == uv_map)

    # Get bake type mapping
    bake_mapping = get_bake_type_mapping()

    # Get selected bake types
    selected_bakes = []
    for attr_name, (bake_type, suffix) in bake_mapping.items():
        if getattr(bake_settings, attr_name, False):
            selected_bakes.append((bake_type, suffix))

    if not selected_bakes:
        return False, f"No bake types selected for {obj.name}"

    # Process each material
    for slot in obj.material_slots:
        material = slot.material
        if not material:
            continue

        # Bake each selected type using clean dictionary approach
        for bake_type, suffix in selected_bakes:
            # Create bake image with proper suffix
            image = create_bake_image(material.name, suffix)

            # Set up material for baking
            tex_node = setup_material_for_baking(material, image)
            if not tex_node:
                continue

            # Select object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # Set bake settings
            scene.cycles.samples = 1
            scene.render.bake.use_selected_to_active = False

            try:
                # Use clean dictionary-based bake operation
                perform_bake_operation(bake_type)

                # Save image
                image.pack()
                image.filepath = f"//{material.name}_{suffix}.png"
                image.save()

                print(f"Baked {bake_type} for {obj.name} -> {material.name}")

            except Exception as e:
                print(f"Failed to bake {bake_type} for {obj.name}: {str(e)}")
                continue

    return True, f"Successfully baked {len(selected_bakes)} types for {obj.name}"
