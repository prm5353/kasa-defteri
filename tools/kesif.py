# Harem canlı fiyat soketini ve farklı Origin'lerle bağlanılıp bağlanılamadığını dener.
import re, json, time, urllib.request, ssl
import websocket  # websocket-client
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30);return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except Exception as e: return getattr(e,'code',0),str(e),{}
s,t,h=get("https://www.haremaltin.com/assets/js/socket.io/dist/socket.io.js")
print("SIOVER",re.findall(r'Socket\.IO v[0-9.]+|"version":"[0-9.]+"|protocol\s*=\s*\d',t)[:5])
s,t,h=get("https://www.haremaltin.com/assets/js/functions.js")
for m in re.findall(r'.{0,120}(?:io\(|io\.connect|hrmsocket|canlipiyasalar|price_changed).{0,160}',t): print("FN",m.replace('\n',' ')[:280])
s,t,h=get("https://canlipiyasalar.haremaltin.com/")
print("CANLI",s,t[:300].replace('\n',' '))
for path in ["/socket.io/?EIO=4&transport=polling","/socket.io/?EIO=3&transport=polling"]:
    for org in ["https://www.haremaltin.com","https://prm5353.github.io"]:
        try:
            r=urllib.request.urlopen(urllib.request.Request("https://hrmsocketonly.haremaltin.com"+path,headers={**H,"Origin":org}),timeout=20)
            print("POLL",path,org,r.status,r.headers.get('Access-Control-Allow-Origin'),r.read()[:200])
        except Exception as e: print("POLL",path,org,getattr(e,'code',e))
for eio in (4,3):
    for org in ["https://prm5353.github.io","https://www.haremaltin.com"]:
        try:
            ws=websocket.create_connection(f"wss://hrmsocketonly.haremaltin.com/socket.io/?EIO={eio}&transport=websocket",origin=org,header=["User-Agent: "+H["User-Agent"]],timeout=15)
            print("WS",eio,org,"open",ws.recv()[:150])
            ws.send("40")
            t0=time.time();n=0
            while time.time()-t0<12 and n<6:
                m=ws.recv();n+=1
                if m=="2": ws.send("3");continue
                print("MSG",eio,org,m[:1500])
            ws.close()
        except Exception as e: print("WS",eio,org,"ERR",e)
