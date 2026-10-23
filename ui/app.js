// Add your Logo.dev token here when you are ready to load company logos.
const LOGO_DEV_TOKEN = "pk_aGmc-1iUSfeCn_eLyY4fow";

const notifications = [
  {group:'New',kind:'job',icon:'S',color:'#7956d8',text:'<b>Stripe</b> viewed your application for <b>Product Designer</b>.',time:'12 minutes ago',unread:true},
  {group:'New',kind:'internship',icon:'F',color:'#eb6a62',text:'A new <b>Design Internship</b> matches your profile at Figma.',time:'1 hour ago',unread:true},
  {group:'New',kind:'job',icon:'\u2727',color:'#715ee8',text:'Your profile match is up <b>8 points</b> this week.',time:'3 hours ago',unread:true},
  {group:'Earlier',kind:'job',icon:'A',color:'#ff7385',text:'<b>Airbnb</b> posted 12 new roles in your saved locations.',time:'Yesterday',unread:false},
  {group:'Earlier',kind:'internship',icon:'\u2713',color:'#4dc996',text:'Application submitted to <b>Notion</b>. Good luck!',time:'Oct 10, 2026',unread:false}
];
const alerts = [
  {title:'Product Design \u00b7 Remote',detail:'Daily \u00b7 8 new roles this week',icon:'\u2726',color:'#b69cff',on:true},
  {title:'Internships \u00b7 Europe',detail:'Weekly \u00b7 12 new roles this week',icon:'\u2316',color:'#65aaff',on:true},
  {title:'UX Research \u00b7 United States',detail:'Daily \u00b7 3 new roles this week',icon:'\u25ce',color:'#55d6a1',on:false},
  {title:'Software Engineering \u00b7 Hybrid',detail:'Daily \u00b7 14 new roles this week',icon:'\u2318',color:'#ffb969',on:true},
  {title:'Graduate Programs \u00b7 Global',detail:'Weekly \u00b7 6 new programs this week',icon:'\u2727',color:'#ff7c91',on:false}
];

function renderAlerts() {
  const list = document.querySelector('#alert-list');
  list.innerHTML = alerts.map((a,i)=>`<div class="alert-row"><span class="alert-type-icon" style="background:${a.color}1e;color:${a.color}">${a.icon}</span><div class="alert-copy"><b>${a.title}</b><small>${a.detail}</small></div><button class="switch" role="switch" aria-checked="${a.on}" aria-label="Toggle ${a.title}" data-alert="${i}"></button></div>`).join('');
  document.querySelector('#alert-count').textContent = `(${alerts.length})`;
  list.querySelectorAll('[data-alert]').forEach(button=>button.addEventListener('click',()=>{const item=alerts[Number(button.dataset.alert)];item.on=!item.on;button.setAttribute('aria-checked',String(item.on));}));
}
function renderNotifications(kind='all') {
  let group='';
  const items=notifications.filter(n=>kind==='all'||n.kind===kind);
  document.querySelector('#notification-list').innerHTML=items.map(n=>{const heading=n.group!==group?`<div class="notification-group-label">${n.group}</div>`:'';group=n.group;return `${heading}<article class="notification-item"><span class="notification-icon" style="background:${n.color}22;color:${n.color}">${n.icon}</span><div class="notification-body"><p>${n.text}</p><small>${n.time}</small></div>${n.unread?'<i class="notification-unread"></i>':''}</article>`;}).join('');
}
// ---- Real data from the API (src/api/main.py) ----
// Start the API first:  uvicorn src.api.main:app --reload
// Use the same origin in production. Live Server keeps its local API fallback.
const API_URL=(window.CAREER_API_URL || (location.port === '5500' ? 'http://127.0.0.1:8000' : '')).replace(/\/$/, '');
let activeMapFilters={workMode:'',jobType:''};
function normalizeCountry(value) {
  return String(value||'').trim().toLocaleLowerCase();
}

async function fetchJson(path) {
  const response=await fetch(API_URL+path);
  if(!response.ok) throw new Error(`API answered ${response.status} for ${path}`);
  return response.json();
}

