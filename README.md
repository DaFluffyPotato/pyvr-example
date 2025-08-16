**Update 2025:**
I've been working on the continuation of this project (closed source) called [GunSlaw VR](https://dafluffypotato.com/gunslaw). I've added some notes to the README based on my later findings.

**This repository is an example Python VR project.**

This was originally meant to be boilerplate for VR gamedev with ModernGL, Pygame, GLFW, and PyOpenXR, but I ended up going straight for making something functional. Some of the naming is strange as a result. There's a lot of spaghetti and dead code that I left in there as well.

Various portions of the code are not fully optimized. The pathfinding especially can bog things down a bit. I get a stable 72fps with Link to my Quest 3 still. World generation and navmesh generation can take a few seconds when starting the demo.

![example](example.gif)

Based on testing with GunSlaw VR, the OpenXR input handling should be mostly compatible with most devices. There may be some crashes when unfocusing the VR application (especially on Index) though.

Audio device selection is hardcoded to select the Oculus Virtual Audio Device, which will cause some issues on some setups. There's also a bug in PyOpenAL I had to fix in later versions of this project in order to properly allow for device selection.

**Controls (Oculus Touch):**
- Left Stick: Movement (hand oriented, not head)
- Right Stick: Snap Turn
- X: Jump
- B/Y: Mag Release
- Grip: Grab (weapons)
- Trigger: Grab (mags/bolts) & Shoot

Some interactions are restricted to the applicable hand depending on how an item is held. All grabs need to be held continuously. Some games implement grabbing as a toggle; this is not one of them.

Health and kills (on your current life) are shown on the watch face. Extra mags for your current weapon are at your hips.

**Architecture:**

I made an architecture chart for GunSlaw VR so you can see how all the dependencies are used. The only difference between this and the latest architecture is the addition of my framework Shobnet for netcode, which doesn't exist in this demo. There's also not as much GLM usage in this demo, which makes the math quite spaghetti.
![architecture_chart](architecture.png)

**The PyOpenXR version listed in the requirements.txt may be incorrect! There was a memory leak in PyOpenXR when I was working on this project. I fixed it in a PR and it's been merged in, but the release was posted to PyPI after I forked GunSlaw VR to its own project, so I haven't tested this with it. The version in the** `requirements.txt` **is the first version with my fix in it (untested).**