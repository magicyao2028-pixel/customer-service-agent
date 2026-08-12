const analysisDate="2026-08-12";
const policies=[
  {id:"POL-RET-000",category:"damaged product",title:"Legacy Damaged Product Review",updated:"2026-01-01",effective:"2026-01-01",reviewDue:"2026-12-31",supersedes:[],priority:"medium",sla:360,owner:"Returns Support",keywords:["damaged","broken","leaking","crushed","photo evidence"],escalate:["chargeback"],evidence:["order number","photo of the damage"]},
  {id:"POL-RET-001",category:"damaged product",title:"Damaged Product Evidence and Review",updated:"2026-07-15",effective:"2026-08-01",reviewDue:"2027-07-31",supersedes:["POL-RET-000"],priority:"medium",sla:240,owner:"Returns Support",keywords:["damaged","broken","leaking","crushed","photo evidence"],escalate:["chargeback","media complaint","third complaint"],evidence:["order number","clear photo or video of the damage"]},
  {id:"POL-DEL-002",category:"delivery delay",title:"Delivery Delay Investigation",updated:"2026-07-18",effective:"2026-08-01",reviewDue:"2027-07-31",supersedes:[],priority:"medium",sla:120,owner:"Logistics Support",keywords:["delivery delay","late delivery","tracking","not arrived","parcel delayed"],escalate:["medicine","event deadline","chargeback"],evidence:["order number","latest tracking status"]},
  {id:"POL-SAFE-003",category:"safety concern",title:"Product Safety Incident Escalation",updated:"2026-07-22",effective:"2026-08-01",reviewDue:"2027-07-31",supersedes:[],priority:"critical",sla:15,owner:"Duty Manager",keywords:["allergic","injury","unsafe","contamination","became sick","safety concern"],escalate:["hospital","police","public post"],evidence:["order number if available","product batch or package photo","concise incident description"]},
  {id:"POL-REF-004",category:"refund request",title:"Refund Eligibility Review",updated:"2026-07-12",effective:"2026-08-01",reviewDue:"2027-07-31",supersedes:[],priority:"low",sla:480,owner:"Billing Support",keywords:["refund","money back","cancel order","return payment"],escalate:["fraud","chargeback","legal action"],evidence:["order number","reason for the refund request"]}
];
const trace=[
  ["validate_ticket","Validate ticket identity, channel and message."],
  ["redact_sensitive_data","Remove selected sensitive text before policy matching."],
  ["classify_issue","Match the sanitized ticket to explicit policy keywords."],
  ["resolve_policy_version","Check category score, effective window and supersession."],
  ["retrieve_policy","Attach the approved current policy, evidence and service deadline."],
  ["route_handoff","Route exceptions and customer drafts to an authorized human."]
];
const escapeHtml=value=>String(value).replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);

function resolvePolicy(message){
  const lower=message.toLowerCase();
  const matched=policies.map(policy=>({...policy,matched:policy.keywords.filter(word=>lower.includes(word))})).filter(policy=>policy.matched.length);
  if(!matched.length)return {status:"no policy",candidateIds:[],excluded:[],reason:"No approved policy matched"};
  const categoryScores=new Map();
  matched.forEach(policy=>categoryScores.set(policy.category,Math.max(categoryScores.get(policy.category)||0,policy.matched.length)));
  const bestScore=Math.max(...categoryScores.values());
  const bestCategories=[...categoryScores.entries()].filter(([,score])=>score===bestScore).map(([category])=>category);
  const candidateIds=matched.filter(policy=>bestCategories.includes(policy.category)).map(policy=>policy.id);
  if(bestCategories.length>1)return {status:"policy conflict",candidateIds,excluded:[],reason:"Best policy categories tie"};
  const category=bestCategories[0];
  const versions=matched.filter(policy=>policy.category===category);
  const excluded=[];
  const current=versions.filter(policy=>{
    if(analysisDate<policy.effective){excluded.push({id:policy.id,reason:"not yet effective"});return false;}
    if(analysisDate>policy.reviewDue){excluded.push({id:policy.id,reason:"review overdue"});return false;}
    return true;
  });
  if(!current.length)return {status:"policy stale",category,candidateIds,excluded,reason:"No matching policy is inside its review window"};
  const superseded=new Set(current.flatMap(policy=>policy.supersedes));
  const remaining=current.filter(policy=>{
    if(superseded.has(policy.id)){excluded.push({id:policy.id,reason:"superseded"});return false;}
    return true;
  });
  if(remaining.length!==1)return {status:"policy conflict",category,candidateIds,excluded,reason:"Multiple current policy versions remain"};
  return {status:"selected",policy:remaining[0],category,candidateIds,excluded,reason:"One current unsuperseded policy selected"};
}

