import maya.cmds as cmds

class InfinityToolUI:
    def __init__(self):
        self.window = "infinityToolWin"
        self.setup_ui()

    def setup_ui(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)
        
        self.window = cmds.window(self.window, title="Animation Curve Infinity Tool", widthHeight=(400, 300))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnOffset=('both', 10))
        
        # Header
        cmds.text(label="Animation Curve Infinity Tool", font="boldLabelFont", height=30)
        cmds.separator(height=10)
        
        # Instructions
        cmds.text(label="Select objects or animation curves, then choose infinity type to apply:", 
                 align='left', wordWrap=True)
        cmds.separator(height=5)
        
        # Infinity type selection
        cmds.frameLayout(label="Infinity Type", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.rowLayout(numberOfColumns=2, columnWidth2=[80, 200])
        cmds.text(label="Type: ")
        self.infinity_type = cmds.optionMenu()
        cmds.menuItem(label='Constant')
        cmds.menuItem(label='Linear')
        cmds.menuItem(label='Cycle')
        cmds.menuItem(label='Cycle Relative')
        cmds.menuItem(label='Oscillate')
        cmds.optionMenu(self.infinity_type, edit=True, select=3)  # Default to Cycle
        cmds.setParent('..')
        
        cmds.setParent('..')  # columnLayout
        cmds.setParent('..')  # frameLayout
        
        # Options
        cmds.frameLayout(label="Options", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        self.apply_pre_chk = cmds.checkBox(label="Apply to Pre-Infinity", value=True)
        self.apply_post_chk = cmds.checkBox(label="Apply to Post-Infinity", value=True)
        self.ensure_keys_chk = cmds.checkBox(label="Ensure 2+ keys for cycling", value=True)
        self.verbose_chk = cmds.checkBox(label="Verbose output", value=False)
        
        cmds.setParent('..')  # columnLayout
        cmds.setParent('..')  # frameLayout
        
        cmds.separator(height=15)
        
        # Action buttons - Make them more prominent
        cmds.text(label="Actions:", font="boldLabelFont")
        cmds.separator(height=5)
        
        cmds.rowLayout(numberOfColumns=1, adjustableColumn=1)
        cmds.button(label="APPLY INFINITY TO SELECTION", command=self.apply_infinity_to_selection, 
                   backgroundColor=(0.4, 0.7, 0.4), height=35)
        cmds.setParent('..')
        
        cmds.separator(height=5)
        
        cmds.rowLayout(numberOfColumns=1, adjustableColumn=1)
        cmds.button(label="Generate Script Only", command=self.generate_script, 
                   backgroundColor=(0.7, 0.7, 0.4), height=25)
        cmds.setParent('..')
        
        cmds.separator(height=15)
        
        # Status and info
        cmds.frameLayout(label="Current Selection Info", collapsable=True, collapse=False, 
                        marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.button(label="Refresh Selection Info", command=self.refresh_selection_info)
        self.info_text = cmds.scrollField(wordWrap=True, height=80, editable=False,
                                         backgroundColor=(0.9, 0.9, 0.9))
        
        cmds.setParent('..')  # columnLayout
        cmds.setParent('..')  # frameLayout
        
        cmds.showWindow(self.window)
        
        # Initial refresh
        self.refresh_selection_info()

    def get_infinity_value(self):
        """Get the integer value for the selected infinity type."""
        selection = cmds.optionMenu(self.infinity_type, query=True, select=True)
        infinity_map = {
            1: 0,  # Constant
            2: 1,  # Linear
            3: 2,  # Cycle
            4: 3,  # Cycle Relative
            5: 4   # Oscillate
        }
        return infinity_map.get(selection, 2)  # Default to Cycle

    def get_infinity_name(self):
        """Get the string name for the selected infinity type."""
        selection = cmds.optionMenu(self.infinity_type, query=True, select=True)
        infinity_names = {
            1: 'constant',
            2: 'linear', 
            3: 'cycle',
            4: 'cycleRelative',
            5: 'oscillate'
        }
        return infinity_names.get(selection, 'cycle')

    def collect_anim_curves_from_nodes(self, nodes):
        """Collect all animation curves connected to the given nodes."""
        curves = []
        for node in nodes:
            if not cmds.objExists(node):
                continue
            
            # Method 1: keyframe query
            try:
                kcurves = cmds.keyframe(node, query=True, name=True) or []
                for c in kcurves:
                    if c not in curves:
                        curves.append(c)
            except Exception:
                pass
            
            # Method 2: listConnections by animCurve
            try:
                conns = cmds.listConnections(node, source=True, destination=False) or []
                for c in conns:
                    try:
                        if cmds.objExists(c) and cmds.nodeType(c).startswith('animCurve') and c not in curves:
                            curves.append(c)
                    except Exception:
                        continue
            except Exception:
                pass
        
        return curves

    def ensure_two_keys(self, curve):
        """Ensure the given curve has at least two keys."""
        try:
            key_times = cmds.keyframe(curve, query=True, timeChange=True) or []
            if len(key_times) < 2:
                value = cmds.keyframe(curve, query=True, valueChange=True)[0]
                playback_start = cmds.playbackOptions(query=True, min=True)
                playback_end = cmds.playbackOptions(query=True, max=True)
                cmds.setKeyframe(curve, time=playback_start, value=value)
                cmds.setKeyframe(curve, time=playback_end, value=value)
                return True
        except Exception:
            pass
        return False

    def apply_infinity_advanced(self, curves, infinity_value, infinity_name, apply_pre, apply_post, verbose=False):
        """Apply infinity settings with multiple fallback strategies."""
        if not curves:
            return [], []
        
        # Normalize to list
        if isinstance(curves, str):
            curves = [curves]
        
        updated = []
        failed = []
        
        for curve in curves:
            if not cmds.objExists(curve):
                if verbose:
                    print(f"INFINITY: Curve missing {curve}")
                failed.append(curve)
                continue
            
            # Get curve info for debugging
            try:
                node_type = cmds.nodeType(curve)
                key_count = cmds.keyframe(curve, query=True, keyframeCount=True) or 0
                pre_val_before = cmds.getAttr(curve + '.preInfinity')
                post_val_before = cmds.getAttr(curve + '.postInfinity')
                
                print(f"INFINITY: Processing {curve} (type={node_type}, keys={key_count}, pre={pre_val_before}, post={post_val_before})")
            except Exception as e:
                print(f"INFINITY: Could not get curve info for {curve}: {e}")
            
            success = False
            
            # Strategy 1: Direct setAttr with unlock
            try:
                # Check and unlock attributes if needed
                pre_locked = False
                post_locked = False
                
                if apply_pre:
                    try:
                        pre_locked = cmds.getAttr(f'{curve}.preInfinity', lock=True)
                        if pre_locked:
                            cmds.setAttr(f'{curve}.preInfinity', lock=False)
                    except Exception:
                        pass
                    cmds.setAttr(f'{curve}.preInfinity', infinity_value)
                
                if apply_post:
                    try:
                        post_locked = cmds.getAttr(f'{curve}.postInfinity', lock=True)
                        if post_locked:
                            cmds.setAttr(f'{curve}.postInfinity', lock=False)
                    except Exception:
                        pass
                    cmds.setAttr(f'{curve}.postInfinity', infinity_value)
                
                # Verify
                pre_ok = True
                post_ok = True
                if apply_pre:
                    pre_val = cmds.getAttr(curve + '.preInfinity')
                    pre_ok = (pre_val == infinity_value)
                if apply_post:
                    post_val = cmds.getAttr(curve + '.postInfinity')
                    post_ok = (post_val == infinity_value)
                
                # Relock if needed
                if apply_pre and pre_locked:
                    cmds.setAttr(f'{curve}.preInfinity', lock=True)
                if apply_post and post_locked:
                    cmds.setAttr(f'{curve}.postInfinity', lock=True)
                
                if pre_ok and post_ok:
                    print(f"INFINITY: Direct setAttr success {curve} -> pre={pre_val if apply_pre else 'unchanged'}, post={post_val if apply_post else 'unchanged'}")
                    updated.append(curve)
                    success = True
                    
            except Exception as e:
                print(f"INFINITY: Direct setAttr failed {curve}: {e}")
            
            # Strategy 2: setInfinity command
            if not success:
                try:
                    kwargs = {}
                    if apply_pre:
                        kwargs['preInfinite'] = infinity_name
                    if apply_post:
                        kwargs['postInfinite'] = infinity_name
                    
                    if kwargs:
                        cmds.setInfinity(curve, **kwargs)
                        
                        # Verify it worked
                        pre_ok = True
                        post_ok = True
                        if apply_pre:
                            pre_val = cmds.getAttr(curve + '.preInfinity')
                            pre_ok = (pre_val == infinity_value)
                        if apply_post:
                            post_val = cmds.getAttr(curve + '.postInfinity')
                            post_ok = (post_val == infinity_value)
                        
                        if pre_ok and post_ok:
                            print(f"INFINITY: setInfinity success {curve}")
                            updated.append(curve)
                            success = True
                            
                except Exception as e:
                    print(f"INFINITY: setInfinity failed {curve}: {e}")
            
            # Strategy 3: MEL command
            if not success:
                try:
                    import maya.mel as mel
                    mel.eval(f"select -r {curve};")
                    
                    if apply_pre:
                        mel.eval(f"setInfinity -pri {infinity_name};")
                    if apply_post:
                        mel.eval(f"setInfinity -poi {infinity_name};")
                    
                    # Verify
                    pre_ok = True
                    post_ok = True
                    if apply_pre:
                        pre_val = cmds.getAttr(curve + '.preInfinity')
                        pre_ok = (pre_val == infinity_value)
                    if apply_post:
                        post_val = cmds.getAttr(curve + '.postInfinity')
                        post_ok = (post_val == infinity_value)
                    
                    if pre_ok and post_ok:
                        print(f"INFINITY: MEL success {curve}")
                        updated.append(curve)
                        success = True
                        
                except Exception as e:
                    print(f"INFINITY: MEL failed {curve}: {e}")
            
            # Strategy 4: Force with numeric MEL values
            if not success:
                try:
                    import maya.mel as mel
                    mel.eval(f"select -r {curve};")
                    
                    if apply_pre:
                        mel.eval(f"setInfinity -pri {infinity_value};")
                    if apply_post:
                        mel.eval(f"setInfinity -poi {infinity_value};")
                    
                    # Verify
                    pre_ok = True
                    post_ok = True
                    if apply_pre:
                        pre_val = cmds.getAttr(curve + '.preInfinity')
                        pre_ok = (pre_val == infinity_value)
                    if apply_post:
                        post_val = cmds.getAttr(curve + '.postInfinity')
                        post_ok = (post_val == infinity_value)
                    
                    if pre_ok and post_ok:
                        print(f"INFINITY: Numeric MEL success {curve}")
                        updated.append(curve)
                        success = True
                        
                except Exception as e:
                    print(f"INFINITY: Numeric MEL failed {curve}: {e}")
            
            if not success:
                print(f"INFINITY: All strategies failed for {curve}")
                failed.append(curve)
        
        return updated, failed

    def apply_infinity_to_selection(self, *_):
        """Apply infinity settings to selected objects."""
        sel = cmds.ls(selection=True) or []
        if not sel:
            cmds.warning("No objects selected.")
            return
        
        # Get settings
        infinity_value = self.get_infinity_value()
        infinity_name = self.get_infinity_name()
        apply_pre = cmds.checkBox(self.apply_pre_chk, query=True, value=True)
        apply_post = cmds.checkBox(self.apply_post_chk, query=True, value=True)
        ensure_keys = cmds.checkBox(self.ensure_keys_chk, query=True, value=True)
        verbose = cmds.checkBox(self.verbose_chk, query=True, value=True)
        
        if not apply_pre and not apply_post:
            cmds.warning("Must select at least Pre-Infinity or Post-Infinity.")
            return
        
        # Separate direct curves from other objects
        direct_curves = [s for s in sel if cmds.objExists(s) and cmds.nodeType(s).startswith('animCurve')]
        target_nodes = [s for s in sel if s not in direct_curves]
        
        # Collect all curves
        curves = list(direct_curves)
        curves += self.collect_anim_curves_from_nodes(target_nodes)
        curves = list(dict.fromkeys(curves))  # Remove duplicates
        
        if not curves:
            cmds.warning("No animation curves found on selection.")
            return
        
        print(f"INFINITY: Found {len(curves)} curve(s) to process")
        
        # Ensure 2+ keys if cycling and option is enabled
        if ensure_keys and infinity_name in ['cycle', 'cycleRelative']:
            keys_added = 0
            for curve in curves:
                if self.ensure_two_keys(curve):
                    keys_added += 1
            if keys_added > 0 and verbose:
                print(f"INFINITY: Added keys to {keys_added} curve(s)")
        
        # Apply infinity (force verbose on to debug)
        updated, failed = self.apply_infinity_advanced(curves, infinity_value, infinity_name, 
                                                      apply_pre, apply_post, True)
        
        # Generate script for failed curves
        if failed:
            self.generate_manual_script(failed, infinity_value, apply_pre, apply_post)
        
        # Report results
        if updated and not failed:
            msg = f"Applied {infinity_name} infinity to {len(updated)} curve(s)"
            cmds.inViewMessage(amg=msg, pos='midCenter', fade=True)
            print(f"INFINITY: SUCCESS - {msg}")
        elif updated:
            msg = f"Partial success: {len(updated)}/{len(curves)} curves updated"
            cmds.inViewMessage(amg=msg, pos='midCenter', fade=True)
            print(f"INFINITY: PARTIAL - {msg}")
        else:
            msg = "Failed to update any curves"
            cmds.warning(msg)
            print(f"INFINITY: FAILED - {msg}")
        
        # Refresh info
        self.refresh_selection_info()

    def generate_manual_script(self, curves, infinity_value, apply_pre, apply_post):
        """Generate a manual script for failed curves."""
        if not curves:
            return
        
        print("\n# Manual script for failed curves:")
        print("import maya.cmds as cmds")
        
        for curve in curves:
            if cmds.objExists(curve):
                if apply_pre:
                    print(f"cmds.setAttr('{curve}.preInfinity', {infinity_value})")
                if apply_post:
                    print(f"cmds.setAttr('{curve}.postInfinity', {infinity_value})")
        
        print("# End manual script\n")

    def generate_script(self, *_):
        """Generate a script for the current selection and settings."""
        sel = cmds.ls(selection=True) or []
        if not sel:
            cmds.warning("No objects selected.")
            return
        
        # Get settings
        infinity_value = self.get_infinity_value()
        infinity_name = self.get_infinity_name()
        apply_pre = cmds.checkBox(self.apply_pre_chk, query=True, value=True)
        apply_post = cmds.checkBox(self.apply_post_chk, query=True, value=True)
        
        # Collect curves
        direct_curves = [s for s in sel if cmds.objExists(s) and cmds.nodeType(s).startswith('animCurve')]
        target_nodes = [s for s in sel if s not in direct_curves]
        curves = list(direct_curves)
        curves += self.collect_anim_curves_from_nodes(target_nodes)
        curves = list(dict.fromkeys(curves))
        
        if not curves:
            cmds.warning("No animation curves found on selection.")
            return
        
        print(f"\n# Generated script to apply {infinity_name} infinity to {len(curves)} curve(s):")
        print("import maya.cmds as cmds")
        print()
        
        for curve in curves:
            if cmds.objExists(curve):
                if apply_pre:
                    print(f"cmds.setAttr('{curve}.preInfinity', {infinity_value})")
                if apply_post:
                    print(f"cmds.setAttr('{curve}.postInfinity', {infinity_value})")
        
        print("# End generated script\n")

    def refresh_selection_info(self, *_):
        """Refresh the selection information display."""
        sel = cmds.ls(selection=True) or []
        
        if not sel:
            info = "No objects selected."
        else:
            # Separate curves from other objects
            direct_curves = [s for s in sel if cmds.objExists(s) and cmds.nodeType(s).startswith('animCurve')]
            target_nodes = [s for s in sel if s not in direct_curves]
            
            # Collect all curves
            all_curves = list(direct_curves)
            all_curves += self.collect_anim_curves_from_nodes(target_nodes)
            all_curves = list(dict.fromkeys(all_curves))
            
            info_lines = []
            info_lines.append(f"Selected: {len(sel)} object(s)")
            
            if direct_curves:
                info_lines.append(f"Direct curves: {len(direct_curves)}")
            
            if target_nodes:
                info_lines.append(f"Objects with curves: {len(target_nodes)}")
            
            info_lines.append(f"Total curves found: {len(all_curves)}")
            
            if all_curves:
                # Show some curve details
                info_lines.append("\nSample curves:")
                for i, curve in enumerate(all_curves[:5]):  # Show first 5
                    try:
                        pre_inf = cmds.getAttr(curve + '.preInfinity')
                        post_inf = cmds.getAttr(curve + '.postInfinity')
                        key_count = cmds.keyframe(curve, query=True, keyframeCount=True) or 0
                        
                        inf_names = {0: 'const', 1: 'linear', 2: 'cycle', 3: 'cycleRel', 4: 'oscil'}
                        pre_name = inf_names.get(pre_inf, str(pre_inf))
                        post_name = inf_names.get(post_inf, str(post_inf))
                        
                        info_lines.append(f"  {curve}: {key_count} keys, pre={pre_name}, post={post_name}")
                    except Exception:
                        info_lines.append(f"  {curve}: (error reading)")
                
                if len(all_curves) > 5:
                    info_lines.append(f"  ... and {len(all_curves) - 5} more")
            
            info = "\n".join(info_lines)
        
        cmds.scrollField(self.info_text, edit=True, text=info)


def launch_infinity_tool():
    """Launch the Infinity Tool UI."""
    InfinityToolUI()

if __name__ == "__main__":
    launch_infinity_tool()