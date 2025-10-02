def disconnect_motionpath_uvalue(path_locator):
    """
    Disconnects and deletes any animCurve node connected to the motionPath node's uValue attribute for the given path_locator.
    """
    path_anim_node = cmds.listConnections(f"{path_locator}.uValue", type="motionPath")
    if not path_anim_node:
        cmds.warning("No motionPath node found for the pathLocator.")
        return
    path_anim_node = path_anim_node[0]
    # Find the input connection to uValue (should be an animCurve)
    connections = cmds.listConnections(f"{path_anim_node}.uValue", source=True, destination=False, plugs=True)
    if connections:
        for src in connections:
            cmds.disconnectAttr(src, f"{path_anim_node}.uValue")
            node_name = src.split('.')[0]
            if cmds.nodeType(node_name).startswith('animCurve'):
                cmds.delete(node_name)
        cmds.warning(f"Disconnected and deleted animCurve(s) from {path_anim_node}.uValue.")
    else:
        cmds.warning(f"No input connection to {path_anim_node}.uValue to disconnect or delete.")
"""
Curve Builder Tool

Creates an EP curve with NURBS controls for deformation.
"""

import maya.cmds as cmds

def create_ep_curve_with_controls(num_points):
    """
    Creates an EP curve (linear NURBS) with the specified number of points,
    each with a NURBS curve control that can deform the curve.
    Adds a master control, creates a locator, and attaches it to the path animation.
    Also creates a child locator under the main locator.
    """
    if num_points < 2:
        cmds.error("Number of points must be at least 2.")
        return

    # Create points for a straight line along Z
    spacing = 1.0
    points = [(0, 0, i * spacing) for i in range(num_points)]

    # Create the EP curve (degree 3 for smoother curves)
    curve = cmds.curve(name='creaturePath', p=points, degree=3)  # Renamed to 'creaturePath'

    if not cmds.objExists(curve):
        cmds.error("Failed to create the EP curve. Please try again.")
        return

    # Make the curve non-selectable
    cmds.setAttr(f'{curve}.overrideEnabled', 1)
    cmds.setAttr(f'{curve}.overrideDisplayType', 2)  # 2 = Reference, making it non-selectable

    # Create a top-level group
    top_group = cmds.group(empty=True, name='creaturePathTool')

    # Create a root group to contain all controls
    root_group = cmds.group(empty=True, name='curve_controls_grp', parent=top_group)

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

    # Create a master control
    master_control = cmds.circle(name='master_control', radius=0.5, normal=(0,1,0))[0]  # Reduced size by 50%
    cmds.xform(master_control, translation=(0, 0, 0))
    cmds.makeIdentity(master_control, apply=True, rotate=True, scale=True)

    # Parent the curve and root group under the master control
    cmds.parent(curve, root_group, master_control)

    # Parent the master control under the top group
    cmds.parent(master_control, top_group)

    # Create a locator and attach it to the path animation
    locator = cmds.spaceLocator(name='pathLocator')[0]
    cmds.xform(locator, translation=(0, 0, 0))
    cmds.pathAnimation(locator, c=curve, fractionMode=True, follow=True, followAxis="x", upAxis="y",
                       worldUpType="vector", worldUpVector=(0, 1, 0), inverseUp=False, inverseFront=False, bank=False,
                       startTimeU=cmds.playbackOptions(query=True, minTime=True),
                       endTimeU=cmds.playbackOptions(query=True, maxTime=True))

    # Create a child locator under the main locator
    child_locator = cmds.spaceLocator(name='childLocator')[0]
    cmds.parent(child_locator, locator)
    cmds.xform(child_locator, translation=(0, 1, 0))  # Offset the child locator slightly

    cmds.select(curve)
    cmds.warning(f"EP Curve created with {num_points} NURBS controls, a master control, a locator with a child locator attached to the path animation, and organized under 'creaturePathTool'.")

