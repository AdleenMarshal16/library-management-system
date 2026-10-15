
const $=s=>document.querySelector(s),dlg=$("#dlg"),day=n=>new Date(Date.now()+n*864e5).toISOString().slice(0,10),today=day(0);
const COL=["#c8553d","#4a7bd0","#3f9d6b","#e3a93b","#8a5cc2","#2f9bb0","#d0678f"];
const hue=s=>[...s].reduce((a,c)=>a+c.charCodeAt(0)*7,0)%360,esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const grad=t=>`linear-gradient(135deg,hsl(${hue(t)} 55% 45%),hsl(${(hue(t)+40)%360} 60% 30%))`;
const API=location.protocol=="file:"?"http://127.0.0.1:5000/api":"/api";
let S={authors:[],books:[],loans:[]},view="dash",q="",fg="";
const out=b=>S.loans.filter(l=>l.bookId==b.id&&!l.returned).length;
const genres=()=>[...new Set(S.books.map(b=>b.genre))].sort(),late=l=>!l.returned&&l.due<today;
const gcol=g=>COL[genres().indexOf(g)%COL.length];
function dash(){const issued=S.loans.filter(l=>!l.returned),od=issued.filter(late),total=S.books.reduce((a,b)=>a+b.copies,0);
 const gc=genres().map(g=>[g,S.books.filter(b=>b.genre==g).length]),mx=Math.max(...gc.map(x=>x[1]),1);
 let acc=0;const n=S.books.length||1,cone=gc.map(([g,c])=>{const s=acc;acc+=c/n*100;return`${gcol(g)} ${s}% ${acc}%`}).join(",");
 const top=S.authors.map(a=>[a.name,S.books.filter(b=>b.author==a.name).length]).sort((a,b)=>b[1]-a[1]).slice(0,5);
 return`<div class=head><div><h1>Dashboard</h1><p>Welcome back, ${esc(U.name.split(" ")[0])} — here's your library at a glance.</p></div><button class=p onclick="bookForm()">＋ Add book</button></div>
 <div class=cards>${[["Titles",S.books.length,"📚"],["Authors",S.authors.length,"✍️"],["Copies available",total-issued.length,"✅"],["Currently issued",issued.length,"🔖"],["Overdue",od.length,"⏰"]].map(k=>`<div class="box kpi"><i>${k[2]}</i><b>${k[1]}</b><span>${k[0]}</span></div>`).join("")}</div>
 <div class=two><div class=box><h3>Books by genre</h3>${gc.map(([g,c])=>`<div class=bar><em>${esc(g)}</em><div><i style="width:${c/mx*100}%;background:${gcol(g)}"></i></div><b>${c}</b></div>`).join("")}</div>
 <div class=box><h3>Collection mix</h3><div class=donut style="background:conic-gradient(${cone})"><div>${S.books.length}</div></div><div class=leg>${gc.map(([g])=>`<span><i style="background:${gcol(g)}"></i>${esc(g)}</span>`).join("")}</div></div></div>
 <div class=two><div class=box><h3 style="margin-bottom:8px">Recently added</h3><table>${S.books.slice(-5).reverse().map(b=>`<tr><td><div class=bk><div class=mini style="background:${grad(b.title)}"></div><div><b>${esc(b.title)}</b><br><small style="color:var(--mute)">${esc(b.author)}</small></div></div></td><td><span class=tag>${esc(b.genre)}</span></td></tr>`).join("")}</table></div>
 <div class=box><h3>Top authors</h3>${top.map(([a,c],i)=>`<div class=bar><em style="width:130px;overflow:hidden;white-space:nowrap">${esc(a)}</em><div><i style="width:${c/top[0][1]*100}%;background:${COL[i]}"></i></div><b>${c}</b></div>`).join("")}</div></div>`}
