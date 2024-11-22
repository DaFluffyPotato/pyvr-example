import ctypes

import numpy as np
import glm
import xr

from .elements import ElementSingleton, Element
from .mat3d import quat_scale
from .const import TRIGGER_THRESHOLD

class FloatButton(Element):
    def __init__(self, button_type):
        self.type = button_type
        self.value = 0
        self.pressed = False
        self.holding = False

    def update(self, value):
        self.pressed = False
        if self.value > TRIGGER_THRESHOLD:
            if not self.holding:
                self.pressed = True
            self.holding = True
        else:
            self.holding = False
        
        self.value = value

class Controller(Element):
    def __init__(self, hand):
        super().__init__()

        self.parent = None

        self.hand = hand
        self.tracked = False
        self.pos = (0, 0, 0)
        self.rot = (0, 0, 0, 1)
        self.aim_pos = (0, 0, 0)
        self.aim_rot = (0, 0, 0, 1)

        self.pressed_upper = False
        self.holding_upper = False
        self.pressed_lower = False
        self.holding_lower = False

        self.interacting = None

        self.squeeze = FloatButton('squeeze')
        self.trigger = FloatButton('trigger')

        self.log = []

    def log_state(self):
        self.log.append((glm.vec3(self.pos), self.glm_quat, glm.vec3(self.aim_pos), self.aim_glm_quat, self.e['XRWindow'].dt))
        self.log = self.log[-50:]

    def velocity(self, timeframe):
        if len(self.log):
            total_time = 0
            for sample in self.log[::-1]:
                total_time += sample[4]
                if total_time >= timeframe:
                    break
            return (glm.vec3(self.pos) - sample[0]) / total_time
        return glm.vec3(0.0, 0.0, 0.0)
    
    def angular_velocity(self, timeframe):
        # angular difference (q1 -> q2) is q2 * inv(q1)
        # scaling rotation is q ^ scale
        if len(self.log):
            total_time = 0
            for sample in self.log[::-1]:
                total_time += sample[4]
                if total_time >= timeframe:
                    break
            return quat_scale(self.aim_glm_quat * glm.inverse(sample[3]), 1 / total_time)
        return glm.vec3(0.0, 0.0, 0.0)

    def copy_to(self, controller):
        controller.tracked = self.tracked
        controller.pos = self.pos
        controller.rot = self.rot
        controller.aim_pos = self.aim_pos
        controller.aim_rot = self.aim_rot

        controller.pressed_upper = self.pressed_upper
        controller.holding_upper = self.holding_upper
        controller.pressed_lower = self.pressed_lower
        controller.holding_lower = self.holding_lower

        controller.squeeze = self.squeeze
        controller.trigger = self.trigger

    def transform(self, transform):
        # translate
        self.pos = tuple(transform.rotation_matrix * glm.vec3(self.pos) + transform.pos)
        self.aim_pos = tuple(transform.rotation_matrix * glm.vec3(self.aim_pos) + transform.pos)

        # rotate
        new_rot = tuple(glm.quat(transform.rotation_matrix) * self.glm_quat)
        self.rot = (*new_rot[1:], new_rot[0])
        new_aim_rot = tuple(glm.quat(transform.rotation_matrix) * self.aim_glm_quat)
        self.aim_rot = (*new_aim_rot[1:], new_aim_rot[0])

    @property
    def glm_quat(self):
        return glm.quat(self.rot[3], *self.rot[:3])

    @property
    def aim_glm_quat(self):
        return glm.quat(self.aim_rot[3], *self.aim_rot[:3])
    
    @property
    def grip_vector(self):
        return self.glm_quat * glm.vec3(0, 0, -1)
    
    @property
    def aim_vector(self):
        return self.aim_glm_quat * glm.vec3(0, 0, -1)

