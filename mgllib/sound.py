import os

import glm
from pyogg import VorbisFile
import openal
from openal.al import *
from openal.alc import *
from openal import Source, Buffer, Listener, oalGetListener

from .elements import ElementSingleton
from .const import SOUND_DISTANCE_SCALE

class Sounds(ElementSingleton):
    def __init__(self, path):
        super().__init__()

        self.path = path

        self.sources = []
        self.sounds = {}

        self.set_audio_device('OpenAL Soft on Headphones (Oculus Virtual Audio Device)')

        self.head_pos = glm.vec3(0)

    def load_sounds(self):
        for sound in os.listdir(self.path):
            if sound.split('.')[-1] == 'ogg':
                self.sounds[sound.split('.')[0]] = Buffer(VorbisFile(f'{self.path}/{sound}'))

        self.listener = oalGetListener()

    def set_audio_device(self, audio_device):
        openal.oalQuit()
        try:
            if audio_device:
                openal.oalInit(audio_device.encode('utf-8'))
            else:
                openal.oalInit()
        except openal.ALError:
            print('could not open requested audio device:', audio_device)
            openal.oalInit()
        except openal.alc.ALCError:
            print('could not open requested audio device:', audio_device)
            openal.oalInit()

        self.load_sounds()
    
    def make_source(self, sound):
        buffer = self.sounds[sound]
        try:
            new_source = Source(buffer)
            new_source.local = False
            self.sources.append(new_source)
            return new_source
        except openal.ALError:
            for old_source in self.sources:
                if old_source.get_state() == openal.AL_STOPPED:
                    old_source._set_buffer(buffer)
                    return old_source
        # no sources are available
        return None
    
    def play(self, sound, volume=1.0):
        source = self.make_source(sound)
        if source:
            source.set_gain(volume)
            source.local = True
            source.set_position(self.listener.position)
            source.play()

    def play_from(self, sound, volume=1.0, position=glm.vec3(0.0)):
        position = position * SOUND_DISTANCE_SCALE
        source = self.make_source(sound)
        if source:
            source.set_gain(volume)
            source.set_position(tuple(position))
            source.local = False
            source.play()

    def place_listener(self, pos, orientation):
        new_pos = tuple(pos * SOUND_DISTANCE_SCALE)
        self.listener.move_to(new_pos)

        self.head_pos = glm.vec3(pos)

        for source in self.sources:
            if source.local and (source.get_state() != openal.AL_STOPPED):
                source.set_position(new_pos)

        # openal orientation is a forward vector and an up vector combined into a vec6 tuple
        nose = glm.vec3(0, 0, -1)
        up = glm.vec3(0, 1, 0)
        openal_orientation = tuple(list(glm.mat4(orientation) * nose) + list(glm.mat4(orientation) * up))

        self.listener.set_orientation(openal_orientation)

    