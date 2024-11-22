#version 330

out vec4 f_color;

in vec3 tex_coords;

uniform samplerCube skybox;

void main()
{
    f_color = texture(skybox, tex_coords);
}