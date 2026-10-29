const {chromium}=require('playwright');
const [,, start, end, fps]=process.argv.map(Number);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1.5});
await p.goto('file:///home/claude/explainer/'+(process.env.VID||'video.html')+'');await p.waitForTimeout(1000);
for(let f=start;f<end;f++){const t=f/fps;await p.evaluate(t=>window.seek(t),t);
 await p.screenshot({path:`frames/f${String(f).padStart(5,'0')}.jpg`,type:'jpeg',quality:88});
 if(f%250===0)console.log('frame',f);}
await b.close();})();
