const num=v=>{const n=parseFloat(String(v).replace(',','.'));return isNaN(n)?0:n};
const KUR_WS='wss://hrmsocketonly.haremaltin.com/socket.io/?EIO=4&transport=websocket';
const KUR_MAP={gram:'KULCEALTIN',ceyrek:'CEYREK_YENI',usd:'USDTRY',eur:'EURTRY'};

function kurFetch(){return new Promise((res,rej)=>{let ws;const got={};const done=()=>{try{ws&&ws.close()}catch(e){}};
  const to=setTimeout(()=>{done();Object.keys(got).length?res(got):rej(new Error('zaman aşımı'))},15000);
  try{ws=new WebSocket(KUR_WS)}catch(e){clearTimeout(to);rej(e);return}
  ws.onerror=()=>{clearTimeout(to);done();Object.keys(got).length?res(got):rej(new Error('bağlanamadı'))};
  ws.onmessage=ev=>{const m=String(ev.data);if(m[0]==='0'){ws.send('40');return}if(m==='2'){ws.send('3');return}
    if(m.startsWith('42')){try{const [ename,payload]=JSON.parse(m.slice(2));if(ename!=='price_changed')return;const d=payload?.data||{};
      Object.entries(KUR_MAP).forEach(([k,code])=>{const v=num(d[code]?.alis);if(v>0)got[k]={v,t:d[code].tarih||''}});
      if(Object.keys(KUR_MAP).every(k=>got[k])){clearTimeout(to);done();res(got)}}catch(e){}}}})}

kurFetch().then(r=>{console.log('OK',JSON.stringify(r));process.exit(0)},e=>{console.log('FAIL',e.message);process.exit(1)});
