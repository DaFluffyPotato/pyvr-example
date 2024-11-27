#version 330

uniform mat4 world_transform;
uniform mat4 view_projection;

uniform float pop = 0.0;

in vec3 vert;
in vec2 uv;
in vec3 normal;
out vec2 frag_uv;
out vec3 frag_normal;
out vec3 frag_position;

void main() {
  vec4 world_position = world_transform * vec4(vert * (1.0 + pow(pop * 2.5, 0.7)), 1.0);
  mat4 normal_matrix = transpose(inverse(world_transform));

  frag_uv = uv;
  frag_normal = normalize((normal_matrix * vec4(normalize(normal), 0.0)).xyz);
  frag_position = world_position.xyz;
  gl_Position = view_projection * world_position;
}