def connect_object_to_curve(object_name):
    """
    Connects the specified object to the EP curve by:
    - Parent constraining the childLocator to the object without offset.
    - Baking the childLocator.
    - Creating a NURBS control parented under the childLocator.
    - Constraining the object to the NURBS control without offset.
    - Setting the NURBS control's transforms to 0 to match the childLocator's worldspace transforms.
    """
    if not object_name or not cmds.objExists(object_name):
        cmds.error("Please specify a valid object to connect.")
        return

    # Find the child locator
    child_locator = cmds.ls("childLocator", type="transform")
    if not child_locator:
        cmds.error("Child locator not found. Please create one first.")
        return

    child_locator = child_locator[0]  # Use the first found child locator

    # Parent constrain the childLocator to the object without offset
    cmds.parentConstraint(object_name, child_locator, maintainOffset=False)

    # Bake the childLocator
    cmds.bakeResults(child_locator, simulation=True, time=(cmds.playbackOptions(query=True, minTime=True),
                                                          cmds.playbackOptions(query=True, maxTime=True)))

    # Create a NURBS control parented under the childLocator
    nurbs_control = cmds.circle(name=f'{object_name}_control', radius=1.0, normal=(0, 1, 0))[0]
    cmds.parent(nurbs_control, child_locator)

    # Constrain the object to the NURBS control without offset
    cmds.parentConstraint(nurbs_control, object_name, maintainOffset=False)

    # Set the NURBS control's transforms to 0 to match the childLocator's worldspace transforms
    cmds.setAttr(f'{nurbs_control}.translate', 0, 0, 0)
    cmds.setAttr(f'{nurbs_control}.rotate', 0, 0, 0)
    cmds.setAttr(f'{nurbs_control}.scale', 1, 1, 1)

    cmds.warning(f"Connected {object_name} to the EP curve with a NURBS control under the child locator.")

def connect_secondary_controls(secondary_controls):
    """
    Connects each secondary control to the EP curve.
    """
    if secondary_controls:
        for control in secondary_controls.split(", "):
            if cmds.objExists(control):
                connect_object_to_curve(control)
            else:
                cmds.warning(f"Secondary control '{control}' does not exist and was skipped.")

def connect_to_ep_curve(controls):
    """
    Connects all specified controls to the EP curve.
    For each control:
    - Create a locator named after the control.
    - Parent the locator under the main pathLocator.
    - Constrain the locator to the control.
    - Bake the locator's animation.
    - Create a NURBS control named after the control.
    - Match the NURBS control's position and rotation to the locator.
    - Constrain the NURBS control to the locator.
    - Constrain the control to the NURBS control.
    """
    if controls:
        path_locator = cmds.ls("pathLocator", type="transform")
        if not path_locator:
            cmds.error("Main pathLocator not found. Please create the EP curve first.")
            return

        path_locator = path_locator[0]  # Use the first found pathLocator

        for control in controls.split(", "):
            if cmds.objExists(control):
                # Create a locator named after the control
                locator = cmds.spaceLocator(name=f"{control}_locator")[0]

                # Parent the locator under the main pathLocator
                cmds.parent(locator, path_locator)

                # Constrain the locator to the control
                cmds.parentConstraint(control, locator, maintainOffset=False)

                # Bake the locator's animation
                cmds.bakeResults(locator, simulation=True, time=(cmds.playbackOptions(query=True, minTime=True),
                                                                cmds.playbackOptions(query=True, maxTime=True)))

                # Create a NURBS control named after the control
                nurbs_control = cmds.circle(name=f"{control}_control", radius=1.0, normal=(0, 1, 0))[0]

                # Match the NURBS control's position and rotation to the locator
                locator_position = cmds.xform(locator, query=True, worldSpace=True, translation=True)
                locator_rotation = cmds.xform(locator, query=True, worldSpace=True, rotation=True)
                cmds.xform(nurbs_control, worldSpace=True, translation=locator_position)
                cmds.xform(nurbs_control, worldSpace=True, rotation=locator_rotation)

                # Freeze transformations on the NURBS control
                cmds.makeIdentity(nurbs_control, apply=True, translate=True, rotate=True, scale=True)

                # Constrain the NURBS control to the locator
                cmds.parentConstraint(locator, nurbs_control, maintainOffset=False)

                # Constrain the control to the NURBS control
                cmds.parentConstraint(nurbs_control, control, maintainOffset=False)

                cmds.warning(f"Connected {control} to the EP curve with a locator and NURBS control.")
            else:
                cmds.warning(f"Control '{control}' does not exist and was skipped.")

