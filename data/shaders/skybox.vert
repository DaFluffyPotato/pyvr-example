#version 330

in vec3 apos;

out vec3 tex_coords;

uniform mat4 view_projection;
uniform mat4 world_transform;

void main()
{
    tex_coords = apos;
    vec4 world_position = world_transform * vec4(apos, 1.0);

    gl_Position = view_projection * world_position;
}