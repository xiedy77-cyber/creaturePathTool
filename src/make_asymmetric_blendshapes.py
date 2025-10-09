"""
Make Asymmetric Blendshapes Script

This script takes a base mesh and a symmetrical blendshape source and creates
two asymmetric versions - one with left side modified, one with right side modified.

Usage:
    - Select base mesh (e.g., pSphere1) first
    - Select blendshape source (e.g., pSphere2) second
    - Run the script

The script will create:
    - pSphere2_Left: Base mesh on right side, blendshape on left side
    - pSphere2_Right: Base mesh on left side, blendshape on right side
"""

import maya.cmds as cmds


def get_vertex_position(mesh, vertex_id):
    """Get the world position of a vertex."""
    return cmds.pointPosition(f"{mesh}.vtx[{vertex_id}]", world=True)


def set_vertex_position(mesh, vertex_id, position):
    """Set the world position of a vertex."""
    cmds.move(position[0], position[1], position[2], f"{mesh}.vtx[{vertex_id}]", 
              worldSpace=True, absolute=True)


def get_vertex_count(mesh):
    """Get the total number of vertices in a mesh."""
    return cmds.polyEvaluate(mesh, vertex=True)


def duplicate_mesh(original_mesh, new_name):
    """Duplicate a mesh and return the new name."""
    duplicated = cmds.duplicate(original_mesh, name=new_name)[0]
    return duplicated


def is_vertex_on_left_side(mesh, vertex_id, center_tolerance=0.001):
    """
    Determine if a vertex is on the left side of the mesh.
    Assumes the mesh is centered and uses X-axis for left/right determination.
    Returns True for left side (positive X), False for right side (negative X).
    """
    pos = get_vertex_position(mesh, vertex_id)
    x_pos = pos[0]
    
    # If very close to center, consider it center
    if abs(x_pos) < center_tolerance:
        return None  # Center vertex
    
    return x_pos > 0  # Positive X is left side in Maya's default view


def find_mirror_vertex(mesh, vertex_id, tolerance=0.01):
    """
    Find the mirror vertex on the opposite side of the mesh.
    Returns the vertex ID of the mirrored vertex, or None if not found.
    """
    original_pos = get_vertex_position(mesh, vertex_id)
    mirror_x = -original_pos[0]  # Mirror across X-axis
    target_pos = [mirror_x, original_pos[1], original_pos[2]]
    
    vertex_count = get_vertex_count(mesh)
    
    # Search for closest vertex to the mirrored position
    closest_vertex = None
    closest_distance = float('inf')
    
    for i in range(vertex_count):
        if i == vertex_id:
            continue
            
        check_pos = get_vertex_position(mesh, i)
        distance = sum([(a - b) ** 2 for a, b in zip(check_pos, target_pos)]) ** 0.5
        
        if distance < tolerance and distance < closest_distance:
            closest_distance = distance
            closest_vertex = i
    
    return closest_vertex


def calculate_blend_weight(x_position, blend_zone_width=0.5, side='left'):
    """
    Calculate blend weight based on distance from center.
    
    Args:
        x_position (float): X coordinate of the vertex
        blend_zone_width (float): Width of the blend zone on each side of center
        side (str): 'left' or 'right' - which side gets the blendshape
    
    Returns:
        float: Blend weight between 0.0 (base mesh) and 1.0 (blendshape)
    """
    abs_x = abs(x_position)
    
    if side == 'left':
        # Left side gets blendshape
        if x_position > blend_zone_width:  # Far left - full blendshape
            return 1.0
        elif x_position < -blend_zone_width:  # Far right - full base
            return 0.0
        else:  # Blend zone
            # Linear falloff from center to edge
            return (x_position + blend_zone_width) / (2 * blend_zone_width)
    else:  # right side
        # Right side gets blendshape
        if x_position < -blend_zone_width:  # Far right - full blendshape
            return 1.0
        elif x_position > blend_zone_width:  # Far left - full base
            return 0.0
        else:  # Blend zone
            # Linear falloff from center to edge
            return (-x_position + blend_zone_width) / (2 * blend_zone_width)


