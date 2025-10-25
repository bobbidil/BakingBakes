bl_info = {
    "name": "BakingBakes",
    "author": "Bob Tabbington",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "Properties > Render > BakingBakes",
    "description": "Multi-object baking management",
    "warning": "This addon may require comprehensive understanding of baking techniques",
    "doc_url": "",
    "category": "Testing",
}

# __init__.py
if "loaded" in locals():
    import importlib
    importlib.reload(ops)
    importlib.reload(ui)
else:
    from . import ops, ui
loaded = True

import bpy
from bpy.props import CollectionProperty, PointerProperty
from bpy.types import Panel, PropertyGroup, UIList, Operator

# ============================================================================
# DATA MODELS
# ============================================================================

class BakeObjectItem(PropertyGroup):
    """Individual bake object item"""
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to include in baking"
    )

class BakeObjectsList(PropertyGroup):
    """Collection of bake objects"""
    objects: CollectionProperty(type=BakeObjectItem)
    active_index: bpy.props.IntProperty(default=0)
    bake_selected_to_targets: bpy.props.BoolProperty(
        name="Bake Selected Object to Target Objects",
        description="Bake the selected high-poly object to all target low-poly objects in the list",
        default=False
    )

    # Selected to Active settings
    use_cage: bpy.props.BoolProperty(
        name="Use Cage",
        description="Use cage object for baking",
        default=False
    )
    cage_object: PointerProperty(
        name="Cage Object",
        type=bpy.types.Object,
        description="Cage object for baking"
    )
    extrusion: bpy.props.FloatProperty(
        name="Extrusion",
        description="Extrusion distance for rays",
        default=0.5,
        min=0.0,
        max=10.0
    )
    max_ray_distance: bpy.props.FloatProperty(
        name="Max Ray Distance",
        description="Maximum ray distance for baking",
        default=0.1,
        min=0.0,
        max=1.0
    )

class BakeSettings(PropertyGroup):
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

class OutputSettings(PropertyGroup):
    """Output settings for baking resolution and format"""
    # Bake resolution (high-res for baking)
    bake_width: bpy.props.IntProperty(
        name="Bake Width",
        description="Width for baking resolution",
        default=1024,
        min=256,
        max=8192
    )
    bake_height: bpy.props.IntProperty(
        name="Bake Height",
        description="Height for baking resolution",
        default=1024,
        min=256,
        max=8192
    )

    # Output resolution (final texture size)
    output_width: bpy.props.IntProperty(
        name="Output Width",
        description="Final output texture width",
        default=1024,
        min=256,
        max=8192
    )
    output_height: bpy.props.IntProperty(
        name="Output Height",
        description="Final output texture height",
        default=1024,
        min=256,
        max=8192
    )

    # Margin settings
    bake_margin: bpy.props.IntProperty(
        name="Bake Margin",
        description="Margin in pixels for baking",
        default=16,
        min=0,
        max=64
    )

    margin_type: bpy.props.EnumProperty(
        name="Margin Type",
        items=[
            ('ADJACENT_FACES', 'Adjacent Faces', 'Extend bake margin over adjacent faces'),
            ('EXTEND', 'Extend', 'Extend bake beyond object bounds'),
        ],
        default='ADJACENT_FACES'
    )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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

# ============================================================================
# CLEAN BAKE OPERATIONS (No more ugly elif chain!)
# ============================================================================

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

# ============================================================================
# BAKING ENGINE
# ============================================================================

def perform_multi_baking(context, obj, bake_settings, output_settings):
    """Perform baking for multiple selected bake types - REFACTORED"""
    scene = context.scene

    # Set bake resolution from output settings
    bake_width = output_settings.bake_width
    bake_height = output_settings.bake_height

    # Set margin settings
    scene.render.bake.margin = output_settings.bake_margin
    scene.render.bake.margin_type = output_settings.margin_type

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
            # Create bake image with proper suffix and resolution
            image = create_bake_image(material.name, suffix, resolution=bake_width)

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

                # Resize to output resolution if different from bake resolution
                if (output_settings.output_width != bake_width or
                    output_settings.output_height != bake_height):
                    image.scale(output_settings.output_width, output_settings.output_height)

                # Save image
                image.pack()
                image.filepath = f"//{material.name}_{suffix}.png"
                image.save()

                print(f"Baked {bake_type} for {obj.name} -> {material.name} ({bake_width}x{bake_height})")

            except Exception as e:
                print(f"Failed to bake {bake_type} for {obj.name}: {str(e)}")
                continue

    return True, f"Successfully baked {len(selected_bakes)} types for {obj.name}"