def match_path_locator_to_object(curve, path_locator, object_name):
    """
    Matches the distance the pathLocator travels along the curve to the Z-distance traveled by the object.
    Deletes the default animCurve on uValue and keys uValue based on the object's Z movement.
    """
    if not cmds.objExists(curve) or not cmds.objExists(path_locator) or not cmds.objExists(object_name):
        cmds.error("Curve, pathLocator, or object does not exist.")
        return

    # Get the motionPath node
    path_anim_node = cmds.listConnections(f"{path_locator}.uValue", type="motionPath")
    if not path_anim_node:
        cmds.error("No motionPath node found for the pathLocator.")
        return
    path_anim_node = path_anim_node[0]

    # Remove the default animation curve on uValue
    anim_curve = cmds.listConnections(f"{path_anim_node}.uValue", type="animCurve")
    if anim_curve:
        cmds.delete(anim_curve)

    # Get curve length and Z positions
    curve_length = cmds.arclen(curve)
    start_frame = int(cmds.playbackOptions(query=True, minTime=True))
    end_frame = int(cmds.playbackOptions(query=True, maxTime=True))
    cmds.currentTime(start_frame)
    start_z = cmds.xform(object_name, query=True, worldSpace=True, translation=True)[2]
    cmds.currentTime(end_frame)
    end_z = cmds.xform(object_name, query=True, worldSpace=True, translation=True)[2]
    z_distance = end_z - start_z

    if z_distance == 0:
        cmds.error("The object does not move in the Z-axis.")
        return

    # Set uValue for each frame
    for frame in range(start_frame, end_frame + 1):
        cmds.currentTime(frame)
        current_z = cmds.xform(object_name, query=True, worldSpace=True, translation=True)[2]
        traveled = current_z - start_z
        proportion = traveled / z_distance
        u_value = max(0.0, min(1.0, proportion))  # Clamp between 0 and 1
        cmds.setAttr(f"{path_anim_node}.uValue", u_value)
        cmds.setKeyframe(f"{path_anim_node}.uValue", time=frame, value=u_value)

    cmds.warning("PathLocator uValue retargeted to match object's Z movement.")

def create_ui():
    """
    Creates the UI for the Curve Builder tool.
    Adds functionality to add objects to fields and connect them to the EP curve.
    """
    if cmds.window("curveBuilderWindow", exists=True):
        cmds.deleteUI("curveBuilderWindow")

    window = cmds.window("curveBuilderWindow", title="Curve Builder", widthHeight=(300, 300))
    cmds.columnLayout(adjustableColumn=True)


    cmds.text(label="Number of Points:")
    num_points_field = cmds.intField(value=5)
    cmds.separator(height=10, style="in")

    # Secondary Controls Field
    cmds.text(label="Secondary Controls:")
    secondary_controls_field = cmds.textField()

    cmds.button(label="Add Selected Objects to Secondary Controls", command=lambda x: cmds.textField(secondary_controls_field, edit=True, text=", ".join(cmds.ls(selection=True)) if cmds.ls(selection=True) else ""))

    cmds.separator(height=10, style="in")

    def create_curve_and_connect_controls(*_):
        num_points = cmds.intField(num_points_field, query=True, value=True)
        create_ep_curve_with_controls(num_points)
        connect_to_ep_curve(cmds.textField(secondary_controls_field, query=True, text=True))

    cmds.button(label="Connect Controls to EP Curve", command=create_curve_and_connect_controls)

    cmds.showWindow(window)

# To run the tool
if __name__ == "__main__":
    create_ui()