def create_asymmetric_blendshapes(base_mesh, blendshape_source, blend_zone_width=0.5):
    """
    Create two asymmetric blendshapes from a base mesh and symmetric blendshape source.
    Uses smooth blending to transition between base and blendshape sides.
    
    Args:
        base_mesh (str): Name of the base mesh
        blendshape_source (str): Name of the blendshape source mesh
        blend_zone_width (float): Width of the blend zone for smooth transition
    
    Returns:
        tuple: (left_mesh_name, right_mesh_name)
    """
    
    # Validate input meshes exist
    if not cmds.objExists(base_mesh):
        cmds.error(f"Base mesh '{base_mesh}' does not exist.")
        return None, None
        
    if not cmds.objExists(blendshape_source):
        cmds.error(f"Blendshape source '{blendshape_source}' does not exist.")
        return None, None
    
    # Check if meshes have the same vertex count
    base_vertex_count = get_vertex_count(base_mesh)
    blend_vertex_count = get_vertex_count(blendshape_source)
    
    if base_vertex_count != blend_vertex_count:
        cmds.error(f"Vertex count mismatch: {base_mesh} has {base_vertex_count} vertices, "
                   f"{blendshape_source} has {blend_vertex_count} vertices.")
        return None, None
    
    # Create duplicates for left and right versions
    left_mesh = duplicate_mesh(blendshape_source, f"{blendshape_source}_Left")
    right_mesh = duplicate_mesh(blendshape_source, f"{blendshape_source}_Right")
    
    print(f"Created asymmetric meshes: {left_mesh}, {right_mesh}")
    
    # Process each vertex with smooth blending
    for vertex_id in range(base_vertex_count):
        # Get positions from both meshes
        base_pos = get_vertex_position(base_mesh, vertex_id)
        blend_pos = get_vertex_position(blendshape_source, vertex_id)
        
        # Get X position for blend calculations
        x_pos = base_pos[0]
        
        # Calculate blend weights for left and right versions
        left_blend_weight = calculate_blend_weight(x_pos, blend_zone_width, 'left')
        right_blend_weight = calculate_blend_weight(x_pos, blend_zone_width, 'right')
        
        # Create blended positions
        # Left mesh: blendshape on left side, base on right side
        left_blended_pos = [
            base_pos[0] + (blend_pos[0] - base_pos[0]) * left_blend_weight,
            base_pos[1] + (blend_pos[1] - base_pos[1]) * left_blend_weight,
            base_pos[2] + (blend_pos[2] - base_pos[2]) * left_blend_weight
        ]
        
        # Right mesh: blendshape on right side, base on left side
        right_blended_pos = [
            base_pos[0] + (blend_pos[0] - base_pos[0]) * right_blend_weight,
            base_pos[1] + (blend_pos[1] - base_pos[1]) * right_blend_weight,
            base_pos[2] + (blend_pos[2] - base_pos[2]) * right_blend_weight
        ]
        
        # Set the blended positions
        set_vertex_position(left_mesh, vertex_id, left_blended_pos)
        set_vertex_position(right_mesh, vertex_id, right_blended_pos)
    
    # Move the new meshes to avoid overlapping
    cmds.move(3, 0, 0, left_mesh, relative=True)
    cmds.move(-3, 0, 0, right_mesh, relative=True)
    
    print(f"Left asymmetric mesh: {left_mesh} (blendshape on left side)")
    print(f"Right asymmetric mesh: {right_mesh} (blendshape on right side)")
    
    return left_mesh, right_mesh


def make_asymmetric_from_selection(blend_zone_width=0.5):
    """
    Create asymmetric blendshapes from selected meshes.
    First selection should be base mesh, second should be blendshape source.
    
    Args:
        blend_zone_width (float): Width of the blend zone for smooth transition
    """
    selection = cmds.ls(selection=True, type='transform')
    
    if len(selection) != 2:
        cmds.error("Please select exactly 2 meshes: base mesh first, then blendshape source.")
        return
    
    base_mesh = selection[0]
    blendshape_source = selection[1]
    
    print(f"Creating asymmetric blendshapes...")
    print(f"Base mesh: {base_mesh}")
    print(f"Blendshape source: {blendshape_source}")
    print(f"Blend zone width: {blend_zone_width} units")
    
    left_mesh, right_mesh = create_asymmetric_blendshapes(base_mesh, blendshape_source, blend_zone_width)
    
    if left_mesh and right_mesh:
        # Select the new meshes
        cmds.select([left_mesh, right_mesh], replace=True)
        print("Asymmetric blendshapes created successfully!")
        print("The new meshes have been selected and positioned to avoid overlap.")
        print(f"Smooth blending applied with {blend_zone_width} unit transition zone.")


def make_asymmetric_with_custom_blend(blend_zone_width=0.5):
    """
    Wrapper function to easily create asymmetric blendshapes with custom blend zone.
    
    Args:
        blend_zone_width (float): Width of the blend zone (0.1 = sharp, 1.0 = very soft)
    """
    make_asymmetric_from_selection(blend_zone_width)
    

