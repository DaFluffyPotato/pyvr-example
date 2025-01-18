#version 330

uniform mat4 world_transform;
uniform mat4 view_projection;

in vec3 vert;
in vec2 uv;
out vec2 frag_uv;
out vec3 frag_position;

void main() {
  vec4 world_position = world_transform * vec4(vert, 1.0);

  frag_uv = uv;
  gl_Position = view_projection * world_position;
}