function books(){const l=S.books.filter(b=>(!q||(b.title+b.author).toLowerCase().includes(q))&&(!fg||b.genre==fg));
 return`<div class=head><div><h1>Books</h1><p>${S.books.length} titles in the catalogue</p></div><button class=p onclick="bookForm()">＋ Add book</button></div>
 <div class=tool><input id=q placeholder="Search title or author…" value="${esc(q)}" oninput="q=this.value.toLowerCase();render(1)"><select onchange="fg=this.value;render()"><option value="">All genres</option>${genres().map(g=>`<option ${g==fg?"selected":""}>${esc(g)}</option>`).join("")}</select></div>
 <div class=box style="padding:8px;overflow:auto"><table><tr><th>Book<th>Genre<th>Year<th>Availability<th></tr>${l.map(b=>{const a=b.copies-out(b);return`<tr><td><div class=bk><div class=mini style="background:${grad(b.title)}"></div><div><b>${esc(b.title)}</b><br><small style="color:var(--mute)">${esc(b.author)}</small></div></div><td><span class=tag>${esc(b.genre)}</span><td>${b.year}<td><span class="tag ${a?"ok":"out"}">${a}/${b.copies} available</span><td style="text-align:right;white-space:nowrap"><button class="g s" ${a?"":"disabled"} onclick="issue(${b.id})">Issue</button> <button class="g s" onclick="bookForm(${b.id})">Edit</button> ${U.role=="admin"?`<button class="g s" onclick="delBook(${b.id})">🗑</button>`:""}</tr>`}).join("")||`<tr><td colspan=5 class=empty>No books match.</tr>`}</table></div>`}
function authors(){return`<div class=head><div><h1>Authors</h1><p>${S.authors.length} authors in the library</p></div><button class=p onclick="authForm()">＋ Add author</button></div><div class=authors>${S.authors.map((a,i)=>{const bs=S.books.filter(b=>b.author==a.name);return`<div class=box><div class=av style="background:${COL[i%7]}">${esc(a.name[0])}</div><h3>${esc(a.name)}</h3><small>${esc(a.country)} · born ${a.born}</small><p>${esc(a.bio)}</p><span class=tag>${bs.length} book${bs.length==1?"":"s"}</span><p style="font-size:12.5px">${bs.map(b=>esc(b.title)).join(" · ")}</p></div>`}).join("")}</div>`}
function loans(){return`<div class=head><div><h1>Borrowings</h1><p>Track issued books and returns</p></div></div><div class=box style="padding:8px;overflow:auto"><table><tr><th>Book<th>Member<th>Issued<th>Due<th>Status<th></tr>${[...S.loans].reverse().map(l=>{const b=S.books.find(x=>x.id==l.bookId)||{title:"(deleted)"};return`<tr><td><b>${esc(b.title)}</b><td>${esc(l.member)}<td>${l.issued}<td>${l.due}<td><span class="tag ${l.returned?"ok":late(l)?"late":"out"}">${l.returned?"Returned":late(l)?"Overdue":"Issued"}</span><td>${l.returned?"":`<button class="g s" onclick="ret(${l.id})">Return</button>`}</tr>`}).join("")||`<tr><td colspan=6 class=empty>No borrowings yet.</tr>`}</table></div>`}
function render(keep){$("#main").innerHTML={dash,books,authors,loans}[view]();document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("on",b.dataset.v==view));if(keep){const i=$("#q");i.focus();i.setSelectionRange(99,99)}}
$("#nav").onclick=e=>{const v=e.target.closest("button")?.dataset.v;if(v){view=v;q=fg="";render()}};
function form(title,fields,vals,cb){$("#dt").textContent=title;$("#fields").innerHTML=fields.map(([k,l,t,o])=>`<label>${l}${t=="select"?`<select name=${k}>${o.map(x=>`<option ${x==vals[k]?"selected":""}>${esc(x)}</option>`).join("")}</select>`:t=="area"?`<textarea name=${k} rows=3>${esc(vals[k]||"")}</textarea>`:`<input name=${k} type=${t} value="${esc(vals[k]??"")}" required>`}</label>`).join("");
 $("#f").onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(e.target));try{await cb(d);dlg.close();load()}catch(x){alert(x.message)}};dlg.showModal()}
