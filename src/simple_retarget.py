"""
Simple Motion Retargeting Script

Takes the forward motion of a selected object and retargets it to follow a selected curve,
preserving translational and rotational offsets.
"""

import maya.cmds as cmds
import math

def retarget_motion_to_curve():
    """
    Retargets the motion of the selected object to the selected curve.
    Assumes first selection is the object, second is the curve.
    """
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        cmds.error("Select exactly one object and one curve.")
        return

    obj = selection[0]
    curve = selection[1]

    if not cmds.objExists(obj):
        cmds.error("Object does not exist.")
        return
    if not cmds.objExists(curve):
        cmds.error("Curve does not exist.")
        return

    # Get animation range
    start_frame = int(cmds.playbackOptions(query=True, minTime=True))
    end_frame = int(cmds.playbackOptions(query=True, maxTime=True))

    # Sample object's position and orientation over time
    positions = []
    rotations = []
    forward_distances = [0.0]

    for frame in range(start_frame, end_frame + 1):
        cmds.currentTime(frame)
        pos = cmds.xform(obj, query=True, translation=True, worldSpace=True)
        rot = cmds.xform(obj, query=True, rotation=True, worldSpace=True)
        positions.append(pos)
        rotations.append(rot)

        if frame > start_frame:
            # Compute forward motion (assuming local Z is forward)
            # Get the object's forward vector in world space
            forward_vec = get_forward_vector(obj)
            # Displacement in forward direction
            prev_pos = positions[-2]
            disp = [pos[0] - prev_pos[0], pos[1] - prev_pos[1], pos[2] - prev_pos[2]]
            forward_dist = dot_product(disp, forward_vec)
            forward_distances.append(forward_distances[-1] + forward_dist)

    total_forward = forward_distances[-1]
    if total_forward == 0:
        cmds.warning("No forward motion detected.")
        return

    # Sample the curve
    num_samples = 1000
    curve_positions = []
    curve_tangents = []
    curve_distances = [0.0]

    for i in range(num_samples + 1):
        u = i / num_samples
        pos = cmds.pointOnCurve(curve, parameter=u, position=True)
        tangent = cmds.pointOnCurve(curve, parameter=u, tangent=True)
        curve_positions.append(pos)
        curve_tangents.append(tangent)
        if i > 0:
            dx = pos[0] - curve_positions[-2][0]
            dy = pos[1] - curve_positions[-2][1]
            dz = pos[2] - curve_positions[-2][2]
            dist = math.sqrt(dx**2 + dy**2 + dz**2)
            curve_distances.append(curve_distances[-1] + dist)

    curve_length = curve_distances[-1]

    # Scale
    scale = curve_length / total_forward

    # Create animation layer
    layer_name = "Simple_Retarget"
    if cmds.animLayer(layer_name, query=True, exists=True):
        cmds.animLayer(layer_name, edit=True, remove=True)
    cmds.animLayer(layer_name)
    cmds.animLayer(layer_name, edit=True, preferred=True)

    # For each frame, set position and rotation
    for idx, frame in enumerate(range(start_frame, end_frame + 1)):
        target_dist = forward_distances[idx] * scale

        # Find u on curve
        u = 0.0
        for i in range(1, len(curve_distances)):
            if curve_distances[i] >= target_dist:
                frac = (target_dist - curve_distances[i-1]) / (curve_distances[i] - curve_distances[i-1]) if curve_distances[i] != curve_distances[i-1] else 0
                u = (i - 1 + frac) / num_samples
                break
        else:
            u = 1.0

        # Position on curve
        curve_pos = cmds.pointOnCurve(curve, parameter=u, position=True)
        curve_tangent = cmds.pointOnCurve(curve, parameter=u, tangent=True)

        # Compute rotation to align with curve tangent
        yaw = math.atan2(curve_tangent[0], curve_tangent[2]) * 180 / math.pi

        # But to preserve offsets, perhaps apply the original local rotation relative to the curve orientation
        # For simplicity, set the world rotation to match curve, but that might not preserve offsets.

        # The user wants "with any translational and rotational offsets"
        # So, the position should be offset from the curve, and rotation offset from the curve direction.

        # But how to determine the offsets?

        # Perhaps the offsets are the initial position and rotation relative to the curve.

        # But since the curve is separate, perhaps assume the object starts at the curve start, and offsets are the differences.

        # For translational offset: the perpendicular distance or something.

        # This is getting complex.

        # Perhaps the "offset" means the local motion is offset along the curve.

        # But the user says "puts that with an offset onto a curve"

        # Perhaps the forward motion is placed along the curve with some offset.

        # To simplify, let's assume no additional offset, just map the forward distance to curve distance.

        # For rotation, set to follow the curve.

        # But to include offsets, perhaps keep the original rotation relative.

        # Let's compute the rotation as curve rotation + original local rotation.

        # First, the curve rotation (yaw)

        # Then, the original rotation at that frame, but adjusted.

        # Perhaps it's easier to think of the object having local animation, and the root follows the curve.

        # So, the position is curve_pos + local_translate transformed by the curve rotation.

        # But the local_translate is the original position relative to start.

        # Yes, that could be.

        # At each frame, the local position relative to start, rotated by the curve orientation, added to curve position.

        # For rotation, the local rotation + curve rotation.

        # Yes, that preserves the offsets.

        # So, let's do that.

        # First, get the initial position and rotation at start_frame.

        cmds.currentTime(start_frame)
        initial_pos = cmds.xform(obj, query=True, translation=True, worldSpace=True)
        initial_rot = cmds.xform(obj, query=True, rotation=True, worldSpace=True)

        # Then, for each frame, compute the local translate and rotate relative to initial.

        # But since the object may have hierarchy, but assume it's the object.

        # For simplicity, assume the object is the root, and its translate and rotate are the local.

        # So, at each frame, local_translate = current_translate - initial_translate (but in world space, it's not local.

        # To get local motion, need to consider the rotation.

        # This is tricky.

        # Perhaps assume the object has no parent, so world translate is local.

        # For rotation, local rotate is world rotate if no parent.

        # So, the offsets are the current translate and rotate minus initial.

        # Then, apply them relative to the curve.

        # So, for position: curve_pos + (current_translate - initial_translate) rotated by curve_rotation

        # For rotation: curve_rotation + (current_rotate - initial_rotate)

        # Yes, that could work.

        # Let's implement that.

        # First, compute curve_rotation as quaternion or euler.

        # For simplicity, assume only yaw for curve.

        curve_rot = [0, yaw, 0]

        # Then, local_translate = [positions[idx][0] - initial_pos[0], positions[idx][1] - initial_pos[1], positions[idx][2] - initial_pos[2]]

        local_translate = [positions[idx][0] - initial_pos[0], positions[idx][1] - initial_pos[1], positions[idx][2] - initial_pos[2]]

        # Rotate local_translate by curve_rot (only yaw)

        rotated_translate = rotate_vector_yaw(local_translate, yaw)

        new_pos = [curve_pos[0] + rotated_translate[0], curve_pos[1] + rotated_translate[1], curve_pos[2] + rotated_translate[2]]

        # For rotation

        local_rot = [rotations[idx][0] - initial_rot[0], rotations[idx][1] - initial_rot[1], rotations[idx][2] - initial_rot[2]]

        new_rot = [curve_rot[0] + local_rot[0], curve_rot[1] + local_rot[1], curve_rot[2] + local_rot[2]]

        # Set keyframes

        cmds.currentTime(frame)
        cmds.setKeyframe(obj + ".translateX", value=new_pos[0], time=frame)
        cmds.setKeyframe(obj + ".translateY", value=new_pos[1], time=frame)
        cmds.setKeyframe(obj + ".translateZ", value=new_pos[2], time=frame)
        cmds.setKeyframe(obj + ".rotateX", value=new_rot[0], time=frame)
        cmds.setKeyframe(obj + ".rotateY", value=new_rot[1], time=frame)
        cmds.setKeyframe(obj + ".rotateZ", value=new_rot[2], time=frame)

    cmds.animLayer(layer_name, edit=True, preferred=False)
    cmds.select(obj)

def get_forward_vector(obj):
    """
    Get the forward vector (local Z) in world space.
    """
    # Get the world matrix
    wm = cmds.xform(obj, query=True, worldSpace=True, matrix=True)
    # Local Z is [8,9,10] in the matrix (row 2)
    forward = [wm[8], wm[9], wm[10]]
    return forward

def dot_product(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def rotate_vector_yaw(vec, yaw_deg):
    """
    Rotate vector around Y axis by yaw degrees.
    """
    yaw_rad = math.radians(yaw_deg)
    cos_y = math.cos(yaw_rad)
    sin_y = math.sin(yaw_rad)
    x = vec[0] * cos_y - vec[2] * sin_y
    z = vec[0] * sin_y + vec[2] * cos_y
    return [x, vec[1], z]

# Run the script
if __name__ == "__main__":
    retarget_motion_to_curve()