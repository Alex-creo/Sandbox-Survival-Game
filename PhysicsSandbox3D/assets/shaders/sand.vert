#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_TextureMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
out vec3 viewPosition;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0 * 150.0;
    viewPosition = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
}
