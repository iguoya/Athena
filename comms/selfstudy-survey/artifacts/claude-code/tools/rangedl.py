import sys,urllib.request,time
url,out,total=sys.argv[1],sys.argv[2],int(sys.argv[3])
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'
buf=bytearray(); tries=0
while len(buf)<total and tries<400:
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Range':f'bytes={len(buf)}-{min(len(buf)+65535,total-1)}'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            d=r.read()
            if r.status==200 and len(buf)>0: raise RuntimeError('range ignored')
            if r.status==200: buf=bytearray(d[:total]); 
            else: buf+=d
    except Exception as e:
        tries+=1; time.sleep(1); continue
print(len(buf),total,tries)
open(out,'wb').write(buf)
