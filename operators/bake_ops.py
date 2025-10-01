"""
Baking operators for BakingBakes addon
"""

import bpy
from bpy.types import Operator
from core.baking import perform_multi_baking, check_uv_maps_for_objects

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
