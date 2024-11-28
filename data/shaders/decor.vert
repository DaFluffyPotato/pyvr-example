#version 330

uniform mat4 world_transform;
uniform mat4 view_projection;

in vec3 vert;
in vec2 uv;
in vec3 normal;
in vec3 origin;
out vec2 frag_uv;
out vec3 frag_normal;
out vec3 frag_position;

void main() {
  frag_uv = uv;
  frag_normal = normal;

  // necessary to keep origin as an input attribute
  vec3 origin_ref = clamp(origin, 0.0, 1.0) * 0.000001;

  frag_position = vert + origin_ref;
  gl_Position = view_projection * vec4(vert, 1.0);
}