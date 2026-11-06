// Copyright (c) 2026 Christian Reitwiessner. Apache-2.0. Authors: Christian Reitwiessner.
'use strict';
const labels = {'main-results':'Main coverage approved',partial:'Partial formalization',obstruction:'Claim obstruction',existing:'Existing formalization recorded','not-assessed':'Not assessed'};
const $ = id => document.getElementById(id);
let papers = [], limit = 30;
let dashboard;
function node(tag, text, cls) { const el = document.createElement(tag); if(text !== undefined) el.textContent = text; if(cls) el.className = cls; return el; }
function link(text, url) { const a = node('a', text); a.href = url; return a; }
function workflow(p) {
  if(p.coverage === 'not-assessed') return {value:0,label:'Not assessed'};
  if(p.coverage === 'existing') return {value:1,label:'Existing work recorded'};
  if(p.coverage === 'main-results') return p.pr_observation?.state === 'merged' ? {value:4,label:'Main coverage approved · merged'} : {value:3,label:'Main coverage approved · integration pending'};
  return {value:2,label:p.coverage === 'obstruction' ? 'Proof recorded · claim obstruction' : 'Proof recorded · main coverage incomplete'};
}
function progressBar(value,max,label) {
  const box=node('div',undefined,'progress-box');
  const bar=node('progress');bar.max=max;bar.value=value;bar.setAttribute('aria-label',label);
  box.append(bar,node('span',label,'progress-label'));return box;
}
function overview() {
  const approved=papers.filter(p=>p.coverage==='main-results').length;
  $('overall-progress').append(progressBar(approved,papers.length,`${approved} / ${papers.length.toLocaleString()} submissions with independently approved main coverage (${(100*approved/papers.length).toFixed(2)}%)`));
  const fragment=document.createDocumentFragment();
  for(const p of papers){const box=node('button',String(p.id),`submission-box ${p.coverage}`);box.type='button';box.title=`Submission ${p.id}: ${p.title} — ${labels[p.coverage]}`;box.setAttribute('aria-label',box.title);box.addEventListener('click',()=>openPaper(p));fragment.append(box);}
  $('submission-map').append(fragment);
}
function render() {
  const term = $('search').value.trim().toLocaleLowerCase(), filter = $('coverage').value;
  let matches = papers.filter(p => (filter === 'all' || (filter === 'tracked' ? p.coverage !== 'not-assessed' : p.coverage === filter)) && `${p.id} ${p.title} ${p.authors} ${p.area}`.toLocaleLowerCase().includes(term));
  const order=$('sort').value;
  matches.sort((a,b)=>order==='title'?a.title.localeCompare(b.title):order==='lines'?(b.source?.lines??-1)-(a.source?.lines??-1)||a.id-b.id:a.id-b.id);
  const fragment=document.createDocumentFragment();
  for(const p of matches){
    const row=node('tr',undefined,'paper-row');row.id=`submission-${p.id}`;
    row.addEventListener('click',event=>{if(!event.target.closest('a,button'))openPaper(p);});
    const number=node('td');const zoom=node('button',String(p.id),'paper-id');zoom.type='button';zoom.setAttribute('aria-label',`Explore submission ${p.id}`);zoom.addEventListener('click',()=>openPaper(p));number.append(zoom);
    const title=node('td');const name=node('button',p.title,'paper-title');name.type='button';name.addEventListener('click',()=>openPaper(p));title.append(name,node('div',p.authors,'authors'),node('div',p.area,'area'));
    const status=node('td');status.append(node('span',labels[p.coverage],`badge ${p.coverage}`));
    if(p.pr_observation)status.append(node('div',`CI: ${p.pr_observation.checks}`,'cell-note'));
    const prog=node('td');const stage=workflow(p);prog.append(progressBar(stage.value,4,`${stage.value}/4 workflow milestones`),node('div',stage.label,'cell-note'));
    const lines=node('td',p.source?p.source.lines.toLocaleString():'—','numeric');if(p.source)lines.append(node('div',`${p.source.files} files`,'cell-note'));
    const resource=node('td');resource.append(node('div',`Time: ${duration(p.resources?.recorded_seconds)}`),node('div',`Tokens: ${p.resources?.tokens==null?'unknown':p.resources.tokens.toLocaleString()}`,'cell-note'));
    const links=node('td',undefined,'table-links');links.append(link('PDF ↗',p.paper_url));if(p.pr)links.append(link(`PR ${p.pr} ↗`,`https://github.com/cslib-community/complexitylib/pull/${p.pr}`));
    row.append(number,title,status,prog,lines,resource,links);fragment.append(row);
  }
  $('papers').replaceChildren(fragment);
  $('results').textContent=`${matches.length.toLocaleString()} matching submissions · all matching rows shown · click a box, ID or title to explore`;
}
for(const id of ['search','coverage','sort'])$(id).addEventListener(id==='search'?'input':'change',render);
fetch('data.json').then(r=>{if(!r.ok)throw new Error(`Snapshot HTTP ${r.status}`);return r.json();}).then(data=>{
  dashboard=data;papers=data.papers;renderResources(data);overview();
  const counts=[['Catalogue submissions',papers.length],['Main coverage approved',papers.filter(p=>p.coverage==='main-results').length],['Partial formalizations',papers.filter(p=>p.coverage==='partial').length],['Claim obstructions',papers.filter(p=>p.coverage==='obstruction').length]];
  for(const [name,value] of counts){const stat=node('div',undefined,'stat');stat.append(node('strong',value.toLocaleString()),node('span',name));$('summary').append(stat);}
  $('freshness').textContent=`Snapshot ${new Date(data.generated_at).toLocaleString()} · coverage record ${data.registry_updated}${data.github_observed ? '' : ' · offline build'}`;
  render();
}).catch(error=>{$('freshness').textContent='Snapshot unavailable';$('results').textContent=`Could not load the status snapshot: ${error.message}. Please reload or consult the tracking issue.`;$('results').className='error';});