function triage(message){
  const resolution=resolvePolicy(message);
  const policy=resolution.policy;
  if(!policy)return {...resolution,category:resolution.category||"unknown",priority:"needs review",sla:"—",handoff:true,owner:"Support Lead",response:"I do not have one unambiguous current policy for this request. A human support lead must review it before a reply is sent."};
  const lower=message.toLowerCase();
  const escalations=policy.escalate.filter(word=>lower.includes(word));
  const handoff=policy.priority==="critical"||escalations.length>0;
  return {...resolution,...policy,status:handoff?"escalated":"triaged",priority:policy.priority==="critical"?"critical":escalations.length?"high":policy.priority,handoff,reason:policy.priority==="critical"?"Critical policy":escalations.join(", ")||"Routine queue",response:`Thank you for reporting this. Under ${policy.id}, please provide ${policy.evidence.join(", ")}. A human reviewer will confirm the next action.`};
}

function render(){
  const result=triage(document.getElementById("message").value);
  document.getElementById("run-status").textContent=`Resolved for ${analysisDate}`;
  const chip=document.getElementById("decision-chip");chip.textContent=result.status;chip.className=`decision-chip ${result.status.replaceAll(" ","-")}`;
  document.getElementById("category").textContent=result.category;
  document.getElementById("priority").textContent=result.priority;
  document.getElementById("sla").textContent=result.sla==="—"?"Not set":`${result.sla} minutes`;
  document.getElementById("handoff-required").textContent=result.handoff?"Required":"Routine review";
  document.getElementById("owner").textContent=result.owner;
  document.getElementById("reason").textContent=result.reason;
  document.getElementById("response").textContent=result.response;
  const resolutionLine=`Analysis date ${analysisDate} · candidates ${result.candidateIds.map(escapeHtml).join(", ")||"none"}${result.excluded.length?` · excluded ${result.excluded.map(item=>`${escapeHtml(item.id)} (${escapeHtml(item.reason)})`).join(", ")}`:""}`;
  document.getElementById("policy-card").innerHTML=result.id?`<div class="policy-meta">${escapeHtml(result.id)} · effective ${escapeHtml(result.effective)} · review due ${escapeHtml(result.reviewDue)}</div><h3>${escapeHtml(result.title)}</h3><p>${resolutionLine}</p><p>Matched terms: ${result.matched.map(escapeHtml).join(", ")}. The response remains subject to human review.</p><div class="evidence-list">${result.evidence.map(item=>`<span>${escapeHtml(item)}</span>`).join("")}</div>`:`<div class="empty"><strong>${escapeHtml(result.status)}</strong><br>${resolutionLine}<br>${escapeHtml(result.reason)}. The Agent abstained and prepared a support-lead handoff.</div>`;
  document.getElementById("trace-list").innerHTML=trace.map(([tool,purpose])=>`<li><strong>${tool}</strong> — ${tool==="retrieve_policy"&&!result.id?`Stopped: ${escapeHtml(result.status)}.`:purpose}</li>`).join("");
}

document.getElementById("run-button").addEventListener("click",render);
document.querySelectorAll("[data-message]").forEach(button=>button.addEventListener("click",()=>{document.getElementById("message").value=button.dataset.message;render();}));
render();
