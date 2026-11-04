'use strict';
const config=JSON.parse(document.getElementById('reader-data').textContent);
document.documentElement.classList.add('reader-enhanced');
const route=document.getElementById('route'),sidebar=document.querySelector('.sidebar'),reading=document.getElementById('reading');
if(matchMedia('(max-width:1250px)').matches){route.open=false;if(document.getElementById('panel-nav'))document.getElementById('panel-nav').open=false;}
const viewport=document.getElementById('paper-viewport'),world=document.getElementById('paper-world'),trunk=document.getElementById('paper-trunk');
const sections=[...document.querySelectorAll('.article-section')],branchDetails=[...document.querySelectorAll('.story-detail')];
const camera={cx:0,cy:0,scale:1},paper={width:0,height:0,trunkX:0,trunkY:32,column:0,gap:0};
let initialized=false,landed=null,currentSection=null,currentBranch='',scrollFrame=0,layoutFrame=0,motion=null,motionId=0;
let returnPoint=null,spaceHeld=false,pointer=null,hashFrame=0,suppressNextClick=false;
let wheelZoom=false,overviewReturnPose=null;
let mapOverrides=new Map(),mapAllBranches=false,mapSignature=null;
const readingStorageKey='materials-reader-position:'+location.pathname+':'+(config.readerIdentity||'legacy');
let readingSaveTimer=0,recoveryCandidate=loadReadingPosition(),recoveryPending=!!recoveryCandidate;
const MAX_PAPER_SCALE=3;
function fitPaperScale(){return Math.min(1,(viewport.clientWidth-32)/paper.width,(viewport.clientHeight-32)/paper.height);}
function minPaperScale(){return Math.max(.001,Math.min(.05,fitPaperScale()*.75));}
function scaleLabel(scale){const percent=scale*100;return(percent<10?percent.toFixed(1):Math.round(percent))+'%';}
function sliderForScale(scale){const min=minPaperScale();return Math.round(1000*Math.log(Math.max(min,scale)/min)/Math.log(MAX_PAPER_SCALE/min));}
function scaleForSlider(value){const min=minPaperScale();return min*(MAX_PAPER_SCALE/min)**(Number(value)/1000);}
const reducedMotion=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;
const copyPose=()=>({...camera});
function worldRect(element){
 let x=0,y=0,node=element;
 while(node&&node!==world){x+=node.offsetLeft;y+=node.offsetTop;node=node.offsetParent;}
 return{x,y,width:element.offsetWidth,height:element.offsetHeight};
}
function keepCurrentNodeVisible(){
 if(!matchMedia('(min-width:1251px)').matches||!route.open||sidebar.matches(':hover')||sidebar.contains(document.activeElement))return;
 const link=document.querySelector('#reading-map [data-graph-node="'+(currentBranch||currentSection)+'"]')||document.querySelector('#reading-map [data-graph-node="'+currentSection+'"]');if(!link)return;
 const wrap=route.querySelector('.flow-wrap'),v=wrap.getBoundingClientRect(),r=link.getBoundingClientRect();
 if(r.top<v.top+8)wrap.scrollTop+=r.top-v.top-8;else if(r.bottom>v.bottom-8)wrap.scrollTop+=r.bottom-v.bottom+8;
}
function setCurrent(sectionId,branchId=''){
 const wasOverview=document.body.dataset.mapOverview==='true';
 if(sectionId===currentSection&&branchId===currentBranch&&!wasOverview)return;
 delete document.body.dataset.mapOverview;
 if(branchId&&branchId!==currentBranch){const branch=document.getElementById(branchId);mapOverrides.delete(sectionId+'|'+branch.dataset.side);}
 currentSection=sectionId;currentBranch=branchId;
 document.getElementById('paper-return').disabled=!(branchId||returnPoint);
 document.body.dataset.currentSection=sectionId;document.body.dataset.currentBranch=branchId;
 renderReadingMap();
 sections.forEach(section=>section.classList.toggle('active-story',section.id===sectionId));
 branchDetails.forEach(detail=>detail.classList.toggle('active-branch',detail.id===branchId));
 document.querySelectorAll('.paper-connections [data-branch-id]').forEach(path=>path.classList.toggle('active-link',path.dataset.branchId===branchId));
 const main=config.readingGraph.nodes.find(n=>n.id===sectionId),role=main?main.code+' · '+main.title:sectionId;
 const branch=document.getElementById(branchId),where=branch?(branch.dataset.side==='left'?'左侧枝':'右侧枝'):'主干';
 const selected=config.readingGraph.nodes.find(n=>n.id===branchId);
 document.getElementById('current-location').textContent='正在读：'+(selected?selected.code+' · '+selected.title:role);
 document.getElementById('route-current').textContent=' · '+role.split(' · ')[0];
 document.getElementById('paper-position').textContent=(selected?selected.code:main?.code||'')+' · '+where;
 const finding=document.getElementById('current-finding');finding.textContent=main?.finding||'';finding.hidden=!finding.textContent;
 updatePaperOverview();
 requestAnimationFrame(keepCurrentNodeVisible);
}
function syncFromCamera(){
 scrollFrame=0;if(!initialized||document.getElementById('figure-dialog').open)return;
 if(viewport.clientWidth/camera.scale>=paper.width-2&&viewport.clientHeight/camera.scale>=paper.height-2){setMapOverview();return;}
 const y=camera.cy-viewport.clientHeight/(2*camera.scale)+Math.min(150,viewport.clientHeight*.24)/camera.scale;
 const branch=branchDetails.find(el=>{const r=worldRect(el);return camera.cx>=r.x&&camera.cx<=r.x+r.width&&y>=r.y-30&&y<r.y+r.height;});
 if(branch){setCurrent(branch.dataset.storySection,branch.id);return;}
 let section=sections[0];for(const candidate of sections){if(worldRect(candidate).y<=y)section=candidate;else break;}
 if(Math.abs(camera.cx-(paper.trunkX+paper.column/2))<paper.column*.4&&camera.cy+viewport.clientHeight/(2*camera.scale)>=paper.trunkY+trunk.offsetHeight-Math.min(200,viewport.clientHeight*.25)/camera.scale)section=sections.at(-1);
 setCurrent(section.id);
}
function requestScrollSync(){if(!scrollFrame)scrollFrame=requestAnimationFrame(syncFromCamera);}
function clampPose(pose){
 const sx=viewport.clientWidth/(2*pose.scale),sy=viewport.clientHeight/(2*pose.scale);
 return{cx:paper.width<2*sx?paper.width/2:Math.max(sx,Math.min(paper.width-sx,pose.cx)),cy:paper.height<2*sy?paper.height/2:Math.max(sy,Math.min(paper.height-sy,pose.cy)),scale:pose.scale};
}
function paintCamera(){
 world.style.transform=`translate(${viewport.clientWidth/2-camera.cx*camera.scale}px,${viewport.clientHeight/2-camera.cy*camera.scale}px) scale(${camera.scale})`;
 world.dataset.cameraX=camera.cx.toFixed(3);world.dataset.cameraY=camera.cy.toFixed(3);world.dataset.cameraScale=camera.scale.toFixed(4);
 const label=scaleLabel(camera.scale);document.getElementById('paper-scale').textContent=label;
 const slider=document.getElementById('paper-zoom-slider');slider.value=sliderForScale(camera.scale);slider.setAttribute('aria-valuetext',label);
 document.getElementById('paper-minus').disabled=camera.scale<=minPaperScale()*1.001;document.getElementById('paper-plus').disabled=camera.scale>=MAX_PAPER_SCALE*.999;
 updatePaperOverview();
 requestScrollSync();
 queueReadingSave();
}

