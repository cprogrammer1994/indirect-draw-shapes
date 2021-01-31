import json

import glnext
from glnext_compiler import glsl
from PIL import Image

shapes = json.loads(open('shapes.json').read())

objects = [
    {
        'shape': 'monkey',
        'position': [0.0, 0.0, 1.0],
        'rotation': [0.0, 0.0, 0.707, 0.707],
        'size': [1.0, 1.0, 1.0],
    },
    {
        'shape': 'capsule',
        'position': [0.0, 0.0, 0.0],
        'rotation': [0.0, 0.0, 0.0, 1.0],
        'size': [1.0, 0.1, 0.0],
    }
]

instance = glnext.instance()
fbo = instance.framebuffer((512, 512))
render = fbo.render(
    vertex_shader=glsl('''
        #version 450
        #pragma shader_stage(vertex)

        layout (binding = 0) uniform Buffer {
            mat4 mvp;
        };

        layout (location = 0) in vec3 in_vert;
        layout (location = 1) in vec3 in_norm;

        layout (location = 2) in vec3 in_pos;
        layout (location = 3) in vec4 in_quat;
        layout (location = 4) in vec3 in_scale;

        layout (location = 0) out vec3 out_norm;

        vec3 qtransform(vec4 q, vec3 v) {
            return v + 2.0 * cross(cross(v, q.xyz) + q.w * v, q.xyz);
        }

        void main() {
            vec3 vert;
            if (gl_VertexIndex < 3516) {
                vert = in_vert * in_scale;
            } else if (gl_VertexIndex < 4284) {
                vert = in_vert * in_scale.y + vec3(0.0, 0.0, sign(in_vert.z) * (in_scale.x - in_scale.y / 2.0));
            } else {
                vert = in_vert * in_scale.y * 2.0 + vec3(normalize(in_vert.xy) * (in_scale.x - in_scale.y * 2.0), 0.0);
            }
            gl_Position = mvp * vec4(in_pos + qtransform(in_quat, vert), 1.0);
            out_norm = qtransform(in_quat, in_norm);
        }
    '''),
    fragment_shader=glsl('''
        #version 450
        #pragma shader_stage(fragment)

        layout (binding = 0) uniform Buffer {
            mat4 mvp;
        };

        layout (location = 0) in vec3 in_norm;

        layout (location = 0) out vec4 out_color;

        void main() {
            vec3 sight = -vec3(mvp[0].w, mvp[1].w, mvp[2].w);
            float lum = dot(normalize(sight), normalize(in_norm)) * 0.7 + 0.3;
            out_color = vec4(lum, lum, lum, 1.0);
        }
    '''),
    vertex_format='3h 3h',
    instance_format='3f 4f 3f',
    vertex_buffer=bytes.fromhex(shapes['data']),
    indirect_count=len(objects),
    instance_count=len(objects),
    buffers=[
        {
            'name': 'uniform_buffer',
            'type': 'uniform_buffer',
            'binding': 0,
            'size': 64,
        }
    ]
)

render['uniform_buffer'].write(glnext.camera((4, 3, 2), (0, 0, 0)))

instance_buffer = []
indirect_buffer = []

for i, obj in enumerate(objects):
    instance_buffer += [*obj['position'], *obj['rotation'], *obj['size']]
    indirect_buffer += [shapes['shapes'][obj['shape']]['count'], 1, shapes['shapes'][obj['shape']]['offset'], i]

render['instance_buffer'].write(glnext.pack(instance_buffer))
render['indirect_buffer'].write(glnext.pack(indirect_buffer))

instance.run()

Image.frombuffer('RGBA', (512, 512), fbo.output[0].read(), 'raw', 'RGBA', 0, -1).show()
