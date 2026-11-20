import os
import sys

from flask import Flask, jsonify, request, Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from consumer_service.database import SessionLocal, SubwayPosition

app = Flask(__name__)


def position_to_dict(position):
    return {
        "id": position.id,
        "trip_id": position.trip_id,
        "route_id": position.route_id,
        "direction_id": position.direction_id,
        "latitude": position.latitude,
        "longitude": position.longitude,
        "bearing": position.bearing,
        "current_status": position.current_status,
        "stop_id": position.stop_id,
        "timestamp": position.timestamp,
    }

UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Subway Position Board</title>
<style>
  :root{
    --bg:#0b0d0f;
    --panel:#121417;
    --line:#22262b;
    --amber:#ffb000;
    --amber-dim:#7a5600;
    --green:#00e08a;
    --red:#ff5d5d;
    --text:#e8e6df;
    --muted:#6b7280;
    --mono: "IBM Plex Mono","SF Mono",Consolas,"Courier New",monospace;
  }
  *{box-sizing:border-box;}
  body{
    margin:0;
    background:var(--bg);
    color:var(--text);
    font-family:var(--mono);
    min-height:100vh;
  }
  .wrap{max-width:1100px;margin:0 auto;padding:24px 20px 60px;}
 
  header{
    display:flex;
    align-items:baseline;
    justify-content:space-between;
    border-bottom:2px solid var(--amber-dim);
    padding-bottom:14px;
    margin-bottom:18px;
    flex-wrap:wrap;
    gap:10px;
  }
  .brand{display:flex;align-items:baseline;gap:10px;}
  .brand .glyph{
    color:var(--amber);
    font-size:22px;
    letter-spacing:2px;
    font-weight:700;
  }
  .brand small{color:var(--muted);letter-spacing:3px;text-transform:uppercase;font-size:10px;}
  .status{
    display:flex;align-items:center;gap:8px;
    font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);
  }
  .dot{width:8px;height:8px;border-radius:50%;background:var(--muted);flex:none;}
  .dot.ok{background:var(--green);box-shadow:0 0 8px var(--green);}
  .dot.bad{background:var(--red);box-shadow:0 0 8px var(--red);}
 
  .controls{
    display:grid;
    grid-template-columns:140px 100px 130px auto;
    gap:10px;
    background:var(--panel);
    border:1px solid var(--line);
    padding:14px;
    margin-bottom:18px;
  }
  @media (max-width:760px){ .controls{grid-template-columns:1fr 1fr;} }
 
  label{
    font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);
    display:block;margin-bottom:5px;
  }
  input, select{
    width:100%;
    background:#0f1114;
    border:1px solid var(--line);
    color:var(--text);
    font-family:var(--mono);
    font-size:13px;
    padding:8px 9px;
  }
  input:focus, select:focus{outline:1px solid var(--amber);border-color:var(--amber);}
 
  button{
    background:var(--amber);
    color:#171000;
    border:none;
    font-family:var(--mono);
    font-weight:700;
    letter-spacing:1px;
    font-size:12px;
    text-transform:uppercase;
    padding:0 18px;
    cursor:pointer;
    align-self:end;
    height:37px;
  }
  button:hover{background:#ffc23d;}
  button:focus-visible{outline:2px solid var(--text);}
 
  .meta{
    display:flex;justify-content:space-between;align-items:center;
    font-size:11px;color:var(--muted);letter-spacing:1px;
    margin-bottom:8px;
  }
  .meta span.count{color:var(--amber);}
 
  table{width:100%;border-collapse:collapse;font-size:13px;}
  thead th{
    text-align:left;
    color:var(--muted);
    font-weight:600;
    letter-spacing:1px;
    text-transform:uppercase;
    font-size:10px;
    padding:8px 10px;
    border-bottom:1px solid var(--line);
  }
  tbody td{
    padding:10px 10px;
    border-bottom:1px solid var(--line);
    white-space:nowrap;
  }
  tbody tr{transition:background .15s;}
  tbody tr:hover{background:#171a1e;}
 
  .route-pill{
    display:inline-block;
    min-width:26px;
    text-align:center;
    background:var(--amber);
    color:#171000;
    font-weight:700;
    padding:2px 7px;
    font-size:12px;
  }
  .status-pill{
    font-size:10px;letter-spacing:1px;text-transform:uppercase;padding:3px 7px;
    border:1px solid var(--line);color:var(--muted);
  }
  .status-pill.moving{color:var(--green);border-color:var(--green);}
  .status-pill.stopped{color:var(--amber);border-color:var(--amber);}
 
  .coords{color:var(--muted);font-size:12px;}
 
  .empty, .error, .loading{
    padding:40px 20px;text-align:center;color:var(--muted);
    border:1px dashed var(--line);font-size:13px;letter-spacing:1px;
  }
  .error{color:var(--red);border-color:var(--red);}
 
  @keyframes flap{
    0%{opacity:0; transform:translateY(-4px);}
    100%{opacity:1; transform:translateY(0);}
  }
  tbody tr{animation:flap .25s ease-out;}
 
  footer{
    margin-top:22px;color:var(--muted);font-size:11px;letter-spacing:1px;
    display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;
  }
</style>
</head>
<body>
<div class="wrap">
 
  <header>
    <div class="brand">
      <span class="glyph">&#9673; TRANSIT</span>
      <small>live vehicle position board</small>
    </div>
    <div class="status" id="apiStatus">
      <span class="dot" id="apiDot"></span>
      <span id="apiStatusText">checking service&hellip;</span>
    </div>
  </header>
 
  <div class="controls">
    <div>
      <label for="routeId">Route ID</label>
      <input id="routeId" type="text" placeholder="all routes" spellcheck="false">
    </div>
    <div>
      <label for="limit">Limit</label>
      <input id="limit" type="number" value="100" min="1" max="1000">
    </div>
    <div>
      <label for="interval">Auto-refresh</label>
      <select id="interval">
        <option value="0">Off</option>
        <option value="5000" selected>5s</option>
        <option value="10000">10s</option>
        <option value="30000">30s</option>
      </select>
    </div>
    <button id="refreshBtn">Refresh</button>
  </div>
 
  <div class="meta">
    <span id="metaLeft">&mdash;</span>
    <span id="metaRight"></span>
  </div>
 
  <div id="results"></div>
 
  <footer>
    <span>GET /api/positions[/&lt;route_id&gt;]</span>
    <span id="clock"></span>
  </footer>
</div>
 
<script>
const els = {
  routeId: document.getElementById('routeId'),
  limit: document.getElementById('limit'),
  interval: document.getElementById('interval'),
  refreshBtn: document.getElementById('refreshBtn'),
  results: document.getElementById('results'),
  metaLeft: document.getElementById('metaLeft'),
  metaRight: document.getElementById('metaRight'),
  apiDot: document.getElementById('apiDot'),
  apiStatusText: document.getElementById('apiStatusText'),
  clock: document.getElementById('clock'),
};
 
let timer = null;
 
function fmtTime(ts){
  if(!ts) return '\u2014';
  const d = new Date(ts);
  if(isNaN(d.getTime())) return String(ts);
  return d.toLocaleTimeString();
}
 
function statusClass(status){
  if(!status) return '';
  const s = String(status).toUpperCase();
  if(s.includes('STOP') || s.includes('DWELL')) return 'stopped';
  if(s.includes('MOV') || s.includes('TRANSIT') || s.includes('INCOMING')) return 'moving';
  return '';
}
 
function renderRows(positions){
  if(!positions.length){
    els.results.innerHTML = '<div class="empty">No positions returned. Nothing is currently reporting for this route.</div>';
    return;
  }
  const rows = positions.map(p => `
    <tr>
      <td><span class="route-pill">${escapeHtml(p.route_id ?? '\u2014')}</span></td>
      <td>${escapeHtml(p.trip_id ?? '\u2014')}</td>
      <td>${p.direction_id ?? '\u2014'}</td>
      <td><span class="status-pill ${statusClass(p.current_status)}">${escapeHtml(p.current_status ?? 'unknown')}</span></td>
      <td>${escapeHtml(p.stop_id ?? '\u2014')}</td>
      <td class="coords">${fmtNum(p.latitude)}, ${fmtNum(p.longitude)}</td>
      <td>${p.bearing != null ? p.bearing + '\u00b0' : '\u2014'}</td>
      <td>${fmtTime(p.timestamp)}</td>
    </tr>
  `).join('');
 
  els.results.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Route</th>
          <th>Trip</th>
          <th>Dir</th>
          <th>Status</th>
          <th>Stop</th>
          <th>Lat, Lon</th>
          <th>Bearing</th>
          <th>Updated</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}
 
function fmtNum(n){
  return typeof n === 'number' ? n.toFixed(4) : (n ?? '\u2014');
}
 
function escapeHtml(str){
  return String(str).replace(/[&<>"']/g, s => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[s]));
}
 
async function pingApi(){
  try{
    const res = await fetch('/api/ping', { cache: 'no-store' });
    if(!res.ok) throw new Error('bad status');
    els.apiDot.className = 'dot ok';
    els.apiStatusText.textContent = 'service online';
    return true;
  }catch(e){
    els.apiDot.className = 'dot bad';
    els.apiStatusText.textContent = 'service unreachable';
    return false;
  }
}
 
async function loadPositions(){
  const route = els.routeId.value.trim();
  let limit = parseInt(els.limit.value, 10) || 100;
  limit = Math.min(Math.max(limit, 1), 1000);
  els.limit.value = limit;
 
  const path = route ? `/api/positions/${encodeURIComponent(route)}` : '/api/positions';
  const url = `${path}?limit=${limit}`;
 
  els.results.innerHTML = '<div class="loading">Fetching positions&hellip;</div>';
 
  await pingApi();
 
  try{
    const res = await fetch(url, { cache: 'no-store' });
    if(!res.ok){
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    renderRows(data);
    els.metaLeft.textContent = route ? `Filtered to route ${route}` : 'All routes';
    els.metaRight.innerHTML = `<span class="count">${data.length}</span> record${data.length===1?'':'s'} &middot; last pull ${new Date().toLocaleTimeString()}`;
  }catch(err){
    els.results.innerHTML = `<div class="error">Could not load positions from ${url}<br>${escapeHtml(err.message)}</div>`;
    els.metaLeft.textContent = 'Error';
    els.metaRight.textContent = '';
  }
}
 
function restartTimer(){
  if(timer) clearInterval(timer);
  const ms = parseInt(els.interval.value, 10);
  if(ms > 0){
    timer = setInterval(loadPositions, ms);
  }
}
 
els.refreshBtn.addEventListener('click', loadPositions);
els.interval.addEventListener('change', restartTimer);
els.routeId.addEventListener('keydown', e => { if(e.key === 'Enter') loadPositions(); });
els.limit.addEventListener('keydown', e => { if(e.key === 'Enter') loadPositions(); });
 
function tickClock(){
  els.clock.textContent = new Date().toLocaleTimeString();
}
setInterval(tickClock, 1000);
tickClock();
 
loadPositions();
restartTimer();
</script>
</body>
</html>
"""

@app.route("/ui")
def ui():
    return Response(UI_HTML, mimetype="text/html")

@app.route("/")
def home():
    return jsonify({"service": "query_service", "status": "ok"})


@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok"})


@app.route("/api/positions", methods=["GET"])
def get_positions():
    limit = request.args.get("limit", default=100, type=int)
    limit = min(max(limit, 1), 1000)

    db = SessionLocal()
    try:
        positions = (
            db.query(SubwayPosition)
            .order_by(SubwayPosition.timestamp.desc())
            .limit(limit)
            .all()
        )
        return jsonify([position_to_dict(p) for p in positions])
    finally:
        db.close()


@app.route("/api/positions/<route_id>", methods=["GET"])
def get_positions_by_route(route_id):
    limit = request.args.get("limit", default=100, type=int)
    limit = min(max(limit, 1), 1000)

    db = SessionLocal()
    try:
        positions = (
            db.query(SubwayPosition)
            .filter(SubwayPosition.route_id == route_id)
            .order_by(SubwayPosition.timestamp.desc())
            .limit(limit)
            .all()
        )
        return jsonify([position_to_dict(p) for p in positions])
    finally:
        db.close()


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
        host="0.0.0.0",
        port=Config.QUERY_API_PORT,
    )
