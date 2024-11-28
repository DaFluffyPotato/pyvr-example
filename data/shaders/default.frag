#version 330

uniform sampler2D tex;
uniform sampler2D normal_tex;
uniform sampler2D metallic_tex;
uniform int texture_flags;
uniform vec3 world_light_pos;
uniform vec3 eye_pos;
uniform float ambient_strength = 0.5;
uniform float light_strength = 1.25;
uniform float shine_strength = 16;

out vec4 f_color;
in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_position;

int bit_check(int value, int bit_i) {
  return (value >> bit_i) & 0x1;
}

void main() {
  vec4 base_color = texture(tex, frag_uv);

  if (base_color.a <= 0) {
    discard;
  }
  
  float local_shininess = texture(metallic_tex, frag_uv).r * bit_check(texture_flags, 2);
  vec3 local_normal = ((texture(normal_tex, frag_uv).rgb * 2.0) - 1.0) * bit_check(texture_flags, 1);

  vec3 computed_normal = normalize(vec3(frag_normal.x + local_normal.y, frag_normal.y + local_normal.x, frag_normal.z));

  vec3 light_vec = normalize(world_light_pos);
  vec3 eye_vec = normalize(eye_pos - frag_position);
  vec3 half_vec = normalize(light_vec + eye_vec);

  vec4 ambient = ambient_strength * base_color;
  vec4 diffuse = base_color * clamp(dot(light_vec, computed_normal), 0.0, 1.0) * (1.0 - ambient_strength) * light_strength;
  vec3 specular = vec3(1.0, 1.0, 1.0) * pow(clamp(dot(computed_normal, half_vec), 0.0, 1.0), shine_strength) * local_shininess;

  f_color = vec4(diffuse.rgb + ambient.rgb + specular, 1.0);
}