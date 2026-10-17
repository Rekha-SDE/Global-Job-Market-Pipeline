// Add your Logo.dev token here when you are ready to load company logos.
const LOGO_DEV_TOKEN = "PASTE_YOUR_TOKEN_HERE";

// Sample marker data; replace this array with API results later.
const companies = [
  {name:'Google',city:'Zurich, Switzerland',coords:[47.376,8.541],country:'Switzerland',kind:'internship',role:'Software Engineering Intern',tag:'Internship',color:'#4285f4'},
  {name:'Microsoft',city:'Singapore',coords:[1.352,103.82],country:'Singapore',kind:'job',role:'Data Engineer',tag:'Full-time',color:'#00a4ef'},
  {name:'Amazon',city:'New York, United States',coords:[40.713,-74.006],country:'United States',kind:'job',role:'Backend Developer',tag:'Full-time',color:'#ff9900'},
  {name:'Apple',city:'Cupertino, United States',coords:[37.323,-122.032],country:'United States',kind:'internship',role:'Machine Learning Intern',tag:'Internship',color:'#a2aaad'},
  {name:'Spotify',city:'Stockholm, Sweden',coords:[59.329,18.069],country:'Sweden',kind:'job',role:'Machine Learning Engineer',tag:'Full-time',color:'#1db954'},
  {name:'Tesla',city:'Berlin, Germany',coords:[52.52,13.405],country:'Germany',kind:'job',role:'Embedded Software Engineer',tag:'Full-time',color:'#e82127'},
  {name:'Meta',city:'London, United Kingdom',coords:[51.507,-0.128],country:'United Kingdom',kind:'job',role:'Data Scientist',tag:'Full-time',color:'#0866ff'},
  {name:'ASML',city:'Eindhoven, Netherlands',coords:[51.441,5.478],country:'Netherlands',kind:'internship',role:'Software Intern',tag:'Internship',color:'#00a3e0'},
  {name:'Swisscom',city:'Bern, Switzerland',coords:[46.948,7.447],country:'Switzerland',kind:'internship',role:'Data Analytics Intern',tag:'Internship',color:'#ff3b30'},
  {name:'NVIDIA',city:'Santa Clara, United States',coords:[37.354,-121.956],country:'United States',kind:'internship',role:'Data Science Intern',tag:'Internship',color:'#76b900'}
];

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
function updateMapFilters() {
  const countrySelect=document.querySelector('#map-country');
  const selectedCountry=countrySelect?countrySelect.value:'all';
  (window.careerMapMarkers||[]).forEach(item=>{
    const toggle=document.querySelector(`#${item.kind==='job'?'jobs':'internships'}-toggle`);
    const typeEnabled=toggle?toggle.checked:true;
    const countryEnabled=selectedCountry==='all'||item.country===selectedCountry;
    item.allowed=typeEnabled&&countryEnabled;
  });
  declutterMarkers();
}

// Hide a logo when it would sit on top of an earlier one. Zoom in and the hidden ones appear.
function declutterMarkers() {
  const map=window.careerMap;
  if(!map||!window.careerMapMarkers) return;
  const placed=[];
  window.careerMapMarkers.forEach(item=>{
    let show=item.allowed!==false;
    if(show){
      const point=map.project(item.lngLat);
      if(placed.some(other=>Math.hypot(other.x-point.x,other.y-point.y)<MARKER_SIZE*0.95)) show=false;
      else placed.push(point);
    }
    item.el.style.display=show?'':'none';
  });
}

// Website of each company: used to load its real logo.
const COMPANY_DOMAINS={
  Google:'google.com',Microsoft:'microsoft.com',Amazon:'amazon.com',Apple:'apple.com',Meta:'meta.com',
  Tesla:'tesla.com',Spotify:'spotify.com',ASML:'asml.com',Swisscom:'swisscom.ch',NVIDIA:'nvidia.com'
};

// Company marker: shows the real logo in a white circle.
// Logo.dev is used when a token is set (sharper), otherwise Google's free favicon service.
// If no logo loads, the colored letter circle stays.
function companyLogo(company) {
  const fallback=`<span class="map-company-fallback" style="--company-color:${company.color}">${company.name[0]}</span>`;
  const domain=COMPANY_DOMAINS[company.name]||`${company.name.toLowerCase().replace(/[^a-z0-9]/g,'')}.com`;
  const hasToken=LOGO_DEV_TOKEN && !LOGO_DEV_TOKEN.startsWith('PASTE');
  const logoUrl=hasToken
    ? `https://img.logo.dev/${domain}?token=${LOGO_DEV_TOKEN}&size=128`
    : `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
  const img=`<img src="${logoUrl}" alt="${company.name} logo" style="display:none" onload="this.style.display='block';this.previousElementSibling.style.display='none'" onerror="this.remove()">`;
  return `<span class="map-company-pin">${fallback}${img}</span>`;
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
const MARKER_SIZE=38;        // company logo circle size in pixels (also set in style.css)

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

  // Company markers: round pins (letter or logo) with a popup on click.
  window.careerMapMarkers=companies.map(company=>{
    const el=document.createElement('div');
    el.className='cm-marker';
    el.innerHTML=companyLogo(company);
    const popup=new maplibregl.Popup({offset:30,maxWidth:'260px'}).setHTML(`<div class="company-popup"><b>${company.name}</b><span>${company.role}</span><small>${company.city}</small><em>${company.tag}</em></div>`);
    new maplibregl.Marker({element:el}).setLngLat([company.coords[1],company.coords[0]]).setPopup(popup).addTo(map);
    return {kind:company.kind,country:company.country,el,lngLat:[company.coords[1],company.coords[0]],allowed:true};
  });
  updateMapFilters();

  let ready=false;
  map.on('load',()=>{ready=true;keepWorldFit(map);declutterMarkers();});
  map.on('zoomend',declutterMarkers);
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
document.querySelectorAll('.map-filter-row input').forEach(input=>input.addEventListener('change',updateMapFilters));
document.querySelector('#map-country')?.addEventListener('change',event=>{
  updateMapFilters();
  const map=window.careerMap;
  if(!map) return;
  const country=event.target.value;
  if(country==='all'){fitWorld(map);return;}
  const places=companies.filter(item=>item.country===country);
  if(!places.length) return;
  const bounds=new maplibregl.LngLatBounds();
  places.forEach(item=>bounds.extend([item.coords[1],item.coords[0]]));
  map.fitBounds(bounds,{padding:80,maxZoom:6,duration:1200});
});
document.querySelector('#reset-map')?.addEventListener('click',()=>{
  const countrySelect=document.querySelector('#map-country');if(countrySelect) countrySelect.value='all';
  updateMapFilters();
  if(window.careerMap) fitWorld(window.careerMap);
});
document.querySelector('#mark-read')?.addEventListener('click',()=>{notifications.forEach(item=>item.unread=false);renderNotifications(document.querySelector('[data-notif-tab].active').dataset.notifTab);});
document.querySelector('.create-alert')?.addEventListener('click',()=>{
  const title=prompt('What would you like to be alerted about?\nExample: Data analyst \u00b7 Remote');
  if(title?.trim()){alerts.unshift({title:title.trim(),detail:'Daily \u00b7 New alert',icon:'\u2727',color:'#b69cff',on:true});renderAlerts();}
});
try{renderAlerts();renderNotifications();}catch(error){console.warn('Panels failed:',error);}
initMap().catch(error=>console.error('Map failed:',error));