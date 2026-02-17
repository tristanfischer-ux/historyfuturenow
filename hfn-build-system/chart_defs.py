#!/usr/bin/env python3
"""
Chart definitions for History Future Now articles.
Returns a dict of slug -> list of chart dicts, each with:
  - id: canvas element id
  - figure_num: Figure N label
  - title: chart title
  - desc: short description
  - source: data source citation
  - position: 'after_para_N' or 'after_heading_TEXT' or 'before_end'
  - js: Chart.js JavaScript code
  - tall: boolean for taller chart area
"""

# Shared color scheme matching demographic-timebomb
COLORS = """const C = {
  accent:'#c43425', blue:'#2563eb', green:'#0d9a5a', amber:'#b8751a',
  purple:'#7c3aed', teal:'#0c8f8f', cyan:'#0284c7', dim:'#8a8479',
  rose:'#e11d48', indigo:'#4f46e5', emerald:'#059669', slate:'#475569',
  text:'#1a1815', grid:'#f2eeea'
};
const ds=(l,d,c,da)=>({label:l,data:d,borderColor:c,backgroundColor:c+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:c,borderWidth:2.5,borderDash:da||[]});
const yearTick=v=>String(v);
const gridOpts={x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:yearTick}},y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11}}}};
const legend={display:true,position:'bottom',labels:{padding:16,usePointStyle:true,pointStyle:'circle',font:{size:12}}};
const noLegend={display:false};
const tooltipStyle={backgroundColor:'#1a1815ee',titleFont:{size:13},bodyFont:{size:12},padding:10,cornerRadius:6};
Chart.defaults.plugins.tooltip.callbacks.title=function(items){if(!items.length)return'';const l=items[0].label;return typeof l==='string'&&/^[\d,]+$/.test(l.trim())?l.replace(/,/g,''):l;};
const chartPad={bottom:20,left:8,right:8,top:8};
if(Chart.defaults.plugins.annotation)Chart.defaults.plugins.annotation.clip=false;
Chart.defaults.scales.category.ticks.autoSkip=false;
const xy=(xs,ys)=>xs.map((x,i)=>({x:+x,y:ys[i]}));
const dxy=(l,xs,ys,c,da)=>({label:l,data:xy(xs,ys),borderColor:c,backgroundColor:c+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:c,borderWidth:2.5,borderDash:da||[]});
const linX=(min,max,extra)=>{const e=extra||{};const t=e.ticks||{};const rest={};for(const k in e)if(k!=='ticks')rest[k]=e[k];return{type:'linear',min,max,grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:yearTick,...t},...rest};};
"""

