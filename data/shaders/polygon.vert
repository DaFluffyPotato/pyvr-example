#version 330

uniform mat4 world_transform;
uniform mat4 view_projection;

in vec3 vert;

void main() {
  vec4 world_position = world_transform * vec4(vert, 1.0);
  
  gl_Position = view_projection * world_position;
}