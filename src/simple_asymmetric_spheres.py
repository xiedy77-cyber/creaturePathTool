"""
Simple Asymmetric Blendshape Creator

This script works with any two selected meshes to create asymmetric versions.

To use:
1. Select your base mesh first
2. Add your blendshape source to the selection (Ctrl/Cmd + click)
3. Run: make_asymmetric_spheres() in Maya's script editor

The script will create:
- [BlendshapeName]_Left: Base mesh on right side, blendshape on left side  
- [BlendshapeName]_Right: Base mesh on left side, blendshape on right side
"""

import maya.cmds as cmds


def make_asymmetric_spheres():
    """
    Create asymmetric blendshapes from selected meshes.
    First selection should be base mesh, second should be blendshape source.
    """
    # Get selected meshes
    selection = cmds.ls(selection=True, type='transform')
    
    if len(selection) != 2:
        cmds.error("Please select exactly 2 meshes: base mesh first, then blendshape source.")
        return
    
    base_mesh = selection[0]
    blend_mesh = selection[1]
    
    print(f"Using selected meshes: {base_mesh} (base) and {blend_mesh} (blendshape)")
    
    print(f"Processing {base_mesh} and {blend_mesh}...")
    
    # Get vertex counts
    base_vtx_count = cmds.polyEvaluate(base_mesh, vertex=True)
    blend_vtx_count = cmds.polyEvaluate(blend_mesh, vertex=True)
    
    if base_vtx_count != blend_vtx_count:
        cmds.error(f"Vertex count mismatch: {base_mesh}({base_vtx_count}) vs {blend_mesh}({blend_vtx_count})")
        return
    
    print(f"Both meshes have {base_vtx_count} vertices. Creating asymmetric versions...")
    
    # Create duplicates
    left_mesh = cmds.duplicate(blend_mesh, name=f"{blend_mesh}_Left")[0]
    right_mesh = cmds.duplicate(blend_mesh, name=f"{blend_mesh}_Right")[0]
    
    # Process each vertex
    for vtx_id in range(base_vtx_count):
        # Get positions
        base_pos = cmds.pointPosition(f"{base_mesh}.vtx[{vtx_id}]", world=True)
        blend_pos = cmds.pointPosition(f"{blend_mesh}.vtx[{vtx_id}]", world=True)
        
        # Check which side the vertex is on (using X coordinate)
        x_pos = base_pos[0]
        
        # If vertex is on the left side (positive X in Maya's default orientation)
        if x_pos > 0.001:  # Left side
            # Left mesh keeps blendshape, right mesh gets base position
            cmds.move(base_pos[0], base_pos[1], base_pos[2], 
                     f"{right_mesh}.vtx[{vtx_id}]", worldSpace=True, absolute=True)
                     
        elif x_pos < -0.001:  # Right side  
            # Right mesh keeps blendshape, left mesh gets base position
            cmds.move(base_pos[0], base_pos[1], base_pos[2], 
                     f"{left_mesh}.vtx[{vtx_id}]", worldSpace=True, absolute=True)
        
        # Center vertices (between -0.001 and 0.001) keep blendshape on both sides
    
    # Position the new meshes to avoid overlap
    cmds.move(4, 0, 0, left_mesh, relative=True)
    cmds.move(-4, 0, 0, right_mesh, relative=True)
    
    # Select the new meshes
    cmds.select([left_mesh, right_mesh], replace=True)
    
    print(f"Success! Created:")
    print(f"  {left_mesh} - Base mesh on right side, blendshape on left side")
    print(f"  {right_mesh} - Base mesh on left side, blendshape on right side")
    print("The new meshes are now selected and positioned to avoid overlap.")


def create_simple_asymmetric_ui():
    """Create a simple UI for the asymmetric blendshape tool."""
    
    window_name = "simpleAsymmetricWindow"
    
    # Delete existing window if it exists
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Create window
    window = cmds.window(window_name, title="Simple Asymmetric Blendshapes", 
                        widthHeight=(380, 200), resizeToFitChildren=True)
    
    # Main layout
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=('both', 10))
    
    # Title
    cmds.text(label="Simple Asymmetric Blendshapes", font="boldLabelFont", height=30)
    cmds.separator(height=10)
    
    # Instructions
    cmds.text(label="Instructions:", align="left", font="boldLabelFont")
    cmds.text(label="1. Select the base mesh", align="left")
    cmds.text(label="2. Add the blendshape source to selection (Ctrl/Cmd + click)", align="left")
    cmds.text(label="3. Click 'Create Asymmetric Blendshapes'", align="left")
    cmds.separator(height=15)
    
    # Main action button
    cmds.button(label="Create Asymmetric Blendshapes", height=40,
               backgroundColor=[0.4, 0.6, 0.4],
               command=lambda x: make_asymmetric_spheres())
    
    cmds.separator(height=10)
    cmds.button(label="Close", height=30,
               backgroundColor=[0.5, 0.5, 0.5],
               command=lambda x: cmds.deleteUI(window_name))
    
    # Show window
    cmds.showWindow(window)


# Run the function
if __name__ == "__main__":
    create_simple_asymmetric_ui()