function duration(seconds) { return seconds == null ? 'Unknown' : `${(seconds/3600).toFixed(2)} h`; }
function metric(name,value) { const el=node('div');el.append(node('strong',value),node('span',name));return el; }
function renderResources(data) {
  const resources=data.papers.map(p=>p.resources).filter(Boolean);
  const events=resources.flatMap(r=>r.measurements);
  const recorded=events.filter(e=>e.total_tokens != null);
  const seconds=resources.reduce((sum,r)=>sum+(r.recorded_seconds ?? 0),0);
  const budget=data.project_budget;
  $('resource-summary').append(metric('Recorded task wall time',events.length ? duration(seconds) : 'Unknown'),metric(`Tokens · ${recorded.length}/${events.length} tasks measured`,recorded.length ? recorded.reduce((sum,e)=>sum+e.total_tokens,0).toLocaleString() : 'Unknown'),metric('Project time budget',budget.time_hours == null ? 'Not set' : `${budget.time_hours} h`),metric('Project token budget',budget.tokens == null ? 'Not set' : budget.tokens.toLocaleString()));
}
function openPaper(p) {
  const container=$('paper-detail');container.replaceChildren();
  container.append(node('div',`SUBMISSION ${p.id}`,'eyebrow'),node('h2',p.title),node('p',p.authors),link('Read the paper PDF ↗',p.paper_url),node('p',p.scope || 'This submission has not yet been assessed in this tracker.'),node('p',p.remaining ? `Remaining / limitations: ${p.remaining}` : 'No formalization status is recorded. This does not establish that no formalization exists elsewhere.','remaining'));
  const stage=workflow(p);container.append(progressBar(stage.value,4,`${stage.value}/4 workflow milestones · ${stage.label}`));
  const res=p.resources;
  if(res) {
    const ledger=node('section',undefined,'ledger');ledger.append(node('h3','Resource ledger'),node('p',`Recorded task wall time: ${duration(res.recorded_seconds)} across ${res.recorded_tasks} recorded tasks.`),node('p',`Measured tokens: ${res.tokens == null ? 'Unknown' : res.tokens.toLocaleString()} · ${res.token_coverage}.`),node('p',`Time budget: ${res.budget.time_hours == null ? 'not set' : `${res.budget.time_hours} h`}. Token budget: ${res.budget.tokens == null ? 'not set' : res.budget.tokens.toLocaleString()}.`));
    for(const event of res.measurements){ledger.append(node('p',`${event.label}: ${event.started_at} → ${event.finished_at}. Tokens: ${event.total_tokens == null ? 'unknown' : event.total_tokens}.`));}
    container.append(ledger);
  }
  if(!p.source){container.append(node('p','No theorem declarations are indexed for this paper yet.'));$('paper-dialog').showModal();return;}
  container.append(node('h3','Theorem explorer'),node('p','Declarations extracted from the explicitly scoped source files, including supporting lemmas. This index is not a list of independently classified main results. Links point to the exact counted revision. Full Lean statements and proofs are authoritative.','result-note'));
  const input=node('input');input.type='search';input.placeholder='Search theorem name, statement or source path';input.setAttribute('aria-label','Search formalized theorems');input.className='detail-controls';container.append(input);
  const results=node('div');container.append(results);let shown=25;
  const more=node('button','Show more theorems');more.type='button';container.append(more);
  function show(){const term=input.value.toLocaleLowerCase();const matches=p.source.results.filter(r=>`${r.name} ${r.file} ${r.statement}`.toLocaleLowerCase().includes(term));results.replaceChildren(node('p',`${matches.length} matching declarations`,'result-note'));for(const r of matches.slice(0,shown)){const article=node('article',undefined,'result');const h=node('h3');h.append(link(r.name+' ↗',r.url));article.append(h,node('p',`${r.file}:${r.line}`,'result-note'),node('pre',r.statement));results.append(article);}more.hidden=matches.length<=shown;}
  input.addEventListener('input',()=>{shown=25;show();});more.addEventListener('click',()=>{shown+=50;show();});show();
  $('paper-dialog').showModal();
}
$('close-dialog').addEventListener('click',()=>$('paper-dialog').close());