def create_asymmetric_ui():
    """Create a simple UI for the asymmetric blendshape tool."""
    
    window_name = "asymmetricBlendshapeWindow"
    
    # Delete existing window if it exists
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Create window
    window = cmds.window(window_name, title="Make Asymmetric Blendshapes", 
                        widthHeight=(420, 280), resizeToFitChildren=True)
    
    # Main layout
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=('both', 10))
    
    # Title
    cmds.text(label="Make Asymmetric Blendshapes", font="boldLabelFont", height=30)
    cmds.separator(height=10)
    
    # Instructions
    cmds.text(label="Instructions:", align="left", font="boldLabelFont")
    cmds.text(label="1. Select the base mesh (e.g., pSphere1)", align="left")
    cmds.text(label="2. Add the blendshape source to selection (e.g., pSphere2)", align="left")
    cmds.text(label="3. Adjust blend zone width if needed", align="left")
    cmds.text(label="4. Click 'Create Asymmetric Blendshapes'", align="left")
    cmds.separator(height=15)
    
    # Blend zone controls
    cmds.text(label="Blend Zone Settings:", align="left", font="boldLabelFont")
    blend_row = cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150), 
                              columnAlign2=('right', 'left'), columnAttach2=('right', 'left'))
    cmds.text(label="Blend Width:")
    blend_field = cmds.floatField(value=0.5, minValue=0.1, maxValue=2.0, precision=2,
                                 annotation="Width of smooth transition zone (0.1=sharp, 1.0=soft)")
    cmds.setParent('..')
    
    # Preset buttons
    cmds.separator(height=10)
    preset_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(130, 130, 130))
    cmds.button(label="Sharp (0.1)", width=125,
               command=lambda x: cmds.floatField(blend_field, edit=True, value=0.1))
    cmds.button(label="Medium (0.5)", width=125,
               command=lambda x: cmds.floatField(blend_field, edit=True, value=0.5))
    cmds.button(label="Soft (1.0)", width=125,
               command=lambda x: cmds.floatField(blend_field, edit=True, value=1.0))
    cmds.setParent('..')
    
    cmds.separator(height=15)
    
    # Main action button
    def create_with_blend_zone(*args):
        blend_width = cmds.floatField(blend_field, query=True, value=True)
        make_asymmetric_from_selection(blend_width)
    
    cmds.button(label="Create Asymmetric Blendshapes", height=40,
               backgroundColor=[0.4, 0.6, 0.4],
               command=create_with_blend_zone)
    
    cmds.separator(height=10)
    cmds.button(label="Close", height=30,
               backgroundColor=[0.5, 0.5, 0.5],
               command=lambda x: cmds.deleteUI(window_name))
    
    # Show window
    cmds.showWindow(window)


# Example usage functions
def example_with_spheres():
    """
    Example function that creates test spheres and demonstrates the tool.
    """
    # Create base sphere
    base_sphere = cmds.polySphere(name="pSphere1")[0]
    
    # Create blendshape source sphere with some deformation
    blend_sphere = cmds.polySphere(name="pSphere2")[0]
    
    # Add some deformation to the blendshape source
    cmds.select(f"{blend_sphere}.vtx[200:220]")  # Select some vertices
    cmds.move(0, 1, 0, relative=True)  # Move them up
    
    # Select both spheres
    cmds.select([base_sphere, blend_sphere], replace=True)
    
    print("Example spheres created. Run make_asymmetric_from_selection() to test.")


def create_blend_zone_visualization(mesh_name, blend_zone_width=0.5):
    """
    Create visual markers to show the blend zones on a mesh.
    
    Args:
        mesh_name (str): Name of the mesh to visualize blend zones on
        blend_zone_width (float): Width of the blend zone
    """
    if not cmds.objExists(mesh_name):
        cmds.error(f"Mesh '{mesh_name}' does not exist.")
        return
    
    # Create locators to mark the blend zone boundaries
    left_marker = cmds.spaceLocator(name=f"{mesh_name}_BlendZone_Left")[0]
    right_marker = cmds.spaceLocator(name=f"{mesh_name}_BlendZone_Right")[0]
    center_marker = cmds.spaceLocator(name=f"{mesh_name}_BlendZone_Center")[0]
    
    # Position the markers
    cmds.move(blend_zone_width, 0, 0, left_marker)
    cmds.move(-blend_zone_width, 0, 0, right_marker)
    cmds.move(0, 0, 0, center_marker)
    
    # Color the locators
    cmds.color(left_marker, rgb=(0, 1, 0))  # Green for left boundary
    cmds.color(right_marker, rgb=(1, 0, 0))  # Red for right boundary  
    cmds.color(center_marker, rgb=(1, 1, 0))  # Yellow for center
    
    # Group them
    blend_group = cmds.group([left_marker, right_marker, center_marker], 
                           name=f"{mesh_name}_BlendZone_Markers")
    
    print(f"Blend zone visualization created for {mesh_name}")
    print(f"Green marker: Left blend boundary (+{blend_zone_width})")
    print(f"Red marker: Right blend boundary (-{blend_zone_width})")
    print(f"Yellow marker: Center line (0)")
    
    return blend_group


if __name__ == "__main__":
    # Run the UI
    create_asymmetric_ui()