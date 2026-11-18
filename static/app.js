const $=id=>document.getElementById(id);
const guildName={enemy:"Vanguard",ally:"Chora pra Warning",unknown:"Não identificado"};
function formatDate(value){if(!value)return "—";const d=new Date(value);return Number.isNaN(d.getTime())?"—":d.toLocaleString("pt-BR")}
function esc(value){return String(value??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
async function load(){
 const [s,d]=await Promise.all([fetch("/api/summary"),fetch("/api/deaths?limit=150")]);
 if(s.status===401||d.status===401){location.href="/login";return}
 const summary=await s.json(),deaths=await d.json();
 ["total","enemy","ally","unknown"].forEach(k=>$(k).textContent=summary[k]??0);
 $("deaths").innerHTML=deaths.length?deaths.map(x=>'<tr><td><strong>'+esc(x.victim)+'</strong></td><td>'+esc(x.level??"—")+'</td><td><span class="tag '+esc(x.guild)+'">'+esc(guildName[x.guild]||guildName.unknown)+'</span></td><td>'+esc(x.killer||"—")+'</td><td>'+esc(formatDate(x.happened_at||x.created_at))+'</td></tr>').join(""):'<tr><td colspan="5" class="empty">Nenhuma morte registrada ainda.</td></tr>';
}
function connect(){
 const scheme=location.protocol==="https:"?"wss":"ws";const ws=new WebSocket(scheme+"://"+location.host+"/ws");
 ws.onopen=()=>{$("connection").textContent="Monitor conectado";$("connection").style.color="var(--green)"};
 ws.onclose=()=>{$("connection").textContent="Reconectando...";$("connection").style.color="var(--muted)";setTimeout(connect,4000)};
 ws.onerror=()=>ws.close();ws.onmessage=()=>load();
}
$("refresh").addEventListener("click",load);load().catch(()=>{});connect();setInterval(()=>load().catch(()=>{}),30000);
