"""Generate static transfer previews from PuffyEngine's character equations.

Reference: Leviathan-Rack2/src/puffy/PuffyEngine.cpp, October 2026.
Full Puff, linked characters, fully wet; excludes DC removal and output dynamics.
Run from any directory with Python 3 (standard library only).
"""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]
COLORS = dict(BLOOM='#a7dc79', SPINE='#ffd44d', FRENZY='#ff8a80',
              RIPTIDE='#69b5ff', VOID='#b985ff', SWARM='#ffffff', TEETH='#ff912d')
FOLD = [0,.2135,.2691,.2240,.2986,.4132,.5851,.5660,.4583,.4193,.4931,.5556,
        .4583,.3220,.2552,.3142,.3750,.3186,.2170,.2240,.3958,.5122,.5243,
        .4748,.5556,.7378,.8837,.8733,.8333,.8602,.9427,1,1]
def clamp(x, lo=-1, hi=1): return max(lo, min(hi, x))
def tanh(x):
    v = abs(x)
    if v >= 8: return math.copysign(1, x)
    q = v*128; i = int(q); f = q-i
    return math.copysign(math.tanh(i/128)*(1-f)+math.tanh((i+1)/128)*f, x)
def sine(cycles):
    q = ((cycles+2) % 1)*2048; i = int(q); f = q-i
    return math.sin(2*math.pi*i/2048)*(1-f)+math.sin(2*math.pi*(i+1)/2048)*f
def triangle(cycles):
    f = (cycles+2) % 1
    return 4*f if f < .25 else 2-4*f if f < .75 else 4*f-4

def shape(name, x, chaos=0):
    if name == 'BLOOM': return tanh(5*x)/tanh(5)
    if name == 'SPINE':
        z = 10*x
        return z*(1.5-.5*z*z) if abs(z)<1 else math.copysign(1,z)
    if name in ('FRENZY','TEETH'):
        warped = x+.12*x*x*(1-x*x)
        wave = sine(2*warped) if name=='FRENZY' else triangle(2*warped)
        bias = .156554 if x>=0 else .014334
        return clamp(wave/1.5+bias*x*(1-x*x)+.75*x*abs(x))
    if name == 'RIPTIDE':
        z=2.5*x; v=abs(z)
        if v<1:
            q=v*32; i=int(q); f=q-i
            y=FOLD[i]*(1-f)+FOLD[i+1]*f
        else: y=1
        if v>1:
            f=(min(v-1,8)*4)%1
            y*=1-.06*(1-abs(2*f-1))
        return math.copysign(y,x)
    if name == 'VOID':
        v=abs(x)
        return math.copysign(min(1,math.floor(v/.05)*.125) if v<.4 else 1,x)
    if name == 'SWARM':
        z=5*max(.35,1+.6*chaos)*x
        y=clamp(tanh(z)/tanh(5))
        t=clamp((abs(z)-1)*2,0,1); gate=t*t*(3-2*t); unit=.5+.5*chaos
        y*=1-gate*.24*.6*(1-unit)
        y+=(math.copysign(1,x)-y)*.65*min(abs(y),1)**2*unit
        return clamp(y)
    raise ValueError(name)

def point(x,y): return f'{52+340*(x+1)/2:.3f},{28+204*(1-y)/2:.3f}'
def path(points): return 'M'+' L'.join(point(x,y) for x,y in points)
def samples(name):
    xs={-1+i/600 for i in range(1201)}
    if name=='VOID':
        # Bracket discontinuities so the steps remain vertical, not diagonal ramps.
        for i in range(-8,9):
            x=i*.05
            xs.update((x-1e-8,x,x+1e-8))
    return sorted(xs)

def render(name):
    color=COLORS[name]
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 294" role="img" aria-labelledby="title desc"><title id="title">{name} transfer curve at 100% Puff</title><desc id="desc">Input and shaped output from minus five to plus five volts. Colored line: fully wet shaping. Dashed diagonal: unchanged input.'+(' Shaded band: sampled SWARM variation; line: zero-chaos reference.' if name=='SWARM' else '')+'</desc>',
         '<rect width="420" height="294" rx="12" fill="#080e18"/>']
    for i in range(5):
        x=52+85*i;y=28+51*i
        color_grid='#536075' if i==2 else '#233044'
        svg.append(f'<path d="M{x} 28 V232 M52 {y} H392" fill="none" stroke="{color_grid}" stroke-width="1"/>')
    svg.append('<path d="M52 232 L392 28" stroke="#7d899a" stroke-dasharray="5 5" fill="none"/>')
    xs=samples(name)
    if name=='SWARM':
        bounds=[(x,min(shape(name,x,-1+j/40) for j in range(81)),max(shape(name,x,-1+j/40) for j in range(81))) for x in xs]
        band=[(x,lo) for x,lo,hi in bounds]+[(x,hi) for x,lo,hi in reversed(bounds)]
        svg.append(f'<path d="{path(band)} Z" fill="{color}" fill-opacity=".18"/>')
    svg.append(f'<path d="{path([(x,shape(name,x)) for x in xs])}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"/>')
    svg.append('<g fill="#afbed0" font-family="system-ui,sans-serif" font-size="12">')
    for x,label in [(52,'−5'),(222,'0'),(392,'+5')]:svg.append(f'<text x="{x}" y="252" text-anchor="middle">{label}</text>')
    for y,label in [(32,'+5'),(134,'0'),(236,'−5')]:svg.append(f'<text x="42" y="{y}" text-anchor="end">{label}</text>')
    svg.append('<text x="222" y="276" text-anchor="middle">Input (V)</text><text transform="translate(16 130) rotate(-90)" text-anchor="middle">Shaped output (V)</text></g></svg>')
    return '\n'.join(svg)

if __name__=='__main__':
    for name in COLORS:
        (ROOT/'manuals/img'/f'Puffy_{name.title()}_Curve.svg').write_text(render(name)+'\n')
