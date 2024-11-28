#version 330

uniform mat4 world_transform;
uniform mat4 view_projection;
uniform float time = 0.0;

in vec3 vert;
in vec2 uv;
in vec3 normal;
in vec3 origin;
out vec2 frag_uv;
out vec3 frag_normal;
out vec3 frag_position;

const float motion_scale = 0.02;

void main() {
  frag_uv = uv;
  frag_normal = normal;

  float height = (vert - origin).y;
  float xz_offset = length((vert - origin).xz);

  // the trunk should only move on the xz plane near the top
  // branched out leaves far away from the trunk should be free to move up and down
  float xz_motion = height * 0.3 + xz_offset;
  float y_motion = xz_offset;

  float seed = vert.x * 0.5 + vert.y * 0.6 + vert.z * 0.55;

  vec3 offset = vec3(cos(time * 0.74 + seed * 0.5) * xz_motion * motion_scale, cos(time * 2.65 + seed) * y_motion * motion_scale, cos(time * 0.68 + seed * 0.5) * xz_motion * motion_scale);

  frag_position = vert + offset;
  gl_Position = view_projection * vec4(frag_position, 1.0);
}