# ============================================================================
# OPERATORS
# ============================================================================

class BAKINGBAKES_OT_AddObject(Operator):
    """Add selected object to bake list"""
    bl_idname = "bakingbakes.add_object"
    bl_label = "Add Object"
    bl_description = "Add selected object to bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        # Get selected objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Add objects to bake list
        for obj in selected_objects:
            # Check if object is already in list
            if not any(item.object == obj for item in bake_objects.objects):
                item = bake_objects.objects.add()
                item.object = obj

        return {'FINISHED'}

class BAKINGBAKES_OT_RemoveObject(Operator):
    """Remove object from bake list"""
    bl_idname = "bakingbakes.remove_object"
    bl_label = "Remove Object"
    bl_description = "Remove selected object from bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        if bake_objects.objects:
            # Remove active item
            index = bake_objects.active_index
            if 0 <= index < len(bake_objects.objects):
                bake_objects.objects.remove(index)
                # Adjust active index
                bake_objects.active_index = min(index, len(bake_objects.objects) - 1)

        return {'FINISHED'}

class BAKINGBAKES_OT_ClearObjects(Operator):
    """Clear all objects from bake list"""
    bl_idname = "bakingbakes.clear_objects"
    bl_label = "Clear All"
    bl_description = "Remove all objects from bake list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects

        bake_objects.objects.clear()
        bake_objects.active_index = 0

        return {'FINISHED'}

class BAKINGBAKES_OT_RefreshObjects(Operator):
    """Refresh bake objects list"""
    bl_idname = "bakingbakes.refresh_objects"
    bl_label = "Refresh"
    bl_description = "Refresh the bake objects list"

    def execute(self, context):
        self.report({'INFO'}, "Bake objects list refreshed")
        return {'FINISHED'}

