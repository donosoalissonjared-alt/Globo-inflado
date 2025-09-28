// index.js — Single-file PvZ mabar demo
// Cara pakai (lokal):
// 1) simpan sebagai index.js
// 2) npm init -y
// 3) npm install express socket.io
// 4) node index.js
// 5) buka http://localhost:3000 di 2+ browser/HP untuk mabar (pakai nama room sama)

const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http, { cors: { origin: "*" } });
const port = process.env.PORT || 3000;

// Serve single-page client from a string (so only 1 file needed)
const clientHtml = `<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>PVZ Mabar - Single File</title>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,Segoe UI,Roboto,Arial}
  #gameDiv{width:100%;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#cfeecf}
  .controls{display:flex;gap:8px;margin-bottom:8px}
  input{padding:6px;border-radius:6px;border:1px solid #888}
  button{padding:6px 10px;border-radius:6px;border:1px solid #666;background:#fff}
</style>
</head>
<body>
<div id="gameDiv">
  <div class="controls">
    <input id="room" placeholder="room name" value="lobby"/>
    <button id="join">Join</button>
    <button id="leave">Leave</button>
    <span id="info"></span>
  </div>
  <div id="phaser-container"></div>
</div>

<!-- Phaser CDN -->
<script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
<!-- Socket.IO client served by server at /socket.io/socket.io.js -->
<script src="/socket.io/socket.io.js"></script>

<script>
(() => {
  const socket = io(); // connect to same origin server
  let room = null;
  document.getElementById('join').onclick = ()=>{
    room = document.getElementById('room').value || 'lobby';
    socket.emit('joinRoom', room);
    document.getElementById('info').textContent = 'Joined ' + room;
  };
  document.getElementById('leave').onclick = ()=>{
    if(!room) return;
    socket.emit('leaveRoom', room);
    document.getElementById('info').textContent = 'Left ' + room;
    room = null;
  };

  const GRID_ROWS = 5, GRID_COLS = 9;
  const WIDTH = 900, HEIGHT = 500;
  const config = {
    type: Phaser.AUTO,
    parent: 'phaser-container',
    width: WIDTH,
    height: HEIGHT,
    backgroundColor: 0xd9f7d9,
    scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: { preload, create, update }
  };
  const game = new Phaser.Game(config);

  function preload(){}

  function create(){
    const scene = this;
    scene.cellW = WIDTH / GRID_COLS;
    scene.cellH = HEIGHT / GRID_ROWS;
    scene.plants = []; // local
    scene.otherPlants = {}; // {id: []}
    scene.zombies = [];
    scene.suns = [];

    // click to place plant (simple shooter for demo)
    scene.input.on('pointerdown', (p) => {
      const c = Math.floor(p.x / scene.cellW);
      const r = Math.floor(p.y / scene.cellH);
      if (r<0||r>=GRID_ROWS||c<0||c>=GRID_COLS) return;
      if (scene.plants.find(pl=>pl.r===r&&pl.c===c)) return;
      const plant = { r, c, type: 'shooter' };
      scene.plants.push(plant);
      drawPlant(scene, plant, 0x5aa85a);
      if (room) socket.emit('placePlant', { room, plant });
    });

    socket.on('placePlant', (data) => {
      if (!scene.otherPlants[data.id]) scene.otherPlants[data.id] = [];
      scene.otherPlants[data.id].push(data.plant);
      drawPlant(scene, data.plant, 0x88aaff);
    });

    socket.on('roomUpdate', (r) => {
      // optional: show number of players
      document.getElementById('info').textContent = (room ? 'Room: ' + room + ' — players: ' + (r.players ? r.players.length : 0) : '');
    });

    // spawn simple zombies locally
    scene.time.addEvent({ delay: 1600, loop: true, callback: ()=>{
      const rIdx = Phaser.Math.Between(0, GRID_ROWS-1);
      scene.zombies.push({ x: WIDTH + 40, r: rIdx, hp: 100, speed: 0.05 + Math.random()*0.07 });
    }});

    // suns dropping (visual only)
    scene.time.addEvent({ delay: 6000, loop: true, callback: ()=>{
      const x = Phaser.Math.Between(50, WIDTH-50);
      scene.suns.push({ x, y: -20, vy: 0, id: 's'+Date.now() });
    }});
  }

  function drawPlant(scene, plant, color){
    const x = plant.c * scene.cellW + scene.cellW*0.12;
    const y = plant.r * scene.cellH + scene.cellH*0.12;
    const w = scene.cellW*0.76, h = scene.cellH*0.76;
    const g = scene.add.graphics();
    g.fillStyle(color, 1);
    g.fillRect(x + w*0.1, y + h*0.2, w*0.8, h*0.6);
    plant._gfx = g;
  }

  function update(time, dt){
    const scene = game.scene.scenes[0];
    if (!scene) return;
    // zombies move and eat plants
    for (let i = scene.zombies.length - 1; i >= 0; i--) {
      const z = scene.zombies[i];
      z.x -= z.speed * dt;
      const frontC = Math.floor((z.x - 10) / scene.cellW);
      const plantAhead = scene.plants.find(p => p.r === z.r && p.c === frontC);
      if (plantAhead && z.x <= (plantAhead.c + 0.85) * scene.cellW) {
        plantAhead.hp = (plantAhead.hp || 100) - 0.02 * dt;
        if (plantAhead.hp <= 0) {
          const idx = scene.plants.indexOf(plantAhead);
          if (idx >= 0) {
            if (plantAhead._gfx) plantAhead._gfx.destroy();
            scene.plants.splice(idx, 1);
          }
        }
        continue;
      }
      if (z.x < 10) {
        // local game over: clear plants
        scene.zombies.splice(i,1);
        for (let p of scene.plants) if (p._gfx) p._gfx.destroy();
        scene.plants.length = 0;
        console.log('game over (local)');
      }
    }

    // update suns visuals
    for (let i = scene.suns.length - 1; i >= 0; i--) {
      const s = scene.suns[i];
      s.vy += 0.0009 * dt;
      s.y += s.vy * dt;
      if (!s._gfx) {
        const g = scene.add.graphics();
        g.fillStyle(0xffd54d, 1);
        g.fillCircle(s.x, s.y, 12);
        s._gfx = g;
      } else {
        s._gfx.clear();
        s._gfx.fillStyle(0xffd54d, 1);
        s._gfx.fillCircle(s.x, s.y, 12);
      }
      if (s.y > HEIGHT - 8) {
        if (s._gfx) s._gfx.destroy();
        scene.suns.splice(i,1);
      }
    }
  }
})();
</script>
</body>
</html>`;

