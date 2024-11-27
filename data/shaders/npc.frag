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
uniform float pop = 0.0;

out vec4 f_color;
in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_position;

// LICENSE for 3D Simplex Noise
/* https://www.shadertoy.com/view/XsX3zB
 *
 * The MIT License
 * Copyright © 2013 Nikita Miropolskiy
 * 
 * ( license has been changed from CCA-NC-SA 3.0 to MIT
 *
 *   but thanks for attributing your source code when deriving from this sample 
 *   with a following link: https://www.shadertoy.com/view/XsX3zB )
*/
/* discontinuous pseudorandom uniformly distributed in [-0.5, +0.5]^3 */
vec3 random3(vec3 c) {
  float j = 4096.0*sin(dot(c,vec3(17.0, 59.4, 15.0)));
  vec3 r;
  r.z = fract(512.0*j);
  j *= .125;
  r.x = fract(512.0*j);
  j *= .125;
  r.y = fract(512.0*j);
  return r-0.5;
}

/* skew constants for 3d simplex functions */
const float F3 =  0.3333333;
const float G3 =  0.1666667;

const float noise_scale = 2.0;

/* 3d simplex noise */
float simplex3d(vec3 p) {
  /* 1. find current tetrahedron T and it's four vertices */
  /* s, s+i1, s+i2, s+1.0 - absolute skewed (integer) coordinates of T vertices */
  /* x, x1, x2, x3 - unskewed coordinates of p relative to each of T vertices*/

  /* calculate s and x */
  vec3 s = floor(p + dot(p, vec3(F3)));
  vec3 x = p - s + dot(s, vec3(G3));

  /* calculate i1 and i2 */
  vec3 e = step(vec3(0.0), x - x.yzx);
  vec3 i1 = e*(1.0 - e.zxy);
  vec3 i2 = 1.0 - e.zxy*(1.0 - e);

  /* x1, x2, x3 */
  vec3 x1 = x - i1 + G3;
  vec3 x2 = x - i2 + 2.0*G3;
  vec3 x3 = x - 1.0 + 3.0*G3;

  /* 2. find four surflets and store them in d */
  vec4 w, d;

  /* calculate surflet weights */
  w.x = dot(x, x);
  w.y = dot(x1, x1);
  w.z = dot(x2, x2);
  w.w = dot(x3, x3);

  /* w fades from 0.6 at the center of the surflet to 0.0 at the margin */
  w = max(0.6 - w, 0.0);

  /* calculate surflet components */
  d.x = dot(random3(s), x);
  d.y = dot(random3(s + i1), x1);
  d.z = dot(random3(s + i2), x2);
  d.w = dot(random3(s + 1.0), x3);

  /* multiply d by w^4 */
  w *= w;
  w *= w;
  d *= w;

  /* 3. return the sum of the four surflets */
  return dot(d, vec4(52.0));
}

int bit_check(int value, int bit_i) {
  return (value >> bit_i) & 0x1;
}

void main() {
  float noise_val = simplex3d(frag_position * noise_scale) * 0.7 + simplex3d(frag_position * noise_scale * 3.5) * 0.3;
  if (noise_val * 0.5 + 0.5 < pow(pop, 0.35)) {
    discard;
  }

  vec4 base_color = texture(tex, frag_uv);
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