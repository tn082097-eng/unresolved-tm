import json, pickle, numpy as np
from PIL import Image, ImageDraw, ImageFont
from rasterio.warp import transform as wt
from scipy import ndimage
SP="/tmp/claude-0/-home-user-unresolved-tm/f33d53a4-bd75-53cd-ab64-ac188271f1df/scratchpad"
dem=np.load(f'{SP}/dem10.npy'); hand=np.load(f'{SP}/hand_clean.npy'); acc=np.load(f'{SP}/acc.npy')
minX,maxX,minY,maxY,RES,W,H=[float(v) for v in open(f'{SP}/grid.txt').read().split()]; W,H=int(W),int(H)
feats=pickle.load(open(f"{SP}/nhd_feats.pkl",'rb'))
places=json.load(open(f'{SP}/places.json'))
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def to_px(lons,lats):
    X,Y=wt('EPSG:4326','EPSG:26918',list(lons),list(lats))
    return (np.array(X)-minX)/RES, (maxY-np.array(Y))/RES

def hillshade(z,res=10.0,az=315,alt=40,ve=1.6):
    zz=np.where(np.isnan(z),np.nanmin(z),z)*ve
    gy,gx=np.gradient(zz,res); s=np.arctan(np.hypot(gx,gy)); asp=np.arctan2(-gx,gy)
    a,l=np.radians(az),np.radians(alt)
    return np.clip(np.sin(l)*np.cos(s)+np.cos(l)*np.sin(s)*np.cos(a-asp),0,1)

def base(scale=2):
    hs=hillshade(dem)
    g=32+hs*150
    rgb=np.dstack([g*0.99,g*0.97,g*0.92]).astype(np.float64)
    # elevation warmth
    v=np.nan_to_num((dem-np.nanmin(dem))/(np.nanmax(dem)-np.nanmin(dem)))
    rgb[:,:,0]=np.clip(rgb[:,:,0]*(0.92+0.42*v),0,255)
    rgb[:,:,1]=np.clip(rgb[:,:,1]*(0.94+0.20*v),0,255)
    rgb[:,:,2]=np.clip(rgb[:,:,2]*(1.06-0.34*v),0,255)
    # HAND bands (flood susceptibility) - blue, brightest = most susceptible
    for thr,col,al in ((5.0,[104,150,186],0.42),(3.0,[ 86,150,206],0.55),
                       (2.0,[ 74,158,222],0.68),(1.0,[ 92,196,244],0.82)):
        m=np.isfinite(hand)&(hand<=thr)
        for k in range(3):
            rgb[:,:,k][m]=(1-al)*rgb[:,:,k][m]+al*col[k]
    nd=~np.isfinite(dem); rgb[nd]=[22,28,36]
    return Image.fromarray(rgb.astype(np.uint8))

img=base()
d=ImageDraw.Draw(img)
# NHD channels: width by name importance
MAIN={"Hudson River":6,"Stockport Creek":5,"Kinderhook Creek":4,"Claverack Creek":4,
      "Agawamuck Creek":3,"Taghkanic Creek":3}
for nm,ft,pts in feats:
    if len(pts)<2: continue
    xs,ys=to_px([p[0] for p in pts],[p[1] for p in pts])
    seg=list(zip(xs,ys))
    if nm in MAIN: d.line(seg,fill=(214,238,255),width=MAIN[nm],joint="curve")
    elif nm:      d.line(seg,fill=(150,196,226),width=2)
    else:         d.line(seg,fill=(120,164,196),width=1)

f_town=ImageFont.truetype(BOLD,26); f_ck=ImageFont.truetype(MONO,21)
f_note=ImageFont.truetype(MONO,19)
def halo(xy,txt,font,fill=(255,255,255),anchor="lm"):
    x,y=xy
    for dx,dy in ((-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)):
        d.text((x+dx,y+dy),txt,font=font,fill=(6,10,14),anchor=anchor)
    d.text((x,y),txt,font=font,fill=fill,anchor=anchor)

# creek labels at a representative vertex
lbl_at={"Stockport Creek":0.5,"Kinderhook Creek":0.35,"Claverack Creek":0.55,
        "Agawamuck Creek":0.5,"Taghkanic Creek":0.45,"Hudson River":0.30}
placed={}
for nm,frac in lbl_at.items():
    pts=[p for n2,ft,ps in feats if n2==nm for p in ps]
    if not pts: continue
    pts=sorted(pts,key=lambda p:-p[1])
    p=pts[int(len(pts)*frac)]
    xs,ys=to_px([p[0]],[p[1]])
    halo((xs[0]+10,ys[0]),nm.upper(),f_ck,fill=(200,232,255))
# towns
for n,la,lo in places:
    xs,ys=to_px([lo],[la]); x,y=xs[0],ys[0]
    if not(0<=x<W and 0<=y<H): continue
    d.ellipse([x-7,y-7,x+7,y+7],fill=(250,250,248),outline=(8,12,16),width=3)
    halo((x+14,y),n,f_town)
# measured confluence
cx,cy=to_px([-73.7426],[42.3134]); cx,cy=cx[0],cy[0]
d.ellipse([cx-52,cy-52,cx+52,cy+52],outline=(255,120,90),width=6)
d.line([(cx+40,cy-40),(cx+150,cy-150)],fill=(255,120,90),width=4)
halo((cx+158,cy-206),"CONFLUENCE - 1.1 m elevation",f_note,fill=(255,178,150))
halo((cx+158,cy-182),"Kinderhook Ck + Claverack Ck",f_note,fill=(255,178,150))
halo((cx+158,cy-158),"form Stockport Ck: 0.32 m/km",f_note,fill=(255,178,150))
halo((cx+158,cy-134),"3.6 km wide floodplain",f_note,fill=(255,178,150))

# legend
lx,ly=34,H-250
d.rectangle([lx-16,ly-22,lx+560,ly+212],fill=(10,14,20))
halo((lx,ly),"HEIGHT ABOVE NEAREST DRAINAGE",ImageFont.truetype(BOLD,23),fill=(240,244,248))
for i,(t,col) in enumerate([("<= 1 m  most susceptible",[92,196,244]),("<= 2 m",[74,158,222]),
                            ("<= 3 m",[86,150,206]),("<= 5 m",[104,150,186])]):
    yy=ly+40+i*34
    d.rectangle([lx,yy,lx+46,yy+22],fill=tuple(col))
    halo((lx+60,yy+11),t,f_note,fill=(226,234,242))
halo((lx,ly+186),"3DEP 1 m LiDAR (NY_ColumbiaRensselaer_2016) resampled to 10 m",
     ImageFont.truetype(MONO,17),fill=(150,168,186))
# scale bar 5 km
sbx,sby=W-420,H-70
d.rectangle([sbx,sby,sbx+500,sby+10],fill=(250,250,248),outline=(8,12,16),width=2)
halo((sbx,sby-22),"5 km",f_note,fill=(250,250,248))

img.save(f'{SP}/fig_region_full.png')
img.resize((1500,int(1500*H/W)),Image.LANCZOS).save(f'{SP}/fig_region.png')
print("wrote fig_region.png", img.size, "->", (1500,int(1500*H/W)))