function bookForm(id){const b=S.books.find(x=>x.id==id)||{};form(id?"Edit book":"Add book",[["title","Title","text"],["author","Author","select",S.authors.map(a=>a.name)],["genre","Genre","text"],["year","Year","number"],["copies","Copies","number"]],b,d=>call(id?"PUT":"POST",id?"/books/"+id:"/books",d))}
function authForm(){form("Add author",[["name","Name","text"],["country","Country","text"],["born","Birth year","number"],["bio","Short bio","area"]],{},d=>call("POST","/authors",{...d,born:+d.born}))}
function issue(id){form("Issue book",[["member","Member name","text"],["due","Due date","date"]],{due:day(14)},d=>call("POST","/loans",{bookId:id,member:d.member,due:d.due}))}
async function ret(id){try{await call("POST","/loans/"+id+"/return");load()}catch(e){alert(e.message)}}
async function delBook(id){if(confirm("Delete this book?")){try{await call("DELETE","/books/"+id);load()}catch(e){alert(e.message)}}}

/* ---------- Authentication ---------- */
let U=null,mode="in";
const call=async(m,p,b)=>{const t=sessionStorage.athToken||localStorage.athToken;let r;
 try{r=await fetch(API+p,{method:m,headers:{"Content-Type":"application/json",...(t?{Authorization:"Bearer "+t}:{})},body:b&&JSON.stringify(b)})}catch{throw new Error("Cannot reach the server. Is the backend running?")}
 const d=await r.json().catch(()=>({}));if(r.status==401&&t&&!p.startsWith("/log")&&!p.startsWith("/reg"))logout();if(!r.ok)throw new Error(d.error||"Request failed");return d};
async function load(){try{S=await call("GET","/all");render()}catch(e){alert(e.message)}}
function loginUI(err=""){document.body.classList.remove("in");$("#login").innerHTML=`<div class=lc><div class=logo>Athenaeum<small>LIBRARY SYSTEM</small></div>
 <div class=tabs><button class="${mode=="in"?"on":""}" onclick="mode='in';loginUI()">Sign in</button><button class="${mode=="up"?"on":""}" onclick="mode='up';loginUI()">Create account</button></div>
 <form onsubmit="auth(event)">${mode=="up"?'<label>Full name<input id=an required></label>':""}<label>Username<input id=au required autocomplete=username></label><label>Password<input id=ap type=password required autocomplete=current-password></label>
 <label class=chk><input id=ar type=checkbox checked> Keep me signed in</label><p class=err>${esc(err)}</p><button class=p style="padding:11px">${mode=="in"?"Sign in":"Create account"}</button></form>
 ${mode=="in"?'<div class=hint>Demo: <b>admin</b> / admin123 &nbsp;·&nbsp; <b>staff</b> / staff123</div>':""}</div>`;($("#au")).focus()}
async function auth(e){e.preventDefault();const un=$("#au").value.trim(),pw=$("#ap").value;
 try{const d=await call("POST",mode=="in"?"/login":"/register",{username:un,password:pw,name:$("#an")?.value.trim()});
  sessionStorage.athToken=d.token;if($("#ar")?.checked)localStorage.athToken=d.token;U=d.user;enter()}catch(x){loginUI(x.message)}}
function enter(){document.body.classList.add("in");$("#login").innerHTML="";view="dash";q=fg="";
 $("#me").innerHTML=`<b>${esc(U.name)}</b><small>${U.role}</small><button onclick="logout()">Sign out</button>`;load()}
function logout(){sessionStorage.removeItem("athToken");localStorage.removeItem("athToken");U=null;mode="in";loginUI()}
(async()=>{if(sessionStorage.athToken||localStorage.athToken){try{U=(await call("GET","/me")).user;return enter()}catch{}}loginUI()})();
