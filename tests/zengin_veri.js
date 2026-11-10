/* test: tutarlılık kontrolü için örnek kayıtlar (gerçek kişisel veri değil) */
(async()=>{
 await put({id:'a2',k:'account',name:'Ziraat',balance:10000,balanceAt:1,ts:1});
 await put({id:'rmaas',k:'rec',name:'Maaş',amount:80000,day:15,dir:'gelir',account:'Banka',ts:1});
 await put({id:'rkredi',k:'rec',name:'İhtiyaç kredisi',amount:15000,day:20,dir:'gider',account:'Banka',count:24,ts:1});
 await put({id:'d1',k:'debt',who:'Ali',dir:'alacak',amount:2000,cur:'TRY',ts:1});
 await saveTx([
  {id:'i1',type:'gelir',amount:80000,date:'2026-10-15',account:'Banka',source:'Maaş',recId:'rmaas',ts:11},
  {id:'i2',type:'gelir',amount:50000,date:'2026-11-03',account:'Banka',source:'Araç satışı',ts:12},
  {id:'i3',type:'gelir',amount:7000,date:'2026-11-04',account:'Banka',source:'Ticari gelir',ts:13},
  {id:'e1',type:'gider',amount:3000,date:'2026-11-02',account:'Banka',personId:'me',category:'Araç',sub:'',merchant:'Servis',ts:14},
  {id:'e2',type:'gider',amount:4000,date:'2026-11-06',account:'Banka',personId:'me',category:'Ticari',sub:'',merchant:'Toptancı',ts:15},
  {id:'e3',type:'gider',amount:1000,date:'2026-11-06',cardId:'c1',personId:'me',category:'Ticari',sub:'',merchant:'Kırtasiye',ts:16},
  {id:'e4',type:'gider',amount:20000,date:'2026-11-08',cardId:'c1',personId:'p1',category:'',sub:'',merchant:'Fatih alışveriş',ts:17},
  {id:'e5',type:'gider',amount:2500,date:'2026-10-12',account:'Banka',personId:'me',category:'Diğer',sub:'',merchant:'Nakit diğer',ts:18},
  {id:'e6',type:'gider',amount:1500,date:'2026-11-07',account:'Banka',personId:'me',category:'Diğer',sub:'',merchant:'Nakit diğer2',ts:19},
  {id:'p1t',type:'tahsilat',amount:5000,date:'2026-11-09',account:'Banka',personId:'p1',merchant:'Fatih ödedi',ts:20},
  {id:'tr1',type:'transfer',amount:7000,date:'2026-11-09',account:'Banka',toAccount:'Ziraat',ts:21},
  {id:'tr2',type:'transfer',amount:10000,date:'2026-11-09',account:'Banka',toCardId:'c1',ts:22},
 ]);
 const I={...(S.catIcons||{}),__non:['Araç'],__nonInc:['Araç satışı']};await saveCatAll(catTree(),I);
})()
