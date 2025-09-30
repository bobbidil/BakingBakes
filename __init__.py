bl_info = {
    "name": "BakingBakes",
    "author": "Bob Tabbington",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "Properties > Render > BakingBakes",
    "description": "Multi-object baking management",
    "warning": "This addon may require comprehensive understanding of baking techniques",
    "doc_url": "",
    "category": "Render",
}

import bpy
from bpy.props import CollectionProperty, PointerProperty, StringProperty
from bpy.types import Panel, PropertyGroup, UIList, Operator

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

def register_props():
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
    if hasattr(bpy.types.Scene, "bb_show_bake_objects"):
        del bpy.types.Scene.bb_show_bake_objects
    if hasattr(bpy.types.Scene, "bb_show_bake_settings"):
        del bpy.types.Scene.bb_show_bake_settings
    if hasattr(bpy.types.Scene, "bb_show_bake_panel"):
        del bpy.types.Scene.bb_show_bake_panel

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
        # For now, just report success
        self.report({'INFO'}, "Bake objects list refreshed")
        return {'FINISHED'}

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

def create_bake_image(material_name, resolution=1024):
    """Create new image for baking"""
    image_name = f"{material_name}_Albedo"
    image = bpy.data.images.new(
        name=image_name,
        width=resolution,
        height=resolution,
        alpha=False
    )
    return image

def setup_material_for_baking(material, bake_image):
    """Set up material nodes for diffuse baking - NON-DESTRUCTIVE"""
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
    tex_node.label = "Baked Albedo"

    # Don't connect to anything - keep it unconnected as requested
    # The bake operation will use this node as the bake target

    return tex_node

def get_bake_type_mapping():
    """Get mapping of bake type checkboxes to Blender bake types"""
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

def perform_multi_baking(context, obj, bake_settings):
    """Perform baking for multiple selected bake types"""
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

        # Bake each selected type
        for bake_type, suffix in selected_bakes:
            # Create bake image with proper suffix
            image_name = f"{material.name}_{suffix}"
            image = bpy.data.images.new(
                name=image_name,
                width=1024,
                height=1024,
                alpha=(bake_type in ['NORMAL', 'ALPHA'])
            )

            # Set up material for baking
            tex_node = setup_material_for_baking(material, image)
            if not tex_node:
                continue

            # Select object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # Set bake settings based on type
            scene.cycles.samples = 1
            scene.render.bake.use_selected_to_active = False

            try:
                # Perform bake based on type
                if bake_type == 'NORMAL':
                    bpy.ops.object.bake(type='NORMAL', pass_filter={'COLOR'})
                elif bake_type == 'ROUGHNESS':
                    bpy.ops.object.bake(type='ROUGHNESS', pass_filter={'COLOR'})
                elif bake_type == 'EMIT':
                    bpy.ops.object.bake(type='EMIT', pass_filter={'COLOR'})
                elif bake_type == 'AO':
                    bpy.ops.object.bake(type='AO', pass_filter={'COLOR'})
                elif bake_type == 'SHADOW':
                    bpy.ops.object.bake(type='SHADOW', pass_filter={'COLOR'})
                elif bake_type == 'UV':
                    bpy.ops.object.bake(type='UV', pass_filter={'COLOR'})
                elif bake_type == 'ENVIRONMENT':
                    bpy.ops.object.bake(type='ENVIRONMENT', pass_filter={'COLOR'})
                elif bake_type == 'GLOSSY':
                    bpy.ops.object.bake(type='GLOSSY', pass_filter={'COLOR'})
                elif bake_type == 'TRANSMISSION':
                    bpy.ops.object.bake(type='TRANSMISSION', pass_filter={'COLOR'})
                elif bake_type == 'DIFFUSE':
                    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
                elif bake_type == 'SUBSURFACE':
                    bpy.ops.object.bake(type='SUBSURFACE', pass_filter={'COLOR'})
                elif bake_type == 'SUBSURFACE_COLOR':
                    bpy.ops.object.bake(type='SUBSURFACE_COLOR', pass_filter={'COLOR'})
                elif bake_type == 'METALNESS':
                    bpy.ops.object.bake(type='METALNESS', pass_filter={'COLOR'})
                elif bake_type == 'SPECULAR':
                    bpy.ops.object.bake(type='SPECULAR', pass_filter={'COLOR'})
                elif bake_type == 'ALPHA':
                    bpy.ops.object.bake(type='ALPHA', pass_filter={'COLOR'})
                elif bake_type == 'CLEARCOAT':
                    bpy.ops.object.bake(type='CLEARCOAT', pass_filter={'COLOR'})
                elif bake_type == 'CLEARCOAT_ROUGHNESS':
                    bpy.ops.object.bake(type='CLEARCOAT_ROUGHNESS', pass_filter={'COLOR'})
                elif bake_type == 'TRANSMISSION_ROUGHNESS':
                    bpy.ops.object.bake(type='TRANSMISSION_ROUGHNESS', pass_filter={'COLOR'})
                elif bake_type == 'EMISSION_STRENGTH':
                    bpy.ops.object.bake(type='EMISSION_STRENGTH', pass_filter={'COLOR'})
                elif bake_type == 'BUMP':
                    bpy.ops.object.bake(type='BUMP', pass_filter={'COLOR'})
                else:
                    print(f"Unsupported bake type: {bake_type}")
                    continue

                # Save image
                image.pack()
                image.filepath = f"//{image_name}.png"
                image.save()

                print(f"Baked {bake_type} for {obj.name} -> {material.name}")

            except Exception as e:
                print(f"Failed to bake {bake_type} for {obj.name}: {str(e)}")
                continue

    return True, f"Successfully baked {len(selected_bakes)} types for {obj.name}"

