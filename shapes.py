import glnext
import json

def floats(line):
    a, b, c = line.split()[1:]
    return [float(a), float(b), float(c)]

def vertnorm(v, n):
    return floats(verts[int(v) - 1]) + floats(norms[int(n) - 1])

def triangle(line):
    av, an, bv, bn, cv, cn = line.replace('/', ' ').split()[1:]
    return vertnorm(av, an) + vertnorm(bv, bn) + vertnorm(cv, cn)

text = open('shapes.obj').read()

verts = [x for x in text.splitlines() if x.startswith('v ')]
norms = [x for x in text.splitlines() if x.startswith('vn ')]
faces = {}

for line in text.splitlines():
    if line.startswith('o '):
        name = line.split()[1]
        faces[name] = []

    if line.startswith('f '):
        faces[name].append(line)

data = []
result = {'shapes': {}}

for name in ['cube', 'sphere', 'cylinder', 'cone', 'monkey', 'plane', 'circle', 'capsule', 'torus']:
    result['shapes'][name] = {
        'offset': len(data) // 6,
        'count': len(faces[name]) * 3,
    }
    for face in faces[name]:
        data += triangle(face)

result['data'] = glnext.pack('3h 3h', data).hex()

open('shapes.json', 'w').write(json.dumps(result))