// provide root route
app.get('/', (req, res) => {
  res.set('Content-Type', 'text/html; charset=utf-8');
  res.send(clientHtml);
});

// minimal API to know server is healthy
app.get('/_health', (req, res) => res.send({ ok: true, ts: Date.now() }));

// socket logic (relay style)
let rooms = {};
io.on('connection', (socket) => {
  console.log('connect', socket.id);

  socket.on('joinRoom', (room) => {
    socket.join(room);
    rooms[room] = rooms[room] || { players: [] };
    if (!rooms[room].players.includes(socket.id)) rooms[room].players.push(socket.id);
    io.to(room).emit('roomUpdate', rooms[room]);
    socket.to(room).emit('playerJoined', { id: socket.id });
  });

  socket.on('leaveRoom', (room) => {
    socket.leave(room);
    if (rooms[room]) {
      rooms[room].players = rooms[room].players.filter(id => id !== socket.id);
      io.to(room).emit('roomUpdate', rooms[room]);
    }
  });

  socket.on('placePlant', (data) => {
    if (data && data.room) {
      socket.to(data.room).emit('placePlant', { id: socket.id, plant: data.plant });
    }
  });

  socket.on('collectSun', (data) => {
    if (data && data.room) {
      socket.to(data.room).emit('collectSun', { id: socket.id, sunId: data.sunId });
    }
  });

  socket.on('bullet', (data) => {
    if (data && data.room) {
      socket.to(data.room).emit('bullet', { id: socket.id, bullet: data.bullet });
    }
  });

  socket.on('disconnecting', () => {
    const roomsJoined = Array.from(socket.rooms);
    for (const r of roomsJoined) {
      if (rooms[r]) {
        rooms[r].players = rooms[r].players.filter(id => id !== socket.id);
        io.to(r).emit('roomUpdate', rooms[r]);
      }
    }
  });
});

http.listen(port, () => console.log('Server ready at http://localhost:' + port + ' (or on your hosting URL)'));