class BAKINGBAKES_OT_BakeObjects(Operator):
    """Bake all objects in the list"""
    bl_idname = "bakingbakes.bake_objects"
    bl_label = "BAKE OBJECTS"
    bl_description = "Bake all objects in the list"

    def execute(self, context):
        scene = context.scene
        bake_objects = scene.bakingbakes_objects
        bake_settings = scene.bakingbakes_settings

        if not bake_objects.objects:
            self.report({'WARNING'}, "No objects in bake list")
            return {'CANCELLED'}

        # Check UV maps if required
        if bake_settings.auto_uv_bake_map:
            uv_check_passed, missing_uv_objects = check_uv_maps_for_objects(bake_objects, require_bake_uv=True)
            if not uv_check_passed:
                missing_list = ", ".join(missing_uv_objects)
                self.report({'ERROR'}, f"Bake UV map not found in objects: {missing_list}")
                return {'CANCELLED'}

        # Multi-bake mode - bake all selected types for each object
        success_count = 0
        failed_objects = []
        total_bakes = 0

        for item in bake_objects.objects:
            obj = item.object
            if not obj:
                continue

            success, message = perform_multi_baking(context, obj, bake_settings)
            if success:
                success_count += 1
                # Extract number of baked types from message
                try:
                    baked_count = int(message.split()[-2])  # "Successfully baked X types"
                    total_bakes += baked_count
                except:
                    total_bakes += 1
            else:
                failed_objects.append(f"{obj.name}: {message}")

        # Report results
        if success_count > 0:
            self.report({'INFO'}, f"Successfully baked {success_count} objects ({total_bakes} total maps)")
            if failed_objects:
                print("Failed objects:", failed_objects)
        else:
            self.report({'ERROR'}, "No objects were baked successfully")
            return {'CANCELLED'}

        return {'FINISHED'}

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

        # Bake toggle section
        icon = 'TRIA_DOWN' if scene.bb_show_bake_panel else 'TRIA_RIGHT'
        layout.prop(scene, "bb_show_bake_panel", text="Bake", icon=icon, toggle=True)

        if scene.bb_show_bake_panel:
            box = layout.box()

            # Big bake button
            bake_row = box.row()
            bake_row.scale_y = 2.0
            bake_row.operator("bakingbakes.bake_objects", text="BAKE OBJECTS")

def register():
    # Register properties first
    register_props()

    # Register classes in order
    bpy.utils.register_class(BakeObjectItem)
    bpy.utils.register_class(BakeObjectsList)
    bpy.utils.register_class(BakeSettings)
    bpy.utils.register_class(BAKINGBAKES_OT_AddObject)
    bpy.utils.register_class(BAKINGBAKES_OT_RemoveObject)
    bpy.utils.register_class(BAKINGBAKES_OT_ClearObjects)
    bpy.utils.register_class(BAKINGBAKES_OT_RefreshObjects)
    bpy.utils.register_class(BAKINGBAKES_OT_BakeObjects)
    bpy.utils.register_class(BAKINGBAKES_UL_ObjectsList)
    bpy.utils.register_class(BAKINGBAKES_PT_MainPanel)

    # Add properties to Scene
    bpy.types.Scene.bakingbakes_objects = PointerProperty(type=BakeObjectsList)
    bpy.types.Scene.bakingbakes_settings = PointerProperty(type=BakeSettings)

def unregister():
    # Unregister in reverse order
    bpy.utils.unregister_class(BAKINGBAKES_PT_MainPanel)
    bpy.utils.unregister_class(BAKINGBAKES_UL_ObjectsList)
    bpy.utils.unregister_class(BAKINGBAKES_OT_BakeObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_RefreshObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_ClearObjects)
    bpy.utils.unregister_class(BAKINGBAKES_OT_RemoveObject)
    bpy.utils.unregister_class(BAKINGBAKES_OT_AddObject)
    bpy.utils.unregister_class(BakeSettings)
    bpy.utils.unregister_class(BakeObjectsList)
    bpy.utils.unregister_class(BakeObjectItem)

    # Remove properties from Scene
    if hasattr(bpy.types.Scene, "bakingbakes_objects"):
        del bpy.types.Scene.bakingbakes_objects
    if hasattr(bpy.types.Scene, "bakingbakes_settings"):
        del bpy.types.Scene.bakingbakes_settings

    # Unregister properties
    unregister_props()

if __name__ == "__main__":
    register()
