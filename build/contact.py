import sys, os
from PIL import Image, ImageDraw
n=sys.argv[1]; prev=f"build/preview_b{n}"; import re; files=sorted(os.listdir(prev), key=lambda f: int(re.sub(r"[^0-9]","",f) or 0))
imgs=[Image.open(os.path.join(prev,f)).convert("RGB") for f in files]
cols=8; tw=150; th=int(imgs[0].size[1]*tw/imgs[0].size[0]); rows=(len(imgs)+cols-1)//cols; pad=4
s=Image.new("RGB",(cols*tw+(cols+1)*pad, rows*th+(rows+1)*pad),"#c8c8c8"); d=ImageDraw.Draw(s)
for i,im in enumerate(imgs):
    r,c=divmod(i,cols); x=pad+c*(tw+pad); y=pad+r*(th+pad); s.paste(im.resize((tw,th)),(x,y)); d.text((x+2,y+2),str(i+1),fill="red")
s.save(f"build/b{n}_contact.png"); print(len(imgs))