// Job titles and company names come from the internet, so we escape them before showing them.
function escapeHtml(value) {
  const entities={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
  return String(value==null?'':value).replace(/[&<>"']/g,char=>entities[char]);
}
function safeUrl(value) {
  return /^https?:\/\//i.test(String(value||''))?escapeHtml(value):'#';
}
function formatNumber(value) {
  return Number(value||0).toLocaleString('en-US');
}
function isChecked(selector) {
  const box=document.querySelector(selector);
  return box?box.checked:true;
}
function showApiNotice(message) {
  const notice=document.querySelector('#file-protocol-notice');
  if(notice){notice.textContent=message;notice.hidden=false;}
}
function hideApiNotice() {
  const notice=document.querySelector('#file-protocol-notice');
  if(notice) notice.hidden=true;
}

// Show only the markers allowed by the country search, and hide overlapping bubbles.
function updateMapFilters() {
  const countryInput=document.querySelector('#map-country');
  const query=countryInput?countryInput.value.trim():'';
  const markers=window.careerMapMarkers||[];
  const selected=query?markers.find(item=>normalizeCountry(item.country)===normalizeCountry(query)):null;
  const status=document.querySelector('#map-country-status');
  if(status) status.textContent=query&&!selected
    ?`No mapped jobs found for "${query}". Choose a country from the suggestions.`
    :!query&&!markers.length?'No map locations match these filters.':'';
  (window.careerMapMarkers||[]).forEach(item=>{
    item.allowed=!query||item===selected;
  });
  declutterMarkers();
  return selected;
}

// ---- Two levels on the map ----
// Zoomed out : one bubble per country (number of jobs).
// Zoomed in  : one logo per company and city (where the jobs are).
const CITY_ZOOM=4.5;        // zoom in beyond this level and the company logos appear
const COMPANY_LIMIT=60;     // how many companies are drawn at once
const COMPANY_PIN_SIZE=42;  // logo circle size in pixels (also set in style.css)

function isCityMode() {
  return !!window.careerMap&&window.careerMap.getZoom()>=CITY_ZOOM;
}

// The biggest bubbles come first. A smaller one is hidden when it would sit on a bigger one.
// Zoom in and the hidden ones appear.
function declutterMarkers() {
  const map=window.careerMap;
  if(!map) return;
  const cityMode=isCityMode();
  const placed=[];
  const place=(x,y,size)=>{
    if(placed.some(other=>Math.hypot(other.x-x,other.y-y)<(other.size+size)/2*0.9)) return false;
    placed.push({x,y,size});
    return true;
  };
  (window.careerMapMarkers||[]).forEach(item=>{
    let show=!cityMode&&item.allowed!==false;
    if(show){const point=map.project(item.lngLat);show=place(point.x,point.y,item.size);}
    item.el.style.display=show?'':'none';
  });
  (window.careerCompanyMarkers||[]).forEach(item=>{
    let show=cityMode;
    if(show){const point=map.project(item.lngLat);show=place(point.x+item.offset[0],point.y+item.offset[1],item.size);}
    item.el.style.display=show?'':'none';
  });
}

// ---- Company logos ----
// Logos come from Logo.dev (free key). Without a key you see a colored letter instead.
function logoName(name) {
  const cleaned=String(name).replace(/\(.*?\)/g,' ')
    .replace(/\b(gmbh|ag|se|kg|ug|ltd|limited|inc|llc|b\.?v\.?|n\.?v\.?|s\.?a\.?|plc|group|holding|corp|corporation)\b\.?/gi,' ')
    .replace(/[&,]+/g,' ').replace(/\s+/g,' ').trim();
  return cleaned||String(name);
}
function avatarColor(name) {
  let hash=0;
  for(const char of String(name)) hash=(hash*31+char.charCodeAt(0))%360;
  return `hsl(${hash},55%,42%)`;
}
function companyLogoHtml(name) {
  const initial=escapeHtml(String(name).trim().charAt(0).toUpperCase()||'?');
  const hasToken=LOGO_DEV_TOKEN&&!LOGO_DEV_TOKEN.startsWith('PASTE');
  const image=hasToken
    ? `<img src="https://img.logo.dev/name/${encodeURIComponent(logoName(name))}?token=${encodeURIComponent(LOGO_DEV_TOKEN)}&size=96&format=png" alt="" loading="lazy" onload="this.parentElement.classList.add('has-logo')" onerror="this.remove()">`
    : '';
  return `<span class="company-logo" style="background:${avatarColor(name)}"><b>${initial}</b>${image}</span>`;
}

// Companies in the same city are spread around the city point (like sunflower seeds),
// so their logos do not sit on top of each other.
function sunflowerOffset(index,size) {
  if(index===0) return [0,0];
  const radius=size*Math.sqrt(index);
  const angle=index*2.399963;
  return [Math.round(radius*Math.cos(angle)),Math.round(radius*Math.sin(angle))];
}

function companyPopupHtml(item,jobs) {
  const jobList=jobs.map(job=>
    `<li><div><a href="${safeUrl(job.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title)}</a>`+
    `<small>${escapeHtml([job.job_type,job.work_mode].filter(Boolean).join(' - '))}</small></div></li>`).join('');
  return `<div class="country-popup"><div class="popup-head">${companyLogoHtml(item.company)}<div>`+
    `<h4>${escapeHtml(item.company)}</h4>`+
    `<div class="popup-count">${escapeHtml(item.city)}, ${escapeHtml(item.country)} - <b>${formatNumber(item.openings)}</b> open jobs</div>`+
    `</div></div><h5>Open jobs</h5><ul>${jobList||'<li>No data</li>'}</ul></div>`;
}

async function loadCompanyDetails(item,popup) {
  const query=`company=${encodeURIComponent(item.company)}&city=${encodeURIComponent(item.city)}`;
  try {
    const jobs=await fetchJson(`/jobs?${query}&limit=6`);
    popup.setHTML(companyPopupHtml(item,jobs));
  } catch(error) {
    console.error(error);
    popup.setHTML(`<div class="country-popup"><h4>${escapeHtml(item.company)}</h4><div class="popup-count">Could not load details.</div></div>`);
  }
}

function clearCompanyMarkers() {
  (window.careerCompanyMarkers||[]).forEach(item=>item.marker.remove());
  window.careerCompanyMarkers=[];
}

let companyRequestId=0;
let companyTimer=null;

// Ask the API for the companies inside the part of the map you are looking at.
async function loadCompanyMarkers() {
  const map=window.careerMap;
  if(!map) return;
  const requestId=++companyRequestId;   // lets us ignore answers that arrive too late

  if(!isCityMode()){clearCompanyMarkers();declutterMarkers();return;}

  const bounds=map.getBounds();
  const params=new URLSearchParams({
    min_lat:String(bounds.getSouth()),max_lat:String(bounds.getNorth()),
    min_lng:String(Math.max(-180,bounds.getWest())),max_lng:String(Math.min(180,bounds.getEast())),
    limit:String(COMPANY_LIMIT),jobs:String(isChecked('#jobs-toggle')),
    internships:String(isChecked('#internships-toggle')),
  });
  const countryInput=document.querySelector('#map-country');
  const countryQuery=countryInput?countryInput.value.trim():'';
  const selectedCountry=countryQuery&&(window.careerMapMarkers||[]).find(item=>normalizeCountry(item.country)===normalizeCountry(countryQuery));
  if(countryQuery&&!selectedCountry){clearCompanyMarkers();return;}
  if(selectedCountry) params.set('country',selectedCountry.country);
  if(activeMapFilters.workMode) params.set('work_mode',activeMapFilters.workMode);
  if(activeMapFilters.jobType) params.set('job_type',activeMapFilters.jobType);
  const query=`/company-markers?${params.toString()}`;
  let rows;
  try {
    rows=await fetchJson(query);
    hideApiNotice();
  } catch(error) {
    console.error(error);
    showApiNotice('Could not reach the API. Start it with: uvicorn src.api.main:app --reload');
    return;
  }
  if(requestId!==companyRequestId) return;   // the map moved again: a newer request is running

  clearCompanyMarkers();
  const countInCity={};
  window.careerCompanyMarkers=rows.map(row=>{
    const cityKey=`${row.city}|${row.country}`;
    const index=countInCity[cityKey]||0;
    countInCity[cityKey]=index+1;
    const offset=sunflowerOffset(index,COMPANY_PIN_SIZE);

    const el=document.createElement('div');
    el.className='cm-marker';
    el.title=`${row.company} - ${row.city}`;
    el.innerHTML=`<span class="company-pin" style="width:${COMPANY_PIN_SIZE}px;height:${COMPANY_PIN_SIZE}px">`+
      `${companyLogoHtml(row.company)}${row.openings>1?`<i class="pin-count">${formatNumber(row.openings)}</i>`:''}</span>`;

    const lngLat=[Number(row.longitude),Number(row.latitude)];
    const item={company:row.company,city:row.city,country:row.country,openings:row.openings,el,lngLat,offset,size:COMPANY_PIN_SIZE};
    const popup=new maplibregl.Popup({offset:[offset[0],offset[1]-COMPANY_PIN_SIZE/2-6],maxWidth:'320px'})
      .setHTML(`<div class="country-popup"><h4>${escapeHtml(row.company)}</h4><div class="popup-count">Loading...</div></div>`);
    popup.on('open',()=>loadCompanyDetails(item,popup));
    item.marker=new maplibregl.Marker({element:el,offset}).setLngLat(lngLat).setPopup(popup).addTo(map);
    return item;
  });
  declutterMarkers();
}

function scheduleCompanyLoad() {
  clearTimeout(companyTimer);
  companyTimer=setTimeout(loadCompanyMarkers,250);   // wait until the map stops moving
}

// The text inside a country popup.
function popupHtml(item,companies,jobs) {
  const companyList=companies.map(company=>
    `<li><div>${escapeHtml(company.company)}</div><span>${formatNumber(company.openings)}</span></li>`).join('');
  const jobList=jobs.map(job=>
    `<li><div><a href="${safeUrl(job.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title)}</a>`+
    `<small>${escapeHtml(job.company)}${job.city?' - '+escapeHtml(job.city):''}</small></div></li>`).join('');
  return `<div class="country-popup"><h4>${escapeHtml(item.country)}</h4>`+
    `<div class="popup-count"><b>${formatNumber(item.jobs)}</b> jobs, <b>${formatNumber(item.internships)}</b> internships</div>`+
    `<h5>Top hiring companies</h5><ul>${companyList||'<li>No data</li>'}</ul>`+
    `<h5>Latest jobs</h5><ul>${jobList||'<li>No data</li>'}</ul></div>`;
}

// When a bubble is clicked, ask the API for that country's top companies and latest jobs.
async function loadCountryDetails(item,popup) {
  const country=encodeURIComponent(item.country);
  try {
    const [companies,jobs]=await Promise.all([
      fetchJson(`/companies?country=${country}&limit=5`),
      fetchJson(`/jobs?country=${country}&limit=5`)
    ]);
    popup.setHTML(popupHtml(item,companies,jobs));
  } catch(error) {
    console.error(error);
    popup.setHTML(`<div class="country-popup"><h4>${escapeHtml(item.country)}</h4><div class="popup-count">Could not load details.</div></div>`);
  }
}

// Fill the country dropdown with the countries that really have jobs.
function fillCountryDropdown(markers) {
  const datalist=document.querySelector('#map-country-options');
  const select=document.querySelector('#country-filter');
  const current=select?select.value:'';
  if(datalist) datalist.replaceChildren();
  if(select) select.innerHTML='<option value="">All countries</option>';
  [...new Set(markers.map(marker=>marker.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b)).forEach(country=>{
    const option=document.createElement('option');
    option.value=country;option.textContent=country;
    if(datalist) datalist.appendChild(option.cloneNode(true));
    if(select) select.appendChild(option);
  });
  if(select) select.value=markers.some(marker=>marker.country===current)?current:'';
}

// Ask the API for the country markers and draw them on the map.
async function loadMarkers() {
  const map=window.careerMap;
  if(!map) return;
  let markers=[];
  try {
    const params=new URLSearchParams({jobs:String(isChecked('#jobs-toggle')),internships:String(isChecked('#internships-toggle'))});
    if(activeMapFilters.workMode) params.set('work_mode',activeMapFilters.workMode);
    if(activeMapFilters.jobType) params.set('job_type',activeMapFilters.jobType);
    markers=await fetchJson(`/map-markers?${params.toString()}`);
    hideApiNotice();
  } catch(error) {
    console.error(error);
    showApiNotice('Could not reach the API. Start it with: uvicorn src.api.main:app --reload');
  }

  (window.careerMapMarkers||[]).forEach(item=>item.marker.remove());   // remove old bubbles
  const maxCount=Math.max(1,...markers.map(marker=>marker.jobs));
  window.careerMapMarkers=markers.map(data=>{
    const size=Math.round(38+30*Math.sqrt(data.jobs/maxCount));   // bigger country = bigger bubble
    const el=document.createElement('div');
    el.className='cm-marker';
    el.title=`${data.country}: ${formatNumber(data.jobs)} jobs`;
    el.innerHTML=`<span class="country-bubble" style="width:${size}px;height:${size}px"><b>${formatNumber(data.jobs)}</b></span>`;

    const lngLat=[Number(data.longitude),Number(data.latitude)];
    const item={country:data.country,jobs:data.jobs,internships:data.internships,el,lngLat,size,allowed:true};
    const popup=new maplibregl.Popup({offset:size/2+6,maxWidth:'300px'})
      .setHTML(`<div class="country-popup"><h4>${escapeHtml(data.country)}</h4><div class="popup-count">Loading...</div></div>`);
    popup.on('open',()=>loadCountryDetails(item,popup));
    item.marker=new maplibregl.Marker({element:el}).setLngLat(lngLat).setPopup(popup).addTo(map);
    return item;
  });
  fillCountryDropdown(markers);
  updateMapFilters();
}

// A small card on the map with the total number of jobs in the database.
async function loadTotals() {
  const target=document.querySelector('#career-map');
  const card=target?target.parentElement:null;
  if(!card) return;
  try {
    const stats=await fetchJson('/stats');
    let badge=card.querySelector('.map-total');
    if(!badge){badge=document.createElement('div');badge.className='map-total';card.appendChild(badge);}
    badge.innerHTML=`<b>${formatNumber(stats.total_jobs)}</b><small>jobs in the database</small><small class="hint">Zoom in to see companies</small>`;
  } catch(error) {
    console.warn('Stats failed:',error);
  }
}

// ---- Interactive world map: MapLibre GL + free OpenFreeMap vector tiles (no API key) ----
// Zooming reveals country, state/province and local boundaries, then cities, towns and villages.
const MAPLIBRE_JS='https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js';
const MAPLIBRE_CSS='https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css';
const STYLE_URL='https://tiles.openfreemap.org/styles/positron';
const WORLD=[[-180,-58],[180,80]];   // [lng,lat] corners: all continents, without most of Antarctica

// Map colors: change these to restyle the map.
const WATER='#04060c';                 // dark black water
const LAND='#18223f', LAND_ALT='#1b2748', BUILDING='#243564';   // dark navy land
const GOLD='#c99a2e', GOLD_DARK='#000000';                      // golden borders
const TEXT_ON_LAND='#e6edff', HALO_ON_LAND='#0a1020';           // labels on land
const TEXT_ON_WATER='#8fa6d6', HALO_ON_WATER='#04060c';         // labels on water
const WATERWAY='#1b3a78', ROAD='#2a3a66', ROAD_CASING='#0c1428'; // rivers and roads
const LABELS_START_ZOOM=3;   // country and ocean names appear from this zoom (world view stays clean)

function loadMapLibre() {
  return new Promise((resolve,reject)=>{
    if(window.maplibregl) return resolve();
    const css=document.createElement('link');
    css.rel='stylesheet';css.href=MAPLIBRE_CSS;document.head.appendChild(css);
    const js=document.createElement('script');
    js.src=MAPLIBRE_JS;js.onload=resolve;js.onerror=reject;document.head.appendChild(js);
  });
}

// Take the free OpenFreeMap "positron" style and recolor it:
// dark blue water, light blue land, gold borders, readable labels.
function restyleStyle(style) {
  const vectorSource=Object.keys(style.sources).find(key=>style.sources[key].type==='vector');
  const layers=[];
  let boundariesAdded=false;

  // Our own boundary layers: country (thick), state/province (medium), local (thin, appears later).
  const boundaryLayers=[
    {id:'gold-local',type:'line',source:vectorSource,'source-layer':'boundary',minzoom:6,
      filter:['all',['>=',['get','admin_level'],5],['!=',['get','maritime'],1]],
      layout:{'line-join':'round'},
      paint:{'line-color':GOLD,'line-opacity':0.75,'line-dasharray':[1,2],
        'line-width':['interpolate',['linear'],['zoom'],6,0.5,12,1.4]}},
    {id:'gold-state',type:'line',source:vectorSource,'source-layer':'boundary',minzoom:3,
      filter:['all',['any',['==',['get','admin_level'],3],['==',['get','admin_level'],4]],['!=',['get','maritime'],1]],
      layout:{'line-join':'round'},
      paint:{'line-color':GOLD,'line-opacity':0.95,'line-dasharray':[3,2],
        'line-width':['interpolate',['linear'],['zoom'],3,0.6,8,1.6,14,2.4]}},
    {id:'gold-country-casing',type:'line',source:vectorSource,'source-layer':'boundary',
      filter:['all',['==',['get','admin_level'],2],['!=',['get','maritime'],1]],
      layout:{'line-join':'round','line-cap':'round'},
      paint:{'line-color':GOLD_DARK,'line-opacity':0.3,
        'line-width':['interpolate',['linear'],['zoom'],0,2,8,5,14,7]}},
    {id:'gold-country',type:'line',source:vectorSource,'source-layer':'boundary',
      filter:['all',['==',['get','admin_level'],2],['!=',['get','maritime'],1]],
      layout:{'line-join':'round','line-cap':'round'},
      paint:{'line-color':GOLD,
        'line-opacity':['interpolate',['linear'],['zoom'],0,0.35,4,0.75,8,1],
        'line-width':['interpolate',['linear'],['zoom'],0,0.4,4,0.9,8,2.2,14,3.4]}}
  ];

  style.layers.forEach(layer=>{
    const sourceLayer=layer['source-layer'];
    layer.paint=layer.paint||{};
    layer.layout=layer.layout||{};

    // Insert our boundary layers just below the first label layer.
    if(layer.type==='symbol'&&!boundariesAdded){layers.push(...boundaryLayers);boundariesAdded=true;}

    if(layer.type==='background'){
      layer.paint['background-color']=LAND;
    } else if(sourceLayer==='boundary'){
      return;   // drop the original boundary lines; ours replace them
    } else if(layer.type==='fill'){
      if(sourceLayer==='water'){layer.paint['fill-color']=WATER;layer.paint['fill-opacity']=1;}
      else if(sourceLayer==='building'){layer.paint['fill-color']=BUILDING;layer.paint['fill-opacity']=0.6;}
      else {layer.paint['fill-color']=LAND_ALT;layer.paint['fill-opacity']=0.55;}
      delete layer.paint['fill-outline-color'];
      delete layer.paint['fill-pattern'];
    } else if(layer.type==='line'){
      if(sourceLayer==='waterway'){layer.paint['line-color']=WATERWAY;}
      else if(sourceLayer==='transportation'||sourceLayer==='aeroway'){
        layer.paint['line-color']=layer.id.includes('casing')?ROAD_CASING:ROAD;
        layer.paint['line-opacity']=0.85;
      } else {layer.paint['line-color']=ROAD_CASING;}
    } else if(layer.type==='symbol'){
      if(sourceLayer==='poi'||sourceLayer==='housenumber'){layer.layout.visibility='none';}
      else {
        const onWater=sourceLayer==='water_name'||sourceLayer==='waterway';
        layer.paint['text-color']=onWater?TEXT_ON_WATER:TEXT_ON_LAND;
        layer.paint['text-halo-color']=onWater?HALO_ON_WATER:HALO_ON_LAND;
        layer.paint['text-halo-width']=onWater?1.2:1.6;
        layer.paint['text-halo-blur']=0.4;
        // Reveal towns and villages a little earlier while zooming in.
        const id=layer.id.toLowerCase();
        const earliest=id.includes('village')?8.5:id.includes('town')?6:id.includes('hamlet')?10:id.includes('state')?3.5:null;
        if(earliest!==null&&layer.minzoom!==undefined&&layer.minzoom>earliest) layer.minzoom=earliest;
        // Keep the world view clean: country and ocean names start from LABELS_START_ZOOM.
        if(sourceLayer==='water_name'||(sourceLayer==='place'&&(id.includes('country')||id.includes('continent')))) layer.minzoom=Math.max(layer.minzoom||0,LABELS_START_ZOOM);
      }
    }
    layers.push(layer);
  });
  if(!boundariesAdded) layers.push(...boundaryLayers);
  style.layers=layers;
  return style;
}

// Show the whole world inside the card.
function fitWorld(map,animate=true) {
  map.resize();
  map.fitBounds(WORLD,{padding:0,duration:animate?800:0});
}
// Do not allow zooming out further than the whole world.
function keepWorldFit(map) {
  map.resize();
  const camera=map.cameraForBounds(WORLD,{padding:0});
  if(!camera) return;
  map.setMinZoom(camera.zoom);
  if(map.getZoom()<camera.zoom) map.jumpTo({zoom:camera.zoom});
}

async function initMap() {
  const target=document.querySelector('#career-map');
  const notice=document.querySelector('#file-protocol-notice');
  if(notice) notice.hidden=true;

  // Jobs and Internships are ticked by default so all markers show on first load.
  const jobsToggle=document.querySelector('#jobs-toggle');
  const internshipsToggle=document.querySelector('#internships-toggle');
  if(jobsToggle) jobsToggle.checked=true;
  if(internshipsToggle) internshipsToggle.checked=true;

  try { await loadMapLibre(); }
  catch(error){target.innerHTML='<div class="map-offline">The map needs an internet connection to load.</div>';return;}

  let style;
  try {
    const response=await fetch(STYLE_URL);
    style=restyleStyle(await response.json());
  } catch(error){
    target.innerHTML='<div class="map-offline">Could not load the map style. Check your internet connection.</div>';
    return;
  }

  const map=new maplibregl.Map({
    container:target,
    style,
    bounds:WORLD,
    fitBoundsOptions:{padding:0},
    minZoom:0.5,
    maxZoom:18,
    dragRotate:false,
    pitchWithRotate:false,
    attributionControl:{compact:true}
  });
  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
  window.careerMap=map;

  window.careerMapMarkers=[];   // filled by loadMarkers() with real data from the API

  let ready=false;
  map.on('load',()=>{ready=true;keepWorldFit(map);loadMarkers();loadTotals();});
  map.on('moveend',()=>{declutterMarkers();scheduleCompanyLoad();});
  map.on('resize',declutterMarkers);
  map.on('error',()=>{
    if(!ready&&notice){notice.textContent='Could not load the map. Check your internet connection.';notice.hidden=false;}
  });
  window.addEventListener('resize',()=>keepWorldFit(map));
}

document.querySelectorAll('[data-notif-tab]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-notif-tab]').forEach(tab=>tab.classList.remove('active'));
  button.classList.add('active');renderNotifications(button.dataset.notifTab);
}));
// Jobs / Internships checkboxes: ask the API again, so the numbers change.
document.querySelectorAll('.map-filter-row input[type="checkbox"]').forEach(input=>input.addEventListener('change',()=>{loadMarkers();loadCompanyMarkers();}));
document.querySelectorAll('[data-nav-kind]').forEach(link=>link.addEventListener('click',event=>{
  const kind=link.dataset.navKind;
  if(kind==='companies'){
    const selected=updateMapFilters();
    const target=selected||(window.careerMapMarkers||[]).find(item=>item.allowed!==false);
    if(target&&window.careerMap) window.careerMap.flyTo({center:target.lngLat,zoom:CITY_ZOOM+0.5,duration:1200});
    return;
  }
  event.preventDefault();
  document.querySelector('#map')?.scrollIntoView({behavior:'smooth',block:'start'});
  const jobs=document.querySelector('#jobs-toggle');
  const internships=document.querySelector('#internships-toggle');
  const showJobs=kind==='jobs';
  jobs.checked=showJobs;
  internships.checked=!showJobs;
  activeMapFilters.jobType=showJobs?'':'Internship';
  document.querySelector('#type-filter').value=activeMapFilters.jobType;
  loadMarkers();
  loadCompanyMarkers();
}));
// Country search: keep only the chosen country's markers and zoom to it.
function applyCountryInput() {
  const countryInput=document.querySelector('#map-country');
  const query=countryInput?countryInput.value.trim():'';
  const selected=updateMapFilters();
  const quickCountry=document.querySelector('#country-filter');
  if(selected){
    countryInput.value=selected.country;
    if(quickCountry) quickCountry.value=selected.country;
  } else if(quickCountry) quickCountry.value='';
  const map=window.careerMap;
  if(!query){if(map) fitWorld(map);loadCompanyMarkers();return;}
  if(!selected){clearCompanyMarkers();return;}
  if(map) map.flyTo({center:selected.lngLat,zoom:5,duration:1200});
  loadCompanyMarkers();
}
document.querySelector('#map-country')?.addEventListener('change',applyCountryInput);
document.querySelector('#country-filter')?.addEventListener('change',event=>{
  const input=document.querySelector('#map-country');
  if(input) input.value=event.target.value;
  applyCountryInput();
});
document.querySelector('.apply-filter')?.addEventListener('click',async()=>{
  activeMapFilters={
    workMode:document.querySelector('#mode-filter')?.value||'',
    jobType:document.querySelector('#type-filter')?.value||'',
  };
  const country=document.querySelector('#country-filter')?.value||'';
  const input=document.querySelector('#map-country');
  if(input) input.value=country;
  await loadMarkers();
  applyCountryInput();
  loadCompanyMarkers();
});
document.querySelector('.reset-filters')?.addEventListener('click',async()=>{
  document.querySelector('#country-filter').value='';
  document.querySelector('#mode-filter').value='';
  document.querySelector('#type-filter').value='';
  activeMapFilters={workMode:'',jobType:''};
  document.querySelector('#map-country').value='';
  await loadMarkers();
  applyCountryInput();
});
document.querySelector('#reset-map')?.addEventListener('click',async()=>{
  document.querySelector('#country-filter').value='';
  document.querySelector('#map-country').value='';
  activeMapFilters={workMode:'',jobType:''};
  document.querySelector('#mode-filter').value='';
  document.querySelector('#type-filter').value='';
  await loadMarkers();
  applyCountryInput();
});
document.querySelector('#mark-read')?.addEventListener('click',()=>{notifications.forEach(item=>item.unread=false);renderNotifications(document.querySelector('[data-notif-tab].active').dataset.notifTab);});
document.querySelector('.create-alert')?.addEventListener('click',()=>{
  const title=prompt('What would you like to be alerted about?\nExample: Data analyst \u00b7 Remote');
  if(title?.trim()){alerts.unshift({title:title.trim(),detail:'Daily \u00b7 New alert',icon:'\u2727',color:'#b69cff',on:true});renderAlerts();}
});
try{renderAlerts();renderNotifications();}catch(error){console.warn('Panels failed:',error);}
initMap().catch(error=>console.error('Map failed:',error));

// Show the signed-in account and revoke its session when the profile is clicked.
async function loadProfile() {
  const token=sessionStorage.getItem('careerMapToken');
  const link=document.querySelector('#profile-link');
  if(!link||!token) return;
  try {
    const response=await fetch(`${API_URL}/auth/me`,{headers:{Authorization:`Bearer ${token}`}});
    if(!response.ok) throw new Error('Session expired');
    const user=await response.json();
    const initials=user.name.trim().split(/\s+/).slice(0,2).map(part=>part[0]).join('').toUpperCase();
    document.querySelector('#profile-name').textContent=user.name;
    document.querySelector('#profile-avatar').textContent=initials;
    document.querySelector('#profile-status').textContent='Sign out';
    link.href='#sign-out';
    link.setAttribute('aria-label',`Sign out ${user.name}`);
    link.addEventListener('click',async(event)=>{
      event.preventDefault();
      try {await fetch(`${API_URL}/auth/logout`,{method:'POST',headers:{Authorization:`Bearer ${token}`}});} catch(error) {console.warn('Could not revoke session:',error);}
      sessionStorage.removeItem('careerMapToken');
      sessionStorage.removeItem('careerMapUser');
      window.location.reload();
    },{once:true});
  } catch(error) {
    sessionStorage.removeItem('careerMapToken');
    sessionStorage.removeItem('careerMapUser');
    console.info('No active account session:',error.message);
  }
}
loadProfile();
