#version 330

uniform sampler2D tex;

out vec4 f_color;
in vec2 frag_uv;

void main() {
  vec4 base_color = texture(tex, frag_uv);

  if (base_color.a <= 0) {
    discard;
  }

  f_color = vec4(base_color.rgb, 1.0);
}