class XRInput(ElementSingleton):
    def __init__(self):
        super().__init__()

    @property
    def left_hand(self):
        return self.hands[0]

    @property
    def right_hand(self):
        return self.hands[1]

    def init(self, context):
        self.context = context
        self.session = context.session

        self.action_set = context.default_action_set

        self.suggested_bindings = None

        self.raw_head_pos = (0, 0, 0)
        self.head_transform = glm.translate(glm.vec3((0, 0, 0)))

        controller_paths = (xr.Path * 2)(xr.string_to_path(context.instance, '/user/hand/left'), xr.string_to_path(context.instance, '/user/hand/right'))
        controller_pose_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.POSE_INPUT,
            action_name='hand_pose',
            localized_action_name='Hand Pose',
            count_subaction_paths=len(controller_paths),
            subaction_paths=controller_paths,
        ))

        controller_aim_pose_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.POSE_INPUT,
            action_name='hand_aim_pose',
            localized_action_name='Hand Aim Pose',
            count_subaction_paths=len(controller_paths),
            subaction_paths=controller_paths,
        ))

        self.left_stick_x_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='left_stick_x',
            localized_action_name='Left Stick X',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_stick_y_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='left_stick_y',
            localized_action_name='Left Stick Y',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_stick_x_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='right_stick_x',
            localized_action_name='Right Stick X',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_stick_y_action = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='right_stick_y',
            localized_action_name='Right Stick Y',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_lower_button = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.BOOLEAN_INPUT,
            action_name='right_lower_button',
            localized_action_name='Right Lower Button',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_upper_button = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.BOOLEAN_INPUT,
            action_name='right_upper_button',
            localized_action_name='Right Upper Button',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_lower_button = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.BOOLEAN_INPUT,
            action_name='left_lower_button',
            localized_action_name='Left Lower Button',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_upper_button = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.BOOLEAN_INPUT,
            action_name='left_upper_button',
            localized_action_name='Left Upper Button',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_squeeze = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='left_squeeze',
            localized_action_name='Left Squeeze',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_trigger = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='left_trigger',
            localized_action_name='Left Trigger',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_squeeze = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='right_squeeze',
            localized_action_name='Right Squeeze',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.right_trigger = xr.create_action(action_set=self.action_set, create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.FLOAT_INPUT,
            action_name='right_trigger',
            localized_action_name='Right Trigger',
            count_subaction_paths=0,
            subaction_paths=None,
        ))

        self.left_stick = None
        self.right_stick = None

        # docs suggest that /thumbstick as a vector2 may be necessary for some controllers

        self.suggested_bindings = (xr.ActionSuggestedBinding * 16)(
            xr.ActionSuggestedBinding(action=controller_pose_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/grip/pose")),
            xr.ActionSuggestedBinding(action=controller_pose_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/grip/pose")),
            xr.ActionSuggestedBinding(action=controller_aim_pose_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/aim/pose")),
            xr.ActionSuggestedBinding(action=controller_aim_pose_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/aim/pose")),
            xr.ActionSuggestedBinding(action=self.left_stick_x_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/thumbstick/x")),
            xr.ActionSuggestedBinding(action=self.left_stick_y_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/thumbstick/y")),
            xr.ActionSuggestedBinding(action=self.right_stick_x_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/thumbstick/x")),
            xr.ActionSuggestedBinding(action=self.right_stick_y_action, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/thumbstick/y")),
            xr.ActionSuggestedBinding(action=self.right_lower_button, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/a/click")),
            xr.ActionSuggestedBinding(action=self.right_upper_button, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/b/click")),
            xr.ActionSuggestedBinding(action=self.left_lower_button, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/x/click")),
            xr.ActionSuggestedBinding(action=self.left_upper_button, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/y/click")),
            xr.ActionSuggestedBinding(action=self.left_squeeze, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/squeeze/value")),
            xr.ActionSuggestedBinding(action=self.left_trigger, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/left/input/trigger/value")),
            xr.ActionSuggestedBinding(action=self.right_squeeze, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/squeeze/value")),
            xr.ActionSuggestedBinding(action=self.right_trigger, binding=xr.string_to_path(instance=context.instance, path_string=f"/user/hand/right/input/trigger/value")))

        self.suggest_bindings()

        self.action_indices = ['left_grip', 'right_grip', 'left_aim', 'right_aim']
        self.action_spaces = {
            'left_grip': xr.create_action_space(session=self.session, create_info=xr.ActionSpaceCreateInfo(action=controller_pose_action, subaction_path=controller_paths[0])),
            'right_grip': xr.create_action_space(session=self.session, create_info=xr.ActionSpaceCreateInfo(action=controller_pose_action, subaction_path=controller_paths[1])),
            'left_aim': xr.create_action_space(session=self.session, create_info=xr.ActionSpaceCreateInfo(action=controller_aim_pose_action, subaction_path=controller_paths[0])),
            'right_aim': xr.create_action_space(session=self.session, create_info=xr.ActionSpaceCreateInfo(action=controller_aim_pose_action, subaction_path=controller_paths[1])),
        }

        self.head_space = xr.create_reference_space(session=self.session, create_info=xr.ReferenceSpaceCreateInfo(xr.ReferenceSpaceType.VIEW, xr.typedefs.Posef(xr.typedefs.Quaternionf(0, 0, 0, 1), xr.typedefs.Vector3f(0, 0, 0))))

        self.hands = [Controller(0), Controller(1)]

    def suggest_bindings(self):
        if self.suggested_bindings:
            '''
            xr.suggest_interaction_profile_bindings(
                instance=self.context.instance,
                suggested_bindings=xr.InteractionProfileSuggestedBinding(
                    interaction_profile=xr.string_to_path(
                        self.context.instance,
                        "/interaction_profiles/meta/touch_controller_quest_2",
                    ),
                    count_suggested_bindings=len(self.suggested_bindings),
                    suggested_bindings=self.suggested_bindings,
                ),
            )'''
            # the controller profiles below have limited component paths
            
            xr.suggest_interaction_profile_bindings(
                instance=self.context.instance,
                suggested_bindings=xr.InteractionProfileSuggestedBinding(
                    interaction_profile=xr.string_to_path(
                        self.context.instance,
                        "/interaction_profiles/oculus/touch_controller",
                    ),
                    count_suggested_bindings=len(self.suggested_bindings),
                    suggested_bindings=self.suggested_bindings,
                ),
            )
            '''
            xr.suggest_interaction_profile_bindings(
                instance=self.context.instance,
                suggested_bindings=xr.InteractionProfileSuggestedBinding(
                    interaction_profile=xr.string_to_path(
                        self.context.instance,
                        "/interaction_profiles/htc/vive_controller",
                    ),
                    count_suggested_bindings=len(self.suggested_bindings),
                    suggested_bindings=self.suggested_bindings,
                ),
            )'''


    def update(self, frame_state):
        if self.context.session_state == xr.SessionState.FOCUSED:
            # needed to get input updates
            active_action_set = xr.ActiveActionSet(action_set=self.context.default_action_set, subaction_path=xr.NULL_PATH)
            xr.sync_actions(session=self.session, sync_info=xr.ActionsSyncInfo(count_active_action_sets=1, active_action_sets=ctypes.pointer(active_action_set)))

            # check states
            for space_id in self.action_spaces:
                space = self.action_spaces[space_id]
                index = self.action_indices.index(space_id)

                space_location = xr.locate_space(
                    space=space,
                    base_space=self.context.space,
                    time=frame_state.predicted_display_time,
                )
                if space_location.location_flags & xr.SPACE_LOCATION_POSITION_VALID_BIT:
                    hand = self.hands[index % 2]
                    if index < 2:
                        hand.tracked = True
                        hand.pos = tuple(space_location.pose.position)
                        hand.rot = tuple(space_location.pose.orientation)
                    else:
                        hand.aim_pos = tuple(space_location.pose.position)
                        hand.aim_rot = tuple(space_location.pose.orientation)

            space_location = xr.locate_space(
                space=self.head_space,
                base_space=self.context.space,
                time=frame_state.predicted_display_time,
                )
            
            new_raw_head_pos = tuple(space_location.pose.position)[:3]
            if self.raw_head_pos:
                self.head_movement = tuple(new_raw_head_pos[i] - self.raw_head_pos[i] for i in range(3))
            self.raw_head_pos = new_raw_head_pos

            # hack to remove y component from head transform (since free vertical head movement is allowed while x/z needs to apply to movement)
            head_transform_vec = self.raw_head_pos
            head_transform_vec = (head_transform_vec[0], 0, head_transform_vec[2])
            # generate head transform matrix
            self.head_transform = np.array(glm.translate(glm.vec3(head_transform_vec)).to_list())

            # place hands relative to head rather than in absolute playspace
            for hand in self.hands:
                hand.aim_pos = [hand.aim_pos[i] - self.raw_head_pos[i] if (i != 1) else hand.aim_pos[i] for i in range(3)]
                hand.pos = [hand.pos[i] - self.raw_head_pos[i] if (i != 1) else hand.pos[i] for i in range(3)]

            left_stick_x = xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_stick_x_action, subaction_path=xr.NULL_PATH)).current_state
            left_stick_y = xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_stick_y_action, subaction_path=xr.NULL_PATH)).current_state
            self.left_stick = (left_stick_x, left_stick_y)

            right_stick_x = xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.right_stick_x_action, subaction_path=xr.NULL_PATH)).current_state
            right_stick_y = xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_stick_x_action, subaction_path=xr.NULL_PATH)).current_state
            self.right_stick = (right_stick_x, right_stick_y)

            left_lower = xr.get_action_state_boolean(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_lower_button, subaction_path=xr.NULL_PATH))
            self.hands[0].holding_lower = left_lower.current_state
            self.hands[0].pressed_lower = left_lower.current_state and left_lower.changed_since_last_sync

            left_upper = xr.get_action_state_boolean(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_upper_button, subaction_path=xr.NULL_PATH))
            self.hands[0].holding_upper = left_upper.current_state
            self.hands[0].pressed_upper = left_upper.current_state and left_lower.changed_since_last_sync

            right_lower = xr.get_action_state_boolean(session=self.session, get_info=xr.ActionStateGetInfo(action=self.right_lower_button, subaction_path=xr.NULL_PATH))
            self.hands[1].holding_lower = right_lower.current_state
            self.hands[1].pressed_lower = right_lower.current_state and right_lower.changed_since_last_sync

            right_upper = xr.get_action_state_boolean(session=self.session, get_info=xr.ActionStateGetInfo(action=self.right_upper_button, subaction_path=xr.NULL_PATH))
            self.hands[1].holding_upper = right_upper.current_state
            self.hands[1].pressed_upper = right_upper.current_state and right_upper.changed_since_last_sync

            self.hands[0].squeeze.update(xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_squeeze, subaction_path=xr.NULL_PATH)).current_state)
            self.hands[0].trigger.update(xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.left_trigger, subaction_path=xr.NULL_PATH)).current_state)
            self.hands[1].squeeze.update(xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.right_squeeze, subaction_path=xr.NULL_PATH)).current_state)
            self.hands[1].trigger.update(xr.get_action_state_float(session=self.session, get_info=xr.ActionStateGetInfo(action=self.right_trigger, subaction_path=xr.NULL_PATH)).current_state)