"""
Curve Builder Tool

Creates an EP curve with NURBS controls for deformation.
"""

import maya.cmds as cmds

def create_ep_curve_with_controls(num_points):
    """
    Creates an EP curve (linear NURBS) with the specified number of points,
    each with a NURBS curve control that can deform the curve.
    """
    if num_points < 2:
        cmds.error("Number of points must be at least 2.")
        return

    # Create points for a straight line along Z
    spacing = 1.0
    points = [(0, 0, i * spacing) for i in range(num_points)]

    # Create the EP curve (degree 3 for smoother curves)
    curve = cmds.curve(name='ep_curve', p=points, degree=3)

    # Create a root group to contain all controls
    root_group = cmds.group(empty=True, name='curve_controls_grp')

    # Create NURBS controls for each point
    for i in range(num_points):
        # Create a small circle as control, rotated 90 in X (normal Z-up)
        control = cmds.circle(name=f'curve_control_{i}', radius=0.1, normal=(0,0,1))[0]
        cmds.xform(control, translation=points[i])
        # Freeze transformations to zero out rotation while keeping translate
        cmds.makeIdentity(control, apply=True, rotate=True, scale=True)

        # Parent the control under the root group
        cmds.parent(control, root_group)

        # Add expressions to drive cv positions
        cmds.expression(name=f'cv_{i}_x', string=f'{curve}.controlPoints[{i}].xValue = {control}.translateX')
        cmds.expression(name=f'cv_{i}_y', string=f'{curve}.controlPoints[{i}].yValue = {control}.translateY')
        cmds.expression(name=f'cv_{i}_z', string=f'{curve}.controlPoints[{i}].zValue = {control}.translateZ')

    cmds.select(curve)
    cmds.warning(f"EP Curve created with {num_points} NURBS controls.")

def create_ui():
    """
    Creates the UI for the Curve Builder tool.
    """
    if cmds.window("curveBuilderWindow", exists=True):
        cmds.deleteUI("curveBuilderWindow")

    window = cmds.window("curveBuilderWindow", title="Curve Builder", widthHeight=(300, 200))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Number of Points:")
    num_points_field = cmds.intField(value=5)

    cmds.button(label="Create EP Curve with Controls", command=lambda x: create_ep_curve_with_controls(
        cmds.intField(num_points_field, query=True, value=True)
    ))

    cmds.showWindow(window)

# To run the tool
if __name__ == "__main__":
    create_ui()