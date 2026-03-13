/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║           GHOST PROXY — Cloudflare Worker                   ║
 * ║  真正的服务端代理：所有请求从CF服务器发出，URL Base64混淆     ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 部署方法：
 *   1. Cloudflare Dashboard → Workers & Pages → Create Worker
 *   2. 粘贴全部内容 → Deploy
 *   3. 访问 https://your-worker.your-name.workers.dev
 *
 * 工作原理（对比上一版的根本区别）：
 *   ❌ 旧版：iframe src = /proxy?url=xxx  → 页面里的子资源直接从浏览器发出 → 被拦截
 *   ✅ 新版：
 *      1. Worker 服务端 fetch 目标页面
 *      2. 重写 HTML 中所有 href/src → /x/<base64编码的URL>
 *      3. 注入 JS 拦截 fetch/XHR，动态请求也走代理
 *      4. 浏览器只看到 workers.dev 域名，防火墙无从拦截
 */

const PROXY_PATH = '/x/';
const SW_PATH    = '/sw.js';

// ─── URL 编解码（自定义Base64避免过滤器识别） ───────────────────────
function encodeUrl(url) {
  return btoa(unescape(encodeURIComponent(url)))
    .replace(/\+/g, '@')
    .replace(/\//g, '-')
    .replace(/=/g, '');
}

function decodeUrl(s) {
  try {
    const b64 = s.replace(/@/g, '+').replace(/-/g, '/');
    const padded = b64 + '='.repeat((4 - b64.length % 4) % 4);
    return decodeURIComponent(escape(atob(padded)));
  } catch { return null; }
}

// ─── 主入口 ──────────────────────────────────────────────────────
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const workerOrigin = url.origin;

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: cors() });
    }

    if (url.pathname === '/ping') {
      return new Response('pong', { headers: cors() });
    }

    // Service Worker 脚本
    if (url.pathname === SW_PATH) {
      return new Response(buildSW(workerOrigin), {
        headers: {
          'Content-Type': 'application/javascript',
          'Service-Worker-Allowed': '/',
          ...cors()
        }
      });
    }

    // 前端 UI
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(buildHTML(workerOrigin), {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      });
    }

    // 代理请求 /x/<encoded>
    if (url.pathname.startsWith(PROXY_PATH)) {
      const encoded = url.pathname.slice(PROXY_PATH.length);
      const decoded = decodeUrl(encoded);
      if (!decoded) return new Response('Bad encoded URL', { status: 400 });

      // 拼回查询字符串
      const targetUrl = decoded + (url.search || '');
      return handleProxy(request, targetUrl, workerOrigin);
    }

    return new Response('Not found', { status: 404 });
  }
};

// ─── 代理处理 ─────────────────────────────────────────────────────
async function handleProxy(request, targetUrl, workerOrigin) {
  let parsed;
  try { parsed = new URL(targetUrl); }
  catch { return new Response('Invalid URL', { status: 400 }); }

  const targetOrigin = parsed.origin;
  const targetBase   = targetUrl.slice(0, targetUrl.lastIndexOf('/') + 1);

  // 构造转发头
  const upHeaders = new Headers();
  const drop = new Set(['host','cf-connecting-ip','cf-ipcountry','cf-ray','cf-visitor',
                        'x-forwarded-for','x-forwarded-proto','x-real-ip']);
  for (const [k, v] of request.headers) {
    if (!drop.has(k.toLowerCase())) upHeaders.set(k, v);
  }
  upHeaders.set('Host', parsed.host);
  upHeaders.set('Referer', targetOrigin + '/');
  upHeaders.set('Origin', targetOrigin);

  // 服务端发出请求（浏览器完全不接触目标服务器）
  let res;
  try {
    res = await fetch(targetUrl, {
      method: request.method,
      headers: upHeaders,
      body: ['GET','HEAD'].includes(request.method) ? null : request.body,
      redirect: 'follow',
    });
  } catch (e) {
    return new Response(`代理请求失败: ${e.message}`, { status: 502, headers: cors() });
  }

  const ct = res.headers.get('content-type') || '';

  if (ct.includes('text/html')) {
    const html = await res.text();
    const rewritten = rewriteHTML(html, targetOrigin, targetBase, workerOrigin);
    const h = new Headers(cors());
    h.set('Content-Type', 'text/html; charset=utf-8');
    stripSecurity(h);
    return new Response(rewritten, { status: res.status, headers: h });
  }

  if (ct.includes('text/css')) {
    const css = await res.text();
    const rewritten = rewriteCSS(css, targetOrigin, targetBase, workerOrigin);
    const h = new Headers(cors());
    h.set('Content-Type', ct);
    return new Response(rewritten, { status: res.status, headers: h });
  }

  if (ct.includes('javascript')) {
    const js = await res.text();
    const rewritten = rewriteJS(js, targetOrigin, workerOrigin);
    const h = new Headers(cors());
    h.set('Content-Type', ct);
    return new Response(rewritten, { status: res.status, headers: h });
  }

  // 其他资源（图片/字体/视频）直接透传
  const h = new Headers(cors());
  for (const [k, v] of res.headers) {
    if (!['x-frame-options','content-security-policy','strict-transport-security',
          'cross-origin-opener-policy','cross-origin-embedder-policy',
          'cross-origin-resource-policy'].includes(k.toLowerCase())) {
      h.set(k, v);
    }
  }
  return new Response(res.body, { status: res.status, headers: h });
}

