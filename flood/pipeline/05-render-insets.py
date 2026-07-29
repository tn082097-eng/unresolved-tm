import numpy as np, math, pickle, warnings, json, rasterio
warnings.filterwarnings('ignore')
from rasterio.warp import transform as wt
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
SP="/tmp/claude-0/-home-user-unresolved-tm/f33d53a4-bd75-53cd-ab64-ac188271f1df/scratchpad"
B="/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/NY_ColumbiaRensselaer_2016_C18/TIFF/USGS_1M_18_{}_NY_ColumbiaRensselaer_2016_C18.tif"
hand=np.load(f'{SP}/hand_clean.npy')
minX,maxX,minY,maxY,RES,GW,GH=[float(v) for v in open(f'{SP}/grid.txt').read().split()]; GW,GH=int(GW),int(GH)
feats=pickle.load(open(f"{SP}/nhd_feats.pkl",'rb'))
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def read_1m(lon,lat,half=1500):
    X,Y=[v[0] for v in wt('EPSG:4326','EPSG:26918',[lon],[lat])]
    x0,x1,y0,y1=X-half,X+half,Y-half,Y+half
    n=int(2*half); out=np.full((n,n),np.nan,np.float32)
    for xi in range(int(math.floor(x0/10000)),int(math.floor(x1/10000))+1):
        for yi in range(int(math.ceil(y0/10000)),int(math.ceil(y1/10000))+1):
            try: ds=rasterio.open(B.format(f"x{xi}y{yi}"))
            except Exception: continue
            with ds:
                b=ds.bounds
                ix0,ix1=max(x0,b.left),min(x1,b.right); iy0,iy1=max(y0,b.bottom),min(y1,b.top)
                if ix0>=ix1 or iy0>=iy1: continue
                c0,c1=int(round(ix0-x0)),int(round(ix1-x0)); r0,r1=int(round(y1-iy1)),int(round(y1-iy0))
                a=ds.read(1,window=from_bounds(ix0,iy0,ix1,iy1,ds.transform),out_shape=(r1-r0,c1-c0),
                          boundless=True,fill_value=ds.nodata).astype(np.float32)
                a[a<=-9999]=np.nan
                blk=out[r0:r1,c0:c1]; m=np.isnan(blk)&~np.isnan(a); blk[m]=a[m]
    return out,(x0,x1,y0,y1)

def hand_window(x0,x1,y0,y1,n):
    """nearest-neighbour sample the 10 m regional HAND onto the 1 m window grid"""
    cols=((x0+np.arange(n)+0.5)-minX)/RES
    rows=(maxY-(y1-np.arange(n)-0.5))/RES
    ci=np.clip(cols.astype(int),0,GW-1); ri=np.clip(rows.astype(int),0,GH-1)
    return hand[np.ix_(ri,ci)]

def hillshade(z,res=1.0,az=315,alt=40,ve=2.2):
    zz=np.where(np.isnan(z),np.nanmin(z),z)*ve
    gy,gx=np.gradient(zz,res); s=np.arctan(np.hypot(gx,gy)); asp=np.arctan2(-gx,gy)
    a,l=np.radians(az),np.radians(alt)
    return np.clip(np.sin(l)*np.cos(s)+np.cos(l)*np.sin(s)*np.cos(a-asp),0,1)

def make(title,note,lon,lat,creeks,out,half=1500,marks=()):
    z,(x0,x1,y0,y1)=read_1m(lon,lat,half); n=z.shape[0]
    hw=hand_window(x0,x1,y0,y1,n)
    hw=ndimage.uniform_filter(np.where(np.isfinite(hw),hw,99.0),size=9)
    hs=hillshade(z); g=34+hs*152
    rgb=np.dstack([g*0.99,g*0.97,g*0.92]).astype(np.float64)
    for thr,col,al in ((5.0,[104,150,186],0.38),(3.0,[86,150,206],0.50),
                       (2.0,[74,158,222],0.64),(1.0,[92,196,244],0.80)):
        m=np.isfinite(hw)&(hw<=thr)&np.isfinite(z)
        for k in range(3): rgb[:,:,k][m]=(1-al)*rgb[:,:,k][m]+al*col[k]
    rgb[~np.isfinite(z)]=[22,28,36]
    img=Image.fromarray(rgb.astype(np.uint8)); d=ImageDraw.Draw(img)
    # draw each NHD segment separately - concatenating disjoint segments would
    # connect the end of one to the start of the next with a false straight line
    for cname in creeks:
        for nm,ft,ps in feats:
            if nm!=cname or len(ps)<2: continue
            X,Y=wt('EPSG:4326','EPSG:26918',[p[0] for p in ps],[p[1] for p in ps])
            seg=[(X_-x0, y1-Y_) for X_,Y_ in zip(X,Y)]
            if all(p[0]<-40 or p[0]>n+40 or p[1]<-40 or p[1]>n+40 for p in seg): continue
            if len(seg)>1: d.line(seg,fill=(232,246,255),width=5,joint="curve")
    f=ImageFont.truetype(BOLD,36); fm=ImageFont.truetype(MONO,25)
    def halo(xy,t,ft,fill=(255,255,255)):
        for dx,dy in ((-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)):
            d.text((xy[0]+dx,xy[1]+dy),t,font=ft,fill=(6,10,14))
        d.text(xy,t,font=ft,fill=fill)
    for mlon,mlat,mlab in marks:
        X,Y=[v[0] for v in wt('EPSG:4326','EPSG:26918',[mlon],[mlat])]
        mx,my=X-x0,y1-Y
        d.ellipse([mx-42,my-42,mx+42,my+42],outline=(255,120,90),width=6)
        halo((mx+54,my-14),mlab,fm,fill=(255,180,150))
    d.rectangle([0,0,n,100],fill=(10,14,20))
    halo((24,14),title,f); halo((24,60),note,fm,fill=(188,208,226))
    d.rectangle([n-560,n-58,n-60,n-48],fill=(250,250,248),outline=(8,12,16),width=2)
    halo((n-560,n-92),"500 m",fm,fill=(250,250,248))
    halo((24,n-54),"blue = height above nearest drainage (<=1/2/3/5 m)",fm,fill=(204,224,240))
    img.resize((1100,1100),Image.LANCZOS).save(f"{SP}/{out}")
    fr=lambda t: float(100*np.nanmean(hw[np.isfinite(z)]<=t))
    print(f"{out}: HAND<=1m {fr(1):.1f}%  <=2m {fr(2):.1f}%  <=3m {fr(3):.1f}%")
    return dict(pct1=fr(1),pct2=fr(2),pct3=fr(3))

a=make("STOCKPORT CONFLUENCE","Kinderhook Ck + Claverack Ck -> Stockport Ck   1 m LiDAR hillshade",
       -73.7462,42.3110,["Stockport Creek","Kinderhook Creek","Claverack Creek"],"fig_confluence.png",
       marks=[(-73.7426,42.3134,"confluence, 1.1 m")])
b=make("AGAWAMUCK CORRIDOR AT PHILMONT","impoundment above the village and the confined channel below   1 m LiDAR hillshade",
       -73.6470,42.2478,["Agawamuck Creek"],"fig_philmont.png",half=1200)
json.dump({"confluence":a,"philmont":b},open(f"{SP}/inset_stats.json","w"),indent=1)
