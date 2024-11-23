#version 330

uniform sampler2D tex;

out vec4 f_color;
in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_position;

void main() {
  vec4 base_color = texture(tex, frag_uv);

  // necessary to prevent the inputs from being optimized away
  base_color.rgb += (frag_normal + clamp(frag_position, 0.0, 1.0)) * 0.00001;

  f_color = base_color;
}