def get_all_charts():
    charts = {}

    # ═══════════════════════════════════════════════════════
    # TIER 1: HIGH IMPACT
    # ═══════════════════════════════════════════════════════

    # ─── 1. UNINTENDED CONSEQUENCES OF WAR ───
    charts['the-unintended-consequences-of-war-how-the-loss-of-young-men-transformed-womens-roles-in-society-and-ushered-in-the-welfare-state'] = [
        {
            'id': 'warChart1', 'figure_num': 1,
            'title': 'Estimated Male Deaths by Major Conflict',
            'desc': 'Total military/male deaths in millions across six centuries of warfare',
            'source': 'Various historical sources; ranges shown as midpoint estimates',
            'position': 'after_para_6',
            'js': """
(()=>{const ctx=document.getElementById('warChart1');
new Chart(ctx,{type:'bar',data:{labels:["Thirty Years'\\nWar","Napoleonic\\nWars","Crimean\\nWar","American\\nCivil War","World\\nWar I","World\\nWar II"],
datasets:[{label:'Male deaths (millions)',data:[8,5,0.48,0.69,10,19],backgroundColor:[C.dim,C.amber,C.teal,C.blue,C.accent,C.purple],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'M deaths'}}},scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Deaths (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'warChart2', 'figure_num': 2,
            'title': 'Percentage of Males Aged 18-30 Killed in Combat',
            'desc': 'By country and conflict — the devastating toll on fighting-age men',
            'source': 'War casualty estimates from military and demographic records',
            'position': 'after_para_16',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('warChart2');
new Chart(ctx,{type:'bar',data:{
labels:['Soviet Union\\n(WW2)','Germany\\n(WW2)','Germany\\n(WW1)','Confederate\\nStates','Russia\\n(WW1)','Russia\\n(Crimea)','Union\\nStates','France\\n(WW1)','Ottoman\\n(Crimea)'],
datasets:[{label:'% killed',data:[49,45,28,19,18.7,7.5,13,17,3.7],
backgroundColor:[C.accent,C.accent+'cc',C.purple,C.blue,C.purple+'cc',C.teal,C.blue+'cc',C.amber,C.teal+'cc'],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of males 18-30 killed'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'% of males aged 18-30',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
        {
            'id': 'warChart3', 'figure_num': 3,
            'title': 'Male-to-Female Combat Death Ratio',
            'desc': 'For every woman killed in combat, this many men died',
            'source': 'Derived from military casualty records and demographic analysis',
            'position': 'after_para_28',
            'js': """
(()=>{const ctx=document.getElementById('warChart3');
new Chart(ctx,{type:'bar',data:{
labels:['China (WW2)','Soviet Union (WW2)','Germany (WW2)','Am. Civil War (Union)','Am. Civil War (Confed.)','Crimean War'],
datasets:[{label:'Male deaths per female death',data:[30,16,12.8,11,6,3.5],
backgroundColor:[C.accent,C.purple,C.amber,C.blue,C.blue+'99',C.teal],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+':1 male-to-female ratio'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Male deaths per 1 female combat death',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'warChart4', 'figure_num': 4,
            'title': "Women's Workforce Participation",
            'desc': 'How war accelerated female entry into the paid workforce',
            'source': 'US Bureau of Labor Statistics, ILO historical data',
            'position': 'after_para_42',
            'js': """
(()=>{const ctx=document.getElementById('warChart4');
const yrs=[1900,1910,1920,1930,1940,1943,1945,1950,1960,1970,1980,1990,2000,2020];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('US women in labor force (%)',yrs,[20,23,24,24,27,37,34,30,35,43,52,57,60,57],C.purple),
dxy('UK women in labor force (%)',yrs,[29,30,28,29,31,46,42,35,38,44,52,58,60,58],C.blue)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{x:linX(1900,2020),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},min:15,max:65,title:{display:true,text:'% of women in workforce',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'warChart5', 'figure_num': 5,
            'title': 'Timeline: Key Welfare State Milestones',
            'desc': 'How the loss of men drove government into the role of provider',
            'source': 'Legislative records of UK, US, France, Germany',
            'position': 'after_para_55',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('warChart5');
const milestones=[
{y:1806,l:'France: Conseil de Famille',c:C.blue},
{y:1854,l:'UK: Royal Patriotic Fund',c:C.purple},
{y:1862,l:'US: Pension Bureau',c:C.accent},
{y:1914,l:'UK: Separation Allowance',c:C.purple},
{y:1916,l:'UK: War Widows Pension',c:C.purple},
{y:1918,l:'UK: Women over 30 vote',c:C.green},
{y:1920,l:'Germany: National Pension Law',c:C.amber},
{y:1942,l:"US: Servicemen's Dependents Act",c:C.accent},
{y:1944,l:'US: GI Bill',c:C.accent},
{y:1945,l:'UK: Family Allowances Act',c:C.purple},
{y:1948,l:'UK: National Health Service',c:C.purple}
];
new Chart(ctx,{type:'bar',data:{labels:milestones.map(m=>m.y),datasets:[{data:milestones.map((_,i)=>i+1),backgroundColor:milestones.map(m=>m.c),borderRadius:4,borderSkipped:false,barPercentage:.6}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{title:i=>[milestones[i[0].dataIndex].l],label:i=>'Year: '+milestones[i.dataIndex].y}}},
scales:{x:{display:false},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'warChart6', 'figure_num': 6,
            'title': 'Cumulative Male War Dead Across All Six Conflicts',
            'desc': 'The accelerating toll: from thousands to tens of millions',
            'source': 'Aggregate from conflict data in this article',
            'position': 'after_para_72',
            'js': """
(()=>{const ctx=document.getElementById('warChart6');
const yrs=[1618,1650,1803,1815,1853,1856,1861,1865,1914,1918,1939,1945];
new Chart(ctx,{type:'line',data:{
datasets:[{label:'Cumulative male dead (millions)',data:xy(yrs,[0,8,8,13,13,13.5,13.5,14.2,14.2,24.2,24.2,43.2]),
borderColor:C.accent,backgroundColor:C.accent+'15',fill:true,tension:.3,pointRadius:4,pointBackgroundColor:C.accent,borderWidth:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.parsed.y+'M cumulative deaths'}}},
scales:{x:linX(1610,1950,{ticks:{color:C.dim,maxRotation:45}}),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Cumulative deaths (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'warChart7', 'figure_num': 7,
            'title': 'The State Steps In: Government as Surrogate Provider',
            'desc': 'Each conflict expanded the role of government as provider',
            'source': 'Legislative records; analysis from this article',
            'position': 'after_para_84',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('warChart7');
const items=[
{l:'Augsburg widows fund',y1:1618,y2:1648,c:C.dim},
{l:'France: Conseil de Famille',y1:1806,y2:1830,c:C.amber},
{l:'UK: Royal Patriotic Fund',y1:1854,y2:1880,c:C.purple},
{l:'US: Pension Bureau',y1:1862,y2:1900,c:C.blue},
{l:'UK: Separation Allowance',y1:1914,y2:1920,c:C.purple},
{l:'Germany: Pension Law',y1:1920,y2:1945,c:C.amber},
{l:'US: GI Bill',y1:1944,y2:1975,c:C.blue},
{l:'UK: NHS',y1:1948,y2:2025,c:C.green},
{l:'UK: Family Allowances',y1:1945,y2:2025,c:C.green},
{l:'US: Great Society',y1:1964,y2:2025,c:C.blue}
];
new Chart(ctx,{type:'bar',data:{labels:items.map(i=>i.l),
datasets:[{label:'Period',data:items.map(i=>[i.y1,i.y2]),backgroundColor:items.map(i=>i.c+'88'),borderColor:items.map(i=>i.c),borderWidth:1,borderRadius:3,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[items[i[0].dataIndex].l],label:i=>{const d=items[i.dataIndex];return d.y1+' \u2014 '+(d.y2>=2025?'ongoing':d.y2)}}}},
scales:{x:{type:'linear',min:1600,max:2030,grid:{color:C.grid},ticks:{color:C.dim,callback:yearTick}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
    ]

    # ─── 2. RENEWABLES AND BATTERY REVOLUTION ───
    charts['the-renewables-and-battery-revolution'] = [
        {
            'id': 'renChart1', 'figure_num': 1,
            'title': 'Global Energy Transitions Over 250 Years',
            'desc': 'Share of global primary energy by source, 1800-2025',
            'source': 'Our World in Data, BP Statistical Review, Smil (2017)',
            'position': 'after_para_5',
            'js': """
(()=>{const ctx=document.getElementById('renChart1');
const yr=['1800','1850','1900','1920','1950','1970','1990','2000','2010','2020','2025'];
new Chart(ctx,{type:'line',data:{labels:yr,datasets:[
ds('Biomass/Wood',[95,85,50,35,20,12,10,10,9,8,7],C.green),
ds('Coal',[4,14,47,55,45,30,27,24,28,27,24],C.dim),
ds('Oil',[0,0,2,8,25,42,38,37,32,30,28],C.accent),
ds('Natural Gas',[0,0,1,2,8,15,20,22,22,24,23],C.amber),
ds('Nuclear',[0,0,0,0,0,0.5,6,6,5,4,4],C.purple),
ds('Renewables (modern)',[0,0,0,0,1,1,1,1,3,7,14],C.teal)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of global primary energy (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'renChart2', 'figure_num': 2,
            'title': 'Solar PV Module Cost Decline',
            'desc': 'From $106/watt in 1976 to $0.20/watt today — a 99.8% decline',
            'source': 'IRENA, Bloomberg NEF, Swanson\'s Law estimates',
            'position': 'after_para_9',
            'js': """
(()=>{const ctx=document.getElementById('renChart2');
new Chart(ctx,{type:'line',data:{
datasets:[{label:'$/watt (2023 dollars)',data:xy([1976,1980,1985,1990,1995,2000,2005,2010,2015,2020,2025],[106,30,12,8,5.5,3.5,2.5,1.5,0.5,0.25,0.20]),
borderColor:C.amber,backgroundColor:C.amber+'15',fill:true,tension:.3,pointRadius:4,pointBackgroundColor:C.amber,borderWidth:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.parsed.y+'/watt'}}},
scales:{x:linX(1976,2025),y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v},title:{display:true,text:'Cost per watt (log scale, 2023$)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'renChart3', 'figure_num': 3,
            'title': 'Lithium-Ion Battery Pack Cost Decline',
            'desc': 'From $1,200/kWh in 2010 to $139/kWh in 2024',
            'source': 'Bloomberg NEF annual battery price survey',
            'position': 'after_para_15',
            'js': """
(()=>{const ctx=document.getElementById('renChart3');
new Chart(ctx,{type:'line',data:{labels:['2010','2012','2014','2016','2018','2020','2022','2024'],
datasets:[{label:'$/kWh',data:[1200,700,500,290,180,140,151,139],
borderColor:C.teal,backgroundColor:C.teal+'15',fill:true,tension:.3,pointRadius:5,pointBackgroundColor:C.teal,borderWidth:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw+'/kWh'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v},title:{display:true,text:'Price per kWh',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'renChart4', 'figure_num': 4,
            'title': 'Energy Density by Fuel Source',
            'desc': 'Megajoules per kilogram — why oil dominated transport',
            'source': 'Engineering reference data, US DOE',
            'position': 'after_para_23',
            'js': """
(()=>{const ctx=document.getElementById('renChart4');
new Chart(ctx,{type:'bar',data:{labels:['Wood','Coal','Crude Oil','Natural Gas','Li-ion Battery','Hydrogen'],
datasets:[{label:'MJ/kg',data:[16,24,42,55,0.9,142],
backgroundColor:[C.green,C.dim,C.accent,C.amber,C.teal,C.purple],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' MJ/kg'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Energy density (MJ/kg)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'renChart5', 'figure_num': 5,
            'title': 'Geopolitical Disruption by Energy Era',
            'desc': 'Each energy transition reshaped the global balance of power',
            'source': 'Historical analysis by History Future Now',
            'position': 'after_para_33',
            'js': """
(()=>{const ctx=document.getElementById('renChart5');
new Chart(ctx,{type:'bar',data:{
labels:['Wood Era\\n(pre-1800)','Coal Era\\n(1800-1920)','Oil Era\\n(1920-2020)','Renewable Era\\n(2020+)'],
datasets:[
{label:'Major conflicts triggered',data:[2,4,6,0],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Empires created/destroyed',data:[1,3,4,1],backgroundColor:C.blue+'cc',borderRadius:3},
{label:'Global trade shifts',data:[1,3,4,3],backgroundColor:C.amber+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,stepSize:1}}}}});
})();"""
        },
        {
            'id': 'renChart6', 'figure_num': 6,
            'title': 'Whale Oil to Petroleum: The First Energy Transition',
            'desc': 'As whale populations collapsed, petroleum filled the gap',
            'source': 'American Oil & Gas Historical Society, IWC data',
            'position': 'after_para_25',
            'js': """
(()=>{const ctx=document.getElementById('renChart6');
new Chart(ctx,{type:'line',data:{labels:['1840','1850','1860','1870','1880','1890','1900'],
datasets:[
ds('Whale oil production (index)',[100,95,80,45,25,15,5],C.blue),
ds('Petroleum production (index)',[0,0,5,30,65,85,100],C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Production (indexed, peak=100)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'renChart7', 'figure_num': 7,
            'title': 'Global Primary Energy Mix Over Time',
            'desc': 'Each energy revolution added to the mix rather than fully replacing its predecessor',
            'source': 'BP Statistical Review; Vaclav Smil; Our World in Data',
            'position': 'after_para_40',
            'js': """
(()=>{const ctx=document.getElementById('renChart7');
const yrs=[1800,1850,1880,1900,1920,1940,1950,1960,1970,1980,1990,2000,2010,2020,2025];
const xyF=(d)=>xy(yrs,d);
new Chart(ctx,{type:'line',data:{
datasets:[
{label:'Biomass',data:xyF([95,85,62,50,38,30,25,20,15,12,10,9,8,7,6]),borderColor:C.dim,backgroundColor:C.dim+'30',fill:true,tension:.35,pointRadius:0,borderWidth:1.5},
{label:'Coal',data:xyF([5,14,35,45,48,42,38,35,28,27,26,23,27,23,20]),borderColor:'#333',backgroundColor:'#33333030',fill:true,tension:.35,pointRadius:0,borderWidth:1.5},
{label:'Oil',data:xyF([0,0,1,3,9,17,23,30,40,38,33,35,31,30,28]),borderColor:C.amber,backgroundColor:C.amber+'30',fill:true,tension:.35,pointRadius:0,borderWidth:1.5},
{label:'Gas',data:xyF([0,0,1,1,3,5,7,10,13,17,20,21,22,23,23]),borderColor:C.teal,backgroundColor:C.teal+'30',fill:true,tension:.35,pointRadius:0,borderWidth:1.5},
{label:'Nuclear',data:xyF([0,0,0,0,0,0,0,0,1,3,5,6,5,4,4]),borderColor:C.purple,backgroundColor:C.purple+'30',fill:true,tension:.35,pointRadius:0,borderWidth:1.5},
{label:'Renewables',data:xyF([0,0,0,0,0,0,0,1,1,2,3,4,6,11,16]),borderColor:C.green,backgroundColor:C.green+'30',fill:true,tension:.35,pointRadius:0,borderWidth:1.5}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{...legend,labels:{...legend.labels,font:{size:10}}},tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'%'}}},
scales:{x:linX(1800,2025),y:{stacked:false,grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},max:100,title:{display:true,text:'Share of global primary energy (%)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 3. EUROPEAN REVOLUTIONS ───
    charts['what-does-it-take-to-get-europeans-to-have-a-revolution'] = [
        {
            'id': 'revChart1', 'figure_num': 1,
            'title': 'European Revolutions by Decade, 1640-2000',
            'desc': 'Over 60 revolutions in 360 years — with clear clustering',
            'source': 'Compiled from revolutions catalogued in this article',
            'position': 'after_para_35',
            'js': """
(()=>{const ctx=document.getElementById('revChart1');
new Chart(ctx,{type:'bar',data:{labels:['1640s','1680s','1710s','1770s','1790s','1800s','1820s','1830s','1840s','1850s','1860s','1870s','1900s','1910s','1970s','1980s','1990s'],
datasets:[{label:'Number of revolutions',data:[1,1,1,1,2,1,1,2,12,2,2,3,3,8,3,7,16],
backgroundColor:['1640s','1680s','1710s','1770s','1790s','1800s','1820s','1830s','1840s','1850s','1860s','1870s','1900s','1910s','1970s','1980s','1990s'].map(d=>{
const y=parseInt(d);return y<1800?C.blue:y<1900?C.amber:y<1950?C.accent:C.purple}),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle},scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:45}},y:{grid:{color:C.grid},ticks:{color:C.dim,stepSize:2},title:{display:true,text:'Number of revolutions',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'revChart2', 'figure_num': 2,
            'title': 'Revolution Causes: Social vs Ethnic Inequality',
            'desc': '24 driven by social inequality within a country, 39 by ethnic/national oppression',
            'source': 'Classification from this article\'s analysis',
            'position': 'after_para_67',
            'js': """
(()=>{const ctx=document.getElementById('revChart2');
new Chart(ctx,{type:'doughnut',data:{labels:['Social inequality\\n(within ethnic group)','Ethnic/national\\ninequality'],
datasets:[{data:[24,39],backgroundColor:[C.blue,C.accent],borderWidth:0,hoverOffset:8}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},cutout:'55%',plugins:{legend:{position:'bottom',labels:{padding:20,font:{size:13}}},
tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' revolutions ('+Math.round(i.raw/63*100)+'%)'}}}}});
})();"""
        },
        {
            'id': 'revChart3', 'figure_num': 3,
            'title': 'The Four Great Waves of Revolution',
            'desc': 'Revolutions cluster in contagious waves triggered by catalytic events',
            'source': 'Categorisation from this article',
            'position': 'after_para_99',
            'js': """
(()=>{const ctx=document.getElementById('revChart3');
new Chart(ctx,{type:'bar',data:{
labels:['1789-1832\\nFrench Revolution\\nwave','1848\\nSpring of\\nNations','1917-1919\\nPost-WW1\\ncollapse','1989-1991\\nFall of\\nCommunism'],
datasets:[{label:'Countries affected',data:[6,12,8,18],backgroundColor:[C.blue,C.amber,C.accent,C.purple],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle},scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,stepSize:5},title:{display:true,text:'Countries with revolutions',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'revChart4', 'figure_num': 4,
            'title': 'Revolution Conditions: Past vs Present',
            'desc': 'Comparing conditions that triggered past revolutions to today',
            'source': 'Analytical framework from this article',
            'position': 'after_para_131',
            'js': """
(()=>{const ctx=document.getElementById('revChart4');
new Chart(ctx,{type:'radar',data:{
labels:['Social\\ninequality','Foreign\\nrule','Military\\nexperience','Leadership','Clear\\nenemy','Contagion\\neffect','Economic\\nhardship'],
datasets:[
{label:'1848 conditions',data:[9,8,7,7,9,10,9],borderColor:C.accent,backgroundColor:C.accent+'20',pointBackgroundColor:C.accent,borderWidth:2},
{label:'2011-today',data:[7,4,2,2,3,8,6],borderColor:C.blue,backgroundColor:C.blue+'20',pointBackgroundColor:C.blue,borderWidth:2}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{r:{grid:{color:C.grid},ticks:{display:false},pointLabels:{font:{size:11},color:C.dim},min:0,max:10}}}});
})();"""
        },
        {
            'id': 'revChart5', 'figure_num': 5,
            'title': 'Youth Unemployment in Crisis Countries (2011)',
            'desc': 'The modern tinderbox: half of young Spaniards without work',
            'source': 'Eurostat, ILO, national statistics offices',
            'position': 'after_para_163',
            'js': """
(()=>{const ctx=document.getElementById('revChart5');
new Chart(ctx,{type:'bar',data:{labels:['Spain','Greece','Italy','Portugal','Ireland','France','UK','Germany'],
datasets:[{label:'Youth unemployment %',data:[51,48,31,28,26,22,20,8],
backgroundColor:[C.accent,C.accent+'cc',C.accent+'aa',C.amber,C.amber+'cc',C.blue,C.blue+'cc',C.green],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% youth unemployment'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'% of under-25s unemployed',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'revChart6', 'figure_num': 6,
            'title': 'How Revolutions Spread: The Contagion Effect',
            'desc': 'Each major revolution inspired the next — a chain reaction across centuries',
            'source': 'Analysis from this article',
            'position': 'after_para_195',
            'js': """
(()=>{const ctx=document.getElementById('revChart6');
const ch=[
{y:1642,l:'English Civil War',i:3,c:C.blue},{y:1688,l:'Glorious Revolution',i:2,c:C.blue},
{y:1775,l:'American Revolution',i:5,c:C.accent},{y:1789,l:'French Revolution',i:9,c:C.accent},
{y:1798,l:'Irish Rebellion',i:2,c:C.green},{y:1804,l:'Serbian Revolution',i:3,c:C.purple},
{y:1821,l:'Greek Revolution',i:3,c:C.purple},{y:1830,l:'French Rev. (July)',i:4,c:C.amber},
{y:1848,l:'1848 Pan-European',i:10,c:C.accent},{y:1917,l:'Russian Revolution',i:8,c:C.accent},
{y:1918,l:'Post-WW1 Wave',i:7,c:C.purple},{y:1989,l:'Fall of Communism',i:9,c:C.green}
];
new Chart(ctx,{type:'bubble',data:{datasets:[{
data:ch.map(c=>({x:c.y,y:c.i,r:c.i*2.5})),
backgroundColor:ch.map(c=>c.c+'66'),borderColor:ch.map(c=>c.c),borderWidth:2
}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[ch[i[0].dataIndex].l],
label:i=>'Year: '+ch[i.dataIndex].y+', Contagion: '+ch[i.dataIndex].i+'/10'}}},
scales:{x:{type:'linear',min:1630,max:2000,grid:{color:C.grid},ticks:{color:C.dim,callback:yearTick},title:{display:true,text:'Year',color:C.dim}},
y:{grid:{color:C.grid},ticks:{color:C.dim},min:0,max:12,title:{display:true,text:'Contagion influence',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 4. NORTH AFRICAN THREAT ───
    charts['the-north-african-threat-and-mediterranean-reunification'] = [
        {
            'id': 'nafChart1', 'figure_num': 1,
            'title': 'Population Growth: North Africa vs Southern Europe',
            'desc': 'The demographic lines are crossing — and the implications are profound',
            'source': 'UN World Population Prospects 2024',
            'position': 'after_para_11',
            'js': """
(()=>{const ctx=document.getElementById('nafChart1');
new Chart(ctx,{type:'line',data:{labels:['1960','1970','1980','1990','2000','2010','2020','2030','2040','2050'],
datasets:[
ds('North Africa (Egypt, Libya, Tunisia, Algeria, Morocco)',[55,70,95,120,150,180,210,245,280,310],C.accent),
ds('Southern Europe (Spain, Italy, Greece, Portugal)',[95,105,112,118,121,124,122,118,113,107],C.blue)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label.split('(')[0].trim()+': '+i.raw+'M'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Population (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'nafChart2', 'figure_num': 2,
            'title': 'Median Age: Youth Bulge vs Ageing Population',
            'desc': 'North Africa is young and growing; Southern Europe is old and shrinking',
            'source': 'UN WPP 2024, CIA World Factbook',
            'position': 'after_para_19',
            'js': """
(()=>{const ctx=document.getElementById('nafChart2');
new Chart(ctx,{type:'bar',data:{labels:['Egypt','Algeria','Morocco','Libya','Tunisia','—','Spain','Italy','Greece','Portugal'],
datasets:[{label:'Median age (years)',data:[24,29,30,29,33,null,45,48,46,46],
backgroundColor:['Egypt','Algeria','Morocco','Libya','Tunisia','—','Spain','Italy','Greece','Portugal'].map(c=>
c==='—'?'transparent':['Egypt','Algeria','Morocco','Libya','Tunisia'].includes(c)?C.accent:C.blue),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw?i.raw+' years':''}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Median age (years)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'nafChart3', 'figure_num': 3,
            'title': 'Fertility Rates: Replacement Level Divergence',
            'desc': 'Most Southern European countries are far below replacement (2.1)',
            'source': 'World Bank, UN WPP 2024',
            'position': 'after_para_27',
            'js': """
(()=>{const ctx=document.getElementById('nafChart3');
const data=[{c:'Egypt',v:2.9},{c:'Algeria',v:2.6},{c:'Morocco',v:2.3},{c:'Libya',v:2.2},{c:'Tunisia',v:2.0},{c:'Spain',v:1.2},{c:'Italy',v:1.2},{c:'Greece',v:1.3},{c:'Portugal',v:1.4}];
new Chart(ctx,{type:'bar',data:{labels:data.map(d=>d.c),datasets:[{label:'TFR',data:data.map(d=>d.v),
backgroundColor:data.map(d=>d.v>=2.1?C.green:d.v>=1.5?C.amber:C.accent),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' children per woman'}},
annotation:{annotations:{line1:{type:'line',yMin:2.1,yMax:2.1,borderColor:C.dim,borderWidth:1.5,borderDash:[5,3],label:{display:true,content:'Replacement level (2.1)',position:'start',font:{size:11}}}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim},min:0,max:3.5,title:{display:true,text:'Total fertility rate',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'nafChart4', 'figure_num': 4,
            'title': 'Historical Control of the Mediterranean',
            'desc': '3,000 years of shifting civilisational dominance',
            'source': 'Historical analysis from this article',
            'position': 'after_para_35',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('nafChart4');
const periods=[
{l:'Phoenicia/Carthage',s:-650,e:-146,c:C.teal},
{l:'Roman Empire',s:-146,e:439,c:C.blue},
{l:'Vandal Kingdom',s:429,e:534,c:C.dim},
{l:'Byzantine',s:534,e:698,c:C.purple},
{l:'Arab/Muslim',s:698,e:1500,c:C.accent},
{l:'Ottoman',s:1500,e:1830,c:C.amber},
{l:'European Colonial',s:1830,e:1960,c:C.blue},
{l:'Independent states',s:1956,e:2025,c:C.green}
];
new Chart(ctx,{type:'bar',data:{labels:periods.map(p=>p.l),
datasets:[{data:periods.map(p=>[(p.s<0?p.s:p.s),(p.e<0?p.e:p.e)]),backgroundColor:periods.map(p=>p.c+'cc'),borderRadius:3,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[periods[i[0].dataIndex].l],
label:i=>{const p=periods[i.dataIndex];return (p.s<0?Math.abs(p.s)+' BC':p.s+' AD')+' – '+(p.e<0?Math.abs(p.e)+' BC':p.e+' AD')+' ('+(p.e-p.s)+' years)'}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v<0?Math.abs(v)+' BC':v+' AD'},title:{display:true,text:'Year',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'naChart5', 'figure_num': 5,
            'title': 'Youth Bulge vs Ageing Society: Algeria vs Italy',
            'desc': 'Two sides of the Mediterranean with opposite demographic profiles',
            'source': 'UN World Population Prospects 2022',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('naChart5');
const ages=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80+'];
new Chart(ctx,{type:'bar',data:{labels:ages,
datasets:[
{label:'Algeria (% of pop.)',data:[20,18,17,15,12,8,5,3,2],backgroundColor:C.accent+'bb',borderRadius:3,borderSkipped:false},
{label:'Italy (% of pop.)',data:[8,9,10,12,14,15,13,11,8],backgroundColor:C.blue+'bb',borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'%'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim},title:{display:true,text:'Age group',color:C.dim}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of total population (%)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 5. COVID LONG TERM IMPACT ───
    charts['the-long-term-impact-of-covid-19'] = [
        {
            'id': 'covChart1', 'figure_num': 1,
            'title': 'The Decline of Western Global Power',
            'desc': 'From peak at the eve of WW1 to today — a century of relative decline',
            'source': 'Maddison Project, World Bank, IMF WEO',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('covChart1');
const yrs=[1870,1900,1913,1945,1960,1980,1990,2000,2010,2020,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('West (% of world GDP)',yrs,[55,55,58,50,48,42,40,38,33,30,28],C.blue),
dxy('East Asia (% of world GDP)',yrs,[18,15,12,8,10,14,18,22,28,32,35],C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1870,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of world GDP (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'covChart2', 'figure_num': 2,
            'title': 'The Rising Value of a Human Life',
            'desc': 'From negligible to £11 million per Covid death in the UK',
            'source': 'UK OBR, NHS, Treasury data; HFN calculation',
            'position': 'after_para_16',
            'js': """
(()=>{const ctx=document.getElementById('covChart2');
new Chart(ctx,{type:'bar',data:{labels:['Medieval\\nEngland','Industrial\\nBritain','WW1\\nBritain','WW2\\nBritain','1970s\\nUK','2000s\\nUK','Covid-19\\nUK'],
datasets:[{label:'Implied value of one life',data:[0.001,0.01,0.05,0.1,0.5,2,11],
backgroundColor:[C.dim,C.dim,C.amber,C.amber,C.blue,C.blue,C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'£'+i.raw+'M per life'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'£'+v+'M'},title:{display:true,text:'Implied value per life, £M (log scale)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'covChart3', 'figure_num': 3,
            'title': 'Covid-19 Accelerated Existing Trends',
            'desc': 'Years of digital adoption compressed into months — shown as growth factor from 2019 baseline',
            'source': 'McKinsey Global Survey, Statista, various',
            'position': 'after_para_24',
            'js': """
(()=>{const ctx=document.getElementById('covChart3');
const labels=['E-commerce\\nshare of retail','Remote\\nworkers','Streaming\\nsubscriptions','Online\\neducation','Telemedicine\\nvisits'];
const pre=[16,5,600,200,10];
const during=[27,42,1100,400,90];
const growth=during.map((v,i)=>+(v/pre[i]).toFixed(1));
new Chart(ctx,{type:'bar',data:{labels,
datasets:[
{label:'Growth factor (2020 vs 2019)',data:growth,backgroundColor:[C.blue,C.accent,C.purple,C.green,C.amber].map(c=>c+'cc'),borderRadius:4,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const idx=i.dataIndex;return labels[idx].replace('\\n',' ')+': '+pre[idx]+' → '+during[idx]+' ('+growth[idx]+'x)'}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'x'},min:0,title:{display:true,text:'Growth factor (2020 vs 2019)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'covChart4', 'figure_num': 4,
            'title': "HFN's 12 Forces Framework: Inevitable vs Broken",
            'desc': 'Six forces that Covid accelerated, and six whose trajectory it broke',
            'source': 'Framework from this article',
            'position': 'after_para_34',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('covChart4');
const forces=[
{l:'Digital acceleration',s:9,t:'inevitable'},{l:'Location irrelevance',s:8,t:'inevitable'},
{l:'Rise of East Asia',s:7,t:'inevitable'},{l:'Value of human life',s:8,t:'inevitable'},
{l:'Global culture',s:6,t:'inevitable'},{l:'Decline of military conflict',s:5,t:'inevitable'},
{l:'Deglobalisation risk',s:7,t:'broken'},{l:'Authoritarian temptation',s:6,t:'broken'},
{l:'Supply chain reshoring',s:8,t:'broken'},{l:'Government debt surge',s:9,t:'broken'},
{l:'Social fragmentation',s:6,t:'broken'},{l:'Education disruption',s:7,t:'broken'}
];
new Chart(ctx,{type:'bar',data:{labels:forces.map(f=>f.l),
datasets:[{data:forces.map(f=>f.s),backgroundColor:forces.map(f=>f.t==='inevitable'?C.green:C.accent),borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[forces[i[0].dataIndex].l],label:i=>'Impact: '+i.raw+'/10 ('+forces[i.dataIndex].t+')'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim},min:0,max:10,title:{display:true,text:'Impact strength (1-10)',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'covChart5', 'figure_num': 5,
            'title': 'East vs West: Covid-19 Response Outcomes',
            'desc': 'East Asian countries managed both health and economic outcomes far better',
            'source': 'WHO, IMF, Johns Hopkins CSSE; data as of late 2020',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('covChart5');
new Chart(ctx,{type:'bar',data:{labels:['South\\nKorea','Taiwan','Japan','Germany','France','UK','US'],
datasets:[
{label:'Deaths per 100k (2020)',data:[6,0.3,12,40,90,100,105],backgroundColor:C.accent+'bb',borderRadius:3,borderSkipped:false,yAxisID:'y'},
{label:'GDP decline % (2020)',data:[1.0,0.5,4.6,4.9,8.0,9.8,3.4],backgroundColor:C.blue+'bb',borderRadius:3,borderSkipped:false,yAxisID:'y1'}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},
y:{type:'linear',position:'left',grid:{color:C.grid},ticks:{color:C.accent,callback:v=>v},min:0,title:{display:true,text:'Deaths per 100k',color:C.accent}},
y1:{type:'linear',position:'right',grid:{drawOnChartArea:false},ticks:{color:C.blue,callback:v=>v+'%'},min:0,max:12,title:{display:true,text:'GDP decline %',color:C.blue}}}}});
})();"""
        },
        {
            'id': 'covChart6', 'figure_num': 6,
            'title': 'The Covid Debt Surge: Additional Government Borrowing',
            'desc': 'Trillions added to national debts in a single year to preserve human life',
            'source': 'IMF Fiscal Monitor; national budget offices',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('covChart6');
new Chart(ctx,{type:'bar',data:{labels:['United\nStates','Japan','Germany','United\nKingdom','France','Italy','Canada'],
datasets:[{label:'Additional Covid borrowing ($bn)',data:[4500,2200,600,500,400,350,300],
backgroundColor:[C.accent,C.purple,C.amber,C.blue,C.teal,C.green,C.cyan],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw+'bn'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v>=1000?'$'+(v/1000)+'T':'$'+v+'bn'},title:{display:true,text:'Additional government borrowing',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 6. DEBT JUBILEES & HYPERINFLATION ───
    charts['debt-jubilees-and-hyperinflation-why-history-shows-that-this-might-be-the-way-forward-for-us-all'] = [
        {
            'id': 'debtChart1', 'figure_num': 1,
            'title': 'Weimar Hyperinflation: Price of Bread',
            'desc': 'From 1 Mark to 3 billion Marks in under three years',
            'source': 'Deutsche Bundesbank historical data',
            'position': 'after_para_9',
            'js': """
(()=>{const ctx=document.getElementById('debtChart1');
const months=[1921.0,1921.5,1922.0,1922.5,1923.0,1923.25,1923.5,1923.67,1923.75,1923.83];
const labels=['Jan 21','Jul 21','Jan 22','Jul 22','Jan 23','Apr 23','Jul 23','Sep 23','Oct 23','Nov 23'];
new Chart(ctx,{type:'line',data:{
datasets:[{label:'Price of bread (Marks)',data:xy(months,[1,2,3,10,250,500,100000,2000000,670000000,3000000000]),
borderColor:C.accent,backgroundColor:C.accent+'15',fill:true,tension:.3,pointRadius:4,pointBackgroundColor:C.accent,borderWidth:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{title:i=>[labels[i[0].dataIndex]],label:i=>{const v=i.parsed.y;return v>=1e9?(v/1e9).toFixed(0)+'B Marks':v>=1e6?(v/1e6).toFixed(0)+'M Marks':v>=1e3?(v/1e3).toFixed(0)+'K Marks':v+' Marks'}}}},
scales:{x:linX(1921,1924,{grid:{color:C.grid},ticks:{color:C.dim,maxRotation:45,callback:function(v){const m=['Jan','Apr','Jul','Oct'];const yr=Math.floor(v);const frac=v-yr;const mi=Math.round(frac*12);if(mi===0)return'Jan '+yr;if(mi===6)return'Jul '+yr;return''}}}),y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim,callback:v=>{if(v>=1e9)return(v/1e9)+'B';if(v>=1e6)return(v/1e6)+'M';if(v>=1e3)return(v/1e3)+'K';return v}},title:{display:true,text:'Price of 1 loaf of bread (Marks, log scale)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'debtChart2', 'figure_num': 2,
            'title': 'Roman Currency Debasement',
            'desc': 'Silver content in the Roman denarius fell from 95% to under 5%',
            'source': 'Metallurgical analyses of Roman coinage',
            'position': 'after_para_15',
            'js': """
(()=>{const ctx=document.getElementById('debtChart2');
new Chart(ctx,{type:'line',data:{
datasets:[{label:'Silver content (%)',data:xy([-27,14,64,117,193,250,270,295],[95,93,90,85,65,40,5,2]),
borderColor:C.dim,backgroundColor:C.dim+'15',fill:true,tension:.35,pointRadius:5,pointBackgroundColor:C.dim,borderWidth:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.parsed.y+'% silver content'}}},
scales:{x:linX(-40,310,{ticks:{color:C.dim,callback:v=>v<0?Math.abs(v)+' BC':v===0?'0':v+' AD'}}),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},min:0,max:100,title:{display:true,text:'Silver content of denarius (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'debtChart3', 'figure_num': 3,
            'title': 'How Hyperinflation Erases Debt',
            'desc': 'A visual demonstration of debt destruction through inflation',
            'source': 'Illustrative calculation from this article',
            'position': 'after_para_21',
            'js': """
(()=>{const ctx=document.getElementById('debtChart3');
new Chart(ctx,{type:'bar',data:{labels:['Government debt\\n(nominal)','Loaf of bread\\n(current price)','Real value\\nof debt'],
datasets:[
{label:'Before hyperinflation',data:[100,0.001,100],backgroundColor:C.blue+'cc',borderRadius:3},
{label:'After hyperinflation',data:[100,1,0.001],backgroundColor:C.accent+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'£'+i.raw+(i.raw>=1?'bn':'bn')}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'£'+v+'bn'}}}}});
})();"""
        },
        {
            'id': 'debtChart4', 'figure_num': 4,
            'title': 'Countries That Have Experienced Hyperinflation (20th Century)',
            'desc': 'Over 40 countries have suffered monthly inflation rates exceeding 50%',
            'source': 'Hanke & Krus, World Hyperinflation Table',
            'position': 'before_end',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('debtChart4');
const regions=[{l:'Europe',n:18,c:C.blue},{l:'Latin America',n:8,c:C.green},{l:'Asia',n:5,c:C.accent},{l:'Africa',n:3,c:C.amber},{l:'Other',n:2,c:C.dim}];
new Chart(ctx,{type:'doughnut',data:{labels:regions.map(r=>r.l+' ('+r.n+')'),
datasets:[{data:regions.map(r=>r.n),backgroundColor:regions.map(r=>r.c+'cc'),borderColor:'#fff',borderWidth:2}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{position:'bottom',labels:{padding:14,usePointStyle:true,font:{size:12}}},
tooltip:{...tooltipStyle,callbacks:{label:i=>regions[i.dataIndex].n+' countries'}}}}});
})();"""
        },
        {
            'id': 'debtChart5', 'figure_num': 5,
            'title': 'US Federal Interest + Entitlements vs Tax Revenue',
            'desc': 'CBO projects mandatory spending plus interest will consume all federal tax income',
            'source': 'US Congressional Budget Office',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('debtChart5');
new Chart(ctx,{type:'line',data:{labels:['2000','2005','2010','2015','2020','2025','2030','2035'],
datasets:[
ds('Interest + Entitlements (% GDP)',[12,13,15,15,20,22,24,27],C.accent),
ds('Federal tax revenue (% GDP)',[20,17,15,18,16,17,18,18],C.blue,[5,5])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'% of GDP',color:C.dim},min:10,max:30}}}});
})();"""
        },
    ]

    # ═══════════════════════════════════════════════════════
    # TIER 2: MEDIUM IMPACT
    # ═══════════════════════════════════════════════════════

    # ─── 7. CRISIS: DECLINE OF THE WEST ───
    charts['crisis-or-an-explanation-on-the-origins-of-the-decline-of-the-west'] = [
        {
            'id': 'crisisChart1', 'figure_num': 1,
            'title': 'The Faustian Bargain: 500 Years of Western Expansion and Retreat',
            'desc': 'Trade policy shifts from mercantilism to free trade and their consequences',
            'source': 'Historical analysis by History Future Now',
            'position': 'after_para_33',
            'js': """
(()=>{const ctx=document.getElementById('crisisChart1');
const yrs=[1500,1600,1700,1800,1850,1900,1950,1980,2000,2010,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Western share of global trade (%)',yrs,[15,25,35,45,60,70,55,50,45,38,30],C.blue),
dxy('Financial sector as % of economy',yrs,[2,3,3,4,5,7,8,12,18,22,20],C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1500,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'}}}}});
})();"""
        },
        {
            'id': 'crisisChart2', 'figure_num': 2,
            'title': 'Manufacturing Output: West vs East',
            'desc': 'The great reversal — Asia reclaims manufacturing dominance',
            'source': 'Maddison, UNIDO, World Bank',
            'position': 'after_para_67',
            'js': """
(()=>{const ctx=document.getElementById('crisisChart2');
const yrs=[1750,1800,1850,1900,1950,1980,2000,2010,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('China + India',yrs,[73,68,40,12,5,8,18,30,42],C.accent),
dxy('Europe + N. America',yrs,[22,28,55,82,85,70,62,48,38],C.blue)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1750,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of global manufacturing (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'crisisChart3', 'figure_num': 3,
            'title': 'Financial Services as Share of GDP',
            'desc': 'Finance grew from servant of the economy to its master',
            'source': 'Bank of England; Bureau of Economic Analysis; OECD',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('crisisChart3');
const yrs=[1950,1960,1970,1980,1990,2000,2006,2008,2010,2015,2020];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('UK financial services (% GDP)',yrs,[3,4,5,6,8,10,12,10,9,8,7],C.blue),
dxy('US financial services (% GDP)',yrs,[3,4,4,5,7,8,9,8,7,7,8],C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.parsed.y+'% of GDP'}}},
scales:{x:linX(1950,2020),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Financial services as % of GDP',color:C.dim},min:0,max:15}}}});
})();"""
        },
    ]

    # ─── 8. RISE OF THE WEST: LUCK ───
    charts['the-rise-of-the-west-was-based-on-luck-that-has-run-out'] = [
        {
            'id': 'luckChart1', 'figure_num': 1,
            'title': 'GDP Share by Civilisation, 1-2025 AD',
            'desc': 'For most of history, Asia dominated. Western dominance was an anomaly.',
            'source': 'Angus Maddison Project Database, World Bank WDI',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('luckChart1');
const yrs=[1,500,1000,1500,1700,1820,1870,1913,1950,1980,2000,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('China',yrs,[26,23,22,25,22,33,17,9,5,5,12,19],C.accent),
dxy('India',yrs,[33,28,28,24,24,16,12,8,4,3,5,8],C.amber),
dxy('Western Europe',yrs,[11,12,9,18,22,23,33,33,26,24,20,15],C.blue),
dxy('USA',yrs,[0,0,0,0,0.2,2,9,19,27,22,22,16],C.purple)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of world GDP (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'luckChart2', 'figure_num': 2,
            'title': 'The Lucky Breaks That Made the West',
            'desc': 'Remove any one and the Rise of the West might never have happened',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('luckChart2');
const b=[
{y:1348,l:'Black Death kills 1/3 of Europe',i:8,c:C.dim},
{y:1440,l:'Gutenberg printing press',i:7,c:C.amber},
{y:1453,l:'Fall of Constantinople',i:6,c:C.purple},
{y:1492,l:'Columbus reaches Americas',i:9,c:C.accent},
{y:1517,l:'Protestant Reformation',i:7,c:C.blue},
{y:1642,l:'English Civil War / Parliament',i:6,c:C.blue},
{y:1750,l:'Deforestation forces coal shift',i:9,c:C.dim},
{y:1789,l:'French Revolution',i:7,c:C.accent},
{y:1815,l:'Britain defeats Napoleon',i:6,c:C.purple}
];
new Chart(ctx,{type:'bubble',data:{datasets:[{
data:b.map(x=>({x:x.y,y:x.i,r:x.i*2.2})),
backgroundColor:b.map(x=>x.c+'55'),borderColor:b.map(x=>x.c),borderWidth:2
}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[b[i[0].dataIndex].l],label:i=>'Year: '+b[i.dataIndex].y+', Impact: '+b[i.dataIndex].i+'/10'}}},
scales:{x:{type:'linear',min:1300,max:1850,grid:{color:C.grid},ticks:{color:C.dim,callback:yearTick},title:{display:true,text:'Year',color:C.dim}},
y:{grid:{color:C.grid},ticks:{color:C.dim},min:0,max:11,title:{display:true,text:'Historical impact (1-10)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'luckChart3', 'figure_num': 3,
            'title': 'Western Share of Global GDP: Rise and Fall',
            'desc': 'Western dominance was a historical anomaly now reverting to the long-run mean',
            'source': 'Maddison Project; IMF WEO',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('luckChart3');
const yrs=[1,1000,1500,1600,1700,1820,1870,1913,1950,1973,2000,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('West (Europe+US)',yrs,[12,12,18,22,24,30,42,50,52,48,42,30],C.blue),
dxy('China',yrs,[26,22,25,29,22,33,17,9,5,5,12,20],C.accent),
dxy('India',yrs,[32,28,24,22,24,16,12,8,4,3,5,8],C.amber)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of world GDP (%)',color:C.dim},max:55}}}});
})();"""
        },
    ]

    # ─── 9. JOBS: GET RID OF EXPENSIVE WESTERNERS ───
    charts['jobs-first-get-rid-of-expensive-westerners-second-get-rid-of-people-entirely'] = [
        {
            'id': 'jobsChart1', 'figure_num': 1,
            'title': 'The True Cost of a "Cheap" Imported Product',
            'desc': 'A £100 import may save £15 upfront but cost society far more',
            'source': 'Illustrative calculation from this article',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('jobsChart1');
new Chart(ctx,{type:'bar',data:{labels:['Product\\nprice','Lost income\\ntax','Unemployment\\nbenefits','Healthcare\\n& social cost','Total cost\\nto society'],
datasets:[
{label:'Imported (China)',data:[100,0,0,0,100],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Domestic (UK/EU)',data:[115,-25,-15,-5,70],backgroundColor:C.blue+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'£'+Math.abs(i.raw)+(i.raw<0?' saved':' cost')}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'£'+v}}}}});
})();"""
        },
        {
            'id': 'jobsChart2', 'figure_num': 2,
            'title': 'Manufacturing Jobs Migration: West to East',
            'desc': 'Millions of manufacturing jobs relocated since 2000',
            'source': 'ILO, BLS, Eurostat, World Bank',
            'position': 'after_para_16',
            'js': """
(()=>{const ctx=document.getElementById('jobsChart2');
new Chart(ctx,{type:'line',data:{labels:['2000','2005','2010','2015','2020','2025'],
datasets:[
ds('China manufacturing jobs (M)',[80,100,110,105,100,95],C.accent),
ds('US manufacturing jobs (M)',[17,14,12,12,12,13],C.blue),
ds('EU manufacturing jobs (M)',[35,32,28,26,25,24],C.purple)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label.split('(')[0].trim()+': '+i.raw+'M'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Manufacturing jobs (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'outsChart3', 'figure_num': 3,
            'title': 'US-China Trade Deficit: A River of Wealth Flowing East',
            'desc': 'Cumulative deficits represent a massive transfer of wealth',
            'source': 'US Census Bureau; Eurostat',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('outsChart3');
new Chart(ctx,{type:'line',data:{labels:['2000','2002','2004','2006','2008','2010','2012','2014','2016','2018','2020'],
datasets:[
ds('US deficit with China ($bn)',[84,103,162,234,268,273,315,345,347,419,311],C.accent),
ds('EU deficit with China ($bn)',[35,40,70,120,170,150,130,140,160,185,165],C.blue)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw+'bn deficit'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v+'bn'},title:{display:true,text:'Annual trade deficit ($bn)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 10. ROBOTICS AND SLAVERY ───
    charts['robotics-and-slavery'] = [
        {
            'id': 'robotChart1', 'figure_num': 1,
            'title': 'Humanoid Robot Comparison',
            'desc': 'Price, speed, and capabilities of leading humanoid robots',
            'source': 'Company announcements, IEEE Spectrum, 2024',
            'position': 'after_para_10',
            'js': """
(()=>{const ctx=document.getElementById('robotChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Tesla Optimus','Figure 01','Unitree H1','Boston Dynamics\\nAtlas'],
datasets:[
{label:'Target price ($K)',data:[20,50,90,150],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Max speed (m/s)',data:[2.0,1.5,3.3,2.5],backgroundColor:C.blue+'cc',borderRadius:3,yAxisID:'y1'}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v+'K'},title:{display:true,text:'Price ($K)',color:C.dim},position:'left'},
y1:{grid:{display:false},ticks:{color:C.blue,callback:v=>v+'m/s'},title:{display:true,text:'Max speed (m/s)',color:C.blue},position:'right'}}}});
})();"""
        },
        {
            'id': 'robotChart2', 'figure_num': 2,
            'title': 'Labour Cost Convergence: Human vs Robot',
            'desc': 'As robot costs fall, they approach human minimum wage parity',
            'source': 'IFR, McKinsey, projected estimates',
            'position': 'after_para_17',
            'js': """
(()=>{const ctx=document.getElementById('robotChart2');
const yrs=[2020,2022,2024,2026,2028,2030,2035];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Robot cost per hour ($)',yrs,[12,9,7,5,3.5,2.5,1],C.accent),
dxy('US minimum wage ($/hr)',yrs,[7.25,7.25,7.25,8,9,10,12],C.blue,[5,3]),
dxy('China factory wage ($/hr)',yrs,[3.5,4,4.5,5,5.5,6,7],C.amber,[3,3])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(2020,2035),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v+'/hr'},title:{display:true,text:'Cost per working hour ($)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'robotChart3', 'figure_num': 3,
            'title': 'Historical Parallels: Slavery to Immigration to Automation',
            'desc': 'Each era found a different source of cheap, exploitable labour',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('robotChart3');
const eras=[
{l:'Colonial slavery',y1:1500,y2:1865,s:'African slaves',c:C.accent},
{l:'Industrial labour',y1:1760,y2:1920,s:'Rural poor in factories',c:C.amber},
{l:'Mass immigration',y1:1945,y2:2025,s:'Global South workers',c:C.blue},
{l:'Humanoid robots',y1:2025,y2:2060,s:'AI-powered machines',c:C.purple}
];
new Chart(ctx,{type:'bar',data:{labels:eras.map(e=>e.l),
datasets:[{data:eras.map(e=>[e.y1,e.y2]),backgroundColor:eras.map(e=>e.c+'88'),borderColor:eras.map(e=>e.c),borderWidth:1,borderRadius:3,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[eras[i[0].dataIndex].l],label:i=>{const e=eras[i.dataIndex];return e.s+' ('+e.y1+' \u2014 '+(e.y2>2024?'future':e.y2)+')'}}}},
scales:{x:{type:'linear',min:1450,max:2070,grid:{color:C.grid},ticks:{color:C.dim,callback:yearTick}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
    ]

    # ─── 11. WHERE ARE ALL THE JOBS GOING ───
    charts['where-are-all-the-jobs-going-lessons-from-the-first-industrial-revolution-and-150-years-of-pain'] = [
        {
            'id': 'indChart1', 'figure_num': 1,
            'title': 'Sector Employment Shifts: 250 Years',
            'desc': 'The great migration from farms to factories to offices to… what?',
            'source': 'BLS, ONS, Maddison historical estimates',
            'position': 'after_para_4',
            'js': """
(()=>{const ctx=document.getElementById('indChart1');
const yrs=[1750,1800,1850,1900,1950,1980,2000,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Agriculture',yrs,[75,65,40,25,10,3,2,1.5],C.green),
dxy('Manufacturing',yrs,[15,20,35,40,35,25,15,8],C.amber),
dxy('Services',yrs,[10,15,25,35,55,72,83,90],C.blue)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1750,2025),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of employment (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'jobsHistChart2', 'figure_num': 2,
            'title': 'The Industrialisation Misery Gap',
            'desc': 'Decades passed between job destruction and new job creation',
            'source': 'Clark, A Farewell to Alms; Crafts & Mills wage data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('jobsHistChart2');
const yrs=[1760,1780,1800,1810,1820,1830,1840,1850,1860,1880,1900,1910];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Industrial output (index)',yrs,[10,15,22,30,40,55,70,100,130,180,250,300],C.blue),
dxy('Real wages (index)',yrs,[100,100,95,90,90,92,95,100,110,130,160,180],C.accent),
dxy('Artisan income (index)',yrs,[100,90,70,55,45,40,38,40,50,65,80,90],C.dim,[5,5])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1760,1910),y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Index (1850=100 for output)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'jobsHistChart3', 'figure_num': 3,
            'title': 'Sector Shifts: Farm to Factory to Office to...?',
            'desc': 'Each wave of automation destroyed old jobs and eventually created new ones',
            'source': 'BLS historical data; Maddison; Our World in Data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('jobsHistChart3');
const yrs=[1800,1850,1900,1920,1950,1970,1990,2000,2020,2040];
const xyF=(d)=>xy(yrs,d);
new Chart(ctx,{type:'line',data:{
datasets:[
{label:'Agriculture',data:xyF([75,60,40,30,12,4,3,2,2,1]),borderColor:C.green,backgroundColor:C.green+'20',fill:true,tension:.35,pointRadius:2,borderWidth:2},
{label:'Manufacturing',data:xyF([15,25,35,40,38,35,22,15,10,5]),borderColor:C.blue,backgroundColor:C.blue+'20',fill:true,tension:.35,pointRadius:2,borderWidth:2},
{label:'Services',data:xyF([10,15,25,28,45,55,65,70,72,60]),borderColor:C.purple,backgroundColor:C.purple+'20',fill:true,tension:.35,pointRadius:2,borderWidth:2},
{label:'AI & automation?',data:xyF([0,0,0,0,0,0,0,1,5,25]),borderColor:C.accent,backgroundColor:C.accent+'20',fill:true,tension:.35,pointRadius:2,borderWidth:2,borderDash:[5,5]}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{...legend,labels:{...legend.labels,font:{size:10}}},tooltip:tooltipStyle},
scales:{x:linX(1800,2040,{ticks:{color:C.dim,callback:v=>v===2040?v+'?':''+v}}),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'% of workforce',color:C.dim},max:80}}}});
})();"""
        },
    ]

    # ─── 12. THE 150 YEAR LIFE ───
    charts['the-150-year-life-how-radical-longevity-will-transform-our-world'] = [
        {
            'id': 'longChart1', 'figure_num': 1,
            'title': 'Human Life Expectancy Through History',
            'desc': 'From 30 years in the Stone Age to a potential 150 years ahead',
            'source': 'Our World in Data, historical demographic estimates',
            'position': 'after_para_13',
            'js': """
(()=>{const ctx=document.getElementById('longChart1');
new Chart(ctx,{type:'bar',data:{labels:['Stone\\nAge','Classical\\nAntiquity','Medieval\\nEurope','1800','1900','1950','2000','2025','2050?','2100?'],
datasets:[{label:'Life expectancy',data:[30,35,40,40,50,60,70,78,90,150],
backgroundColor:[C.dim,C.dim,C.dim,C.dim,C.amber,C.amber,C.blue,C.blue,C.green+'aa',C.green],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' years'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Life expectancy (years)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'longChart2', 'figure_num': 2,
            'title': 'Life Stages Reimagined for 150 Years',
            'desc': 'How education, careers, and retirement reshape with radical longevity',
            'source': 'Framework by History Future Now',
            'position': 'after_para_27',
            'js': """
(()=>{const ctx=document.getElementById('longChart2');
new Chart(ctx,{type:'bar',data:{
labels:['Traditional\\n(80yr life)','Extended\\n(150yr life)'],
datasets:[
{label:'Education',data:[22,35],backgroundColor:C.blue+'cc',borderRadius:3},
{label:'Career 1',data:[35,40],backgroundColor:C.amber+'cc',borderRadius:3},
{label:'Career 2',data:[0,30],backgroundColor:C.green+'cc',borderRadius:3},
{label:'Career 3',data:[0,20],backgroundColor:C.purple+'cc',borderRadius:3},
{label:'Retirement',data:[18,25],backgroundColor:C.dim+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{stacked:true,grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Years of life',color:C.dim}}},
datasets:{bar:{stacked:true}}}});
})();"""
        },
        {
            'id': 'longChart3', 'figure_num': 3,
            'title': 'Dependency Ratio: The Fiscal Challenge of Living to 150',
            'desc': 'If retirement age stays at 65, the ratio of workers to retirees collapses',
            'source': 'Illustrative calculation; UN dependency ratio data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('longChart3');
new Chart(ctx,{type:'bar',data:{labels:['1950\n(life: 50)','2000\n(life: 75)','2025\n(life: 80)','2075\n(life: 100)','2150\n(life: 150)'],
datasets:[{label:'Workers per retiree',data:[8,5,3.5,2,0.8],
backgroundColor:[C.green,C.green,C.amber,C.accent,C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' workers per retiree'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Workers per retiree',color:C.dim},min:0}}}});
})();"""
        },
    ]

    # ─── 13. FOOD & CLIMATE INACTION ───
    charts['dealing-with-the-consequences-of-climate-chance-inaction-the-impact-of-food'] = [
        {
            'id': 'foodChart1', 'figure_num': 1,
            'title': 'The Food Gap: Production Capacity vs Population',
            'desc': 'The world may only be able to feed 5 billion — but will have 10 billion mouths',
            'source': 'FAO, UN WPP, article estimates',
            'position': 'after_para_5',
            'js': """
(()=>{const ctx=document.getElementById('foodChart1');
new Chart(ctx,{type:'line',data:{labels:['2000','2010','2020','2030','2040','2050'],
datasets:[
ds('World population (bn)',[6.1,6.9,7.8,8.5,9.2,10],C.accent),
ds('Sustainable food capacity (bn)',[7,6.5,6,5.5,5.2,5],C.green,[5,3])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'bn'},title:{display:true,text:'Billions of people',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'foodChart2', 'figure_num': 2,
            'title': 'Critical Resource Depletion Timelines',
            'desc': 'Aquifers, fish stocks, and arable soil are all declining fast',
            'source': 'FAO, World Bank, USGS groundwater surveys',
            'position': 'after_para_11',
            'js': """
(()=>{const ctx=document.getElementById('foodChart2');
new Chart(ctx,{type:'bar',data:{labels:['Underground\\naquifers','Fish stocks\\n(vs 1955)','Arable soil\\nquality','Biodiversity\\nindex'],
datasets:[{label:'% remaining',data:[40,20,70,35],
backgroundColor:[C.blue,C.teal,C.amber,C.green],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% remaining'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},max:100,title:{display:true,text:'% of resource remaining',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'foodChart3', 'figure_num': 3,
            'title': 'Food Import Dependency: Who Cannot Feed Themselves',
            'desc': 'Many of the most populous regions already import most of their food',
            'source': 'FAO, World Bank food trade data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('foodChart3');
new Chart(ctx,{type:'bar',data:{labels:['Egypt','Saudi\nArabia','Algeria','UAE','Japan','South\nKorea','UK','China','India','US'],
datasets:[{label:'Food imported (%)',data:[60,80,70,90,60,70,40,15,5,5],
backgroundColor:[C.accent,C.accent,C.accent,C.accent,C.amber,C.amber,C.blue,C.green,C.green,C.green],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of food imported'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:45}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Food imported (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'foodChart4', 'figure_num': 4,
            'title': 'Contested Rivers: Upstream Countries Hold the Power',
            'desc': 'Countries controlling river headwaters hold enormous leverage over downstream neighbours',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('foodChart4');
const rivers=[
{l:'Nile',u:'Ethiopia',d:'Egypt',t:8,c:C.accent},
{l:'Tigris-Euphrates',u:'Turkey',d:'Iraq',t:7,c:C.amber},
{l:'Brahmaputra',u:'China',d:'India/Bangladesh',t:9,c:C.purple},
{l:'Mekong',u:'China',d:'SE Asia',t:6,c:C.teal},
{l:'Indus',u:'India',d:'Pakistan',t:8,c:C.blue}
];
new Chart(ctx,{type:'bar',data:{labels:rivers.map(r=>r.l),
datasets:[{label:'Tension',data:rivers.map(r=>r.t),
backgroundColor:rivers.map(r=>r.c+'bb'),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[rivers[i[0].dataIndex].l],
label:i=>{const r=rivers[i.dataIndex];return r.u+' controls flow to '+r.d+' | Tension: '+r.t+'/10'}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Conflict tension (1-10)',color:C.dim},min:0,max:10}}}});
})();"""
        },
    ]

    # ─── 14. KEYNES AND HAYEK ───
    charts['keynes-and-hayek-are-both-dead-and-wrong'] = [
        {
            'id': 'econChart1', 'figure_num': 1,
            'title': 'Interest Rates and Asset Bubbles',
            'desc': 'Low rates fuel borrowing, which fuels bubbles — Hayek was right about this',
            'source': 'Federal Reserve, Bank of England, FRED',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('econChart1');
const yrs=[1980,1985,1990,1995,2000,2005,2008,2010,2015,2020,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
{...dxy('US Federal Funds Rate (%)',yrs,[20,8,8,6,6.5,4.25,0.25,0.25,0.5,0.25,4.5],C.blue),yAxisID:'y'},
{...dxy('US House Price Index (rebased)',yrs,[40,50,55,60,75,120,100,80,95,130,140],C.accent),yAxisID:'y1'}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const l=i.dataset.label;return l.includes('Rate')?l+': '+i.raw+'%':l+': '+i.raw}}}},
scales:{x:linX(1980,2025),
y:{type:'linear',position:'left',grid:{color:C.grid},ticks:{color:C.blue,callback:v=>v+'%'},min:0,title:{display:true,text:'Federal Funds Rate (%)',color:C.blue}},
y1:{type:'linear',position:'right',grid:{drawOnChartArea:false},ticks:{color:C.accent},min:0,title:{display:true,text:'House Price Index',color:C.accent}}}}});
})();"""
        },
        {
            'id': 'keyChart2', 'figure_num': 2,
            'title': 'Versailles to Weimar: How Reparations Led to Catastrophe',
            'desc': 'Keynes warned that crushing reparations would destabilise Germany',
            'source': 'Keynes, Economic Consequences of the Peace (1919)',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('keyChart2');
const yrs=[1918,1920,1922,1924,1926,1928,1929,1930,1931,1932,1933];
new Chart(ctx,{type:'line',data:{
datasets:[
{...dxy('German unemployment %',yrs,[3,4,3,8,10,6,10,15,24,30,25],C.accent),yAxisID:'y'},
{...dxy('Reparations paid (bn gold marks, cumul.)',yrs,[0,1,2,4,5,7,8,8,8,8,8],C.blue,[5,5]),yAxisID:'y1'}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const l=i.dataset.label;return l.includes('unemployment')?l+': '+i.raw+'%':l+': '+i.raw+'bn'}}}},
scales:{x:linX(1918,1933),
y:{type:'linear',position:'left',grid:{color:C.grid},ticks:{color:C.accent,callback:v=>v+'%'},min:0,title:{display:true,text:'Unemployment %',color:C.accent}},
y1:{type:'linear',position:'right',grid:{drawOnChartArea:false},ticks:{color:C.blue,callback:v=>v+'bn'},min:0,title:{display:true,text:'Reparations (bn gold marks)',color:C.blue}}}}});
})();"""
        },
    ]

    # ─── 15. IMMIGRATION HISTORY ───
    charts['what-the-history-of-immigration-teaches-us-about-europes-future'] = [
        {
            'id': 'immChart1', 'figure_num': 1,
            'title': 'Foreign-Born Population in European Countries',
            'desc': 'The share of foreign-born residents has risen dramatically since 1960',
            'source': 'OECD, Eurostat, national statistics',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('immChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Switzerland','Austria','Sweden','Germany','UK','France','Spain','Italy','Ireland','Netherlands'],
datasets:[
{label:'1960',data:[10,5,4,3,4,7,0.5,0.5,2,4],backgroundColor:C.blue+'88',borderRadius:3},
{label:'2020',data:[30,19,20,17,14,13,14,11,18,14],backgroundColor:C.accent+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Foreign-born as % of population',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'immChart2', 'figure_num': 2,
            'title': 'Immigration to Europe: Volume and Share Over Time',
            'desc': 'From post-war reconstruction labour to the 2015 refugee crisis — absolute numbers and population share',
            'source': 'UN Migration Data Portal; Eurostat',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('immChart2');
const yrs=[1950,1960,1970,1980,1990,2000,2005,2010,2015,2020];
new Chart(ctx,{type:'line',data:{
datasets:[
{...dxy('Foreign-born in EU (millions)',yrs,[10,14,18,20,23,33,40,47,54,55],C.accent),yAxisID:'y'},
{...dxy('Foreign-born as % of EU pop.',yrs,[3.0,3.5,4.5,5.0,5.5,7.0,8.5,9.5,10.5,11.0],C.blue,[5,5]),yAxisID:'y1'}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const l=i.dataset.label;return l.includes('millions')?l+': '+i.raw+'M':l+': '+i.raw+'%'}}}},
scales:{x:linX(1950,2020),
y:{type:'linear',position:'left',grid:{color:C.grid},ticks:{color:C.accent,callback:v=>v+'M'},min:0,title:{display:true,text:'Foreign-born (millions)',color:C.accent}},
y1:{type:'linear',position:'right',grid:{drawOnChartArea:false},ticks:{color:C.blue,callback:v=>v+'%'},min:0,title:{display:true,text:'Share of EU population (%)',color:C.blue}}}}});
})();"""
        },
        {
            'id': 'immChart3', 'figure_num': 3,
            'title': 'Immigration Waves: Source Regions by Era',
            'desc': 'The composition of immigration to Europe has shifted dramatically',
            'source': 'Analysis from this article; Eurostat',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('immChart3');
new Chart(ctx,{type:'bar',data:{labels:['1950s-60s\nReconstruction','1970s-80s\nFamily reunion','1990s\nPost-Cold War','2000s\nEU expansion','2010s\nRefugee crisis'],
datasets:[
{label:'Intra-European',data:[50,30,40,55,25],backgroundColor:C.blue+'bb',borderRadius:2,borderSkipped:false},
{label:'N. Africa / Turkey',data:[30,35,15,10,15],backgroundColor:C.amber+'bb',borderRadius:2,borderSkipped:false},
{label:'Sub-Saharan Africa',data:[5,10,10,10,20],backgroundColor:C.green+'bb',borderRadius:2,borderSkipped:false},
{label:'Middle East / Asia',data:[5,15,25,15,35],backgroundColor:C.accent+'bb',borderRadius:2,borderSkipped:false},
{label:'Other',data:[10,10,10,10,5],backgroundColor:C.dim+'bb',borderRadius:2,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{...legend,labels:{...legend.labels,font:{size:10}}},tooltip:tooltipStyle},
scales:{x:{stacked:true,grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{stacked:true,grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share by source (%)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 16. LETS TALK ABOUT SEX ───
    charts['lets-talk-about-sex-does-the-separation-of-pleasure-and-procreation-mean-the-end-of-people'] = [
        {
            'id': 'sexChart1', 'figure_num': 1,
            'title': 'Global Fertility Rate Collapse',
            'desc': 'From 5 children per woman in 1960 to 2.3 today — heading below replacement',
            'source': 'UN WPP 2024, World Bank',
            'position': 'after_para_7',
            'js': """
(()=>{const ctx=document.getElementById('sexChart1');
const yrs=[1960,1970,1980,1990,2000,2010,2020,2025,2050,2100];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('World average',yrs,[5.0,4.7,3.7,3.2,2.7,2.5,2.3,2.3,2.1,1.8],C.accent),
dxy('Europe',yrs,[2.6,2.3,1.9,1.7,1.4,1.5,1.5,1.4,1.4,1.5],C.blue),
dxy('Sub-Saharan Africa',yrs,[6.7,6.8,6.8,6.4,5.8,5.2,4.5,4.2,3.0,2.1],C.amber),
{label:'Replacement level',data:xy(yrs,Array(10).fill(2.1)),borderColor:C.dim,borderWidth:1.5,borderDash:[5,3],pointRadius:0,fill:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:linX(1960,2100),y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Children per woman (TFR)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'sexChart2', 'figure_num': 2,
            'title': 'Sub-Replacement Fertility: A Global Phenomenon',
            'desc': 'Most developed nations now have fertility rates below the replacement level of 2.1',
            'source': 'UN World Population Prospects 2022; World Bank',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('sexChart2');
new Chart(ctx,{type:'bar',data:{labels:['South\nKorea','Spain','Italy','Japan','Germany','China','UK','France','US','Brazil','India','Nigeria'],
datasets:[{label:'Total fertility rate (2023)',data:[0.72,1.16,1.24,1.20,1.35,1.09,1.49,1.79,1.62,1.65,2.03,5.14],
backgroundColor:['#c43425','#c43425','#c43425','#c43425','#c43425','#c43425','#b8751a','#b8751a','#b8751a','#b8751a','#0d9a5a','#0d9a5a'],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' children per woman'}},
annotation:{annotations:{replacement:{type:'line',yMin:2.1,yMax:2.1,borderColor:C.dim,borderDash:[6,4],borderWidth:1.5,label:{display:true,content:'Replacement (2.1)',position:'end',color:C.dim,font:{size:10}}}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:45}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Total Fertility Rate',color:C.dim},min:0,max:5.5}}}});
})();"""
        },
    ]

    # ─── 17. ELECTRICITY UTILITIES CRISIS ───
    charts['big-european-electricity-utilities-are-facing-an-existential-crisis-how-did-this-happen-and-what-should-they-do'] = [
        {
            'id': 'utilChart1', 'figure_num': 1,
            'title': 'European Utility Share Prices: The Collapse',
            'desc': 'Indexed to 100 in 2007 — most have lost 50-90% of their value',
            'source': 'Bloomberg, company filings',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('utilChart1');
new Chart(ctx,{type:'line',data:{labels:['2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017'],
datasets:[
ds('EDF',[100,70,80,75,50,40,45,40,25,20,22],C.blue),
ds('RWE',[100,65,70,60,45,30,25,28,15,10,18],C.accent),
ds('E.ON',[100,60,65,55,40,30,28,25,18,15,20],C.amber),
ds('ENEL',[100,55,60,50,40,35,30,35,38,35,45],C.purple),
ds('DONG (Ørsted)',[100,85,80,85,90,95,100,110,130,150,180],C.green)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Share price (indexed, 2007=100)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'utilChart2', 'figure_num': 2,
            'title': 'Utility Value Chain: Old Model vs Symbiosis Model',
            'desc': 'The old vertically integrated model is dead — utilities must reinvent as development partners',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('utilChart2');
new Chart(ctx,{type:'bar',data:{labels:['Generation','Distribution','Customer\nmgmt','Development\n& construction','Asset\nmgmt','Trading'],
datasets:[
{label:'Old model (value %)',data:[40,30,20,5,3,2],backgroundColor:C.dim+'bb',borderRadius:3,borderSkipped:false},
{label:'Symbiosis model (value %)',data:[5,15,10,30,25,15],backgroundColor:C.green+'bb',borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of utility value (%)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 18. ENERGY PRICE FLOOR ───
    charts['establishing-a-price-floor-for-energy'] = [
        {
            'id': 'floorChart1', 'figure_num': 1,
            'title': 'Oil Price Volatility vs Proposed Price Floor',
            'desc': 'How a price floor mechanism would stabilise energy investment',
            'source': 'Illustrative model from this article',
            'position': 'after_para_6',
            'js': """
(()=>{const ctx=document.getElementById('floorChart1');
new Chart(ctx,{type:'line',data:{labels:['Y1','Y2','Y3','Y4','Y5','Y6','Y7','Y8','Y9','Y10'],
datasets:[
ds('Actual oil price',[100,110,95,105,85,120,90,115,80,100],C.dim),
{label:'Price floor (ratchet)',data:[100,110,110,110,110,120,120,120,120,120],borderColor:C.accent,backgroundColor:C.accent+'15',fill:true,tension:0,pointRadius:3,pointBackgroundColor:C.accent,borderWidth:2.5,borderDash:[]},
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw+'/barrel'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v},title:{display:true,text:'Price per barrel ($)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'epfChart2', 'figure_num': 2,
            'title': 'How The Price Floor Mechanism Works',
            'desc': 'When prices fall below the floor, a tax kicks in — revenue rebated when prices rise',
            'source': 'Illustrative model from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('epfChart2');
new Chart(ctx,{type:'line',data:{labels:['Year 1','Year 2','Year 3','Year 4','Year 5','Year 6','Year 7','Year 8'],
datasets:[
ds('Market price ($/bbl)',[100,110,80,75,60,90,70,55],C.dim,[5,5]),
ds('Consumer price with floor ($/bbl)',[100,110,100,100,100,100,100,100],C.accent),
ds('Tax/rebate buffer ($)',[0,0,20,25,40,10,30,45],C.green)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v},title:{display:true,text:'$/barrel',color:C.dim},min:0,max:130}}}});
})();"""
        },
    ]

    # ─── 19. VERTICAL FARMING ───
    charts['vertical-farming-the-electrical-convergence-power-transport-and-agriculture'] = [
        {
            'id': 'vfChart1', 'figure_num': 1,
            'title': 'Vertical Farming vs Conventional Agriculture',
            'desc': 'Land use, water use, and yield per square metre compared',
            'source': 'Various vertical farming research papers, USDA',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('vfChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Land use\\n(m² per kg)','Water use\\n(litres per kg)','Yield\\n(kg/m²/year)','Pesticides\\n(relative)'],
datasets:[
{label:'Conventional farm',data:[100,200,5,100],backgroundColor:C.amber+'cc',borderRadius:3},
{label:'Vertical farm',data:[1,20,80,0],backgroundColor:C.green+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'vfChart2', 'figure_num': 2,
            'title': 'The Electrical Convergence: Power, Transport, and Agriculture',
            'desc': 'Electrification is merging three previously separate sectors',
            'source': 'Analysis from this article; IEA data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('vfChart2');
const sectors=['Electricity\ngeneration','Transport','Agriculture','Heating &\ncooling'];
new Chart(ctx,{type:'bar',data:{labels:sectors,
datasets:[
{label:'Electrified today (%)',data:[40,3,5,10],backgroundColor:C.blue+'bb',borderRadius:3,borderSkipped:false},
{label:'Electrified by 2050 (%)',data:[80,50,30,60],backgroundColor:C.green+'bb',borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share electrified (%)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 20. PLATFORM TECHNOLOGIES ───
    charts['platform-technologies-how-foundational-technologies-of-the-past-show-us-the-foundational-technologies-of-the-future'] = [
        {
            'id': 'platChart1', 'figure_num': 1,
            'title': 'Platform Technology Adoption Timelines',
            'desc': 'Time from invention to mass adoption is accelerating dramatically',
            'source': 'Various technology adoption studies',
            'position': 'after_para_10',
            'js': """
(()=>{const ctx=document.getElementById('platChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Electricity','Telephone','Radio','Television','Personal\\nComputer','Internet','Smartphone','AI\\nAssistants'],
datasets:[{label:'Years to 50M users',data:[46,75,38,13,16,7,3,0.5],
backgroundColor:[C.dim,C.dim,C.amber,C.amber,C.blue,C.blue,C.purple,C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' years to 50M users'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Years to reach 50 million users',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'platChart2', 'figure_num': 2,
            'title': 'Technology Convergence: Reinforcing Platform Technologies',
            'desc': 'Emerging technologies form an interconnected ecosystem, each accelerating the others',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('platChart2');
const techs=['AI','Robotics','Quantum\nComputing','Biotech','Space\nTech','Vertical\nFarming','Nano-\nmaterials','Brain-Computer\nInterfaces'];
const connections=[8,7,5,6,4,3,4,3];
new Chart(ctx,{type:'bar',data:{labels:techs,
datasets:[{label:'Cross-technology connections',data:connections,
backgroundColor:[C.accent,C.blue,C.purple,C.green,C.teal,C.amber,C.cyan,C.rose],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' connections to other platforms'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Reinforcing connections',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'platChart3', 'figure_num': 3,
            'title': 'Years From Invention to Mass Adoption',
            'desc': 'Each generation of platform technology has adopted faster than the last',
            'source': 'Historical adoption data; Our World in Data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('platChart3');
new Chart(ctx,{type:'bar',data:{labels:['Electricity','Telephone','Automobile','Radio','Television','Computer','Internet','Smartphone','AI assistants'],
datasets:[{label:'Years to 50M users',data:[46,50,62,22,13,14,4,2,0.2],
backgroundColor:[C.dim,C.dim,C.dim,C.amber,C.amber,C.blue,C.blue,C.purple,C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' years to 50M users'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:45}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Years to 50 million users',color:C.dim}}}}});
})();"""
        },
    ]

    # ═══════════════════════════════════════════════════════
    # TIER 3: SUPPORTING CHARTS
    # ═══════════════════════════════════════════════════════

    # ─── 21. CHINA COLONIAL POWER ───
    charts['china-has-many-of-the-characteristics-of-an-emerging-colonial-power-how-does-it-compare-historically'] = [
        {
            'id': 'chinaColChart1', 'figure_num': 1,
            'title': 'Colonial Powers Through History',
            'desc': 'From Phoenician city-states to modern China — the pattern repeats',
            'source': 'Historical analysis from this article',
            'position': 'after_para_8',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('chinaColChart1');
const powers=[{l:'Phoenicia',y:800},{l:'Greek city-states',y:600},{l:'Rome',y:500},{l:'Germanic tribes',y:200},{l:'Spanish Empire',y:350},{l:'British Empire',y:400},{l:'French Empire',y:200},{l:'Chinese expansion',y:50}];
new Chart(ctx,{type:'bar',data:{labels:powers.map(p=>p.l),
datasets:[{label:'Duration (years)',data:powers.map(p=>p.y),
backgroundColor:[C.teal,C.blue,C.purple,C.dim,C.amber,C.blue,C.accent,C.accent],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' years of colonial expansion'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Duration of colonial period (years)',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'chinaColChart2', 'figure_num': 2,
            'title': 'China\'s Global Lending: Belt and Road Investment',
            'desc': 'Chinese overseas development lending now rivals the World Bank',
            'source': 'AidData; Boston University GDP Center; World Bank',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('chinaColChart2');
new Chart(ctx,{type:'bar',data:{labels:['Sub-Saharan\nAfrica','SE Asia','Central\nAsia','Latin\nAmerica','Middle\nEast','Europe','Pacific\nIslands'],
datasets:[{label:'Chinese lending ($bn)',data:[150,120,65,55,40,30,10],
backgroundColor:[C.accent,C.amber,C.purple,C.green,C.teal,C.blue,C.cyan],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.raw+'bn in Chinese loans'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v+'bn'},title:{display:true,text:'Cumulative Chinese lending ($bn)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 22. HINKLEY POINT / BEAMS & COLUMNS ───
    charts['hinkley-point-decision-is-really-about-china-and-brexit'] = [
        {
            'id': 'hinkChart1', 'figure_num': 1,
            'title': 'UK Farm Income: Subsidy Dependence',
            'desc': '53% of UK farm income comes from government subsidies',
            'source': 'Defra, EU CAP data',
            'position': 'after_para_7',
            'js': """
(()=>{const ctx=document.getElementById('hinkChart1');
new Chart(ctx,{type:'doughnut',data:{labels:['Subsidy income','Market income'],
datasets:[{data:[53,47],backgroundColor:[C.accent,C.green],borderWidth:0,hoverOffset:8}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},cutout:'55%',plugins:{legend:{position:'bottom',labels:{padding:20,font:{size:13}}},
tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of farm income'}}}}});
})();"""
        },
        {
            'id': 'hpChart2', 'figure_num': 2,
            'title': 'UK Energy Mix: The Nuclear Gap',
            'desc': 'As old nuclear stations close, the UK faces a growing baseload gap',
            'source': 'BEIS; National Grid; Digest of UK Energy Statistics',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('hpChart2');
new Chart(ctx,{type:'line',data:{labels:['2010','2015','2020','2025','2030','2035'],
datasets:[
ds('Nuclear (GW capacity)',[10,9,8,5,3,6],C.purple),
ds('Renewables (GW capacity)',[10,25,45,60,75,90],C.green),
ds('Gas (GW capacity)',[30,30,28,25,20,10],C.amber),
ds('Demand peak (GW)',[60,55,55,55,58,60],C.accent,[5,5])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{...legend,labels:{...legend.labels,font:{size:10}}},tooltip:tooltipStyle},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'GW capacity',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 23. WHY CHINA COULD INVADE TAIWAN ───
    charts['why-china-could-invade-taiwan-and-get-away-with-it'] = [
        {
            'id': 'taiwanChart1', 'figure_num': 1,
            'title': 'China vs Taiwan: Military Comparison',
            'desc': 'The overwhelming asymmetry in conventional military power',
            'source': 'IISS Military Balance, SIPRI, 2024',
            'position': 'after_para_6',
            'js': """
(()=>{const ctx=document.getElementById('taiwanChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Active military\\n(thousands)','Combat aircraft','Naval vessels','Military budget\\n($bn)'],
datasets:[
{label:'China',data:[2035,3260,730,292],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Taiwan',data:[170,460,90,19],backgroundColor:C.blue+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'twChart2', 'figure_num': 2,
            'title': 'Taiwan Semiconductor Dominance: Global Chip Production',
            'desc': 'Taiwan produces over 60% of the world\'s semiconductors — the real reason it matters',
            'source': 'SIA; TSMC annual reports; BCG analysis',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('twChart2');
new Chart(ctx,{type:'doughnut',data:{labels:['Taiwan (TSMC+others)','South Korea (Samsung)','China','US','Europe','Other'],
datasets:[{data:[63,18,6,5,3,5],
backgroundColor:[C.accent+'cc',C.blue+'cc',C.amber+'cc',C.purple+'cc',C.teal+'cc',C.dim+'cc'],borderColor:'#fff',borderWidth:2}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{position:'bottom',labels:{padding:12,usePointStyle:true,font:{size:11}}},
tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of global advanced chips'}}}}});
})();"""
        },
    ]

    # ─── 24. ROOTS: CLIMATE DENIAL, CREATIONISM, SLAVERY ───
    charts['roots-a-historical-understanding-of-climate-change-denial-creationism-and-slavery-1629-1775'] = [
        {
            'id': 'rootsChart1', 'figure_num': 1,
            'title': 'Four Waves of British Immigration to America',
            'desc': 'Each wave brought distinct cultural values that persist to this day',
            'source': 'David Hackett Fischer, "Albion\'s Seed" (1989)',
            'position': 'after_para_7',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('rootsChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Wave 1: Puritans\\n(1629-1640)','Wave 2: Cavaliers\\n(1642-1675)','Wave 3: Quakers\\n(1675-1715)','Wave 4: Borderers\\n(1717-1775)'],
datasets:[{label:'Settlement region',data:[1,1,1,1],
backgroundColor:[C.blue,C.accent,C.green,C.amber],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[['Puritans → New England','Cavaliers → Virginia/Maryland','Quakers → Delaware Valley','Borderers → Appalachia'][i[0].dataIndex]],
label:i=>['From East Anglia. Education, community, covenant.','From SW England. Hierarchy, honour, slavery.','From N. Midlands. Egalitarian, pacifist, anti-slavery.','From Scottish borders. Individualist, warrior culture.'][i.dataIndex]}}},
scales:{x:{display:false},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'rootsChart2', 'figure_num': 2,
            'title': 'The Pattern Repeats: Economic Interest vs Scientific Evidence',
            'desc': 'From slavery to creationism to climate denial — the same playbook every time',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('rootsChart2');
const issues=[
{l:'Slavery defence',peak:1830,decline:1865,interest:'Plantation economy',c:C.dim},
{l:'Creationism',peak:1925,decline:1960,interest:'Religious authority',c:C.purple},
{l:'Tobacco denial',peak:1965,decline:1998,interest:'Tobacco industry',c:C.amber},
{l:'Climate denial',peak:2010,decline:2030,interest:'Fossil fuel industry',c:C.accent}
];
new Chart(ctx,{type:'bar',data:{labels:issues.map(i=>i.l),
datasets:[{data:issues.map(i=>[i.peak,i.decline]),backgroundColor:issues.map(i=>i.c+'88'),borderColor:issues.map(i=>i.c),borderWidth:1,borderRadius:3,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[issues[i[0].dataIndex].l],label:i=>{const d=issues[i.dataIndex];return 'Peak: '+d.peak+', Decline: '+d.decline+' | Interest: '+d.interest}}}},
scales:{x:{type:'linear',min:1800,max:2040,grid:{color:C.grid},ticks:{color:C.dim,callback:yearTick}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
    ]

    # ─── 25. WHO ARE THE LOSERS IN ENERGY REVOLUTION ───
    charts['who-are-the-losers-in-the-energy-revolution'] = [
        {
            'id': 'losersChart1', 'figure_num': 1,
            'title': 'Winners and Losers of the Energy Transition',
            'desc': 'Some sectors and countries will thrive, others face existential threats',
            'source': 'Analysis by History Future Now',
            'position': 'after_para_7',
            'js': """
(()=>{const ctx=document.getElementById('losersChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Solar/wind\\nmanufacturers','Battery\\nmakers','Electric\\nvehicles','Oil\\nmajors','Coal\\nminers','Gas\\nutilities','Petrostates','Renewable-rich\\nnations'],
datasets:[{label:'Impact score',data:[9,8,7,-8,-9,-6,-7,8],
backgroundColor:[9,8,7,-8,-9,-6,-7,8].map(v=>v>0?C.green:C.accent),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>(i.raw>0?'Winner: +':'Loser: ')+i.raw+'/10'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Impact (-10 = devastated, +10 = thriving)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'losersChart2', 'figure_num': 2,
            'title': 'Stranded Assets: Fossil Fuel Reserves That Cannot Be Burned',
            'desc': 'If climate targets are met, trillions in fossil fuel assets become worthless',
            'source': 'Carbon Tracker Initiative; IEA WEO',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('losersChart2');
new Chart(ctx,{type:'bar',data:{labels:['Coal\nreserves','Oil\nreserves','Gas\nreserves'],
datasets:[
{label:'Can be burned (2°C budget)',data:[20,35,50],backgroundColor:C.amber+'bb',borderRadius:3,borderSkipped:false},
{label:'Must stay in ground',data:[80,65,50],backgroundColor:C.dim+'bb',borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of known reserves'}}},
scales:{x:{stacked:true,grid:{display:false},ticks:{color:C.dim,maxRotation:0}},
y:{stacked:true,grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'Share of known reserves (%)',color:C.dim},max:100}}}});
})();"""
        },
    ]

    # ─── 26. MASS MIGRATION & ROBOTS PARADOX ───
    charts['the-paradox-of-mass-migration-and-robots-in-the-age-of-automation'] = [
        {
            'id': 'paradoxChart1', 'figure_num': 1,
            'title': 'The Paradox: Immigration Rising as Robot Capability Increases',
            'desc': 'Why are we importing workers just as machines can do the work?',
            'source': 'OECD, IFR World Robotics, Eurostat',
            'position': 'after_para_40',
            'js': """
(()=>{const ctx=document.getElementById('paradoxChart1');
new Chart(ctx,{type:'line',data:{labels:['2000','2005','2010','2015','2020','2025','2030'],
datasets:[
ds('Net migration to OECD (M/yr)',[3,3.5,4,5,3.5,5.5,6],C.blue),
ds('Industrial robots installed globally (M)',[0.7,0.9,1.1,1.6,3,4.5,7],C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Millions',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'paradoxChart2', 'figure_num': 2,
            'title': 'The Automation Paradox: Sectors Most Exposed',
            'desc': 'The same sectors that rely on immigrant labour are most vulnerable to automation',
            'source': 'McKinsey Global Institute; OECD migration data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('paradoxChart2');
new Chart(ctx,{type:'bar',data:{labels:['Agriculture','Food\nprocessing','Construction','Warehousing','Cleaning','Hospitality','Garment\nmanufacture','Care work'],
datasets:[
{label:'Immigrant workforce share (%)',data:[45,35,30,40,55,30,50,25],backgroundColor:C.blue+'bb',borderRadius:3,borderSkipped:false},
{label:'Automation potential (%)',data:[60,65,40,75,50,70,85,30],backgroundColor:C.accent+'bb',borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},title:{display:true,text:'%',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 27. GREEN IS NOT RED BUT BLUE ───
    charts['green-is-not-red-but-blue-environmentalism-and-the-mystery-of-right-wing-opposition'] = [
        {
            'id': 'greenChart1', 'figure_num': 1,
            'title': 'The Political Alignment Shift on Environmentalism',
            'desc': 'How green politics moved from conservative market mechanisms to left-wing activism',
            'source': 'Historical analysis by History Future Now',
            'position': 'after_para_4',
            'js': """
(()=>{const ctx=document.getElementById('greenChart1');
new Chart(ctx,{type:'radar',data:{
labels:['National\\nsecurity','Energy\\nprice stability','Market\\nmechanisms','Job\\ncreation','Fiscal\\nresponsibility','Rural\\neconomy'],
datasets:[
{label:'Conservative case for green',data:[9,8,7,6,7,8],borderColor:C.blue,backgroundColor:C.blue+'20',pointBackgroundColor:C.blue,borderWidth:2},
{label:'Left-wing green framing',data:[3,4,3,8,4,5],borderColor:C.accent,backgroundColor:C.accent+'20',pointBackgroundColor:C.accent,borderWidth:2}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},scales:{r:{grid:{color:C.grid},ticks:{display:false},pointLabels:{font:{size:11},color:C.dim},min:0,max:10}}}});
})();"""
        },
        {
            'id': 'greenChart2', 'figure_num': 2,
            'title': 'Conservative Environmentalism Through History',
            'desc': 'Environmentalism has deep conservative roots — before it was captured by the left',
            'source': 'Analysis from this article',
            'position': 'before_end',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('greenChart2');
const events=[
{y:1872,l:'Yellowstone (Republican Grant)',c:C.blue},
{y:1906,l:'Antiquities Act (Republican Roosevelt)',c:C.blue},
{y:1970,l:'EPA created (Republican Nixon)',c:C.blue},
{y:1970,l:'First Earth Day (bipartisan)',c:C.green},
{y:1987,l:'Montreal Protocol (Republican Reagan)',c:C.blue},
{y:1990,l:'Clean Air Act (Republican Bush Sr)',c:C.blue},
{y:2006,l:'Inconvenient Truth — issue politicised',c:C.accent},
{y:2015,l:'Paris Agreement — partisan divide hardens',c:C.accent},
{y:2017,l:'US withdrawal (Republican Trump)',c:C.accent}
];
new Chart(ctx,{type:'bar',data:{labels:events.map(e=>e.y),
datasets:[{data:events.map((_,i)=>i+1),backgroundColor:events.map(e=>e.c+'bb'),borderRadius:4,borderSkipped:false,barPercentage:.6}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>[events[i[0].dataIndex].l],label:i=>'Year: '+events[i.dataIndex].y}}},
scales:{x:{display:false},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
    ]

    # ─── 28. WHY BUYING CHEAP IMPORTS IS EXPENSIVE ───
    charts['why-buying-cheap-imported-products-is-more-expensive-for-individuals-and-not-just-society'] = [
        {
            'id': 'cheapChart1', 'figure_num': 1,
            'title': 'Lifecycle Cost of Imported vs Domestic Products',
            'desc': 'The £15 saving on a product creates £30+ in societal costs',
            'source': 'Illustrative calculation from this article',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('cheapChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Product price','+ Lost tax\\nrevenue','+ Benefits\\npaid','+ Retraining\\ncost','= True cost'],
datasets:[
{label:'Imported',data:[100,12,18,5,135],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Domestic',data:[115,0,0,0,115],backgroundColor:C.blue+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>'£'+i.raw}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'£'+v}}}}});
})();"""
        },
        {
            'id': 'cheapChart2', 'figure_num': 2,
            'title': 'The Hidden Subsidy: Who Pays When Jobs Move Abroad',
            'desc': 'Consumers save on price but taxpayers pay for unemployment, retraining, and social costs',
            'source': 'Analysis from this article; OECD social expenditure data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('cheapChart2');
new Chart(ctx,{type:'bar',data:{labels:['Consumer\nsaving','Lost tax\nrevenue','Unemployment\nbenefits','Retraining\ncosts','Health &\nsocial costs','Net cost to\nsociety'],
datasets:[{data:[100,-40,-25,-15,-30,-10],
backgroundColor:[C.green+'cc',C.accent+'cc',C.accent+'cc',C.accent+'cc',C.accent+'cc',C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>(i.raw>0?'+':'')+i.raw+' (index)'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Index (consumer saving = 100)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 29. HISTORY WRITTEN BY WINNERS ───
    charts['history-is-written-by-the-winners-and-europeans-are-losing'] = [
        {
            'id': 'winChart1', 'figure_num': 1,
            'title': 'Post-WW2 European Displacement',
            'desc': '60 million Europeans forcibly moved as borders were redrawn',
            'source': 'UNHCR historical data, academic estimates',
            'position': 'after_para_4',
            'js': """
(()=>{const ctx=document.getElementById('winChart1');
new Chart(ctx,{type:'bar',data:{labels:['Germans\\nexpelled','Poles\\nrelocated','Ukrainians\\nmoved','Hungarians\\ndisplaced','Others'],
datasets:[{label:'Millions displaced',data:[12.5,8,5,3,31.5],
backgroundColor:[C.accent,C.blue,C.amber,C.purple,C.dim],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'M people displaced'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M'},title:{display:true,text:'Millions of people',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'winnersChart2', 'figure_num': 2,
            'title': 'Whose History Gets Told: Language of Academic Publications',
            'desc': 'English-language dominance in academia means non-Western perspectives are systematically underrepresented',
            'source': 'Web of Science; Scopus analysis',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('winnersChart2');
new Chart(ctx,{type:'doughnut',data:{labels:['English','Chinese','Spanish','French','German','Japanese','Other'],
datasets:[{data:[78,6,3,3,2,1,7],
backgroundColor:[C.blue+'cc',C.accent+'cc',C.amber+'cc',C.purple+'cc',C.teal+'cc',C.rose+'cc',C.dim+'cc'],borderColor:'#fff',borderWidth:2}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{position:'bottom',labels:{padding:12,usePointStyle:true,font:{size:11}}},
tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of global academic output'}}}}});
})();"""
        },
    ]

    # ─── 30. WHY THE MILITARY: ENERGY & TRADE ───
    charts['why-do-we-need-the-military-securing-energy-supplies-and-trade-routes'] = [
        {
            'id': 'milChart1', 'figure_num': 1,
            'title': 'Global Military Spending vs Energy Trade Value',
            'desc': 'How much of military spending is really about securing energy?',
            'source': 'SIPRI, IEA, World Bank',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('milChart1');
new Chart(ctx,{type:'bar',data:{
labels:['US','China','Russia','UK','France','Saudi\\nArabia','India'],
datasets:[
{label:'Military spending ($bn)',data:[886,292,86,68,56,75,84],backgroundColor:C.accent+'cc',borderRadius:3},
{label:'Energy imports ($bn)',data:[200,350,0,40,50,0,160],backgroundColor:C.blue+'cc',borderRadius:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>'$'+v+'bn'}}}}});
})();"""
        },
        {
            'id': 'milChart2', 'figure_num': 2,
            'title': 'Critical Chokepoints: Where Energy Trade Meets Military Power',
            'desc': 'A handful of narrow straits carry the majority of global energy trade',
            'source': 'EIA; US Navy; Lloyd\'s List maritime data',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('milChart2');
new Chart(ctx,{type:'bar',data:{labels:['Strait of\nHormuz','Strait of\nMalacca','Suez\nCanal','Bab el-\nMandeb','Turkish\nStraits','Panama\nCanal'],
datasets:[{label:'Oil flow (million barrels/day)',data:[21,16,5.5,4.8,2.9,0.9],
backgroundColor:[C.accent,C.accent,C.amber,C.amber,C.blue,C.blue],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' million barrels/day'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Oil flow (million bbl/day)',color:C.dim}}}}});
})();"""
        },
    ]

    # ─── 31. LAND DEALS IN AFRICA / FAMINE ───
    charts['why-land-deals-in-africa-could-make-the-great-irish-famine-a-minor-event'] = [
        {
            'id': 'landChart1', 'figure_num': 1,
            'title': 'Foreign Land Acquisitions in Africa',
            'desc': 'Millions of hectares of African farmland acquired by foreign nations and corporations',
            'source': 'Land Matrix, Oxfam, GRAIN database',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('landChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Ethiopia','Sudan','Tanzania','Mozambique','DRC','Madagascar','Sierra Leone','Ghana'],
datasets:[{label:'Land acquired (M hectares)',data:[3.6,3.2,2.5,2.2,1.8,1.5,1.1,0.9],
backgroundColor:C.accent,borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'M hectares'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'M ha'},title:{display:true,text:'Hectares (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'landChart2', 'figure_num': 2,
            'title': 'Arable Land per Capita: Africa vs the World',
            'desc': 'Africa has the land — but foreign deals are transferring control to outsiders',
            'source': 'World Bank; FAO; GRAIN land grab database',
            'position': 'before_end',
            'js': """
(()=>{const ctx=document.getElementById('landChart2');
new Chart(ctx,{type:'bar',data:{labels:['DRC','Sudan','Ethiopia','Mozambique','Tanzania','Nigeria','India','China','UK','Japan'],
datasets:[{label:'Arable land per capita (hectares)',data:[0.18,0.42,0.16,0.22,0.25,0.17,0.12,0.08,0.10,0.03],
backgroundColor:[C.green,C.green,C.green,C.green,C.green,C.amber,C.accent,C.accent,C.blue,C.purple],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' hectares per person'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:9},maxRotation:45}},
y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Arable hectares per capita',color:C.dim}}}}});
})();"""
        },
    ]

    # ═══════════════════════════════════════════════════════
    # NEW ARTICLES: Europe Rearms & Fourth Estate
    # ═══════════════════════════════════════════════════════

    charts['europe-rearms-why-the-continent-that-invented-total-war-is-spending-800-billion-on-defence'] = [
        {
            'id': 'rearmChart1',
            'figure_num': 1,
            'title': 'Europe\'s Six Rearmament Cycles',
            'desc': 'European defence spending as a share of GDP across six cycles of disarmament and rearmament. Each follows the same pattern: devastating war, peace dividend, new threat, frantic rearmament.',
            'source': 'EH.net, NATO, IISS, Kiel Institute.',
            'position': 'after_para_10',
            'js': """(()=>{const ctx=document.getElementById('rearmChart1');
const yrs=[1650,1700,1750,1815,1850,1870,1900,1914,1920,1932,1938,1945,1955,1985,1991,2000,2014,2022,2026];
new Chart(ctx,{type:'line',data:{
datasets:[{label:'W. Europe avg defence % GDP',data:xy(yrs,[8,5,3,2.5,2,3,3.5,4.5,4,1.5,6,45,5,3.2,2.4,1.8,1.4,1.5,2.5]),
borderColor:C.blue,backgroundColor:C.blue+'22',fill:true,tension:0.3,pointRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'400 Years of European Defence Spending: The Cycle Repeats',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'% of GDP',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0},
x:linX(1650,2030,{grid:{display:false},ticks:{color:C.dim,maxRotation:45,font:{size:9}}})}}});
})();"""
        },
        {
            'id': 'rearmChart2',
            'figure_num': 2,
            'title': 'The Peace Dividend: Military Shrinkage 1990–2023',
            'desc': 'Active military personnel in key European NATO countries collapsed after the Cold War. Germany shrank from 585,000 to 183,000. The Netherlands sold its entire tank fleet.',
            'source': 'IISS Military Balance, NATO.',
            'position': 'after_para_28',
            'js': """(()=>{const ctx=document.getElementById('rearmChart2');
new Chart(ctx,{type:'bar',data:{labels:['Germany','France','UK','Italy','Poland','Netherlands'],
datasets:[{label:'1990',data:[585,453,306,361,312,104],backgroundColor:C.blue,borderRadius:4},
{label:'2023',data:[183,203,149,165,150,35],backgroundColor:C.accent,borderRadius:4}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{display:true,position:'bottom',labels:{color:C.dim,usePointStyle:true}},
tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'k personnel'}},
title:{display:true,text:'Active Military Personnel (thousands)',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Thousands',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},beginAtZero:true},
x:{grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'rearmChart3',
            'figure_num': 3,
            'title': 'The Geography of Fear: Spending by Distance from Russia',
            'desc': 'There is an almost perfect correlation between a country\'s distance from Russia and its defence spending. Poland exceeds 4% of GDP. Spain caps at 2.1%.',
            'source': 'NATO 2025 estimates, IISS, CEPA.',
            'position': 'after_para_42',
            'js': """(()=>{const ctx=document.getElementById('rearmChart3');
const colors=['#c0392b','#c0392b','#c0392b','#c0392b','#e67e22','#e67e22','#2980b9','#2980b9','#2980b9','#2980b9','#7f8c8d','#7f8c8d','#7f8c8d'];
new Chart(ctx,{type:'bar',data:{labels:['Poland','Lithuania','Estonia','Latvia','Finland','Greece','UK','France','Germany','Netherlands','Italy','Belgium','Spain'],
datasets:[{label:'% GDP',data:[4.7,3.9,3.4,3.4,2.4,3.1,2.3,2.1,2.1,2.0,1.6,1.3,1.3],backgroundColor:colors,borderRadius:4}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'Defence Spending % GDP (2025): Proximity to Russia Matters',color:C.text,font:{size:13}}},
scales:{x:{title:{display:true,text:'% of GDP',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},beginAtZero:true,max:5.5},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
    ]

    charts['the-death-of-the-fourth-estate-what-the-collapse-of-newspapers-means-for-democracy-power-and-truth'] = [
        {
            'id': 'pressChart1',
            'figure_num': 1,
            'title': 'Five Information Revolutions',
            'desc': 'Every revolution in information technology has destroyed the institutions that controlled the old one and produced decades of political chaos before new institutions stabilised the system.',
            'source': 'History Future Now analysis.',
            'position': 'after_para_8',
            'js': """(()=>{const ctx=document.getElementById('pressChart1');
new Chart(ctx,{type:'bar',data:{labels:['Printing Press\\n1450-1648','Cheap Press\\n1830-1900','Radio/TV\\n1920-1950','Internet\\n1995-2025','AI\\n2023-?'],
datasets:[{label:'Years of chaos before new institutions',data:[198,70,30,30,null],
backgroundColor:[C.blue,C.green,C.amber,C.accent,C.purple+'55'],borderColor:[C.blue,C.green,C.amber,C.accent,C.purple],borderWidth:2}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'Information Revolutions: Years of Chaos Before Stability',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Years of Instability',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},beginAtZero:true},
x:{grid:{display:false},ticks:{color:C.dim,font:{size:9}}}}}});
})();"""
        },
        {
            'id': 'pressChart2',
            'figure_num': 2,
            'title': 'The Collapse of US Newspaper Employment',
            'desc': 'US newspaper employment has fallen 80% from 458,000 in 1990 to under 87,000 in 2025. Over 3,500 newspapers have closed since 2005. 88 million Americans now live in news deserts.',
            'source': 'Bureau of Labor Statistics, Northwestern Medill Local News Initiative.',
            'position': 'after_para_38',
            'js': """(()=>{const ctx=document.getElementById('pressChart2');
const yrs=[1990,1995,2000,2004,2008,2010,2012,2014,2016,2018,2020,2022,2024,2025];
new Chart(ctx,{type:'line',data:{
datasets:[{label:'Total newspaper jobs (thousands)',data:xy(yrs,[458,400,412,380,310,260,230,200,183,160,140,120,92,87]),
borderColor:C.accent,backgroundColor:C.accent+'18',fill:true,tension:0.3,pointRadius:2},
{label:'Newsroom journalists (thousands)',data:xy([2008,2010,2012,2014,2016,2018,2020,2022,2024,2025],[71,62,54,47,42,38,34,31,30,29]),
borderColor:C.blue,fill:false,tension:0.3,borderDash:[5,5],pointRadius:2}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{display:true,position:'bottom',labels:{color:C.dim,usePointStyle:true}},
tooltip:tooltipStyle,title:{display:true,text:'US Newspaper Employment: 80% Decline in 35 Years',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Thousands',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0},
x:linX(1990,2025,{grid:{display:false},ticks:{color:C.dim,font:{size:9}}})}}});
})();"""
        },
        {
            'id': 'pressChart3',
            'figure_num': 3,
            'title': 'The Advertising Revenue Cliff',
            'desc': 'US newspaper ad revenue collapsed from $49B in 2006 to under $9B by 2023 — an 82% decline. Digital advertising never came close to replacing lost print revenue.',
            'source': 'Pew Research Center, Newspaper Association of America.',
            'position': 'after_para_52',
            'js': """(()=>{const ctx=document.getElementById('pressChart3');
new Chart(ctx,{type:'bar',data:{labels:['2000','2003','2006','2008','2010','2012','2014','2016','2018','2020','2022','2023'],
datasets:[{label:'Print advertising ($B)',data:[44,40,46,35,23,19,16,13,11,7,6,5],backgroundColor:C.accent,borderRadius:4},
{label:'Digital advertising ($B)',data:[1,1.5,3,3.5,3,3.4,3.5,3.5,3.5,2.5,2.5,2.8],backgroundColor:C.green,borderRadius:4}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{display:true,position:'bottom',labels:{color:C.dim,usePointStyle:true}},
tooltip:tooltipStyle,title:{display:true,text:'US Newspaper Advertising Revenue: The Cliff',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Billions USD',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},stacked:true,beginAtZero:true},
x:{grid:{display:false},ticks:{color:C.dim},stacked:true}}}});
})();"""
        },
        {
            'id': 'pressChart4',
            'figure_num': 4,
            'title': 'A Tale of Two Newspapers: NYT vs Washington Post',
            'desc': 'The New York Times transformed into a diversified digital subscription business with 12.8 million subscribers. The Washington Post lost nearly half its newsroom in a single day.',
            'source': 'NYT earnings, WaPo Guild, media reports.',
            'position': 'after_para_62',
            'js': """(()=>{const ctx=document.getElementById('pressChart4');
const yrs=[2013,2015,2017,2019,2021,2023,2025,2026];
new Chart(ctx,{type:'line',data:{
datasets:[{label:'NYT digital subscribers (M)',data:xy(yrs,[0.8,1.1,2.6,4.7,8.3,10.4,12.8,12.8]),
borderColor:C.green,backgroundColor:C.green+'18',fill:true,tension:0.3,pointRadius:3},
{label:'WaPo est. subscribers (M)',data:xy(yrs,[0.5,1.0,1.5,3.0,3.0,2.5,1.8,1.2]),
borderColor:C.accent,fill:false,tension:0.3,borderDash:[5,5],pointRadius:3}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{display:true,position:'bottom',labels:{color:C.dim,usePointStyle:true}},
tooltip:tooltipStyle,title:{display:true,text:'Digital Subscribers: NYT Soaring vs WaPo Collapsing',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Millions',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0},
x:linX(2013,2026,{grid:{display:false},ticks:{color:C.dim}})}}});
})();"""
        },
    ],



    # The Great Emptying
    charts['the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people'] = [
        {
            'id': 'emptyChart1',
            'figure_num': 1,
            'title': 'The Global Fertility Collapse',
            'desc': 'Total fertility rates by country. The replacement rate of 2.1 is the minimum needed for a population to sustain itself. Most of the developed world is well below it.',
            'source': 'World Bank, UN Population Division, national statistics offices (2023-2024).',
            'position': 'after_para_6',
            'js': """(()=>{const ctx=document.getElementById('emptyChart1');
new Chart(ctx,{type:'bar',data:{labels:['S. Korea','China','Poland','Spain','Italy','Japan','Greece','Finland','Germany','UK','Sweden','Australia','Denmark','USA','France','Turkey','Mexico','India','Indonesia','S. Africa','Philippines','Egypt','Iraq','Nigeria','Niger'],
datasets:[{label:'Fertility Rate',data:[0.72,1.02,1.10,1.13,1.20,1.20,1.22,1.26,1.36,1.44,1.53,1.58,1.55,1.62,1.68,1.76,1.80,2.00,2.15,2.33,2.78,3.20,3.55,5.20,6.80],
backgroundColor:function(c){var v=c.raw;if(v<1.3)return C.accent;if(v<1.5)return C.amber;if(v<2.1)return C.amber+'aa';if(v<3.0)return C.green;return C.blue},
borderRadius:3}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'Total Fertility Rate by Country (2023-2024)',color:C.text,font:{size:14}},
annotation:{annotations:{replacement:{type:'line',xMin:2.1,xMax:2.1,borderColor:C.dim,borderDash:[6,4],borderWidth:1.5,label:{display:true,content:'Replacement (2.1)',position:'start',color:C.dim,font:{size:10}}}}}},
scales:{x:{title:{display:true,text:'Total Fertility Rate',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim}},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:9}}}}}});
})();"""
        },
        {
            'id': 'emptyChart2',
            'figure_num': 2,
            'title': 'The Long Decline: Fertility Rates 1960-2024',
            'desc': 'Every major economy has fallen below the replacement rate. East Asia has collapsed fastest.',
            'source': 'World Bank, UN Population Division.',
            'position': 'after_para_9',
            'js': """(()=>{const ctx=document.getElementById('emptyChart2');
const yrs=[1960,1965,1970,1975,1980,1985,1990,1995,2000,2005,2010,2015,2020,2024];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('United States',yrs,[3.65,2.91,2.48,1.77,1.84,1.84,2.08,2.02,2.06,2.05,1.93,1.84,1.64,1.62],C.blue),
dxy('United Kingdom',yrs,[2.72,2.89,2.43,1.81,1.90,1.79,1.83,1.71,1.64,1.78,1.92,1.80,1.56,1.44],C.accent),
dxy('Germany',yrs,[2.37,2.50,2.03,1.48,1.56,1.37,1.45,1.25,1.38,1.34,1.39,1.50,1.53,1.36],C.amber),
dxy('Japan',yrs,[2.00,2.14,2.13,1.91,1.75,1.76,1.54,1.42,1.36,1.26,1.39,1.45,1.33,1.20],C.green),
dxy('South Korea',yrs,[6.00,5.63,4.53,3.47,2.83,1.67,1.59,1.65,1.48,1.09,1.23,1.24,0.84,0.72],C.amber,[5,5]),
dxy('China',yrs,[5.76,6.13,5.81,3.57,2.63,2.52,2.51,1.86,1.60,1.62,1.54,1.62,1.28,1.02],C.purple,[5,5])
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Fertility Rates 1960-2024: The Long Decline',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Total Fertility Rate',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0},
x:linX(1960,2024,{grid:{display:false},ticks:{color:C.dim}})}}});
})();"""
        },
        {
            'id': 'emptyChart3',
            'figure_num': 3,
            'title': "Europe's Fertility Crisis",
            'desc': 'Not a single European country is at replacement level. France has dropped to 1.68. Malta, Poland, and Spain are below 1.15.',
            'source': 'Eurostat, national statistics offices (2023-2024).',
            'position': 'after_para_12',
            'js': """(()=>{const ctx=document.getElementById('emptyChart3');
var c=['Malta','Poland','Spain','Lithuania','Italy','Greece','Finland','Austria','Switzerland','Latvia','Germany','Cyprus','Portugal','Estonia','Norway','Netherlands','UK','Belgium','Croatia','Hungary','Sweden','Slovenia','Denmark','Ireland','Bulgaria','Czechia','France','Romania','Turkey'];
var r=[1.08,1.10,1.13,1.16,1.20,1.22,1.26,1.31,1.33,1.35,1.36,1.37,1.41,1.41,1.41,1.43,1.44,1.47,1.47,1.50,1.53,1.55,1.55,1.55,1.63,1.64,1.68,1.71,1.76];
new Chart(ctx,{type:'bar',data:{labels:c,datasets:[{data:r,
backgroundColor:function(c){var v=c.raw;if(v<1.3)return C.accent;if(v<1.5)return C.amber;return C.amber+'aa'},
borderRadius:3}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},aspectRatio:0.65,plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'Europe: Not a Single Country at Replacement',color:C.text,font:{size:14}},
annotation:{annotations:{replacement:{type:'line',xMin:2.1,xMax:2.1,borderColor:C.dim,borderDash:[6,4],borderWidth:1.5,label:{display:true,content:'Replacement (2.1)',position:'start',color:C.dim,font:{size:10}}}}}},
scales:{x:{title:{display:true,text:'Total Fertility Rate',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0.8,max:2.3},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:9}}}}}});
})();"""
        },
        {
            'id': 'emptyChart4',
            'figure_num': 4,
            'title': 'The Economics of Parenthood',
            'desc': 'Hospital services have risen 230%, college tuition 180%, and childcare 142% since 2000 — while wages rose just 85%.',
            'source': 'Bureau of Labor Statistics, Consumer Price Index.',
            'position': 'after_para_19',
            'js': """(()=>{const ctx=document.getElementById('emptyChart4');
const yrs=[2000,2003,2005,2008,2010,2013,2015,2018,2020,2022,2024];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Hospital Services (+230%)',yrs,[0,15,25,40,50,70,90,120,160,200,230],C.accent),
dxy('College Tuition (+180%)',yrs,[0,20,30,45,55,70,85,110,140,160,180],C.rose),
dxy('Childcare (+142%)',yrs,[0,10,18,25,30,40,50,70,100,120,142],C.amber),
dxy('Average Wages (+85%)',yrs,[0,8,12,18,22,28,32,42,55,70,85],C.blue,[8,4]),
dxy('Food (+75%)',yrs,[0,5,8,15,18,22,25,30,45,60,75],C.green),
dxy('Electronics (-94%)',yrs,[0,-15,-30,-40,-55,-65,-75,-82,-88,-92,-94],C.teal,[3,3])
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Cost of Raising Children vs Wages Since 2000',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'% Change Since 2000',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'%'}}},
x:linX(2000,2024,{grid:{display:false},ticks:{color:C.dim}})}}});
})();"""
        },
        {
            'id': 'emptyChart5',
            'figure_num': 5,
            'title': 'Delayed Lives: Marriage Age Rising',
            'desc': 'The average age at first marriage has risen by a full decade since the 1960s, shrinking the window for multiple children.',
            'source': 'Office for National Statistics.',
            'position': 'after_para_22',
            'js': """(()=>{const ctx=document.getElementById('emptyChart5');
new Chart(ctx,{type:'line',data:{labels:['1970','1975','1980','1985','1990','1995','2000','2005','2010','2015','2020'],
datasets:[
ds('Males',[24.6,25.1,25.5,26.3,27.5,28.9,30.0,31.0,31.5,31.8,32.1],C.blue),
ds('Females',[22.4,22.8,23.0,24.1,25.5,26.9,28.2,29.5,30.0,30.3,30.7],C.accent)
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Average Age at First Marriage, England & Wales',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'Age',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:20,max:34},
x:{grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'emptyChart6',
            'figure_num': 6,
            'title': 'The Convergence Trap',
            'desc': 'Immigrant fertility falls toward host-country rates within one generation. Maghreb immigrants in France saw fertility halve across cohorts.',
            'source': 'INSEE, Volant, Pison & Héran, Population & Societies no. 568 (2019).',
            'position': 'after_para_29',
            'js': """(()=>{const ctx=document.getElementById('emptyChart6');
new Chart(ctx,{type:'line',data:{labels:['1931-35','1936-40','1941-45','1946-50','1951-55','1956-60','1961-65'],
datasets:[
ds('Maghreb immigrants',[4.90,4.50,4.10,3.60,3.20,2.95,2.85],C.accent),
ds('All immigrant women',[3.30,3.15,2.95,2.70,2.55,2.50,2.50],C.green),
ds('European immigrants',[2.45,2.40,2.30,2.15,2.05,2.00,2.00],C.teal),
ds('Native-born French',[2.42,2.35,2.25,2.12,2.03,1.95,1.90],C.blue,[8,4])
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Immigrant Fertility Converges to Host Country, France',color:C.text,font:{size:14}},
annotation:{annotations:{replacement:{type:'line',yMin:2.1,yMax:2.1,borderColor:C.dim,borderDash:[6,4],borderWidth:1.5,label:{display:true,content:'Replacement (2.1)',position:'end',color:C.dim,font:{size:10}}}}}},
scales:{y:{title:{display:true,text:'Children per Woman',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:1.5},
x:{title:{display:true,text:'Birth Cohort',color:C.dim},grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'emptyChart7',
            'figure_num': 7,
            'title': 'Immigration as Fiscal Drain',
            'desc': 'In Finland, native Finns are net fiscal contributors while every immigrant group represents a net cost. The Middle East & North Africa group costs €19,200 per person more than native Finns contribute.',
            'source': 'Suomen Perusta (2019), Immigrations and Public Finances in Finland. Age-standardised net fiscal effects relative to native Finnish baseline.',
            'position': 'after_para_33',
            'js': """(()=>{const ctx=document.getElementById('emptyChart7');
new Chart(ctx,{type:'bar',data:{labels:['Native Finnish','Western countries','South Asia','East Asia','E. Europe & Caucasia','All foreign-born','Latin America','Sub-Saharan Africa','SE Asia','Middle East & N. Africa'],
datasets:[{label:'Net fiscal impact per person',data:[2060,0,-1250,-4500,-5390,-6900,-7320,-9010,-11960,-17180],
backgroundColor:function(c){const v=c.raw;if(v>0)return C.green;if(v>=-1000)return C.amber;if(v>-7000)return C.amber+'cc';return C.accent},
borderRadius:3}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:function(c){const v=c.raw;const sign=v>0?'+':'';return sign+'\u20ac'+v.toLocaleString()+' vs. native Finnish'}}},
title:{display:true,text:'Net Fiscal Impact by Region of Origin, Finland',color:C.text,font:{size:14}}},
scales:{x:{title:{display:true,text:'Net Fiscal Impact (\u20ac per person, relative to native Finnish)',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return '\u20ac'+v.toLocaleString()}}},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
        {
            'id': 'emptyChart8',
            'figure_num': 8,
            'title': 'The Welfare Gap',
            'desc': '52% of legal immigrant and 59% of illegal-headed households in the US use at least one welfare program, vs 39% of US-born households.',
            'source': 'Center for Immigration Studies, U.S. Census Bureau.',
            'position': 'after_para_37',
            'js': """(()=>{const ctx=document.getElementById('emptyChart8');
new Chart(ctx,{type:'bar',data:{labels:['Any Welfare','Cash','Food (SNAP)','Medicaid','Housing'],
datasets:[
{label:'U.S.-Born',data:[39,16,25,25,5],backgroundColor:C.blue,borderRadius:3},
{label:'Legal Immigrant',data:[52,23,34,36,5],backgroundColor:C.amber,borderRadius:3},
{label:'Illegal-Headed',data:[59,18,48,39,4],backgroundColor:C.purple,borderRadius:3}
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Welfare Usage by Household Type, United States',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'% of Households',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'%'}},beginAtZero:true},
x:{grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
        {
            'id': 'emptyChart9',
            'figure_num': 9,
            'title': 'The Gerontocracy',
            'desc': 'The percentage of U.S. Congress members over 70 has tripled since the 1990s. Old voters elect old leaders who serve old priorities.',
            'source': 'Congressional Research Service.',
            'position': 'after_para_42',
            'js': """(()=>{const ctx=document.getElementById('emptyChart9');
new Chart(ctx,{type:'line',data:{
datasets:[{label:'% of Congress over 70',data:xy([1950,1960,1970,1980,1985,1990,2000,2005,2010,2015,2020,2025],[8,10,9,6,6,5,8,9,11,14,20,23]),
borderColor:C.purple,backgroundColor:C.purple+'22',fill:true,tension:0.3,pointRadius:4,pointBackgroundColor:C.purple,borderWidth:2.5}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:tooltipStyle,
title:{display:true,text:'The Gerontocracy: % of U.S. Congress Over Age 70',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'% Over 70',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'%'}},min:0},
x:linX(1950,2025,{grid:{display:false},ticks:{color:C.dim}})}}});
})();"""
        },
        {
            'id': 'emptyChart10',
            'figure_num': 10,
            'title': 'The Coming Burden: Old-Age Dependency Ratios',
            'desc': "By 2050, Japan will have 70 retirees for every 100 workers. China's ratio will nearly triple. Pension systems cannot survive these numbers.",
            'source': 'UN Population Division, World Population Prospects (2024 revision).',
            'position': 'after_para_48',
            'js': """(()=>{const ctx=document.getElementById('emptyChart10');
const yrs=[2000,2010,2020,2025,2030,2040,2050,2060];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Japan',yrs,[25,35,48,51,54,64,70,75],C.accent),
dxy('EU-27',yrs,[24,26,32,35,40,48,55,60],C.blue),
dxy('China',yrs,[10,12,17,21,26,38,47,55],C.purple,[5,5]),
dxy('United States',yrs,[19,20,26,29,33,37,39,42],C.green),
dxy('India',yrs,[8,8,10,10,11,15,19,24],C.amber)
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle,
title:{display:true,text:'Old-Age Dependency Ratios: Who Will Pay?',color:C.text,font:{size:14}}},
scales:{y:{title:{display:true,text:'65+ per 100 Working-Age',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0},
x:linX(2000,2060,{grid:{display:false},ticks:{color:C.dim}})}}});
})();"""
        },
    ]

    # ═══════════════════════════════════════════════════════
    # NEW ARTICLES (Feb 2026)
    # ═══════════════════════════════════════════════════════

    # ─── THE ROBOT BARGAIN ───
    charts['the-robot-bargain-how-ai-will-save-ageing-nations-from-the-immigration-trap'] = [
        {
            'id': 'robotBargainChart1', 'figure_num': 1,
            'title': 'Fertility Rates vs Robot Density: The Two Paths',
            'desc': 'Nations with the lowest fertility rates are investing most heavily in robots — Japan and South Korea lead both trends',
            'source': 'UN Population Division (2024); International Federation of Robotics, World Robotics Report 2025',
            'position': 'after_para_6',
            'js': """
(()=>{const ctx=document.getElementById('robotBargainChart1');
new Chart(ctx,{type:'scatter',data:{
datasets:[
{label:'Japan',data:[{x:1.20,y:399}],backgroundColor:C.accent,pointRadius:8,pointHoverRadius:10},
{label:'South Korea',data:[{x:0.72,y:1012}],backgroundColor:C.purple,pointRadius:8,pointHoverRadius:10},
{label:'Germany',data:[{x:1.35,y:415}],backgroundColor:C.blue,pointRadius:8,pointHoverRadius:10},
{label:'United States',data:[{x:1.62,y:285}],backgroundColor:C.green,pointRadius:8,pointHoverRadius:10},
{label:'China',data:[{x:1.09,y:392}],backgroundColor:C.amber,pointRadius:8,pointHoverRadius:10},
{label:'France',data:[{x:1.68,y:163}],backgroundColor:C.teal,pointRadius:8,pointHoverRadius:10},
{label:'UK',data:[{x:1.49,y:111}],backgroundColor:C.cyan,pointRadius:8,pointHoverRadius:10},
{label:'India',data:[{x:2.00,y:7}],backgroundColor:C.dim,pointRadius:8,pointHoverRadius:10}
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:{display:true,position:'bottom',labels:{padding:12,usePointStyle:true,pointStyle:'circle',font:{size:11}}},
tooltip:{...tooltipStyle,callbacks:{label:function(i){return i.dataset.label+': TFR '+i.parsed.x+', '+i.parsed.y+' robots/10k workers'}}}},
scales:{x:{title:{display:true,text:'Total Fertility Rate (children per woman)',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},reverse:true,min:0.5,max:2.2},
y:{title:{display:true,text:'Industrial Robots per 10,000 Workers',color:C.dim},grid:{color:C.grid},ticks:{color:C.dim},min:0}}}});
})();"""
        },
    ]

    # ─── THE SILENCE OF THE SCRIBES ───
    charts['the-silence-of-the-scribes-how-every-civilisation-that-controlled-speech-collapsed'] = [
        {
            'id': 'scribesChart1', 'figure_num': 1,
            'title': 'Government Content Removal Requests to Major Platforms (2024)',
            'desc': 'India, Turkey, and Russia lead the world in demanding platforms remove content — the modern equivalent of burning books',
            'source': 'Google Transparency Report 2024; X Transparency Center 2024; Meta Transparency Reports',
            'position': 'after_para_4',
            'js': """
(()=>{const ctx=document.getElementById('scribesChart1');
new Chart(ctx,{type:'bar',data:{
labels:['India','Turkey','Russia','South Korea','France','Germany','Brazil','United States','UK','Australia'],
datasets:[{label:'Content removal requests (thousands)',data:[78.5,15.3,14.8,12.1,9.7,8.4,7.2,5.9,4.8,2.1],
backgroundColor:[C.accent,C.amber,C.purple,C.blue,C.teal,C.blue+'cc',C.green,C.cyan,C.dim,C.emerald],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,
tooltip:{...tooltipStyle,callbacks:{label:function(i){return i.raw+'K requests'}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'K'}},title:{display:true,text:'Requests (thousands)',color:C.dim}},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
    ]

    # ─── THE SCRAMBLE FOR THE SOLAR SYSTEM ───
    charts['the-scramble-for-the-solar-system-why-the-next-colonial-race-has-already-begun'] = [
        {
            'id': 'solarChart1', 'figure_num': 1,
            'title': 'Cost to Launch 1 kg to Low Earth Orbit',
            'desc': 'SpaceX has reduced launch costs by 97% since the Space Shuttle era — and Starship aims to cut them by another 90%',
            'source': 'NASA, SpaceX public filings, industry estimates. Starship figure is target cost.',
            'position': 'after_para_16',
            'js': """
(()=>{const ctx=document.getElementById('solarChart1');
new Chart(ctx,{type:'bar',data:{
labels:['Space Shuttle\\n(1981-2011)','Atlas V\\n(2002-)','Falcon 9\\n(2010-)','Falcon Heavy\\n(2018-)','Starship\\n(target)'],
datasets:[{label:'Cost per kg to LEO (USD)',data:[54500,13200,2720,1500,200],
backgroundColor:[C.dim,C.amber,C.blue,C.blue+'cc',C.accent],borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,
tooltip:{...tooltipStyle,callbacks:{label:function(i){return '$'+i.raw.toLocaleString()+' per kg'}}}},
scales:{y:{type:'logarithmic',grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return '$'+v.toLocaleString()}},
title:{display:true,text:'USD per kg (log scale)',color:C.dim}},
x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}}}}});
})();"""
        },
    ]

    # ─── WHO GUARDS THE GUARDS ───
    charts['who-guards-the-guards-bureaucracy-empire-and-the-eternal-struggle-to-control-the-state'] = [
        {
            'id': 'guardsChart1', 'figure_num': 1,
            'title': 'Growth of the U.S. Code of Federal Regulations',
            'desc': 'The federal regulatory code has grown 18x since 1950 — from 10,000 pages to over 180,000',
            'source': 'Federal Register, George Washington University Regulatory Studies Center',
            'position': 'after_para_24',
            'js': """
(()=>{const ctx=document.getElementById('guardsChart1');
new Chart(ctx,{type:'line',data:{
datasets:[ds('Pages (thousands)',
[10,19,22,35,54,71,102,106,128,138,157,175,180],
C.accent)]},
labels:['1950','1960','1965','1970','1975','1980','1990','1995','2000','2005','2010','2020','2025']},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,
tooltip:{...tooltipStyle,callbacks:{label:function(i){return i.raw+'K pages'}}},
title:{display:true,text:'U.S. Code of Federal Regulations (thousands of pages)',color:C.text,font:{size:14}}},
scales:{y:{grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'K'}},
title:{display:true,text:'Pages (thousands)',color:C.dim},min:0},
x:{grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
    ]

    # ─── THE RETURN OF THE STATE FACTORY ───
    charts['the-return-of-the-state-factory-why-nations-that-forgot-how-to-make-things-are-remembering'] = [
        {
            'id': 'factoryChart1', 'figure_num': 1,
            'title': 'Manufacturing as % of GDP: The West vs China',
            'desc': 'Western nations hollowed out their manufacturing base while China built the largest industrial economy in history',
            'source': 'World Bank, National Bureau of Statistics of China, OECD',
            'position': 'after_para_22',
            'js': """
(()=>{const ctx=document.getElementById('factoryChart1');
const yrs=['1970','1980','1990','2000','2005','2010','2015','2020','2025'];
new Chart(ctx,{type:'line',data:{labels:yrs,
datasets:[
ds('United States',[24,21,17,15,13,12,12,11,11],C.blue),
ds('United Kingdom',[28,22,17,14,11,10,10,9,9],C.teal),
ds('Germany',[33,29,27,22,21,20,21,19,19],C.amber),
ds('China',[30,35,33,32,32,32,29,27,28],C.accent),
ds('Japan',[34,28,26,21,20,20,21,20,20],C.purple)
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:legend,tooltip:tooltipStyle},
scales:{y:{grid:{color:C.grid},ticks:{color:C.dim,callback:function(v){return v+'%'}},
title:{display:true,text:'Manufacturing % of GDP',color:C.dim},min:5,max:40},
x:{grid:{display:false},ticks:{color:C.dim}}}}});
})();"""
        },
    ]

    # ─── GATES OF NATIONS (Immigration Attitudes) ───
    charts['the-gates-of-nations-how-every-civilisation-in-history-controlled-immigration-until-the-west-stopped'] = [
        {
            'id': 'gatesChart1', 'figure_num': 1,
            'title': 'Foreign-Born Population Share: US, UK, Germany, France (1900–2030)',
            'desc': 'After decades of restriction, Western nations opened their borders from the 1960s onward — a historically unprecedented shift',
            'source': 'UN Population Division; Migration Policy Institute; national census data. 2025–2030 projected.',
            'position': 'after_heading:The Modern Anomaly',
            'js': """
(()=>{const ctx=document.getElementById('gatesChart1');
const yrs=['1900','1910','1920','1930','1940','1950','1960','1970','1980','1990','2000','2010','2020','2025','2030'];
new Chart(ctx,{type:'line',data:{labels:yrs,datasets:[
ds('United States',[13.6,14.7,13.2,11.6,8.8,6.9,5.4,4.7,6.2,7.9,11.1,12.9,13.7,14.3,15.1],C.blue,[]),
ds('United Kingdom',[1.5,1.5,1.5,1.8,2.0,3.4,4.3,5.8,6.2,6.5,8.3,12.0,14.4,15.8,17.0],C.accent,[]),
ds('Germany',[1.9,1.9,1.5,1.5,1.2,1.1,2.8,6.6,7.5,8.4,12.5,13.0,18.8,20.2,21.5],C.green,[]),
ds('France',[2.7,2.8,3.9,6.6,5.1,4.1,5.4,6.5,7.4,7.4,7.4,8.6,10.2,11.0,12.0],C.amber,[]),
{label:'Projected',data:[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],borderColor:C.dim,borderDash:[5,5],borderWidth:1,pointRadius:0,fill:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:tooltipStyle,
annotation:{annotations:{projLine:{type:'line',xMin:'2020',xMax:'2020',borderColor:C.dim+'80',borderWidth:1,borderDash:[4,4],label:{display:true,content:'Projected →',position:'start',font:{size:10},color:C.dim}}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:10}}},y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:10},callback:v=>v+'%'},title:{display:true,text:'Foreign-born % of population',color:C.dim},min:0,max:25}}}});
})();"""
        },
        {
            'id': 'gatesChart2', 'figure_num': 2,
            'title': 'Public Opinion: "Immigration Should Be Reduced" (1965–2024)',
            'desc': 'In every Western country, majorities have consistently wanted less immigration — and been consistently ignored',
            'source': 'Gallup (US); Ipsos MORI (UK); Infratest dimap (Germany). Selected survey years.',
            'position': 'after_heading:Public Opinion',
            'js': """
(()=>{const ctx=document.getElementById('gatesChart2');
const yrs=['1965','1975','1985','1995','2005','2010','2015','2020','2024'];
new Chart(ctx,{type:'line',data:{labels:yrs,datasets:[
ds('US: "Decrease immigration"',[33,42,49,65,52,45,38,36,55],C.blue),
ds('UK: "Too much immigration"',[null,null,null,63,73,77,71,52,58],C.accent),
ds('Germany: "Too many foreigners"',[null,null,null,null,null,53,58,44,67],C.green)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label.split(':')[0]+': '+i.raw+'%'}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:10}}},y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:10},callback:v=>v+'%'},title:{display:true,text:'% agreeing',color:C.dim},min:20,max:85}}}});
})();"""
        },
        {
            'id': 'gatesChart3', 'figure_num': 3,
            'title': 'Net Fiscal Impact of Immigration by Origin Group',
            'desc': 'The fiscal impact of immigration depends heavily on origin — a fact most governments prefer not to disaggregate',
            'source': 'Danish Ministry of Finance (2018); Dutch CPB (2003); UK MAC (2018). Annual net fiscal contribution per capita, approximate.',
            'position': 'after_heading:The Fiscal Equation',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('gatesChart3');
new Chart(ctx,{type:'bar',data:{
labels:['Denmark:\\nWestern immigrants','Denmark:\\nNon-Western immigrants','Netherlands:\\nWestern immigrants','Netherlands:\\nNon-Western immigrants','UK:\\nEEA immigrants','UK:\\nNon-EEA immigrants'],
datasets:[{label:'Net fiscal impact (€/year)',data:[2100,-4200,1800,-2900,2300,-840],
backgroundColor:[C.green,C.accent,C.green+'cc',C.accent+'cc',C.green+'99',C.accent+'99'],borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>{var v=i.raw;return (v>=0?'+':'')+v.toLocaleString()+' €/year per capita'}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:10},callback:v=>(v>=0?'+':'')+v.toLocaleString()+'€'},title:{display:true,text:'Net annual fiscal contribution per capita (€)',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}}}}});
})();"""
        },
    ]

    # ─── THE EMPTY CRADLE BARGAIN ───
    charts['the-empty-cradle-bargain-why-your-decision-not-to-have-children-is-everyones-problem'] = [
        {
            'id': 'cradleChart1', 'figure_num': 1,
            'title': 'The Arithmetic of Extinction',
            'desc': 'How 1.0 children per couple leads to population halving every generation',
            'source': 'Mathematical projection: each generation = previous × (fertility rate ÷ 2)',
            'position': 'after_para_8',
            'js': """
(()=>{const ctx=document.getElementById('cradleChart1');
const gens=['Gen 0\\n(Today)','Gen 1\\n(2055)','Gen 2\\n(2085)','Gen 3\\n(2115)','Gen 4\\n(2145)','Gen 5\\n(2175)'];
new Chart(ctx,{type:'line',data:{labels:gens,
datasets:[
{label:'1.0 children per couple',data:[100,50,25,12.5,6.25,3.1],borderColor:C.accent,backgroundColor:C.accent+'18',fill:true,tension:.3,pointRadius:5,pointBackgroundColor:C.accent,borderWidth:2.5},
{label:'1.5 children per couple',data:[100,75,56,42,32,24],borderColor:C.amber,backgroundColor:C.amber+'10',fill:false,tension:.3,pointRadius:4,pointBackgroundColor:C.amber,borderWidth:2,borderDash:[6,3]},
{label:'2.1 (replacement)',data:[100,100,100,100,100,100],borderColor:C.green,backgroundColor:C.green+'08',fill:false,tension:0,pointRadius:0,borderWidth:2,borderDash:[3,3]}
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'% of original'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},min:0,max:110,title:{display:true,text:'Population (% of starting)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'cradleChart2', 'figure_num': 2,
            'title': 'The Cost of Raising a Child vs. Median Wages',
            'desc': 'Housing, childcare, and education costs have surged while real wages flatlined — all indexed to 1975 = 100',
            'source': 'ONS, BLS, OECD, Nationwide Building Society, Coram Family and Childcare (1975-2024)',
            'position': 'after_heading:The Collapse of the Village',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('cradleChart2');
const yrs=[1975,1980,1985,1990,1995,2000,2005,2010,2015,2020,2024];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('House price / income ratio (UK)',yrs,[100,108,106,122,94,122,161,186,206,219,231],C.accent),
dxy('Childcare cost index',yrs,[100,108,118,132,155,190,240,290,340,380,420],C.purple),
dxy('Real median wages (index)',yrs,[100,102,108,115,113,125,130,128,126,130,132],C.green)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const l=i.dataset.label;if(l.includes('ratio'))return l+': '+i.raw+' ('+[3.6,3.9,3.8,4.4,3.4,4.4,5.8,6.7,7.4,7.9,8.3][i.dataIndex]+'x)';return l+': '+i.raw}}}},
scales:{x:linX(1975,2024),y:{grid:{color:C.grid},ticks:{color:C.dim},min:0,title:{display:true,text:'Index (1975 = 100)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'cradleChart3', 'figure_num': 3,
            'title': 'Female Fertility Decline by Age',
            'desc': 'Chance of conception per cycle and IVF live birth rate — the cliff edge after 35',
            'source': 'ACOG (2014), RCOG (2011), HFEA (2024). Natural conception = per-cycle probability; IVF = live birth rate per cycle.',
            'position': 'after_heading:The Celebrity Mirage',
            'js': """
(()=>{const ctx=document.getElementById('cradleChart3');
const ages=['20','25','28','30','32','35','37','38','40','42','43','45'];
const natural=[25,25,22,20,18,15,12,10,5,3,2,1];
const ivf=[null,33,33,32,30,29,25,20,11,6,4,2];
new Chart(ctx,{type:'line',data:{labels:ages,
datasets:[
{label:'Natural conception (% per cycle)',data:natural,borderColor:C.accent,backgroundColor:C.accent+'18',fill:true,tension:.3,pointRadius:4,pointBackgroundColor:C.accent,borderWidth:2.5},
{label:'IVF live birth rate (% per cycle)',data:ivf,borderColor:C.purple,backgroundColor:C.purple+'10',fill:false,tension:.3,pointRadius:4,pointBackgroundColor:C.purple,borderWidth:2.5,borderDash:[6,3]}
]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'%'}},
annotation:{annotations:{cliff:{type:'line',xMin:'35',xMax:'35',borderColor:C.dim+'80',borderWidth:1.5,borderDash:[4,4],label:{display:true,content:'Sharp decline begins',position:'start',color:C.dim,font:{size:10}}}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:11}},title:{display:true,text:"Woman's age",color:C.dim}},y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},min:0,max:40,title:{display:true,text:'Probability (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'cradleChart4', 'figure_num': 4,
            'title': 'Share of Global Births: European-Heritage & East Asian Populations',
            'desc': 'From 37% of all births in 1960 to a projected 7% by 2100. European-heritage figures adjusted for ethnic composition (excluding immigrant-origin births within Europe, including diaspora births in US, Canada, Australia, Russia, Latin America).',
            'source': 'UN WPP 2024; CDC NCHS; Eurostat; ONS; Statistics Canada; ABS; Russia 2021 Census. Heritage-adjusted, not geographic.',
            'position': 'after_heading:The Innovation Collapse',
            'tall': False,
            'js': """
(()=>{const ctx=document.getElementById('cradleChart4');
const yrsH=[1950,1960,1970,1980,1990,2000,2010,2020,2025];
const sharesH=[40,37,35,28.8,27.7,21.6,19.8,16.3,14.4];
const yrsP=[2025,2030,2040,2050,2060,2070,2080,2090,2100];
const sharesP=[14.4,12.9,11.4,10.4,9.5,8.7,8.2,7.6,7.1];
new Chart(ctx,{type:'line',data:{
datasets:[
dxy('Historic share (%)',yrsH,sharesH,C.accent),
dxy('Projected share (%)',yrsP,sharesP,C.accent,[6,4])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+'% of global births'}},
annotation:{annotations:{
today:{type:'line',yMin:14.4,yMax:14.4,borderColor:C.dim+'60',borderWidth:1,borderDash:[4,4],label:{display:true,content:'Today ≈ 14%',position:'start',color:C.dim,font:{size:10}}},
eurOnly:{type:'label',xValue:2080,yValue:4,content:['European heritage alone: ~2.2%'],color:C.blue,font:{size:9,style:'italic'}}
}}},
scales:{x:linX(1950,2100,{title:{display:true,text:'Year',color:C.dim}}),y:{grid:{color:C.grid},ticks:{color:C.dim,callback:v=>v+'%'},min:0,max:45,title:{display:true,text:'Share of global births (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'cradleChart5', 'figure_num': 5,
            'title': 'Old-Age Dependency Ratios: 2020 vs 2050',
            'desc': 'Retirees per 100 working-age adults — the fiscal time bomb',
            'source': 'UN Population Division, World Population Prospects 2024; World Bank',
            'position': 'after_heading:Cultural Memory Requires People',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('cradleChart5');
const countries=['Japan','S. Korea','Italy','Germany','China','UK','France','US'];
const dep2020=[48,23,37,34,17,30,33,26];
const dep2050=[70,69,62,55,47,40,43,36];
new Chart(ctx,{type:'bar',data:{labels:countries,
datasets:[
{label:'2020',data:dep2020,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'2050 (projected)',data:dep2050,backgroundColor:C.accent,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+' retirees per 100 workers'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10}}},y:{grid:{color:C.grid},ticks:{color:C.dim},title:{display:true,text:'Retirees per 100 working-age adults',color:C.dim},max:80}}}});
})();"""
        },
        {
            'id': 'cradleChart6', 'figure_num': 6,
            'title': 'Pro-Natalist Policy Interventions and Fertility Outcomes',
            'desc': 'Fertility rates before and after major policy packages — ambitious policy moves the needle',
            'source': 'Eurostat, national statistics offices (Hungary KSH, INSEE, SCB, CBS Israel). Before = pre-policy baseline; After = latest available.',
            'position': 'after_heading:Fertility Education and Employer Mandates',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('cradleChart6');
const countries=['Hungary\\n(2010-2024)','France\\n(1995-2024)','Sweden\\n(2005-2024)','Israel\\n(2000-2024)'];
const before=[1.23,1.73,1.85,2.95];
const after=[1.53,1.68,1.45,2.90];
new Chart(ctx,{type:'bar',data:{labels:countries,
datasets:[
{label:'Before / baseline',data:before,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'After / latest',data:after,backgroundColor:C.accent,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw.toFixed(2)+' TFR'}},
annotation:{annotations:{repl:{type:'line',yMin:2.1,yMax:2.1,borderColor:C.green,borderWidth:2,borderDash:[6,3],label:{display:true,content:'Replacement (2.1)',position:'end',color:C.green,font:{size:10}}}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},y:{grid:{color:C.grid},ticks:{color:C.dim},min:0,max:3.5,title:{display:true,text:'Total Fertility Rate (TFR)',color:C.dim}}}}});
})();"""
        },
    ]

    # ── The New Literacy ───────────────────────────────────────────
    charts['the-new-literacy'] = [
        {
            'id': 'newLitChart1', 'figure_num': 1,
            'title': 'Global Literacy Rates Over Five Thousand Years',
            'desc': 'For most of human history, fewer than five per cent of people could read or write. The alphabet, printing press, and compulsory education each triggered step-changes — AI may be triggering the next.',
            'source': 'Our World in Data (2023); Harris, Ancient Literacy (1989); Havelock (1982); UNESCO',
            'position': 'after_para_6',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('newLitChart1');
const yrs=['-3000','-2500','-2000','-1500','-1000','-800','-500','-300','0','500','800','1000','1200','1400','1500','1600','1700','1800','1850','1900','1950','1980','2000','2020'];
const rates=[0.1,0.2,0.4,0.5,0.8,1.5,3,5,5,3,4,5,6,8,9,12,18,38,45,56,80,88,93,97];
new Chart(ctx,{type:'line',data:{datasets:[
dxy('World literacy rate (%)',yrs,rates,C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},
plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{
title:i=>{const v=+i[0].parsed.x;return v<0?Math.abs(v)+' BCE':v+' CE'},
label:i=>i.parsed.y+'% literate'
}},
annotation:{annotations:{
alph:{type:'label',xValue:-800,yValue:12,content:['Phoenician','alphabet'],color:C.blue,font:{size:10,weight:'bold'}},
press:{type:'line',xMin:1440,xMax:1440,yMin:0,yMax:100,borderColor:C.green,borderWidth:1.5,borderDash:[5,3],label:{display:true,content:'Printing press (1440)',position:'start',color:C.green,font:{size:10}}},
edu:{type:'line',xMin:1870,xMax:1870,yMin:0,yMax:100,borderColor:C.purple,borderWidth:1.5,borderDash:[5,3],label:{display:true,content:'Compulsory education (1870s)',position:'start',color:C.purple,font:{size:10}}},
ai:{type:'line',xMin:2024,xMax:2024,yMin:0,yMax:100,borderColor:C.amber,borderWidth:1.5,borderDash:[5,3],label:{display:true,content:'AI coding literacy? (2024)',position:'start',color:C.amber,font:{size:10}}}
}}},
scales:{x:{type:'linear',min:-3200,max:2030,grid:{color:C.grid},ticks:{color:C.dim,font:{size:10},callback:v=>v<0?Math.abs(v)+' BCE':v===0?'0':v+' CE',stepSize:500}},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},min:0,max:100,title:{display:true,text:'Population literate (%)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'newLitChart2', 'figure_num': 2,
            'title': 'The Cost of Creating: Specialists vs AI Tools',
            'desc': 'AI has reduced the cost of digital creation by 80-95 per cent in under two years — a compression comparable to the printing press\'s impact on book production.',
            'source': 'Upwork (2024); Fiverr market data; industry estimates; author analysis',
            'position': 'after_heading:The Printing Press Moment',
            'js': """
(()=>{const ctx=document.getElementById('newLitChart2');
const cats=['Custom app','Video advert','Brand identity','Marketing strategy','Book illustration'];
const specialist=[45000,25000,8000,15000,5000];
const aiTool=[2000,500,200,100,300];
new Chart(ctx,{type:'bar',data:{labels:cats,datasets:[
{label:'With specialists (2023)',data:specialist,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'With AI tools (2026)',data:aiTool,backgroundColor:C.accent,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},indexAxis:'y',
plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{const v=i.raw;return i.dataset.label+': $'+v.toLocaleString()}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>'$'+v.toLocaleString()},title:{display:true,text:'Estimated cost (USD)',color:C.dim}},
y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'newLitChart3', 'figure_num': 3,
            'title': 'Who Can Code? The New Literacy Curve',
            'desc': 'Traditional developers number roughly 30 million. AI-assisted creators — people producing functional software with AI tools — are growing exponentially and may outnumber developers 10:1 by 2030.',
            'source': 'Evans Data Corporation (2024); GitHub; Stack Overflow Developer Survey; Gartner low-code forecasts',
            'position': 'after_para_24',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('newLitChart3');
const yrs=['2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030'];
const devs=[21,22,23,24,25,26,27,27,28,28,29,30,30,31,31,32];
const aiCreators=[0,0,0,0,0,0,0.5,2,8,20,45,80,120,180,250,320];
new Chart(ctx,{type:'line',data:{datasets:[
dxy('Traditional developers (M)',yrs,devs,C.blue),
dxy('AI-assisted creators (M)',yrs,aiCreators,C.accent),
dxy('AI-assisted (projected)',['2025','2026','2027','2028','2029','2030'],[45,80,120,180,250,320],C.accent,[5,4])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},
plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'M people'}}},
scales:{x:{type:'linear',min:2015,max:2030,grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:yearTick,stepSize:2}},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'M'},min:0,title:{display:true,text:'People who can produce functional software (millions)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'newLitChart4', 'figure_num': 4,
            'title': 'The Dependency Curve: Skill Atrophy After Tool Adoption',
            'desc': 'Every democratised tool follows the same arc: flourishing, then dependency, then atrophy. Each successive technology compresses the cycle faster.',
            'source': 'Author synthesis; Carr, The Shallows (2010); National Numeracy (2019); Dahmani & Bohbot (2020)',
            'position': 'after_heading:The Dependency Question',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('newLitChart4');
const gen=['0','1','2','3','4'];
const writing=[30,90,85,70,60];
const arithmetic=[50,80,60,35,30];
const navigation=[60,85,50,30,25];
const aiSkills=[20,95,null,null,null];
const aiProj=[null,95,70,40,null];
new Chart(ctx,{type:'line',data:{labels:gen,datasets:[
{label:'Writing (post-printing press)',data:writing,borderColor:C.blue,backgroundColor:C.blue+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:C.blue,borderWidth:2.5},
{label:'Mental arithmetic (post-calculator)',data:arithmetic,borderColor:C.green,backgroundColor:C.green+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:C.green,borderWidth:2.5},
{label:'Navigation (post-GPS)',data:navigation,borderColor:C.purple,backgroundColor:C.purple+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:C.purple,borderWidth:2.5},
{label:'AI-enabled skills (actual)',data:aiSkills,borderColor:C.accent,backgroundColor:C.accent+'18',fill:false,tension:.35,pointRadius:5,pointBackgroundColor:C.accent,borderWidth:3},
{label:'AI-enabled skills (projected)',data:aiProj,borderColor:C.accent,backgroundColor:C.accent+'18',fill:false,tension:.35,pointRadius:3,pointBackgroundColor:C.accent,borderWidth:2.5,borderDash:[5,4]}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},
plugins:{legend:{display:true,position:'bottom',labels:{padding:12,usePointStyle:true,pointStyle:'circle',font:{size:11}}},tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'/100'}},
annotation:{annotations:{
peak:{type:'label',xValue:1,yValue:100,content:['Flourishing','peak'],color:C.accent,font:{size:10,weight:'bold'}},
dep:{type:'label',xValue:2.5,yValue:18,content:['Dependency','zone'],color:C.dim,font:{size:10,style:'italic'}}
}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>'Gen '+v},title:{display:true,text:'Generations after tool adoption',color:C.dim}},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11}},min:0,max:100,title:{display:true,text:'Skill level / creative output (index)',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'newLitChart5', 'figure_num': 5,
            'title': 'The Scribal Economy Under Threat',
            'desc': 'Over $3 trillion in global "scribal" services — specialist intermediaries between people and digital creation — face AI-driven disintermediation.',
            'source': 'Statista (2025); McKinsey Global Institute (2023); Goldman Sachs (2023)',
            'position': 'after_para_18',
            'js': """
(()=>{const ctx=document.getElementById('newLitChart5');
const sectors=['IT services &\\nsoftware dev','Creative &\\nadvertising','Legal\\nservices','Accounting &\\nfinance','Marketing &\\nPR'];
const sizes=[1240,620,380,340,280];
const automatable=[65,55,45,60,70];
new Chart(ctx,{type:'bar',data:{labels:sectors,datasets:[
{label:'Market size ($B)',data:sizes,backgroundColor:C.blue,borderRadius:3,borderSkipped:false,yAxisID:'y',order:1},
{label:'% automatable by AI',data:automatable,backgroundColor:C.accent+'88',borderColor:C.accent,borderWidth:2,borderRadius:3,borderSkipped:false,yAxisID:'y1',type:'line',tension:.3,pointRadius:5,pointBackgroundColor:C.accent,fill:false,order:0}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},
plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>{if(i.datasetIndex===0)return'Market size: $'+i.raw+'B';return'Automatable: '+i.raw+'%'}}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0}},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>'$'+v+'B'},title:{display:true,text:'Market size ($B)',color:C.dim},min:0,position:'left'},
y1:{grid:{display:false},ticks:{color:C.accent,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'% automatable by AI',color:C.accent},min:0,max:100,position:'right'}
}}});
})();"""
        },
    ]

    # ─── THE BUILDERS ARE DYING ───
    charts['the-builders-are-dying-how-the-populations-that-made-the-modern-world-are-disappearing'] = [
        {
            'id': 'buildersChart1', 'figure_num': 1,
            'title': 'The Builder Premium: % of Global Achievements vs. % of World Population',
            'desc': 'European-heritage and East Asian populations are ~21% of the world but account for 87–95% of major scientific prizes, 71% of manufacturing, and 93% of shipbuilding.',
            'source': 'Nobel Committee, IMU, ACM, World Bank, Clarksons Research, WIPO — cumulative through 2024',
            'position': 'after_para_21',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('buildersChart1');
const cats=['Nobel Prizes\\n(Sciences)','Fields\\nMedal','Turing\\nAward','Abel\\nPrize','Manufacturing\\nOutput','Ship-\\nbuilding','Patent\\nFilings','Top 100\\nUniversities'];
const eur=[87,84,88,100,32,5,18,62];
const eas=[7,6,4,0,39,93,52,15];
const rest=[6,10,8,0,29,2,30,23];
new Chart(ctx,{type:'bar',data:{labels:cats,datasets:[
{label:'European-heritage',data:eur,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'East Asian',data:eas,backgroundColor:C.accent,borderRadius:3,borderSkipped:false},
{label:'Rest of world',data:rest,backgroundColor:C.dim,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,
tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'%'}},
annotation:{annotations:{
popEur:{type:'line',yMin:12,yMax:12,borderColor:'#1a1a1a',borderWidth:2.5,borderDash:[8,5],z:10,label:{display:true,content:'European-heritage population: ~12%',position:'start',backgroundColor:'#1a1a1add',color:'#fff',font:{size:11,weight:'bold'},padding:4}},
popEA:{type:'line',yMin:21,yMax:21,borderColor:'#1a1a1a',borderWidth:2.5,borderDash:[8,5],z:10,label:{display:true,content:'European + East Asian population: ~21%',position:'end',backgroundColor:'#1a1a1add',color:'#fff',font:{size:11,weight:'bold'},padding:4}}
}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0},stacked:true},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'% of global total',color:C.dim},stacked:true,min:0,max:100}}}});
})();"""
        },
        {
            'id': 'buildersChart2', 'figure_num': 2,
            'title': 'Nobel Prizes in Sciences by Civilisational Origin (Cumulative through 2024)',
            'desc': 'Across physics, chemistry, medicine, and economics, European-heritage laureates dominate every discipline.',
            'source': 'Nobel Prize Committee — all individual laureates categorised by heritage',
            'position': 'after_para_18',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('buildersChart2');
const cats=['Physics\\n(~230)','Chemistry\\n(~195)','Medicine\\n(~230)','Economics\\n(~95)','All Sciences\\n(~750)'];
const eur=[88,83,86,91,87];
const eas=[6,8,4,2,5];
const rest=[6,9,10,7,8];
new Chart(ctx,{type:'bar',data:{labels:cats,datasets:[
{label:'European-heritage',data:eur,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'East Asian',data:eas,backgroundColor:C.accent,borderRadius:3,borderSkipped:false},
{label:'Rest of world',data:rest,backgroundColor:C.dim,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'%'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:11},maxRotation:0},stacked:true},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'% of laureates',color:C.dim},stacked:true,min:0,max:100}}}});
})();"""
        },
        {
            'id': 'buildersChart3', 'figure_num': 3,
            'title': 'Who Builds the World? Global Manufacturing, Shipbuilding, and Semiconductors',
            'desc': 'East Asia dominates manufacturing volume and shipbuilding; European-heritage nations lead in pharmaceuticals and aerospace. Together they account for the vast majority.',
            'source': 'World Bank, Clarksons Research, TrendForce, SIPRI — 2024 data',
            'position': 'after_para_20',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('buildersChart3');
const cats=['Manufacturing\\nvalue added','Shipbuilding\\n(new tonnage)','Semiconductor\\nfabrication','Pharmaceutical\\nR&D spend','Aerospace &\\ndefence output','Automotive\\nproduction'];
const eur=[32,5,12,55,65,22];
const eas=[39,93,82,22,18,55];
const rest=[29,2,6,23,17,23];
new Chart(ctx,{type:'bar',data:{labels:cats,datasets:[
{label:'European-heritage',data:eur,backgroundColor:C.blue,borderRadius:3,borderSkipped:false},
{label:'East Asian',data:eas,backgroundColor:C.accent,borderRadius:3,borderSkipped:false},
{label:'Rest of world',data:rest,backgroundColor:C.dim,borderRadius:3,borderSkipped:false}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.raw+'%'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:10},maxRotation:0},stacked:true},
y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'% of global total',color:C.dim},stacked:true,min:0,max:100}}}});
})();"""
        },
        {
            'id': 'buildersChart4', 'figure_num': 4,
            'title': 'Total Fertility Rates: The Builder Nations vs. Replacement Level',
            'desc': 'Every European and East Asian nation is below the 2.1 replacement rate. Most are far below it.',
            'source': 'Eurostat, Statistics Korea, China NBS, Japan MHLW, World Bank — 2024',
            'position': 'after_heading_The Arithmetic of Extinction',
            'tall': True,
            'js': """
(()=>{const ctx=document.getElementById('buildersChart4');
const labels=['South Korea','Hong Kong','Taiwan','Singapore','China','Japan','Spain','Italy','Poland','Greece','Germany','UK','France','Replacement'];
const vals=[0.72,0.77,0.87,0.97,1.02,1.20,1.19,1.24,1.29,1.30,1.35,1.49,1.68,2.1];
const colors=vals.map((v,i)=>i===labels.length-1?C.green:v<1.0?C.accent:v<1.5?C.amber:C.blue);
new Chart(ctx,{type:'bar',data:{labels,datasets:[{label:'TFR',data:vals,backgroundColor:colors,borderRadius:4,borderSkipped:false}]},
options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,
tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw+' children per woman'}},
annotation:{annotations:{replacement:{type:'line',xMin:2.1,xMax:2.1,borderColor:C.green,borderWidth:2,borderDash:[6,4],label:{display:true,content:'Replacement: 2.1',position:'end',backgroundColor:C.green,color:'#fff',font:{size:11}}}}}},
scales:{x:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11}},min:0,max:2.5,title:{display:true,text:'Children per woman',color:C.dim}},y:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}}}}});
})();"""
        },
        {
            'id': 'buildersChart4b', 'figure_num': 5,
            'title': 'Builder Share of Global Births Is Collapsing, 1960–2100',
            'desc': 'European-heritage peoples (adjusted for ethnic composition within Europe and including diaspora in the Americas, Australasia, and Russia) and East Asians accounted for over one in three births in 1960. By 2100, they will account for roughly one in fifteen.',
            'source': 'UN WPP 2024; CDC NCHS (US births by race/ethnicity); Eurostat; ONS (UK births by parents\' country of birth); Statistics Canada; ABS; Russia 2021 Census. European-heritage figures adjust geographic births for immigrant-origin share and add diaspora births (US non-Hispanic white, Canada, Australia, NZ, Latin America, Russia ethnic Russian).',
            'position': 'after_para_10',
            'js': """
(()=>{const ctx=document.getElementById('buildersChart4b');
const yrs=[1960,1970,1980,1990,2000,2010,2020,2025,2030,2040,2050,2060,2070,2080,2090,2100];
const eurPct=[13.3,11.8,10.7,9.1,7.7,6.9,5.9,5.5,5.0,4.4,3.8,3.3,2.9,2.6,2.4,2.2];
const eaPct=[23.7,23.2,18.1,18.6,13.9,12.9,10.4,8.9,7.9,7.0,6.6,6.2,5.8,5.6,5.2,4.9];
const ssaPct=[7.8,9.6,13.0,15.7,20.7,23.6,28.2,31.1,33.5,37.5,41.0,43.5,44.2,44.4,43.8,43.1];
const builderPct=eurPct.map((v,i)=>v+eaPct[i]);
new Chart(ctx,{type:'line',data:{datasets:[
{...dxy('European heritage (adj.)',yrs,eurPct,C.blue),fill:true,backgroundColor:C.blue+'30'},
{...dxy('East Asia (China/Japan/Korea)',yrs,eaPct,C.accent),fill:true,backgroundColor:C.accent+'30'},
{...dxy('Builder total',yrs,builderPct,C.purple,[6,4]),borderWidth:3},
{...dxy('Sub-Saharan Africa',yrs,ssaPct,C.green),borderWidth:3}
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y.toFixed(1)+'% of global births'}},
annotation:{annotations:{
proj:{type:'line',xMin:2025,xMax:2025,borderColor:C.dim,borderWidth:1,borderDash:[4,4],label:{display:true,content:'← Actual | Projected →',position:'start',backgroundColor:C.dim+'cc',color:'#fff',font:{size:10}}},
peak:{type:'label',xValue:1975,yValue:42,content:['37% — more than','1 in 3 births'],color:C.purple,font:{size:11,weight:'bold'}},
nadir:{type:'label',xValue:2075,yValue:11,content:['~7% — 1 in 15'],color:C.purple,font:{size:11,weight:'bold'}},
africaLabel:{type:'label',xValue:2070,yValue:47,content:['Nearly half','of all births'],color:C.green,font:{size:10,style:'italic'}},
eurNote:{type:'label',xValue:2060,yValue:1,content:['European heritage: 2.2%'],color:C.blue,font:{size:9,style:'italic'}}
}}},
scales:{x:linX(1960,2100),y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'Share of global births (%)',color:C.dim},min:0,max:50}}}});
})();"""
        },
        {
            'id': 'buildersChart5', 'figure_num': 6,  # was 5
            'title': 'European and East Asian Share of World Population, 1800–2100',
            'desc': 'The populations that built the modern world are shrinking from over 40% of humanity to under 15%. Note: uses geographic population (people living in Europe/East Asia), not ethnic heritage — the ethnic European-heritage share is lower still.',
            'source': 'UN Population Division 2024, Maddison Project Database 2020. Geographic regions, not ethnic composition.',
            'position': 'after_para_13',
            'js': """
(()=>{const ctx=document.getElementById('buildersChart5');
const yrs=[1800,1850,1900,1950,1970,2000,2025,2050,2075,2100];
const europe=[20.5,21.8,24.7,21.6,17.8,12.0,9.2,7.4,6.1,5.1];
const eastAsia=[28.4,28.0,24.0,24.5,23.9,22.8,20.0,16.2,13.0,10.5];
const combined=europe.map((v,i)=>v+eastAsia[i]);
new Chart(ctx,{type:'line',data:{datasets:[
dxy('Europe (geographic)',yrs,europe,C.blue),
dxy('East Asia (China/Japan/Korea)',yrs,eastAsia,C.accent),
dxy('Combined',yrs,combined,C.purple,[6,4])
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'%'}},
annotation:{annotations:{proj:{type:'line',xMin:2025,xMax:2025,borderColor:C.dim,borderWidth:1,borderDash:[4,4],label:{display:true,content:'← Actual | Projected →',position:'start',backgroundColor:C.dim+'cc',color:'#fff',font:{size:10}}}}}},
scales:{x:linX(1800,2100),y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v+'%'},title:{display:true,text:'% of world population',color:C.dim},min:0,max:55}}}});
})();"""
        },
        {
            'id': 'buildersChart6', 'figure_num': 7,  # was 6
            'title': 'Population Trajectories 2025–2100 (Indexed: 2025 = 100)',
            'desc': 'The scissors: builder populations shrink while sub-Saharan Africa triples.',
            'source': 'UN Population Division, World Population Prospects 2024 (median variant)',
            'position': 'after_para_12',
            'js': """
(()=>{const ctx=document.getElementById('buildersChart6');
const yrs=[2025,2035,2050,2065,2080,2100];
const europe=[100,97,90,82,75,68];
const china=[100,96,84,70,60,52];
const japan=[100,94,83,72,63,56];
const skorea=[100,95,80,64,52,42];
const ssafrica=[100,128,172,222,270,315];
new Chart(ctx,{type:'line',data:{datasets:[
dxy('Europe',yrs,europe,C.blue),
dxy('China',yrs,china,C.accent),
dxy('Japan',yrs,japan,C.purple),
dxy('South Korea',yrs,skorea,C.amber),
dxy('Sub-Saharan Africa',yrs,ssafrica,C.green)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+' (index)'}},
annotation:{annotations:{baseline:{type:'line',yMin:100,yMax:100,borderColor:C.dim,borderWidth:1,borderDash:[4,4]}}}},
scales:{x:linX(2025,2100),y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11}},title:{display:true,text:'Population index (2025 = 100)',color:C.dim},min:0,max:340}}}});
})();"""
        },
        {
            'id': 'buildersChart7', 'figure_num': 8,  # was 7
            'title': 'South Africa: Eskom Load-Shedding Hours per Year, 2007–2024',
            'desc': 'From zero load-shedding to over 6,500 hours — the collapse of a First World power grid.',
            'source': 'CSIR South Africa, Eskom Annual Reports',
            'position': 'after_para_29',
            'js': """
(()=>{const ctx=document.getElementById('buildersChart7');
const yrs=['2007','2008','2014','2015','2018','2019','2020','2021','2022','2023','2024'];
const hrs=[0,600,100,850,150,530,860,1100,2500,6600,2900];
new Chart(ctx,{type:'bar',data:{labels:yrs,datasets:[{label:'Load-shedding hours',data:hrs,
backgroundColor:hrs.map(v=>v>2000?C.accent:v>500?C.amber:C.blue),borderRadius:4,borderSkipped:false}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>i.raw.toLocaleString()+' hours'}}},
scales:{x:{grid:{display:false},ticks:{color:C.dim,font:{size:11}}},y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>v.toLocaleString()+'h'},title:{display:true,text:'Total load-shedding hours',color:C.dim}}}}});
})();"""
        },
        {
            'id': 'buildersChart8', 'figure_num': 9,  # was 8
            'title': 'South Africa: GDP Per Capita (Constant 2015 USD), 1994–2024',
            'desc': 'Thirty years after transition, GDP per capita has declined since 2011.',
            'source': 'World Bank, World Development Indicators',
            'position': 'after_para_30',
            'js': """
(()=>{const ctx=document.getElementById('buildersChart8');
const yrs=[1994,1996,1998,2000,2002,2004,2006,2008,2010,2011,2012,2014,2016,2018,2020,2022,2024];
const gdp=[5400,5500,5500,5600,5700,5900,6300,6600,6800,7000,6950,6850,6700,6650,5900,6200,6100];
new Chart(ctx,{type:'line',data:{datasets:[
dxy('GDP per capita (const. 2015 USD)',yrs,gdp,C.accent)
]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},plugins:{legend:noLegend,tooltip:{...tooltipStyle,callbacks:{label:i=>'$'+i.parsed.y.toLocaleString()}},
annotation:{annotations:{peak:{type:'point',xValue:2011,yValue:7000,backgroundColor:C.accent,radius:6,borderColor:'#fff',borderWidth:2},
peakLabel:{type:'label',xValue:2011,yValue:7350,content:'Peak: $7,000 (2011)',color:C.accent,font:{size:11,weight:'bold'}}}}},
scales:{x:linX(1994,2024),y:{grid:{color:C.grid},ticks:{color:C.dim,font:{size:11},callback:v=>'$'+v.toLocaleString()},title:{display:true,text:'GDP per capita (constant 2015 USD)',color:C.dim},min:5000,max:7500}}}});
})();"""
        },
    ]

    # Flatten any accidentally nested lists
    for k in charts:
        if charts[k] and isinstance(charts[k][0], list):
            charts[k] = charts[k][0]
    return charts


if __name__ == '__main__':
    all_charts = get_all_charts()
    total = sum(len(v) for v in all_charts.values())
    print(f"Total: {total} charts across {len(all_charts)} articles")
    for slug, ch in all_charts.items():
        print(f"  {slug[:60]:60s} → {len(ch)} charts")
