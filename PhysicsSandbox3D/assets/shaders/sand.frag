#version 130
uniform sampler2D p3d_Texture0;
uniform float haze;
in vec2 uv;
in vec3 viewPosition;
out vec4 color;
void main() {
    vec3 sand = pow(texture(p3d_Texture0, uv).rgb, vec3(2.2));
    float ripples = sin(uv.x*9.0 + sin(uv.y*3.0))*.018;
    float fog = (1.0-exp(-length(viewPosition)*.0035))*haze;
    color = vec4(mix(sand+vec3(ripples), vec3(.56,.69,.75),fog),1.0);
}
