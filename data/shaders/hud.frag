#version 330

uniform float blood_flash = 0.0;

const vec3 blood_color = vec3(228.0 / 255.0, 59.0 / 255.0, 68.0 / 255.0);

out vec4 f_color;
in vec2 uv;

void main() {
    float center_dis = length(uv - vec2(0.5, 0.5));
    f_color = vec4(blood_color, blood_flash * (0.8 + min(center_dis * 2, 1) * 0.2));
}