class BAKINGBAKES_OT_BakeObjects(Operator):
    """Bake all objects in the list"""
    bl_idname = "bakingbakes.bake_objects"
    bl_label = "BAKE OBJECTS"
    bl_description = "Bake all objects in the list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects
        bake_settings = scene.bakingbakes_settings
        output_settings = scene.bakingbakes_output

        if not bake_objects.objects:
            self.report({'WARNING'}, "No objects in bake list")
            return {'CANCELLED'}

        # Check bake mode
        if bake_objects.bake_selected_to_targets:
            # SELECTED-TO-ACTIVE MODE: High-poly source to low-poly targets
            return self._bake_selected_to_active(context, bake_objects, bake_settings, output_settings)
        else:
            # NORMAL MODE: Bake each object individually
            return self._bake_individual_objects(context, bake_objects, bake_settings, output_settings)

    def _bake_selected_to_active(self, context, bake_objects, bake_settings, output_settings):
        """Bake from selected high-poly object to target low-poly objects"""
        scene = context.scene

        # Get currently selected object (this is the SOURCE/high-poly)
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'ERROR'}, "No source object selected. Select high-poly object and try again.")
            return {'CANCELLED'}

        source_object = selected_objects[0]  # Use first selected object as source

        # Check that we have target objects in the bake list
        target_objects = [item.object for item in bake_objects.objects if item.object and item.object != source_object]
        if not target_objects:
            self.report({'ERROR'}, "No target objects in bake list. Add low-poly objects to bake list.")
            return {'CANCELLED'}

        # Set up baking settings
        scene.render.bake.margin = output_settings.bake_margin
        scene.render.bake.margin_type = output_settings.margin_type

        # Get selected bake types
        bake_mapping = get_bake_type_mapping()
        selected_bakes = []
        for attr_name, (bake_type, suffix) in bake_mapping.items():
            if getattr(bake_settings, attr_name, False):
                selected_bakes.append((bake_type, suffix))

        if not selected_bakes:
            self.report({'WARNING'}, "No bake types selected")
            return {'CANCELLED'}

        success_count = 0
        total_bakes = 0

        # Bake each target object from the source
        for target_obj in target_objects:
            if not target_obj:
                continue

            # Process each material on target
            for slot in target_obj.material_slots:
                material = slot.material
                if not material:
                    continue

                # Bake each selected type from source to target
                for bake_type, suffix in selected_bakes:
                    # Create bake image
                    image = create_bake_image(material.name, suffix, resolution=output_settings.bake_width)

                    # Set up material for baking
                    tex_node = setup_material_for_baking(material, image)
                    if not tex_node:
                        continue

                    # Set up source and target for selected-to-active baking
                    bpy.ops.object.select_all(action='DESELECT')

                    # Select SOURCE first, then TARGET
                    source_object.select_set(True)
                    target_obj.select_set(True)
                    context.view_layer.objects.active = target_obj  # Target becomes active

                    # Set selected-to-active baking mode
                    scene.render.bake.use_selected_to_active = True
                    scene.render.bake.cage_extrusion = bake_objects.extrusion
                    scene.render.bake.max_ray_distance = bake_objects.max_ray_distance

                    if bake_objects.use_cage and bake_objects.cage_object:
                        scene.render.bake.cage_object = bake_objects.cage_object.name

                    try:
                        # Perform bake operation
                        perform_bake_operation(bake_type)

                        # Resize to output resolution if needed
                        if (output_settings.output_width != output_settings.bake_width or
                            output_settings.output_height != output_settings.bake_height):
                            image.scale(output_settings.output_width, output_settings.output_height)

                        # Save image
                        image.pack()
                        image.filepath = f"//{material.name}_{suffix}.png"
                        image.save()

                        print(f"Baked {bake_type} from {source_object.name} to {target_obj.name}")
                        success_count += 1

                    except Exception as e:
                        print(f"Failed to bake {bake_type} from {source_object.name} to {target_obj.name}: {str(e)}")
                        continue

        self.report({'INFO'}, f"Successfully baked from {source_object.name} to {len(target_objects)} targets ({success_count} total maps)")
        return {'FINISHED'}

    def _bake_individual_objects(self, context, bake_objects, bake_settings, output_settings):
        """Bake each object individually (original mode)"""
        success_count = 0
        failed_objects = []
        total_bakes = 0

        # Check UV maps if required
        if bake_settings.auto_uv_bake_map:
            uv_check_passed, missing_uv_objects = check_uv_maps_for_objects(bake_objects, require_bake_uv=True)
            if not uv_check_passed:
                missing_list = ", ".join(missing_uv_objects)
                self.report({'ERROR'}, f"Bake UV map not found in objects: {missing_list}")
                return {'CANCELLED'}

        for item in bake_objects.objects:
            obj = item.object
            if not obj:
                continue

            success, message = perform_multi_baking(context, obj, bake_settings, output_settings)
            if success:
                success_count += 1
                try:
                    baked_count = int(message.split()[-2])
                    total_bakes += baked_count
                except:
                    total_bakes += 1
            else:
                failed_objects.append(f"{obj.name}: {message}")

        if success_count > 0:
            self.report({'INFO'}, f"Successfully baked {success_count} objects ({total_bakes} total maps)")
            if failed_objects:
                print("Failed objects:", failed_objects)
        else:
            self.report({'ERROR'}, "No objects were baked successfully")
            return {'CANCELLED'}

        return {'FINISHED'}

# ============================================================================
# UI COMPONENTS
# ============================================================================

