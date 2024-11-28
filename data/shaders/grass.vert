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

const float motion_scale = 0.1;

void main() {
  frag_uv = uv;
  frag_normal = normal;

  float height = (vert - origin).y;

  float seed = vert.x * 3920.0 + vert.y * 1238.3 + vert.z * 2391.7;

  vec3 offset = vec3(cos(time * 2.2 + seed) * height * motion_scale, cos(time * 1.2 + seed) * height * motion_scale * 0.4, cos(time * 2.65 + seed) * height * motion_scale);

  frag_position = vert + offset;
  gl_Position = view_projection * vec4(frag_position, 1.0);
}