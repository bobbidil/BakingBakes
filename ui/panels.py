"""
UI panels for BakingBakes addon
"""

import bpy
from bpy.types import Panel, UIList
from core.properties import BakeObjectItem, BakeObjectsList, BakeSettings

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
