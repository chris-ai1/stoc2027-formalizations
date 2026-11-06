// Copyright (c) 2026 Christian Reitwiessner. Apache-2.0. Authors: Christian Reitwiessner.
'use strict';
const labels = {'main-results':'Main coverage approved',partial:'Partial formalization',obstruction:'Claim obstruction',existing:'Existing formalization recorded','not-assessed':'Not assessed'};
const $ = id => document.getElementById(id);
let papers = [], limit = 30;
let dashboard;
function node(tag, text, cls) { const el = document.createElement(tag); if(text !== undefined) el.textContent = text; if(cls) el.className = cls; return el; }
function link(text, url) { const a = node('a', text); a.href = url; return a; }
function render() {
  const term = $('search').value.trim().toLocaleLowerCase(), filter = $('coverage').value;
  let matches = papers.filter(p => (filter === 'all' || (filter === 'tracked' ? p.coverage !== 'not-assessed' : p.coverage === filter)) && `${p.id} ${p.title} ${p.authors} ${p.area}`.toLocaleLowerCase().includes(term));
  const order = $('sort').value;
  matches.sort((a,b) => order === 'title' ? a.title.localeCompare(b.title) : order === 'lines' ? (b.source?.lines ?? -1) - (a.source?.lines ?? -1) || a.id-b.id : a.id-b.id);
  $('papers').replaceChildren();
  for (const p of matches.slice(0,limit)) {
    const row = node('article',undefined,'paper'); row.id = `submission-${p.id}`;
    const number = node('div','SUBMISSION','number'); number.append(node('strong',String(p.id)));
    const body = node('div'); body.append(node('span', labels[p.coverage],`badge ${p.coverage}`),node('h3',p.title),node('p',p.authors,'authors'),node('span',p.area,'area'));
    if(p.scope) body.append(node('p',p.scope,'scope'),node('p',`Limits / remaining: ${p.remaining}`,'remaining'));
    const links = node('div',undefined,'links'); links.append(link('Paper ↗',p.paper_url));
    if(p.pr) links.append(link(`PR ${p.pr} ↗`,`https://github.com/cslib-community/complexitylib/pull/${p.pr}`),link('Independent review ↗',p.review_url));
    if(p.source) {
      const explore=node('button',`Explore ${p.source.results.length.toLocaleString()} theorem declarations`,'explore-button');
      explore.type='button';explore.addEventListener('click',()=>openPaper(p));links.append(explore);
    }
    body.append(links);
    const facts = node('div',undefined,'facts');
    if(p.source) {
      const count=node('p'); count.append(node('strong',p.source.lines.toLocaleString()),document.createTextNode(' library lines')); facts.append(count,node('p',`${p.source.files} scoped files · tests excluded`));
      const rev=node('p','Counted revision '); rev.append(link(p.source.revision.slice(0,7),`https://github.com/cslib-community/complexitylib/commit/${p.source.revision}`)); facts.append(rev);
      const review=node('p',`Review at ${p.reviewed_sha.slice(0,7)}${p.review_is_current_head ? ' · current PR head' : ' · scoped historical evidence'}`,'revision');facts.append(review);
      const detail=node('details');detail.append(node('summary','Counted source files'));const ul=node('ul');for(const path of p.source.paths){const li=node('li');li.append(link(path.replace('Complexity/',''),`https://github.com/cslib-community/complexitylib/blob/${p.source.revision}/${path}`));ul.append(li);}detail.append(ul);body.append(detail);
    }
    if(p.pr_observation){const pr=p.pr_observation;facts.append(node('p',`PR ${pr.state}${pr.draft ? ' · draft' : ''}`),link(`CI: ${pr.checks} ↗`,pr.checks_url));}else if(p.pr){facts.append(node('p','GitHub checks not refreshed in this offline snapshot.'));}
    row.append(number,body,facts);$('papers').append(row);
  }
  $('results').textContent = `${matches.length.toLocaleString()} matching submissions · showing ${Math.min(limit,matches.length).toLocaleString()}`;
  if (!matches.length) $('papers').append(node('p','No matching submissions. Try another search or choose all submissions.'));
  $('more').hidden = matches.length <= limit;
}
for(const id of ['search','coverage','sort']) $(id).addEventListener(id === 'search' ? 'input' : 'change',()=>{limit=30;render();});
$('more').addEventListener('click',()=>{limit+=50;render();});
fetch('data.json').then(r=>{if(!r.ok)throw new Error(`Snapshot HTTP ${r.status}`);return r.json();}).then(data=>{
  dashboard=data;papers=data.papers;renderResources(data);
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
  container.append(node('div',`SUBMISSION ${p.id}`,'eyebrow'),node('h2',p.title),node('p',p.authors),link('Read the paper PDF ↗',p.paper_url),node('p',p.scope),node('p',`Remaining / limitations: ${p.remaining}`,'remaining'));
  const res=p.resources;
  if(res) {
    const ledger=node('section',undefined,'ledger');ledger.append(node('h3','Resource ledger'),node('p',`Recorded task wall time: ${duration(res.recorded_seconds)} across ${res.recorded_tasks} recorded tasks.`),node('p',`Measured tokens: ${res.tokens == null ? 'Unknown' : res.tokens.toLocaleString()} · ${res.token_coverage}.`),node('p',`Time budget: ${res.budget.time_hours == null ? 'not set' : `${res.budget.time_hours} h`}. Token budget: ${res.budget.tokens == null ? 'not set' : res.budget.tokens.toLocaleString()}.`));
    for(const event of res.measurements){ledger.append(node('p',`${event.label}: ${event.started_at} → ${event.finished_at}. Tokens: ${event.total_tokens == null ? 'unknown' : event.total_tokens}.`));}
    container.append(ledger);
  }
  container.append(node('h3','Theorem explorer'),node('p','Declarations extracted from the explicitly scoped source files, including supporting lemmas. This index is not a list of independently classified main results. Links point to the exact counted revision. Full Lean statements and proofs are authoritative.','result-note'));
  const input=node('input');input.type='search';input.placeholder='Search theorem name, statement or source path';input.setAttribute('aria-label','Search formalized theorems');input.className='detail-controls';container.append(input);
  const results=node('div');container.append(results);let shown=25;
  const more=node('button','Show more theorems');more.type='button';container.append(more);
  function show(){const term=input.value.toLocaleLowerCase();const matches=p.source.results.filter(r=>`${r.name} ${r.file} ${r.statement}`.toLocaleLowerCase().includes(term));results.replaceChildren(node('p',`${matches.length} matching declarations`,'result-note'));for(const r of matches.slice(0,shown)){const article=node('article',undefined,'result');const h=node('h3');h.append(link(r.name+' ↗',r.url));article.append(h,node('p',`${r.file}:${r.line}`,'result-note'),node('pre',r.statement));results.append(article);}more.hidden=matches.length<=shown;}
  input.addEventListener('input',()=>{shown=25;show();});more.addEventListener('click',()=>{shown+=50;show();});show();
  $('paper-dialog').showModal();
}
$('close-dialog').addEventListener('click',()=>$('paper-dialog').close());