function loadReadingPosition(){
 try{
  const value=JSON.parse(localStorage.getItem(readingStorageKey)||'null');
  const validPose=p=>p&&['cx','cy','scale'].every(k=>Number.isFinite(p[k]))&&p.scale>0&&p.scale<=3;
  if(!value||value.schema!==1||!validPose(value.pose)||(value.returnPose&&!validPose(value.returnPose))||(value.overviewReturnPose&&!validPose(value.overviewReturnPose)))return null;
  if(typeof value.returnHash!=='string'||(value.returnHash&&!/^#[A-Za-z][A-Za-z0-9_-]*$/.test(value.returnHash)))value.returnHash='';
  if(location.hash&&location.hash!==value.hash)return null;
  return value;
 }catch{return null;}
}
function saveReadingPosition(){
 if(!initialized||recoveryPending)return;
 const container=document.getElementById(currentBranch||currentSection)||trunk;
 const readingY=camera.cy-viewport.clientHeight/(2*camera.scale)+Math.min(150,viewport.clientHeight*.24)/camera.scale;
 const anchors=[container,...container.querySelectorAll('[id]')].filter(e=>e.matches('.article-section,.prose,.figure,.story-detail,.panel-step')&&(currentBranch?e.closest('.story-detail')===container:!e.closest('.story-detail'))).sort((a,b)=>worldRect(a).y-worldRect(b).y);
 let anchor=container;for(const el of anchors){const r=worldRect(el);if(r.y<=readingY)anchor=el;else break;}
 const rect=worldRect(anchor);
 const state={schema:1,pose:copyPose(),column:paper.column,view:[viewport.clientWidth,viewport.clientHeight],section:currentSection,branch:currentBranch,hash:location.hash,anchor:anchor.id,fraction:Math.max(0,Math.min(1,(readingY-rect.y)/Math.max(1,rect.height))),wheelZoom,returnPose:returnPoint?.pose||null,returnHash:returnPoint?.hash||'',overviewReturnPose};
 try{localStorage.setItem(readingStorageKey,JSON.stringify(state));}catch{}
}
function queueReadingSave(){
 clearTimeout(readingSaveTimer);readingSaveTimer=setTimeout(()=>{if(!motion)saveReadingPosition();},250);
}
function cancelReadingRecovery(){recoveryPending=false;recoveryCandidate=null;}
function restoreReadingPosition(){
 const saved=recoveryCandidate;if(!recoveryPending||!saved)return;
 recoveryPending=false;recoveryCandidate=null;
 const target=document.getElementById(saved.branch||saved.section),anchor=document.getElementById(saved.anchor)||target;
 if(!target||!world.contains(target)||!anchor||!world.contains(anchor))return;
 cancelFlight();
 let pose=saved.pose;
 if(saved.column!==paper.column||saved.view?.[0]!==viewport.clientWidth||saved.view?.[1]!==viewport.clientHeight){
  const r=worldRect(anchor),scale=Math.max(minPaperScale(),Math.min(MAX_PAPER_SCALE,saved.pose.scale));
  const detail=target.closest('.story-detail');
  pose={cx:(detail?worldRect(detail).x:paper.trunkX)+paper.column/2,cy:r.y+(Number.isFinite(saved.fraction)?saved.fraction:0)*r.height-Math.min(150,viewport.clientHeight*.24)/scale+viewport.clientHeight/(2*scale),scale};
 }
 Object.assign(camera,clampPose(pose));
 wheelZoom=saved.wheelZoom===true;
 const modeButton=document.getElementById('paper-wheel-mode');modeButton.setAttribute('aria-pressed',String(wheelZoom));modeButton.textContent=wheelZoom?'滚轮：缩放':'滚轮：阅读';
 overviewReturnPose=saved.overviewReturnPose;
 if(saved.branch){
  const entry=document.querySelector('[data-open-branch="'+saved.branch+'"]');
  returnPoint={pose:saved.returnPose||poseAt(document.getElementById(target.dataset.storySection)),focus:entry,hash:saved.returnHash};
 }
 paintCamera();syncFromCamera();
 document.getElementById('reader-status').textContent='已恢复上次阅读位置。';
}
document.addEventListener('pointerdown',cancelReadingRecovery,{capture:true,once:true});
document.addEventListener('wheel',cancelReadingRecovery,{capture:true,once:true});
document.addEventListener('keydown',cancelReadingRecovery,{capture:true,once:true});
window.addEventListener('pagehide',saveReadingPosition);
document.addEventListener('visibilitychange',()=>{if(document.hidden)saveReadingPosition();});
function cancelFlight(){
 motionId++;if(motion){cancelAnimationFrame(motion.frame);motion.resolve(false);motion=null;}world.dataset.moving='false';
}
function flyTo(destination,focus=null){
 cancelFlight();const token=motionId,start=copyPose(),end=clampPose(destination),distance=Math.hypot(end.cx-start.cx,end.cy-start.cy);
 const duration=reducedMotion()?0:Math.min(1500,880+distance*.055);
 const lateral=Math.abs(end.cx-start.cx)>paper.column*.2;
 const travelScale=lateral?Math.max(.12,Math.min(start.scale,end.scale,.66,viewport.clientWidth/(Math.abs(end.cx-start.cx)+paper.column+140),viewport.clientHeight/(Math.abs(end.cy-start.cy)+420))):Math.min(start.scale,end.scale);
 world.dataset.moving='true';
 return new Promise(resolve=>{
  const begun=performance.now();motion={resolve,frame:0};
  const frame=now=>{
   if(token!==motionId)return;
   const t=duration?Math.min(1,(now-begun)/duration):1,e=t*t*t*(10+t*(-15+6*t));
   camera.cx=start.cx+(end.cx-start.cx)*e;camera.cy=start.cy+(end.cy-start.cy)*e;
   camera.scale=start.scale+(end.scale-start.scale)*e-(Math.min(start.scale,end.scale)-travelScale)*Math.sin(Math.PI*t)**2;
   paintCamera();
   if(t<1)motion.frame=requestAnimationFrame(frame);else{motion=null;world.dataset.moving='false';if(focus){markTarget(focus);focus.focus({preventScroll:true});}syncFromCamera();resolve(true);}
  };
  motion.frame=requestAnimationFrame(frame);
 });
}
function poseAt(element,scale=1){
 const r=worldRect(element),detail=element.closest('.story-detail');
 return{cx:detail?worldRect(detail).x+paper.column/2:paper.trunkX+paper.column/2,cy:r.y-26/scale+viewport.clientHeight/(2*scale),scale};
}
function markTarget(target){if(landed)landed.classList.remove('landing');landed=target;target.classList.add('landing');}
function drawConnections(){
 const svg=world.querySelector('.paper-connections'),ns='http://www.w3.org/2000/svg',paths=[];
 svg.setAttribute('viewBox','0 0 '+paper.width+' '+paper.height);
 config.readingGraph.edges.filter(edge=>edge.kind==='branch').forEach(edge=>{
  const detail=document.getElementById(edge.to);
  const left=detail.dataset.side==='left',entry=document.querySelector('[data-open-branch="'+detail.id+'"]'),source=worldRect(entry),leaf=worldRect(detail);
  const x1=left?source.x:source.x+source.width,y1=source.y+source.height/2,x2=left?leaf.x+leaf.width:leaf.x,y2=leaf.y+38;
  const gutter=left?paper.trunkX-paper.gap*.45:paper.trunkX+paper.column+paper.gap*.45;
  const p=document.createElementNS(ns,'path');p.setAttribute('d',`M${x1} ${y1} C${gutter} ${y1} ${gutter} ${y1} ${gutter} ${y1+Math.min(24,Math.max(0,y2-y1))} L${gutter} ${y2} C${gutter} ${y2} ${gutter} ${y2} ${x2} ${y2}`);
  p.dataset.branchId=detail.id;p.dataset.side=detail.dataset.side;p.dataset.from=edge.from;p.dataset.to=edge.to;if(detail.classList.contains('supplement'))p.classList.add('si-link');if(detail.id===currentBranch)p.classList.add('active-link');paths.push(p);
 });
 const rail=paper.trunkX-18;
 config.readingGraph.edges.filter(edge=>edge.kind==='reading-order').forEach(edge=>{
  const a=worldRect(document.getElementById(edge.from).querySelector('.trunk-stage-marker')),b=worldRect(document.getElementById(edge.to).querySelector('.trunk-stage-marker'));
  const p=document.createElementNS(ns,'path');p.setAttribute('d',`M${rail} ${a.y+a.height/2} L${rail} ${b.y+b.height/2} L${b.x-3} ${b.y+b.height/2}`);p.setAttribute('class','paper-order-edge');p.dataset.from=edge.from;p.dataset.to=edge.to;paths.push(p);
 });
 svg.replaceChildren(...paths);
}
function layoutPaper(){
 layoutFrame=0;
 const width=Math.max(220,Math.min(860,viewport.clientWidth-(innerWidth<=820?28:64))),oldWidth=paper.column;
 paper.column=width;paper.gap=Math.max(100,Math.round(width*.19));paper.trunkX=width+paper.gap+32;paper.width=3*width+2*paper.gap+64;
 trunk.style.width=width+'px';trunk.style.left=paper.trunkX+'px';trunk.style.top=paper.trunkY+'px';
 const ends={left:0,right:0};
 branchDetails.forEach(detail=>{
  detail.style.width=width+'px';detail.style.left=(detail.dataset.side==='left'?-(width+paper.gap):width+paper.gap)+'px';
  const junction=detail.closest('.branch-junction'),originY=worldRect(junction).y-paper.trunkY;
  const top=Math.max(originY,ends[detail.dataset.side]);detail.style.top=top+'px';
  ends[detail.dataset.side]=top+detail.offsetHeight+64;
  const r=worldRect(detail);detail.dataset.worldX=r.x;detail.dataset.worldY=r.y;
 });
 paper.height=Math.max(trunk.offsetHeight+paper.trunkY+50,ends.left+paper.trunkY,ends.right+paper.trunkY);
 world.style.width=paper.width+'px';world.style.height=paper.height+'px';drawConnections();drawPaperOverview();
 if(!initialized){initialized=true;Object.assign(camera,{cx:paper.trunkX+width/2,cy:viewport.clientHeight/2,scale:1});}
 else if(oldWidth!==width){cancelFlight();const target=currentBranch?document.getElementById(currentBranch):document.getElementById(currentSection)||trunk;Object.assign(camera,clampPose(poseAt(target)));returnPoint=null;document.getElementById('paper-return').disabled=!currentBranch;}
 paintCamera();
}
function requestTreeLayout(){if(!layoutFrame)layoutFrame=requestAnimationFrame(layoutPaper);}
function navigateTarget(target,entry=null,animated=true){
 overviewReturnPose=null;
 const detail=target.closest('.story-detail');
 if(detail){mapOverrides.delete(detail.dataset.storySection+'|'+detail.dataset.side);renderReadingMap();}
 if(detail&&!returnPoint){
  const hashTarget=document.getElementById(decodeURIComponent(location.hash.slice(1))),fromBranch=!!hashTarget?.closest('.story-detail');
  const origin=document.getElementById(detail.closest('.branch-junction').dataset.origin);
  returnPoint={pose:fromBranch?poseAt(origin):copyPose(),focus:entry||document.querySelector('[data-open-branch="'+detail.id+'"]'),hash:fromBranch?'#'+origin.id:location.hash};
 }else if(!detail){returnPoint=null;}
 document.getElementById('paper-return').disabled=!detail;
 const end=target===reading?{cx:paper.trunkX+paper.column/2,cy:viewport.clientHeight/2,scale:1}:poseAt(target);
 if(animated)return flyTo(end,target);
 cancelFlight();Object.assign(camera,clampPose(end));paintCamera();markTarget(target);target.focus({preventScroll:true});return Promise.resolve(true);
}
function returnToMain(){
 overviewReturnPose=null;
 const branch=document.getElementById(currentBranch),saved=returnPoint;
 const origin=branch?document.getElementById(branch.closest('.branch-junction').dataset.origin):null;
 const end=saved?.pose||poseAt(origin||trunk);
 const focus=saved?.focus||(branch?document.querySelector('[data-open-branch="'+branch.id+'"]'):trunk);
 history.replaceState(null,'',location.pathname+location.search+(saved?.hash||(origin?'#'+origin.id:'')));
 returnPoint=null;document.getElementById('paper-return').disabled=true;
 flyTo(end,focus).then(()=>{document.getElementById('reader-status').textContent='镜头已移回主干原阅读位置。';});
}
document.addEventListener('click',event=>{
 const toggle=event.target.closest?.('[data-map-toggle]');if(toggle){event.preventDefault();const key=toggle.dataset.mapToggle+'|'+toggle.dataset.mapSide;mapOverrides.set(key,!mapNodeExpanded(toggle.dataset.mapToggle,toggle.dataset.mapSide));renderReadingMap();return;}
 const link=event.target.closest?.('a.flow-node,a.outline-link,a.branch-entry,a.return-trunk,a.mini-node,a[href="#reading"]');if(!link)return;
 const target=document.getElementById(link.getAttribute('href').slice(1));if(!target)return;event.preventDefault();
 if(link.classList.contains('return-trunk')){returnToMain();return;}
 navigateTarget(target,link);if(location.hash!=='#'+target.id)history.pushState(null,'','#'+target.id);
 if(link.classList.contains('outline-link')){document.querySelectorAll('.outline-link').forEach(e=>e.classList.remove('active'));link.classList.add('active');}
 if(matchMedia('(max-width:1250px)').matches)route.open=false;
 document.getElementById('reader-status').textContent='镜头正在移向：'+(link.getAttribute('aria-label')||link.textContent.trim());
});
document.getElementById('map-expand-all').onclick=()=>{const allVisible=config.readingGraph.nodes.filter(n=>n.type==='branch').every(n=>mapNodeExpanded(n.section,n.side));mapAllBranches=!allVisible;mapOverrides.clear();renderReadingMap();};
document.getElementById('paper-mini-map').addEventListener('click',event=>{
 if(event.target.closest('a'))return;
 const svg=event.currentTarget,matrix=svg.getScreenCTM();if(!matrix)return;
 const point=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());flyTo({...camera,cx:point.x,cy:point.y});
});
function revealHash(animated=true){
 const id=decodeURIComponent(location.hash.slice(1)),target=id?document.getElementById(id):reading;
 if(target)navigateTarget(target,null,animated);
}
function queueHash(){if(!hashFrame)hashFrame=requestAnimationFrame(()=>{hashFrame=0;revealHash();});}
document.getElementById('paper-return').onclick=returnToMain;
function contextBranch(){
 const active=document.getElementById(currentBranch);
 if(active?.matches('.story-detail'))return active;
 const local=branchDetails.filter(detail=>detail.dataset.storySection===currentSection);
 const candidates=local.length?local:branchDetails;
 const readingY=camera.cy-viewport.clientHeight/(2*camera.scale)+Math.min(150,viewport.clientHeight*.24)/camera.scale;
 return candidates.reduce((best,detail)=>{
  const entry=document.querySelector('[data-open-branch="'+detail.id+'"]');
  const distance=Math.abs(worldRect(entry).y-readingY);
  return !best||distance<best.distance?{detail,distance}:best;
 },null)?.detail;
}
document.getElementById('paper-context').onclick=()=>{
 const detail=contextBranch();
 if(!detail){document.getElementById('reader-status').textContent='本文没有可定位的侧枝。';return;}
 overviewReturnPose=null;
 const r=worldRect(detail),source=worldRect(document.querySelector('[data-open-branch="'+detail.id+'"]'));
 const x1=Math.min(r.x,source.x),x2=Math.max(r.x+r.width,source.x+source.width),y1=Math.min(r.y,source.y),y2=Math.max(r.y+Math.min(100,r.height),source.y+source.height);
 world.dataset.contextBranch=detail.id;
 document.getElementById('reader-status').textContent='镜头正在展示主干与侧枝的连接：'+detail.querySelector('.branch-title').textContent;
 flyTo({cx:(x1+x2)/2,cy:(y1+y2)/2,scale:Math.min(.75,viewport.clientWidth/(x2-x1+100),viewport.clientHeight/(y2-y1+100))});
};
function zoomAt(scale,sx=viewport.clientWidth/2,sy=viewport.clientHeight/2){
 cancelFlight();overviewReturnPose=null;scale=Math.max(minPaperScale(),Math.min(MAX_PAPER_SCALE,scale));
 const wx=camera.cx+(sx-viewport.clientWidth/2)/camera.scale,wy=camera.cy+(sy-viewport.clientHeight/2)/camera.scale;
 Object.assign(camera,clampPose({cx:wx-(sx-viewport.clientWidth/2)/scale,cy:wy-(sy-viewport.clientHeight/2)/scale,scale}));paintCamera();
}
document.getElementById('paper-minus').onclick=()=>zoomAt(camera.scale/1.2);
document.getElementById('paper-plus').onclick=()=>zoomAt(camera.scale*1.2);
function restoreReadingScale(){const pose={...(overviewReturnPose||camera),scale:1};overviewReturnPose=null;return flyTo(pose);}
document.getElementById('paper-scale').onclick=restoreReadingScale;
document.getElementById('paper-zoom-slider').addEventListener('input',event=>zoomAt(scaleForSlider(event.target.value)));
document.getElementById('paper-fit').onclick=()=>{if(!overviewReturnPose)overviewReturnPose=copyPose();flyTo({cx:paper.width/2,cy:paper.height/2,scale:fitPaperScale()});};
document.getElementById('paper-wheel-mode').onclick=event=>{wheelZoom=!wheelZoom;event.currentTarget.setAttribute('aria-pressed',String(wheelZoom));event.currentTarget.textContent=wheelZoom?'滚轮：缩放':'滚轮：阅读';};
viewport.addEventListener('wheel',event=>{
 event.preventDefault();cancelFlight();
 if(event.ctrlKey||event.metaKey||wheelZoom){const rect=viewport.getBoundingClientRect();zoomAt(camera.scale*Math.exp(-event.deltaY*.004),event.clientX-rect.left,event.clientY-rect.top);return;}
 const units=event.deltaMode===1?18:event.deltaMode===2?viewport.clientHeight:1;
 camera.cx+=(event.shiftKey?event.deltaY:event.deltaX)*units/camera.scale;
 camera.cy+=(event.shiftKey?0:event.deltaY)*units/camera.scale;
 Object.assign(camera,clampPose(camera));
 if(Math.abs(camera.cx-(paper.trunkX+paper.column/2))<paper.column*.4&&camera.scale>.8){camera.cy=Math.min(camera.cy,Math.max(viewport.clientHeight/(2*camera.scale),paper.trunkY+trunk.offsetHeight+36-viewport.clientHeight/(2*camera.scale)));}
 paintCamera();
},{passive:false});
function textUnderPointer(event){
 const range=document.caretRangeFromPoint?.(event.clientX,event.clientY);
 const position=!range&&document.caretPositionFromPoint?.(event.clientX,event.clientY);
 const node=range?.startContainer||position?.offsetNode,offset=range?.startOffset??position?.offset;
 if(!node||node.nodeType!==Node.TEXT_NODE||!world.contains(node))return false;
 for(const index of [offset-1,offset]){
  if(index<0||index>=node.length||!node.textContent[index].trim())continue;
  const char=document.createRange();char.setStart(node,index);char.setEnd(node,index+1);
  if([...char.getClientRects()].some(r=>event.clientX>=r.left-1&&event.clientX<=r.right+1&&event.clientY>=r.top-1&&event.clientY<=r.bottom+1))return true;
 }
 return false;
}
viewport.addEventListener('pointerdown',event=>{
 if(event.button!==0&&event.button!==1&&event.pointerType!=='touch')return;
 if(event.target.closest('button,a,summary,input')&&!spaceHeld&&event.button!==1)return;
 if(event.button!==1&&!spaceHeld&&event.pointerType!=='touch'&&textUnderPointer(event))return;
 event.preventDefault();cancelFlight();suppressNextClick=spaceHeld;pointer={id:event.pointerId,x:event.clientX,y:event.clientY,cx:camera.cx,cy:camera.cy};viewport.setPointerCapture(event.pointerId);viewport.classList.add('panning');
});
viewport.addEventListener('pointermove',event=>{if(!pointer||event.pointerId!==pointer.id)return;if(Math.hypot(event.clientX-pointer.x,event.clientY-pointer.y)>5)suppressNextClick=true;Object.assign(camera,clampPose({cx:pointer.cx-(event.clientX-pointer.x)/camera.scale,cy:pointer.cy-(event.clientY-pointer.y)/camera.scale,scale:camera.scale}));paintCamera();});
viewport.addEventListener('click',event=>{if(suppressNextClick){event.preventDefault();event.stopImmediatePropagation();suppressNextClick=false;}},true);
function endPan(){pointer=null;viewport.classList.remove('panning');if(suppressNextClick)setTimeout(()=>suppressNextClick=false,150);}
viewport.addEventListener('pointerup',endPan);viewport.addEventListener('pointercancel',endPan);
window.addEventListener('keydown',event=>{
 if(document.getElementById('figure-dialog').open)return;
 const mapToggle=event.target.closest?.('[data-map-toggle]');if(mapToggle&&event.code==='Space'){event.preventDefault();mapToggle.dispatchEvent(new MouseEvent('click',{bubbles:true}));return;}
 if(event.code==='Space'&&!event.target.closest('button,a,summary,input')){spaceHeld=true;viewport.classList.add('pan-ready');event.preventDefault();}
 if(event.key==='Escape'){
  if(returnPoint||currentBranch){event.preventDefault();returnToMain();}
  else if(matchMedia('(max-width:1250px)').matches&&route.open){route.open=false;route.querySelector('summary').focus({preventScroll:true});}
 }
 if(event.target!==viewport)return;
 if(event.key==='+'||event.key==='='){event.preventDefault();zoomAt(camera.scale*1.2);return;}
 if(event.key==='-'){event.preventDefault();zoomAt(camera.scale/1.2);return;}
 if(event.key==='0'){event.preventDefault();restoreReadingScale();return;}
 const shifts={ArrowUp:[0,-85],ArrowDown:[0,85],ArrowLeft:[-85,0],ArrowRight:[85,0],PageDown:[0,viewport.clientHeight*.8],PageUp:[0,-viewport.clientHeight*.8]};
 if(shifts[event.key]){event.preventDefault();cancelFlight();camera.cx+=shifts[event.key][0]/camera.scale;camera.cy+=shifts[event.key][1]/camera.scale;Object.assign(camera,clampPose(camera));paintCamera();}
});
window.addEventListener('keyup',event=>{if(event.code==='Space'){spaceHeld=false;viewport.classList.remove('pan-ready');}});
window.addEventListener('blur',()=>{spaceHeld=false;endPan();viewport.classList.remove('pan-ready');});
window.addEventListener('resize',requestTreeLayout);window.addEventListener('popstate',queueHash);window.addEventListener('hashchange',queueHash);
matchMedia('(max-width:1250px)').addEventListener('change',event=>{route.open=!event.matches;if(event.matches)if(document.getElementById('panel-nav'))document.getElementById('panel-nav').open=false;requestTreeLayout();});
reading.addEventListener('load',requestTreeLayout,true);reading.addEventListener('toggle',requestTreeLayout,true);
new ResizeObserver(requestTreeLayout).observe(viewport);
if(config.assetMode!=='linked')world.querySelectorAll('img').forEach(image=>image.loading='eager');
renderReadingMap();layoutPaper();if(location.hash)revealHash(false);else requestScrollSync();
if(config.assetMode==='linked')requestAnimationFrame(()=>{layoutPaper();restoreReadingPosition();});
else Promise.all([...world.querySelectorAll('img')].map(image=>image.decode().catch(()=>{}))).then(()=>requestAnimationFrame(()=>{layoutPaper();restoreReadingPosition();}));

/* The reading map and paper geometry share config.readingGraph. */
function mapSvgElement(tag,attributes={},text=''){
 const el=document.createElementNS('http://www.w3.org/2000/svg',tag);
 Object.entries(attributes).forEach(([key,value])=>el.setAttribute(key,String(value)));if(text)el.textContent=text;return el;
}
function mapWrap(text,limit){
 const lines=[];let line='',units=0;
 for(const char of text){const size=/[\x00-\xff]/.test(char)?.55:1;if(units+size>limit&&line){lines.push(line);line='';units=0;}line+=char;units+=size;}
 if(line)lines.push(line);return lines;
}
function mapNodeExpanded(section,side){
 const key=section+'|'+side;
 return mapOverrides.has(key)?mapOverrides.get(key):mapAllBranches||currentSection===section;
}
function renderReadingMap(){
 const svg=document.getElementById('reading-map'),graph=config.readingGraph;
 const mains=graph.nodes.filter(n=>n.type==='main'),expanded=mains.flatMap(n=>['left','right'].filter(side=>mapNodeExpanded(n.id,side)).map(side=>n.id+'|'+side));
 const signature=expanded.join('|');
 if(mapSignature===signature){selectReadingMapNode();return;}
 mapSignature=signature;
 const focused=document.activeElement?.closest?.('#reading-map a'),focusedId=focused?.dataset.graphNode,focusedToggle=focused?.dataset.mapToggle,focusedSide=focused?.dataset.mapSide;
 const pieces=[],positions=new Map();let y=20;
 const makeBox=(node,x,top,width)=>{
  const lines=mapWrap(node.title,(width-26)/24),height=35+lines.length*29+34;
  const link=mapSvgElement('a',{href:'#'+node.target,class:'flow-node map-node '+(node.type==='main'?'main-map-node':'branch-map-node'),tabindex:'0','data-graph-node':node.id,'data-story-section':node.section,'data-branch-id':node.type==='branch'?node.id:'','aria-label':node.code+' · '+node.title+(node.figures?' · '+node.figures:'')});
  link.append(mapSvgElement('title',{},node.code+' · '+node.title+(node.figures?'\n'+node.figures:'')));
  link.append(mapSvgElement('rect',{x,y:top,width,height,rx:10}));
  link.append(mapSvgElement('text',{x:x+width/2,y:top+25,class:'node-role'},node.code+(node.type==='branch'?(node.kind==='si'?' · SI':' · 细讲'):' · 主干')));
  const text=mapSvgElement('text',{class:'map-title',x:x+width/2,y:top+54});
  lines.forEach((line,index)=>text.append(mapSvgElement('tspan',{x:x+width/2,y:top+54+index*29},line)));link.append(text);
  const notes=mapWrap(node.figures,(width-50)/17),note=(notes[0]||'')+(notes.length>1?'…':'');
  link.append(mapSvgElement('text',{class:'map-figures',x:x+width/2,y:top+height-12},note));
  positions.set(node.id,{x,y:top,width,height});pieces.push(link);return height;
 };
 mains.forEach(main=>{
  const mainHeight=makeBox(main,218,y,224),children=graph.nodes.filter(n=>n.type==='branch'&&n.section===main.id);
  let leftY=y,rightY=y;
  children.filter(child=>expanded.includes(main.id+'|'+child.side)).forEach(child=>{const side=child.side==='left';const top=side?leftY:rightY,height=makeBox(child,side?8:468,top,184);if(side)leftY+=height+16;else rightY+=height+16;});
  for(const side of ['left','right']){
   const siblings=children.filter(child=>child.side===side);if(!siblings.length)continue;
   const open=expanded.includes(main.id+'|'+side),left=side==='left',x=left?194:444;
   const label=(open?'收起':'展开')+main.code+'阶段'+(left?'左侧':'右侧')+siblings.length+'条细讲';
   const toggle=mapSvgElement('a',{href:'#'+main.target,tabindex:'0',role:'button','data-map-toggle':main.id,'data-map-side':side,'aria-expanded':String(open),'aria-label':label,class:'map-toggle'});
   toggle.append(mapSvgElement('title',{},label));toggle.append(mapSvgElement('rect',{x,y:y+mainHeight/2-15,width:22,height:30,rx:5}));
   toggle.append(mapSvgElement('text',{x:x+11,y:y+mainHeight/2+8},left?(open?'→':'←'):(open?'←':'→')));pieces.push(toggle);
  }
  y=Math.max(y+mainHeight,leftY-16,rightY-16)+48;
 });
 const paths=[];
 graph.edges.forEach(edge=>{
  const a=positions.get(edge.from),b=positions.get(edge.to);if(!a||!b)return;
  const side=edge.kind==='branch',left=side&&b.x<a.x;
  const x1=side?(left?a.x:a.x+a.width):a.x+a.width/2,y1=side?a.y+a.height/2:a.y+a.height;
  const x2=side?(left?b.x+b.width:b.x):b.x+b.width/2,y2=side?b.y+b.height/2:b.y;
  const d=side?`M${x1} ${y1} C${(x1+x2)/2} ${y1} ${(x1+x2)/2} ${y2} ${x2} ${y2}`:`M${x1} ${y1} L${x2} ${y2}`;
  paths.push(mapSvgElement('path',{d,class:'reading-map-edge '+(side?'detail-edge':'order-edge'),'data-from':edge.from,'data-to':edge.to}));
 });
 svg.setAttribute('viewBox','0 0 660 '+(y-22));svg.replaceChildren(mapSvgElement('title',{},'与主画布一致的阅读顺序与侧枝'),...paths,...pieces);
 if(focusedId)svg.querySelector('[data-graph-node="'+focusedId+'"]')?.focus({preventScroll:true});
 else if(focusedToggle)svg.querySelector('[data-map-toggle="'+focusedToggle+'"][data-map-side="'+focusedSide+'"]')?.focus({preventScroll:true});
 const allVisible=graph.nodes.filter(n=>n.type==='branch').every(n=>mapNodeExpanded(n.section,n.side));
 document.getElementById('map-expand-all').textContent=allVisible?'按当前阶段展开':'展开全部侧枝';
 document.getElementById('map-expand-all').setAttribute('aria-pressed',String(allVisible));selectReadingMapNode();
}
function selectReadingMapNode(){
 document.querySelectorAll('#scientific-map .scientific-node').forEach(link=>link.classList.toggle('active',document.body.dataset.mapOverview!=='true'&&link.dataset.storySection===currentSection));
 const branchRendered=!!document.querySelector('#reading-map [data-graph-node="'+currentBranch+'"]');
 document.querySelectorAll('#reading-map .map-node').forEach(link=>{
  const overview=document.body.dataset.mapOverview==='true';
  const selected=!overview&&link.dataset.graphNode===(currentBranch&&branchRendered?currentBranch:currentSection),context=!overview&&!!currentBranch&&!link.dataset.branchId&&link.dataset.storySection===currentSection;
  link.classList.toggle('active',selected);link.classList.toggle('map-context',context);
  link.classList.toggle('in-view',overview);
  if(selected)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');
 });
}
function drawPaperOverview(){
 const svg=document.getElementById('paper-mini-map'),pieces=[];svg.setAttribute('viewBox','0 0 '+paper.width+' '+paper.height);
 pieces.push(mapSvgElement('rect',{x:0,y:0,width:paper.width,height:paper.height,class:'mini-paper'}));
 document.querySelectorAll('.paper-connections path').forEach(path=>pieces.push(mapSvgElement('path',{d:path.getAttribute('d'),class:'mini-edge'})));
 config.readingGraph.nodes.forEach(node=>{
  const r=worldRect(document.getElementById(node.id)),link=mapSvgElement('a',{href:'#'+node.target,class:'mini-node','data-graph-node':node.id,'data-story-section':node.section,'data-branch-id':node.type==='branch'?node.id:'','aria-label':node.code+' · '+node.title,tabindex:'0'});
  link.append(mapSvgElement('title',{},node.code+' · '+node.title));link.append(mapSvgElement('rect',{x:r.x,y:r.y,width:r.width,height:r.height,class:node.type==='branch'?'mini-branch':'mini-main'}));pieces.push(link);
 });
 pieces.push(mapSvgElement('rect',{id:'mini-viewport',class:'mini-viewport','pointer-events':'none'}));svg.replaceChildren(...pieces);updatePaperOverview();
}
function updatePaperOverview(){
 const frame=document.getElementById('mini-viewport');if(!frame)return;
 const halfW=viewport.clientWidth/(2*camera.scale),halfH=viewport.clientHeight/(2*camera.scale);
 const left=Math.max(0,camera.cx-halfW),top=Math.max(0,camera.cy-halfH),right=Math.min(paper.width,camera.cx+halfW),bottom=Math.min(paper.height,camera.cy+halfH);
 frame.setAttribute('x',left);frame.setAttribute('y',top);frame.setAttribute('width',Math.max(0,right-left));frame.setAttribute('height',Math.max(0,bottom-top));
 document.querySelectorAll('#paper-mini-map .mini-node').forEach(link=>link.classList.toggle('active',document.body.dataset.mapOverview!=='true'&&link.dataset.graphNode===(currentBranch||currentSection)));
}
function setMapOverview(){
 if(document.body.dataset.mapOverview==='true')return;
 document.body.dataset.mapOverview='true';selectReadingMapNode();updatePaperOverview();
 document.getElementById('current-location').textContent='全景：主干和全部侧枝都在当前视窗内';
 document.getElementById('paper-position').textContent='全景 · 同一张纸';document.getElementById('route-current').textContent=' · 全景';
}

const dialog=document.getElementById('figure-dialog'),image=document.getElementById('modal-image');
let activeFigure=null,mode='crop',zoom=1;
function displayImage(reset=true){
 const f=config.figures[activeFigure];
 const parent=f.parent?config.composites[f.parent]:null;
 image.src=mode==='page'?config.pages[f.page_key]:mode==='whole'?parent.image:document.getElementById('figure-'+activeFigure).querySelector('img').src;
 image.alt=mode==='page'?f.location+(f.full_view_description||'原页'):mode==='whole'?parent.label+'完整复合图':f.title;
 image.style.width=(zoom*100)+'%';
 document.getElementById('modal-title').textContent=mode==='whole'?parent.label+' · '+parent.title:f.label+' · '+f.title;
 document.getElementById('modal-source').textContent=f.location+(mode==='page'?' · '+(f.full_view_description||'完整PDF页面'):mode==='whole'?' · 完整原复合图':' · 原图局部');
 document.getElementById('modal-crop').textContent=parent?'当前面板':'图表';
 document.getElementById('modal-whole').hidden=!parent;
 document.getElementById('modal-crop').setAttribute('aria-pressed',String(mode==='crop'));
 document.getElementById('modal-whole').setAttribute('aria-pressed',String(mode==='whole'));
 document.getElementById('modal-page').textContent=f.full_view_label||'查看完整原页';
 document.getElementById('modal-page').setAttribute('aria-pressed',String(mode==='page'));
 if(reset){document.getElementById('image-stage').scrollTop=0;document.getElementById('image-stage').scrollLeft=0;}
}
document.querySelectorAll('[data-open-figure]').forEach(b=>b.addEventListener('click',()=>{
 activeFigure=b.dataset.openFigure;mode=b.dataset.mode||'crop';zoom=1;displayImage();dialog.showModal();
}));
document.getElementById('modal-close').onclick=()=>dialog.close();
dialog.addEventListener('close',requestScrollSync);
document.getElementById('modal-crop').onclick=()=>{mode='crop';zoom=1;displayImage();};
document.getElementById('modal-whole').onclick=()=>{mode='whole';zoom=1;displayImage();};
document.getElementById('modal-page').onclick=()=>{mode='page';zoom=1;displayImage();};
document.getElementById('modal-plus').onclick=()=>{zoom=Math.min(3,zoom+.25);displayImage(false);};
document.getElementById('modal-minus').onclick=()=>{zoom=Math.max(.5,zoom-.25);displayImage(false);};
document.documentElement.dataset.readerReady='true';
document.documentElement.classList.remove('reader-booting');
