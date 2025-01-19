**This repository is an example Python VR project.**

This was originally meant to be boilerplate for VR gamedev with ModernGL, Pygame, GLFW, and PyOpenXR, but I ended up going straight for making something functional. Some of the naming is strange as a result. There's a lot of spaghetti that I left in there as well. I'm cleaning it up in the closed source version for a multiplayer project.

Various portions of the code are not fully optimized. The pathfinding especially can bog things down a bit. I get a stable 72fps with Link to my Quest 3 still. World generation and navmesh generation can take a few seconds when starting the demo.

![example](example.gif)

I'm not entirely sure how OpenXR binding suggestions work. I've specified them for the Oculus Touch Controllers. They may or may not work for other controllers like the Index. I haven't looked into it. If it doesn't work, you can play around with the hardcoded bindings in `xrinput.py`. I only own a Rift CV1 and a Quest 3. lol

I'll be working more with other headsets soon, so I may update this README as I learn stuff that may affect this repository.

**Controls (Oculus Touch):**
- Left Stick: Movement (hand oriented, not head)
- Right Stick: Snap Turn
- X: Jump
- B/Y: Mag Release
- Grip: Grab (weapons)
- Trigger: Grab (mags/bolts) & Shoot

Some interactions are restricted to the applicable hand depending on how an item is held. All grabs need to be held continuously. Some games implement grabbing as a toggle; this is not one of them.

Health and kills (on your current life) are shown on the watch face.