class BAKINGBAKES_UL_ObjectsList(UIList):
    """UI List for bake objects"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.object:
            layout.prop(item.object, "name", text="", emboss=False)
        else:
            layout.label(text="Invalid Object", icon='ERROR')

class BAKINGBAKES_PT_MainPanel(Panel):
    """Main BakingBakes panel with toggle interface"""
    bl_label = "BakingBakes"
    bl_idname = "BAKINGBAKES_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Header
        layout.label(text="BakingBakes", icon='RENDER_RESULT')

        # Bake Objects toggle section
        icon = 'TRIA_DOWN' if scene.bb_show_bake_objects else 'TRIA_RIGHT'
        layout.prop(scene, "bb_show_bake_objects", text="Bake Objects", icon=icon, toggle=True)

        if scene.bb_show_bake_objects:
            box = layout.box()
            bake_objects = scene.bakingbakes_objects

            # Object list
            row = box.row()
            row.template_list(
                "BAKINGBAKES_UL_ObjectsList", "",
                bake_objects, "objects",
                bake_objects, "active_index",
                rows=3
            )

            # List buttons column
            col = row.column(align=True)
            col.operator("bakingbakes.add_object", icon='ADD', text="")
            col.operator("bakingbakes.remove_object", icon='REMOVE', text="")
            col.operator("bakingbakes.clear_objects", icon='X', text="")
            col.operator("bakingbakes.refresh_objects", icon='FILE_REFRESH', text="")

            # Bake Selected to Target Objects checkbox
            box.prop(bake_objects, "bake_selected_to_targets", text="Bake Selected Object to Target Objects")

            # Selected to Active settings subpanel
            if bake_objects.bake_selected_to_targets:
                sub_box = box.box()
                sub_box.label(text="Selected to Active Settings:")

                # Cage settings
                sub_box.prop(bake_objects, "use_cage", text="Use Cage")
                if bake_objects.use_cage:
                    sub_box.prop(bake_objects, "cage_object", text="Cage Object")

                # Ray settings
                sub_box.prop(bake_objects, "extrusion", text="Extrusion")
                sub_box.prop(bake_objects, "max_ray_distance", text="Max Ray Distance")

            # Show count
            if bake_objects.objects:
                box.label(text=f"Total objects: {len(bake_objects.objects)}")
            else:
                box.label(text="No objects in list")

        # Bake Settings toggle section
        icon = 'TRIA_DOWN' if scene.bb_show_bake_settings else 'TRIA_RIGHT'
        layout.prop(scene, "bb_show_bake_settings", text="Bake Settings", icon=icon, toggle=True)

        if scene.bb_show_bake_settings:
            box = layout.box()
            bake_settings = scene.bakingbakes_settings

            # PBR Bake Types - matching the professional layout
            box.label(text="PBR Bakes")

            # Two columns like in the image
            split = box.split(factor=0.5)

            # Left Column
            col1 = split.column()
            col1.prop(bake_settings, "bake_diffuse", text="Diffuse")
            col1.prop(bake_settings, "bake_sss", text="SSS")
            col1.prop(bake_settings, "bake_roughness_glossy", text="Roughness/Glossy")
            col1.prop(bake_settings, "bake_transmission", text="Transmission")
            col1.prop(bake_settings, "bake_clearcoat", text="Clearcoat")
            col1.prop(bake_settings, "bake_emission", text="Emission")
            col1.prop(bake_settings, "bake_specular", text="Specular")
            col1.prop(bake_settings, "bake_bump", text="Bump")

            # Right Column
            col2 = split.column()
            col2.prop(bake_settings, "bake_metalness", text="Metalness")
            col2.prop(bake_settings, "bake_sss_colour", text="SSS Colour")
            col2.prop(bake_settings, "bake_normal", text="Normal")
            col2.prop(bake_settings, "bake_transmission_rough", text="Transmission Rough...")
            col2.prop(bake_settings, "bake_clearcoat_roughness", text="Clearcoat Roughness")
            col2.prop(bake_settings, "bake_emission_strength", text="Emission Strength")
            col2.prop(bake_settings, "bake_alpha", text="Alpha")

            # Dropdown settings row
            row = box.row()
            row.prop(bake_settings, "roughness_mode", text="Rough")
            row.prop(bake_settings, "normal_mode", text="Normal")

            # Baking options
            box.separator()
            box.prop(bake_settings, "auto_uv_bake_map", text="Bake to UV Maps named 'Bake'")

            # Show selected bake types count
            selected_types = sum([
                bake_settings.bake_diffuse, bake_settings.bake_sss, bake_settings.bake_roughness_glossy,
                bake_settings.bake_transmission, bake_settings.bake_clearcoat, bake_settings.bake_emission,
                bake_settings.bake_specular, bake_settings.bake_bump, bake_settings.bake_metalness,
                bake_settings.bake_sss_colour, bake_settings.bake_normal, bake_settings.bake_transmission_rough,
                bake_settings.bake_clearcoat_roughness, bake_settings.bake_emission_strength, bake_settings.bake_alpha
            ])
            box.label(text=f"Selected: {selected_types} bake types")

        # Output Settings toggle section (NEW!)
        icon = 'TRIA_DOWN' if scene.bb_show_output_settings else 'TRIA_RIGHT'
        layout.prop(scene, "bb_show_output_settings", text="Output Settings", icon=icon, toggle=True)

        if scene.bb_show_output_settings:
            box = layout.box()
            output_settings = scene.bakingbakes_output

            # Bake resolution settings
            box.label(text="Bake at:")
            row = box.row()
            row.prop(output_settings, "bake_width", text="Bake Width")
            row.prop(output_settings, "bake_height", text="Bake Height")

            # Output resolution settings
            box.label(text="Output at:")
            row = box.row()
            row.prop(output_settings, "output_width", text="Output Width")
            row.prop(output_settings, "output_height", text="Output Height")

            # Margin settings
            box.label(text="Margin Type:")
            box.prop(output_settings, "margin_type", text="")
            box.prop(output_settings, "bake_margin", text="Bake Margin")

        # Bake toggle section
        icon = 'TRIA_DOWN' if scene.bb_show_bake_panel else 'TRIA_RIGHT'
        layout.prop(scene, "bb_show_bake_panel", text="Bake", icon=icon, toggle=True)

        if scene.bb_show_bake_panel:
            box = layout.box()

            # Big bake button
            bake_row = box.row()
            bake_row.scale_y = 2.0
            bake_row.operator("bakingbakes.bake_objects", text="BAKE OBJECTS")

# ============================================================================
# REGISTRATION
# ============================================================================

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
    bpy.types.Scene.bb_show_output_settings = bpy.props.BoolProperty(
        name="Output Settings",
        description="Show Output Settings",
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
    if hasattr(bpy.types.Scene, "bb_show_output_settings"):
        del bpy.types.Scene.bb_show_output_settings
    if hasattr(bpy.types.Scene, "bb_show_bake_panel"):
        del bpy.types.Scene.bb_show_bake_panel

def register():
    """Register all addon components"""
    # Register properties first
    register_props()

    # Register classes in dependency order
    bpy.utils.register_class(BakeObjectItem)
    bpy.utils.register_class(BakeObjectsList)
    bpy.utils.register_class(BakeSettings)
    bpy.utils.register_class(OutputSettings)

    # Register operators
    bpy.utils.register_class(BAKINGBAKES_OT_AddObject)
    bpy.utils.register_class(BAKINGBAKES_OT_RemoveObject)
    bpy.utils.register_class(BAKINGBAKES_OT_ClearObjects)
    bpy.utils.register_class(BAKINGBAKES_OT_RefreshObjects)
    bpy.utils.register_class(BAKINGBAKES_OT_BakeObjects)

    # Register UI components
    bpy.utils.register_class(BAKINGBAKES_UL_ObjectsList)
    bpy.utils.register_class(BAKINGBAKES_PT_MainPanel)

    # Add properties to Scene
    bpy.types.Scene.bakingbakes_objects = PointerProperty(type=BakeObjectsList)
    bpy.types.Scene.bakingbakes_settings = PointerProperty(type=BakeSettings)
    bpy.types.Scene.bakingbakes_output = PointerProperty(type=OutputSettings)

def unregister():
    """Unregister all addon components"""
    # Unregister in reverse order
    bpy.utils.unregister_class(BAKINGBAKES_PT_MainPanel)
    bpy.utils.unregister_class(BAKINGBAKES_UL_ObjectsList)

    bpy.utils.unregister_class(BAKINGBAKES_OT_BakeObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_RefreshObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_ClearObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_RemoveObject)
    bpy.utils.unregister_class(BAKINGBAKES_OT_AddObject)

    bpy.utils.unregister_class(OutputSettings)
    bpy.utils.unregister_class(BakeSettings)
    bpy.utils.unregister_class(BakeObjectsList)
    bpy.utils.unregister_class(BakeObjectItem)

    # Remove properties from Scene
    if hasattr(bpy.types.Scene, "bakingbakes_objects"):
        del bpy.types.Scene.bakingbakes_objects
    if hasattr(bpy.types.Scene, "bakingbakes_settings"):
        del bpy.types.Scene.bakingbakes_settings
    if hasattr(bpy.types.Scene, "bakingbakes_output"):
        del bpy.types.Scene.bakingbakes_output

    # Unregister properties
    unregister_props()

if __name__ == "__main__":
    register()