// ─── 重写工具 ─────────────────────────────────────────────────────
function toProxyUrl(href, targetOrigin, targetBase, workerOrigin) {
  if (!href) return href;
  const s = href.trim();
  if (s.startsWith('data:') || s.startsWith('blob:') || s.startsWith('javascript:') ||
      s.startsWith('#') || s.startsWith(workerOrigin) || s.startsWith(PROXY_PATH)) return s;

  let abs;
  if (/^https?:\/\//i.test(s))    abs = s;
  else if (s.startsWith('//'))    abs = 'https:' + s;
  else if (s.startsWith('/'))     abs = targetOrigin + s;
  else                            abs = targetBase + s;

  return workerOrigin + PROXY_PATH + encodeUrl(abs);
}

function rewriteHTML(html, targetOrigin, targetBase, workerOrigin) {
  // 重写 href/src/action/poster/data-src
  html = html.replace(/((?:href|src|action|poster|data-src)\s*=\s*)(["'])([^"']*)\2/gi,
    (m, attr, q, val) => {
      if (!val || val.startsWith('data:') || val.startsWith('blob:') || val.startsWith('#')) return m;
      return attr + q + toProxyUrl(val, targetOrigin, targetBase, workerOrigin) + q;
    });

  // 重写 srcset
  html = html.replace(/srcset\s*=\s*(["'])([^"']+)\1/gi, (m, q, set) => {
    const parts = set.split(',').map(p => {
      const [u, ...rest] = p.trim().split(/\s+/);
      return toProxyUrl(u, targetOrigin, targetBase, workerOrigin) + (rest.length ? ' ' + rest.join(' ') : '');
    });
    return 'srcset=' + q + parts.join(', ') + q;
  });

  // 重写内联 style url()
  html = html.replace(/url\((["']?)([^)"'\s]+)\1\)/gi,
    (m, q, u) => 'url(' + q + toProxyUrl(u, targetOrigin, targetBase, workerOrigin) + q + ')');

  // 注入拦截脚本（放在 <head> 最前）
  const injection = buildInjection(targetOrigin, targetBase, workerOrigin);
  if (/<head[\s>]/i.test(html)) {
    html = html.replace(/(<head[\s>][^>]*>)/i, '$1' + injection);
  } else {
    html = injection + html;
  }

  return html;
}

function rewriteCSS(css, targetOrigin, targetBase, workerOrigin) {
  return css.replace(/url\((["']?)([^)"'\s]+)\1\)/gi,
    (m, q, u) => 'url(' + q + toProxyUrl(u, targetOrigin, targetBase, workerOrigin) + q + ')');
}

function rewriteJS(js, targetOrigin, workerOrigin) {
  // 只替换字符串字面量中的跨域绝对URL
  return js.replace(/(["'])(https?:\/\/[^"']{5,})\1/g, (m, q, url) => {
    if (url.startsWith(targetOrigin) || url.startsWith(workerOrigin)) return m;
    return q + workerOrigin + PROXY_PATH + encodeUrl(url) + q;
  });
}

// ─── 注入到被代理页面的脚本 ────────────────────────────────────────
function buildInjection(targetOrigin, targetBase, workerOrigin) {
  return `<script>
(function(){
var P={
  wo:${JSON.stringify(workerOrigin)},
  to:${JSON.stringify(targetOrigin)},
  tb:${JSON.stringify(targetBase)},
  pp:${JSON.stringify(PROXY_PATH)},
  enc:function(u){try{return btoa(unescape(encodeURIComponent(u))).replace(/\\+/g,'@').replace(/\\//g,'-').replace(/=/g,'')}catch(e){return null}},
  wrap:function(u){
    if(!u||/^(data:|blob:|javascript:|#)/.test(u)||u.startsWith(this.wo))return u;
    var a;
    if(/^https?:\\/\\//.test(u))a=u;
    else if(u.startsWith('//'))a='https:'+u;
    else if(u.startsWith('/'))a=this.to+u;
    else a=this.tb+u;
    var e=this.enc(a);return e?this.wo+this.pp+e:u;
  }
};
// 拦截 fetch
var oF=window.fetch;
window.fetch=function(inp,init){
  if(typeof inp==='string'&&/^https?:/.test(inp)&&!inp.startsWith(P.wo))
    inp=P.wrap(inp);
  return oF.call(this,inp,init);
};
// 拦截 XHR
var oO=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(m,u){
  if(typeof u==='string'&&/^https?:/.test(u)&&!u.startsWith(P.wo))u=P.wrap(u);
  return oO.apply(this,[m,u].concat([].slice.call(arguments,2)));
};
// 拦截链接，通知父窗口更新地址栏
document.addEventListener('click',function(e){
  var a=e.target.closest('a[href]');
  if(!a)return;
  var h=a.getAttribute('href');
  if(!h||/^(#|javascript:)/.test(h))return;
  if(h.indexOf(P.pp)!==-1){
    try{
      var enc=h.split(P.pp).pop().split('?')[0];
      var b=enc.replace(/@/g,'+').replace(/-/g,'/');
      var real=decodeURIComponent(escape(atob(b+'='.repeat((4-b.length%4)%4))));
      window.parent.postMessage({type:'ghost-nav',url:real},'*');
    }catch(ex){}
  }
},true);
})();
<\/script>`;
}

// ─── Service Worker ───────────────────────────────────────────────
function buildSW(workerOrigin) {
  return `
var WO=${JSON.stringify(workerOrigin)};
var PP=${JSON.stringify(PROXY_PATH)};
function enc(u){try{return btoa(unescape(encodeURIComponent(u))).replace(/\\+/g,'@').replace(/\\//g,'-').replace(/=/g,'')}catch(e){return null}}
self.addEventListener('install',function(){self.skipWaiting()});
self.addEventListener('activate',function(e){e.waitUntil(self.clients.claim())});
self.addEventListener('fetch',function(e){
  var u=e.request.url;
  if(u.startsWith(WO)||!u.startsWith('http'))return;
  var encoded=enc(u);
  if(!encoded)return;
  e.respondWith(
    fetch(WO+PP+encoded,{method:e.request.method,headers:e.request.headers,
      body:['GET','HEAD'].includes(e.request.method)?null:e.request.body,mode:'cors'})
    .catch(function(){return fetch(e.request)})
  );
});
`;
}

// ─── Helper ───────────────────────────────────────────────────────
function cors() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': '*',
    'Access-Control-Allow-Headers': '*',
  };
}

function stripSecurity(headers) {
  ['x-frame-options','content-security-policy','cross-origin-opener-policy',
   'cross-origin-embedder-policy','cross-origin-resource-policy',
   'strict-transport-security'].forEach(h => headers.delete(h));
}

// ─── 前端 HTML ────────────────────────────────────────────────────
function buildHTML(workerOrigin) {
return `<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ghost Proxy</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Unbounded:wght@300;700;900&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#050507;--s1:#0e0e14;--s2:#161620;
  --b1:#1c1c2a;--b2:#28283c;
  --c1:#00d4ff;--c2:#0062ff;--c3:#7700ff;
  --tx:#dde0ee;--mu:#4a4a6a;
  --bar:54px;
}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--tx);font-family:'Space Mono',monospace}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.025) 2px,rgba(0,0,0,0.025) 4px)}

/* TOOLBAR */
#bar{position:fixed;top:0;left:0;right:0;height:var(--bar);z-index:1000;
  background:rgba(5,5,7,0.97);border-bottom:1px solid var(--b1);
  display:flex;align-items:center;gap:6px;padding:0 10px}
.logo{font-family:'Unbounded',sans-serif;font-weight:900;font-size:11px;letter-spacing:.2em;
  background:linear-gradient(90deg,var(--c1),var(--c2),var(--c3));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;flex-shrink:0;padding-right:6px}
.nb{width:28px;height:28px;border-radius:5px;flex-shrink:0;background:var(--s2);
  border:1px solid var(--b1);cursor:pointer;display:flex;align-items:center;justify-content:center;
  color:var(--mu);transition:all .12s}
.nb:hover{color:var(--c1);border-color:var(--c1);background:rgba(0,212,255,.07)}
.nb:disabled{opacity:.2;cursor:not-allowed;pointer-events:none}
.nb svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
#abar{flex:1;height:34px;display:flex;align-items:center;gap:6px;
  background:var(--s2);border:1px solid var(--b1);border-radius:6px;padding:0 8px;transition:all .15s}
#abar:focus-within{border-color:var(--c2);box-shadow:0 0 0 2px rgba(0,98,255,.18)}
.lk svg{width:10px;height:10px;stroke:var(--c1);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#url{flex:1;background:none;border:none;outline:none;color:var(--tx);
  font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.02em}
#url::placeholder{color:var(--mu)}
#go{background:linear-gradient(135deg,var(--c2),var(--c3));border:none;color:#fff;
  height:22px;padding:0 10px;border-radius:3px;cursor:pointer;
  font-family:'Unbounded',sans-serif;font-size:8px;font-weight:700;letter-spacing:.1em;
  transition:opacity .12s,transform .12s;flex-shrink:0}
#go:hover{opacity:.8;transform:translateY(-1px)}

/* PROGRESS */
#pw{position:fixed;top:var(--bar);left:0;right:0;height:2px;background:var(--b1);z-index:999}
#pr{height:100%;width:0%;background:linear-gradient(90deg,var(--c2),var(--c1));
  transition:width .25s ease;box-shadow:0 0 8px var(--c1)}

/* FRAME AREA */
#wrap{position:fixed;top:calc(var(--bar) + 2px);left:0;right:0;bottom:22px;overflow:hidden}
#frame{width:100%;height:100%;border:none;background:#fff;opacity:0;transition:opacity .25s}
#frame.on{opacity:1}

/* SPLASH */
#splash{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;transition:opacity .3s}
#splash.hide{opacity:0;pointer-events:none}
.sg{position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(var(--b1) 1px,transparent 1px),linear-gradient(90deg,var(--b1) 1px,transparent 1px);
  background-size:48px 48px;mask-image:radial-gradient(ellipse 65% 55% at 50% 50%,black 20%,transparent 100%);opacity:.35}
.go{position:absolute;border-radius:50%;filter:blur(90px);pointer-events:none}
.go1{width:500px;height:280px;background:var(--c2);opacity:.06;top:25%;left:15%}
.go2{width:280px;height:280px;background:var(--c1);opacity:.05;bottom:10%;right:20%}
.st{font-family:'Unbounded',sans-serif;font-weight:900;font-size:clamp(36px,8vw,88px);
  letter-spacing:-.03em;line-height:1;
  background:linear-gradient(135deg,var(--c1) 0%,var(--c2) 40%,var(--c3) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.ss{color:var(--mu);font-size:10px;letter-spacing:.22em;text-transform:uppercase}
.sh{color:var(--b2);font-size:9px;letter-spacing:.1em;text-align:center;line-height:1.8;max-width:380px}
.sh code{color:var(--c1);background:rgba(0,212,255,.08);padding:1px 5px;border-radius:2px}

/* LOADING */
#ld{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  opacity:0;pointer-events:none;transition:opacity .15s}
#ld.on{opacity:1}
.sp{width:26px;height:26px;border-radius:50%;border:1.5px solid var(--b2);
  border-top-color:var(--c1);animation:rot .7s linear infinite}
@keyframes rot{to{transform:rotate(360deg)}}

/* STATUS BAR */
#sb{position:fixed;bottom:0;left:0;right:0;height:22px;z-index:1000;
  background:rgba(5,5,7,.95);border-top:1px solid var(--b1);
  display:flex;align-items:center;padding:0 10px;gap:10px;font-size:9px;color:var(--mu);letter-spacing:.07em}
#sb span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.d{width:5px;height:5px;border-radius:50%;background:var(--mu);flex-shrink:0}
.d.ok{background:var(--c1);box-shadow:0 0 5px var(--c1)}
.d.er{background:#ff3a3a;box-shadow:0 0 5px #ff3a3a}
</style>
</head>
<body>

<div id="bar">
  <span class="logo">GHOST</span>
  <button class="nb" id="bb" disabled title="后退"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg></button>
  <button class="nb" id="bf" disabled title="前进"><svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg></button>
  <button class="nb" id="br" title="刷新"><svg viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg></button>
  <button class="nb" id="bh" title="主页"><svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></button>
  <div id="abar">
    <span class="lk"><svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
    <input id="url" type="text" placeholder="输入网址或搜索词…" autocomplete="off" spellcheck="false"/>
    <button id="go">GO</button>
  </div>
</div>

<div id="pw"><div id="pr"></div></div>

<div id="wrap">
  <div class="sg"></div><div class="go go1"></div><div class="go go2"></div>
  <div id="splash">
    <div class="st">GHOST</div>
    <div class="ss">Cloudflare Proxy</div>
    <div class="sh">
      所有流量经 Cloudflare 服务器转发<br>
      浏览器仅与 <code>workers.dev</code> 通信<br>
      URL 用 Base64 混淆 · 动态请求全部拦截
    </div>
  </div>
  <div id="ld"><div class="sp"></div></div>
  <iframe id="frame"
    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-modals allow-downloads"
  ></iframe>
</div>

<div id="sb">
  <div class="d" id="dot"></div>
  <span id="stxt">就绪 — 等待输入</span>
  <span style="color:var(--b2)">GHOST PROXY v2</span>
</div>

<script>
var WO = ${JSON.stringify(workerOrigin)};
var PP = '/x/';

function enc(u){try{return btoa(unescape(encodeURIComponent(u))).replace(/\\+/g,'@').replace(/\\//g,'-').replace(/=/g,'')}catch(e){return null}}
function dec(s){try{var b=s.replace(/@/g,'+').replace(/-/g,'/');return decodeURIComponent(escape(atob(b+'='.repeat((4-b.length%4)%4))))}catch(e){return null}}

var url  = document.getElementById('url');
var frame= document.getElementById('frame');
var spl  = document.getElementById('splash');
var ld   = document.getElementById('ld');
var pr   = document.getElementById('pr');
var stxt = document.getElementById('stxt');
var dot  = document.getElementById('dot');
var bb=document.getElementById('bb'),bf=document.getElementById('bf'),
    br=document.getElementById('br'),bh=document.getElementById('bh');

var hist=[],hidx=-1;

// Register Service Worker
if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(function(){});
}

function setP(p){pr.style.width=p+'%'}
function setS(msg,ok){
  stxt.textContent=msg;
  dot.className='d'+(ok===true?' ok':ok===false?' er':'');
}

function norm(raw){
  raw=raw.trim();if(!raw)return null;
  if(/^https?:\/\//i.test(raw))return raw;
  if(/^[\w-]+(\.[\w.]+)/.test(raw))return'https://'+raw;
  return'https://www.google.com/search?q='+encodeURIComponent(raw);
}

function go(target,push){
  target=norm(target);if(!target)return;
  spl.classList.add('hide');
  frame.classList.remove('on');
  ld.classList.add('on');
  setP(15);setS('连接中…');
  setTimeout(function(){setP(55)},200);
  setTimeout(function(){setP(82)},600);

  var e=enc(target);
  url.value=target;
  frame.src=PP+e;

  if(push!==false){
    hist=hist.slice(0,hidx+1);
    hist.push(target);hidx=hist.length-1;
  }
  upBtn();
}

function upBtn(){
  bb.disabled=hidx<=0;
  bf.disabled=hidx>=hist.length-1;
}

frame.addEventListener('load',function(){
  setP(100);frame.classList.add('on');ld.classList.remove('on');
  setS('已加载 — 流量经 Cloudflare 服务端转发',true);
  setTimeout(function(){setP(0)},500);
  // 尝试从编码URL反推真实URL更新地址栏
  try{
    var src=frame.src;
    var idx=src.indexOf(PP);
    if(idx!==-1){
      var part=src.slice(idx+PP.length).split('?')[0];
      var real=dec(part);
      if(real)url.value=real;
    }
  }catch(ex){}
});

frame.addEventListener('error',function(){
  ld.classList.remove('on');setS('加载失败',false);setP(0);
});

window.addEventListener('message',function(e){
  if(e.data&&e.data.type==='ghost-nav')go(e.data.url);
});

document.getElementById('go').addEventListener('click',function(){go(url.value)});
url.addEventListener('keydown',function(e){if(e.key==='Enter')go(url.value)});
url.addEventListener('focus',function(){url.select()});

bb.addEventListener('click',function(){if(hidx>0){hidx--;go(hist[hidx],false);upBtn()}});
bf.addEventListener('click',function(){if(hidx<hist.length-1){hidx++;go(hist[hidx],false);upBtn()}});
br.addEventListener('click',function(){if(hist[hidx])go(hist[hidx],false)});
bh.addEventListener('click',function(){
  frame.src='about:blank';frame.classList.remove('on');
  spl.classList.remove('hide');url.value='';
  hist=[];hidx=-1;upBtn();setP(0);setS('就绪');
});

document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&e.key==='l'){e.preventDefault();url.focus()}
});
</script>
</body>
</html>`;
}
