import math

import glm
import pygame

from .elements import Element
from .mat3d import prep_mat
from .textured_quad import TexturedQuad

class Watch(Element):
    def __init__(self, owner):
        super().__init__()

        self.owner = owner
        
        self.transform = None

        self.watch_face = TexturedQuad()
        self.face_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
        self.face_state = None

    def calculate_transform(self):
        left_hand = self.e['Demo'].player.hands[0]
        # first 2 rotations are just an offset for wrist placement
        hand_rotation = glm.mat4(glm.quat(left_hand.aim_rot[3], *(left_hand.aim_rot[:3]))) * glm.rotate(-0.3, glm.vec3(0, 1, 0)) * glm.rotate(-0.08, glm.vec3(1, 0, 0))
        if left_hand.interacting and left_hand.interacting.hand_override:
            hand_pos = glm.translate(left_hand.interacting.hand_override)
        elif left_hand.interacting and (left_hand.interacting.parent.alt_grip == left_hand.interacting):
            hand_pos = glm.translate(left_hand.interacting.world_pos)
        else:
            hand_pos = glm.translate(left_hand.pos)
        local_rotation = glm.rotate(-math.pi * 4 / 9, glm.vec3(0, 0, 1))
        local_scale = glm.scale(glm.vec3(0.035))
        local_offset = glm.translate(glm.vec3(0, 0, 0.09))
        self.transform = hand_pos * hand_rotation * local_offset * local_rotation * local_scale

        self.watch_face.transform = self.transform * glm.translate(glm.vec3(0, 12.4 / 16, -1 / 16)) * glm.scale(glm.vec3(0.7, 1.0, 0.7)) * glm.rotate(math.pi / 2, glm.vec3(0, 1, 0))

    def update(self):
        self.calculate_transform()

        health = self.owner.health / self.owner.max_health
        face_state = (health, self.owner.helmeted, self.e['Demo'].watch_text)
        if face_state != self.face_state:
            self.face_state = face_state

            pygame.draw.circle(self.face_surf, (24, 20, 37), (self.face_surf.get_width() / 2, self.face_surf.get_height() / 2), self.face_surf.get_width() / 2)

            if self.owner.helmeted:
                pygame.draw.arc(self.face_surf, (0, 153, 219), pygame.Rect(self.face_surf.get_width() * 0.1, self.face_surf.get_height() * 0.1, self.face_surf.get_width() * 0.8, self.face_surf.get_height() * 0.8), math.pi / 2 + 0.1, math.pi * 4 / 5 - 0.1, width=int(self.face_surf.get_width() * 0.1))
            pygame.draw.arc(self.face_surf, (38, 43, 68), pygame.Rect(self.face_surf.get_width() * 0.1, self.face_surf.get_height() * 0.1, self.face_surf.get_width() * 0.8, self.face_surf.get_height() * 0.8), -math.pi / 2 + 0.1, math.pi / 2 - 0.1, width=int(self.face_surf.get_width() * 0.1))
            pygame.draw.arc(self.face_surf, (228, 59, 68), pygame.Rect(self.face_surf.get_width() * 0.1, self.face_surf.get_height() * 0.1, self.face_surf.get_width() * 0.8, self.face_surf.get_height() * 0.8), -math.pi / 2 + 0.1, -math.pi / 2 + 0.1 + (math.pi - 0.2) * health, width=int(self.face_surf.get_width() * 0.1))

            watch_text = self.e['Demo'].font.render(self.e['Demo'].watch_text, True, (255, 255, 255))
            self.face_surf.blit(watch_text, (self.face_surf.get_width() / 2 - watch_text.get_width() / 2, self.face_surf.get_height() / 2 - watch_text.get_height() / 2))

            self.watch_face.apply_surface(self.face_surf)

    def render(self, camera, uniforms={}):
        if self.transform:
            uniforms['world_light_pos'] = tuple(camera.light_pos)
            uniforms['world_transform'] = prep_mat(self.transform)
            uniforms['view_projection'] = camera.prepped_matrix
            uniforms['eye_pos'] = camera.eye_pos
            self.e['Demo'].watch_obj.vao.render(uniforms=uniforms)
            self.watch_face.render(camera)