const policies=[
  {id:"POL-RET-001",category:"damaged product",title:"Damaged Product Evidence and Review",updated:"2026-07-15",priority:"medium",sla:240,owner:"Returns Support",keywords:["damaged","broken","leaking","crushed","photo evidence"],escalate:["chargeback","media complaint","third complaint"],evidence:["order number","clear photo or video of the damage"]},
  {id:"POL-DEL-002",category:"delivery delay",title:"Delivery Delay Investigation",updated:"2026-07-18",priority:"medium",sla:120,owner:"Logistics Support",keywords:["delivery delay","late delivery","tracking","not arrived","parcel delayed"],escalate:["medicine","event deadline","chargeback"],evidence:["order number","latest tracking status"]},
  {id:"POL-SAFE-003",category:"safety concern",title:"Product Safety Incident Escalation",updated:"2026-07-22",priority:"critical",sla:15,owner:"Duty Manager",keywords:["allergic","injury","unsafe","contamination","became sick","safety concern"],escalate:["hospital","police","public post"],evidence:["order number if available","product batch or package photo","concise incident description"]},
  {id:"POL-REF-004",category:"refund request",title:"Refund Eligibility Review",updated:"2026-07-12",priority:"low",sla:480,owner:"Billing Support",keywords:["refund","money back","cancel order","return payment"],escalate:["fraud","chargeback","legal action"],evidence:["order number","reason for the refund request"]}
];
const trace=[
  ["validate_ticket","Validate ticket identity, channel and message."],
  ["redact_sensitive_data","Remove selected sensitive text before policy matching."],
  ["classify_issue","Match the sanitized ticket to explicit policy keywords."],
  ["retrieve_policy","Attach the approved policy, evidence and service deadline."],
  ["route_handoff","Route critical or explicitly escalated cases to a human owner."]
];
const escapeHtml=value=>String(value).replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);

function triage(message){
  const lower=message.toLowerCase();
  const ranked=policies.map(policy=>({...policy,matched:policy.keywords.filter(word=>lower.includes(word))})).filter(policy=>policy.matched.length).sort((a,b)=>b.matched.length-a.matched.length||a.id.localeCompare(b.id));
  const policy=ranked[0];
  if(!policy)return {status:"no policy",category:"unknown",priority:"needs review",sla:"—",handoff:true,owner:"Support Lead",reason:"No approved policy matched",response:"I do not have an approved policy for this request. A human support lead must review it before a reply is sent."};
  const escalations=policy.escalate.filter(word=>lower.includes(word));
  const handoff=policy.priority==="critical"||escalations.length>0;
  return {...policy,status:handoff?"escalated":"triaged",priority:policy.priority==="critical"?"critical":escalations.length?"high":policy.priority,handoff,reason:policy.priority==="critical"?"Critical policy":escalations.join(", ")||"Routine queue",response:`Thank you for reporting this. Under ${policy.id}, please provide ${policy.evidence.join(", ")}. A human reviewer will confirm the next action.`};
}

function render(){
  const result=triage(document.getElementById("message").value);
  document.getElementById("run-status").textContent="Triage complete";
  const chip=document.getElementById("decision-chip");chip.textContent=result.status;chip.className=`decision-chip ${result.status.replace(" ","-")}`;
  document.getElementById("category").textContent=result.category;
  document.getElementById("priority").textContent=result.priority;
  document.getElementById("sla").textContent=result.sla==="—"?"Not set":`${result.sla} minutes`;
  document.getElementById("handoff-required").textContent=result.handoff?"Required":"Routine review";
  document.getElementById("owner").textContent=result.owner;
  document.getElementById("reason").textContent=result.reason;
  document.getElementById("response").textContent=result.response;
  document.getElementById("policy-card").innerHTML=result.id?`<div class="policy-meta">${result.id} · updated ${result.updated}</div><h3>${result.title}</h3><p>Matched terms: ${result.matched.map(escapeHtml).join(", ")}. The response remains subject to human review.</p><div class="evidence-list">${result.evidence.map(item=>`<span>${escapeHtml(item)}</span>`).join("")}</div>`:`<div class="empty">No approved policy matched. The Agent abstained and prepared a support-lead handoff.</div>`;
  document.getElementById("trace-list").innerHTML=trace.map(([tool,purpose],index)=>`<li><strong>${tool}</strong> — ${index===3&&!result.id?"Stopped: no policy evidence.":purpose}</li>`).join("");
}

document.getElementById("run-button").addEventListener("click",render);
document.querySelectorAll("[data-message]").forEach(button=>button.addEventListener("click",()=>{document.getElementById("message").value=button.dataset.message;render();}));
render();
