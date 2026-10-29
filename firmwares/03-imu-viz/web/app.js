/*
 * sMove · IMU 3D — live accel + gyro from firmwares/03-imu-viz.
 *
 * No libraries: the 3D view is a small painter's-algorithm renderer on a 2D
 * canvas (5.5 cm x 2.5 cm board, world Y = up), and the orientation is a
 * complementary filter (gyro integration + slow accel/gravity correction).
 */

(() => {
  'use strict';

  /* ------------------------------------------------------------ constants */

  // Board envelope in cm, board axes: X = across, Y = along, Z = outward normal.
  const BOARD = { hx: 1.25, hy: 1.50, hz: 0.42 };

  // Accel -> length mapping (cm per g) and gyro -> length mapping.
  const ACCEL_SCALE = 2.0;
  const GYRO_LEN = 2.6;

  const UP = [0, 1, 0];

  /* --------------------------------------------------------------- vector */

  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
  const len = (a) => Math.hypot(a[0], a[1], a[2]);
  const norm = (a) => {
    const l = len(a) || 1;
    return [a[0] / l, a[1] / l, a[2] / l];
  };
  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

  /* ----------------------------------------------------------- quaternion */

  const qmul = (a, b) => [
    a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
    a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
    a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
    a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0],
  ];

  const qnorm = (q) => {
    const l = Math.hypot(q[0], q[1], q[2], q[3]) || 1;
    return [q[0] / l, q[1] / l, q[2] / l, q[3] / l];
  };

  const qAxisAngle = (axis, angle) => {
    const h = angle / 2;
    const s = Math.sin(h);
    return [Math.cos(h), axis[0] * s, axis[1] * s, axis[2] * s];
  };

  // Rotation matrix (row-major 3x3) of a quaternion.
  const qMat = (q) => {
    const [w, x, y, z] = q;
    return [
      [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
      [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
      [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ];
  };

  const matVec = (m, v) => [
    m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
    m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
    m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
  ];

  const matMul = (a, b) => {
    const out = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        out[r][c] = a[r][0] * b[0][c] + a[r][1] * b[1][c] + a[r][2] * b[2][c];
      }
    }
    return out;
  };

  /* ----------------------------------------------------------------- state */

  // Rest pose: body +Z outward = world up, so the board lies flat on its back.
  const Q_REST = [Math.SQRT1_2, -Math.SQRT1_2, 0, 0]; // -90 deg about X
  const R_REST = qMat(Q_REST);

  const st = {
    q: Q_REST.slice(),
    bias: [0, 0, 0],
    lastT: 0,
    a: [0, 0, 0],
    g: [0, 0, 0],
    trail: [],
    hist: { a: [], g: [] },
    periodMs: 20,
    rateHz: 0,
    count: 0,
    status: 'waiting',
  };

  const HIST = 220;

  /* ------------------------------------------------------------ filter */

  function onSample(s) {
    const a = s.a;
    const g = s.g;

    let dt = st.lastT ? (s.t - st.lastT) / 1e6 : st.periodMs / 1000;
    st.lastT = s.t;
    if (!(dt > 0) || dt > 0.5) dt = st.periodMs / 1000;
    dt = clamp(dt, 0.0005, 0.2);

    // Gyro bias: average the reading while the unit is essentially still.
    const aMag = len(a);
    const gMag = len(g);
    if (Math.abs(aMag - 1) < 0.12 && gMag < 10) {
      for (let i = 0; i < 3; i++) st.bias[i] += (g[i] - st.bias[i]) * 0.008;
    }

    // 1) integrate the (bias-corrected) body rate
    const w = [
      ((g[0] - st.bias[0]) * Math.PI) / 180,
      ((g[1] - st.bias[1]) * Math.PI) / 180,
      ((g[2] - st.bias[2]) * Math.PI) / 180,
    ];
    const wl = Math.hypot(w[0], w[1], w[2]);
    if (wl > 1e-9) {
      const dq = qAxisAngle([w[0] / wl, w[1] / wl, w[2] / wl], wl * dt);
      st.q = qnorm(qmul(st.q, dq)); // body-frame rate -> right-multiply
    }

    // 2) pull the attitude towards the measured gravity
    if (aMag > 0.25) {
      const v = matVec(qMat(st.q), norm(a)); // measured up, in world
      const c = clamp(dot(v, UP), -1, 1);
      const axis = cross(v, UP);
      const al = len(axis);
      if (al > 1e-6) {
        const k = 1 - Math.exp(-dt / 0.55);
        st.q = qnorm(
          qmul(qAxisAngle([axis[0] / al, axis[1] / al, axis[2] / al], Math.acos(c) * k), st.q)
        );
      }
    }

    st.a = a;
    st.g = g;
    st.count++;

    st.hist.a.push(a.slice());
    st.hist.g.push(g.slice());
    if (st.hist.a.length > HIST) st.hist.a.shift();
    if (st.hist.g.length > HIST) st.hist.g.shift();
  }

  /* ------------------------------------------------------------------ view */

  const scene = document.getElementById('scene');
  const ctx = scene.getContext('2d');
  let W = 0;
  let H = 0;

  const cam = { yaw: -0.66, pitch: 0.44, dist: 11.6, target: [0, -0.15, 0] };
  const camHome = { yaw: -0.66, pitch: 0.44, dist: 11.6 };

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    scene.width = Math.round(W * dpr);
    scene.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function camera() {
    const cp = Math.cos(cam.pitch);
    const sp = Math.sin(cam.pitch);
    const cy = Math.cos(cam.yaw);
    const sy = Math.sin(cam.yaw);
    const dir = [cp * sy, sp, cp * cy]; // target -> eye
    const eye = add(cam.target, mul(dir, cam.dist));
    const fwd = mul(dir, -1);
    let right = cross(fwd, UP);
    if (len(right) < 1e-6) right = [1, 0, 0];
    right = norm(right);
    const up = norm(cross(right, fwd));
    return { eye, fwd, right, up, f: Math.min(W, H) * 1.15 };
  }

  function project(cam, p) {
    const rel = sub(p, cam.eye);
    const z = dot(rel, cam.fwd);
    if (z <= 0.15) return null;
    return [
      W / 2 + (cam.f * dot(rel, cam.right)) / z,
      H / 2 - (cam.f * dot(rel, cam.up)) / z,
      z,
    ];
  }

  /* ---------------------------------------------------------------- shapes */

  const HV = [
    [-BOARD.hx, -BOARD.hy, -BOARD.hz], [BOARD.hx, -BOARD.hy, -BOARD.hz],
    [BOARD.hx, BOARD.hy, -BOARD.hz], [-BOARD.hx, BOARD.hy, -BOARD.hz],
    [-BOARD.hx, -BOARD.hy, BOARD.hz], [BOARD.hx, -BOARD.hy, BOARD.hz],
    [BOARD.hx, BOARD.hy, BOARD.hz], [-BOARD.hx, BOARD.hy, BOARD.hz],
  ];

  const FACES = [
    { i: [4, 5, 6, 7], n: [0, 0, 1], rgb: [33, 78, 66] },    // +Z, PCB side
    { i: [1, 0, 3, 2], n: [0, 0, -1], rgb: [15, 22, 30] },   // -Z
    { i: [1, 2, 6, 5], n: [1, 0, 0], rgb: [24, 34, 46] },    // +X
    { i: [0, 4, 7, 3], n: [-1, 0, 0], rgb: [19, 27, 37] },   // -X
    { i: [3, 7, 6, 2], n: [0, 1, 0], rgb: [22, 31, 42] },    // +Y
    { i: [0, 1, 5, 4], n: [0, -1, 0], rgb: [18, 26, 35] },   // -Y
  ];

  const LIGHT = norm([0.55, 0.95, 0.45]);

  function poly(cam, pts) {
    const out = [];
    for (const p of pts) {
      const q = project(cam, p);
      if (!q) return null;
      out.push(q);
    }
    return out;
  }

  function line3(cam, a, b, color, width, dash) {
    const pa = project(cam, a);
    const pb = project(cam, b);
    if (!pa || !pb) return;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.moveTo(pa[0], pa[1]);
    ctx.lineTo(pb[0], pb[1]);
    ctx.stroke();
    ctx.restore();
  }

  function arrow3(cam, p0, p1, color, width) {
    const a = project(cam, p0);
    const b = project(cam, p1);
    if (!a || !b) return;
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const l = Math.hypot(dx, dy);
    if (l < 1.5) return;
    const ux = dx / l;
    const uy = dy / l;
    const head = Math.min(16, Math.max(7, l * 0.24));

    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.shadowColor = color;
    ctx.shadowBlur = 12;

    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0] - ux * head * 0.7, b[1] - uy * head * 0.7);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(b[0], b[1]);
    ctx.lineTo(b[0] - ux * head - uy * head * 0.42, b[1] - uy * head + ux * head * 0.42);
    ctx.lineTo(b[0] - ux * head + uy * head * 0.42, b[1] - uy * head - ux * head * 0.42);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function label3(cam, p, text, color, dx = 0, dy = 0) {
    const q = project(cam, p);
    if (!q) return;
    ctx.save();
    ctx.fillStyle = color;
    ctx.font = '600 10px ui-monospace, Menlo, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, q[0] + dx, q[1] + dy);
    ctx.restore();
  }

  /* ---------------------------------------------------------------- frame */

  function drawGrid(cam) {
    const y = -2.4;
    const half = 9;
    for (let i = -half; i <= half; i++) {
      const fade = 0.11 * (1 - Math.abs(i) / (half + 2)) + 0.03;
      const c = `rgba(96, 150, 200, ${fade.toFixed(3)})`;
      line3(cam, [i, y, -half], [i, y, half], c, 1);
      line3(cam, [-half, y, i], [half, y, i], c, 1);
    }
    // world axes at the grid corner
    const o = [-half, y, half];
    arrow3(cam, o, add(o, [2.2, 0, 0]), 'rgba(255,107,107,0.85)', 1.6);
    arrow3(cam, o, add(o, [0, 2.2, 0]), 'rgba(110,231,160,0.85)', 1.6);
    arrow3(cam, o, add(o, [0, 0, -2.2]), 'rgba(122,162,255,0.85)', 1.6);
    label3(cam, add(o, [2.6, 0, 0]), 'X', 'rgba(255,107,107,0.8)');
    label3(cam, add(o, [0, 2.7, 0]), 'Y', 'rgba(110,231,160,0.8)');
    label3(cam, add(o, [0, 0, -2.6]), 'Z', 'rgba(122,162,255,0.8)');
  }

  function drawBoard(cam) {
    const R = qMat(st.q);
    const world = HV.map((v) => matVec(R, v));

    // faint drop shadow on the grid
    ctx.save();
    const shadowPts = poly(cam, world.map((v) => [v[0] * 1.06, -2.38, v[2] * 1.06]));
    if (shadowPts) {
      ctx.fillStyle = 'rgba(0,0,0,0.26)';
      ctx.beginPath();
      shadowPts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();

    // faces: cull back sides, shade by lambert
    for (const f of FACES) {
      const pts = f.i.map((i) => world[i]);
      const nWorld = matVec(R, f.n);
      const centroid = mul(pts.reduce((s, p) => add(s, p), [0, 0, 0]), 1 / pts.length);
      if (dot(nWorld, sub(cam.eye, centroid)) <= 0) continue;

      const lambert = 0.45 + 0.75 * Math.max(0, dot(nWorld, LIGHT));
      const [r0, g0, b0] = f.rgb;
      const rgb = `${Math.min(255, r0 * lambert) | 0},${Math.min(255, g0 * lambert) | 0},${
        Math.min(255, b0 * lambert) | 0
      }`;

      const proj = poly(cam, pts);
      if (!proj) continue;
      ctx.beginPath();
      proj.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
      ctx.closePath();
      ctx.fillStyle = `rgb(${rgb})`;
      ctx.fill();
      ctx.strokeStyle = 'rgba(126, 186, 226, 0.22)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // the IMU package (U2) on the outward face, plus a pin-1 dot
    const chip = 0.34;
    const zc = BOARD.hz + 0.004;
    const chipPts = poly(cam, [
      [-chip, 0.55 - chip, zc], [chip, 0.55 - chip, zc],
      [chip, 0.55 + chip, zc], [-chip, 0.55 + chip, zc],
    ].map((p) => matVec(R, p)));
    if (chipPts) {
      ctx.beginPath();
      chipPts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
      ctx.closePath();
      ctx.fillStyle = 'rgba(8, 12, 18, 0.92)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(120, 170, 210, 0.4)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // body axes
    const axes = [
      { v: [1, 0, 0], c: 'rgba(255,107,107,0.95)', t: 'x' },
      { v: [0, 1, 0], c: 'rgba(110,231,160,0.95)', t: 'y' },
      { v: [0, 0, 1], c: 'rgba(122,162,255,0.95)', t: 'z' },
    ];
    for (const ax of axes) {
      const tip = matVec(R, mul(norm(ax.v), 1.75));
      arrow3(cam, [0, 0, 0], tip, ax.c, 1.6);
      label3(cam, mul(tip, 1.18), ax.t, ax.c);
    }
  }

  function drawVectors(cam) {
    // accel trail (tips of the last few samples)
    if (st.trail.length > 1) {
      ctx.save();
      ctx.lineWidth = 1.4;
      for (let i = 1; i < st.trail.length; i++) {
        const p = project(cam, st.trail[i - 1]);
        const q = project(cam, st.trail[i]);
        if (!p || !q) continue;
        ctx.strokeStyle = `rgba(255, 180, 84, ${((i / st.trail.length) * 0.45).toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(p[0], p[1]);
        ctx.lineTo(q[0], q[1]);
        ctx.stroke();
      }
      ctx.restore();
    }

    const R = qMat(st.q);

    // accelerometer: direction = measured gravity, length ~ |a|
    const aMag = len(st.a);
    if (aMag > 0.05) {
      const l = clamp(ACCEL_SCALE * aMag, 0.8, 5.5);
      arrow3(cam, [0, 0, 0], matVec(R, mul(norm(st.a), l)), '#ffb454', 2.6);
      label3(cam, matVec(R, mul(norm(st.a), l + 0.55)), `${aMag.toFixed(2)} g`, '#ffb454');
    }

    // gyroscope: direction = rate vector, length saturates at high rates
    const gMag = len(st.g);
    if (gMag > 1.0) {
      const l = GYRO_LEN * (1 - Math.exp(-gMag / 110)) + 0.45;
      arrow3(cam, [0, 0, 0], matVec(R, mul(norm(st.g), l)), '#4fd6ff', 2.2);
      label3(cam, matVec(R, mul(norm(st.g), l + 0.55)), `${gMag.toFixed(0)} °/s`, '#4fd6ff');
    }
  }

  function frame() {
    const cam = camera();
    ctx.clearRect(0, 0, W, H);
    drawGrid(cam);
    drawBoard(cam);
    drawVectors(cam);
    requestAnimationFrame(frame);
  }

  /* -------------------------------------------------------------------- HUD */

  const el = (id) => document.getElementById(id);
  const els = {
    led: el('led'),
    chipRate: el('chipRate'),
    chipPort: el('chipPort'),
    magA: el('magA'),
    magG: el('magG'),
    pitch: el('attPitch'),
    roll: el('attRoll'),
    yaw: el('attYaw'),
    toast: el('toast'),
    aRows: [...document.querySelectorAll('.row[data-axis]')],
    gRows: [...document.querySelectorAll('.row[data-gyro]')],
    chartA: el('chartAccel'),
    chartG: el('chartGyro'),
  };

  const fmt = (v, d = 2) => (v >= 0 ? '+' : '') + v.toFixed(d);

  function bar(row, value, scale) {
    const i = row.querySelector('.meter i');
    const frac = clamp(value / scale, -1, 1);
    const w = Math.abs(frac) * 50;
    i.style.width = `${w}%`;
    i.style.left = frac >= 0 ? '50%' : `${50 - w}%`;
  }

  function attitude() {
    const D = matMul(qMat(st.q), [
      [1, 0, 0],
      [0, 0, -1],
      [0, 1, 0],
    ]); // relative to the flat rest pose
    const pitch = Math.asin(clamp(-D[1][2], -1, 1)) * (180 / Math.PI);
    const yaw = Math.atan2(D[0][2], D[2][2]) * (180 / Math.PI);
    const roll = Math.atan2(D[1][0], D[1][1]) * (180 / Math.PI);
    return [pitch, roll, yaw];
  }

  function hud() {
    const a = st.a;
    const g = st.g;

    els.aRows.forEach((row, i) => {
      row.querySelector('.val').textContent = fmt(a[i], 2);
      bar(row, a[i], 1.6);
    });
    els.gRows.forEach((row, i) => {
      row.querySelector('.val').textContent = fmt(g[i], 1);
      bar(row, g[i], 220);
    });

    els.magA.textContent = len(a).toFixed(2);
    els.magG.textContent = len(g).toFixed(1);

    const [pitch, roll, yaw] = attitude();
    els.pitch.textContent = fmt(pitch, 0);
    els.roll.textContent = fmt(roll, 0);
    els.yaw.textContent = fmt(yaw, 0);

    els.chipRate.textContent = st.rateHz ? `${st.rateHz.toFixed(0)} Hz` : '— Hz';
    const nominal = 1000 / (st.periodMs || 20);
    els.chipRate.classList.toggle('hot', st.rateHz > 0 && st.rateHz < nominal * 0.8);
  }

  /* ---------------------------------------------------------------- charts */

  function fitCanvas(c) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = c.getBoundingClientRect();
    const bw = Math.max(1, Math.round(rect.width * dpr));
    const bh = Math.max(1, Math.round(rect.height * dpr));
    if (c.width !== bw || c.height !== bh) {
      c.width = bw;
      c.height = bh;
    }
    const g2 = c.getContext('2d');
    g2.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: g2, w: rect.width, h: rect.height };
  }

  function drawChart(canvas, series, colors, minScale) {
    const { ctx: c, w, h } = fitCanvas(canvas);
    c.clearRect(0, 0, w, h);

    c.strokeStyle = 'rgba(120,160,200,0.10)';
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(0, h / 2 + 0.5);
    c.lineTo(w, h / 2 + 0.5);
    c.stroke();

    if (!series.length) return;

    let peak = minScale;
    for (const s of series) for (const v of s) peak = Math.max(peak, Math.abs(v));
    peak *= 1.15;

    const n = series[0].length;
    for (let k = 0; k < series.length; k++) {
      c.strokeStyle = colors[k];
      c.lineWidth = 1.3;
      c.beginPath();
      for (let i = 0; i < n; i++) {
        const x = n > 1 ? (i / (n - 1)) * w : 0;
        const y = h / 2 - (series[k][i] / peak) * (h / 2 - 3);
        i ? c.lineTo(x, y) : c.moveTo(x, y);
      }
      c.stroke();
    }
  }

  const AXIS_COLORS = ['rgba(255,107,107,0.85)', 'rgba(110,231,160,0.85)', 'rgba(122,162,255,0.85)'];

  function drawCharts() {
    const aSeries = [0, 1, 2].map((k) => st.hist.a.map((v) => v[k]));
    const gSeries = [0, 1, 2].map((k) => st.hist.g.map((v) => v[k]));
    drawChart(els.chartA, aSeries, AXIS_COLORS, 0.6);
    drawChart(els.chartG, gSeries, AXIS_COLORS, 30);
  }

  /* ------------------------------------------------------------------ link */

  let toastTimer = 0;
  function toast(msg, ms = 4200) {
    els.toast.textContent = msg;
    els.toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove('show'), ms);
  }

  function setStatus(status, detail) {
    st.status = status;
    els.led.className = 'led ' + (status === 'live' || status === 'mock' ? status : 'waiting');
    els.chipPort.textContent = status === 'live' ? 'USB live' : status === 'mock' ? 'mock data' : 'waiting';
    if (status === 'waiting') {
      toast(detail || 'waiting for the board — is it plugged in?');
    } else {
      els.toast.classList.remove('show');
    }
  }

  function connect() {
    const es = new EventSource('/events');
    es.onmessage = (ev) => {
      let m;
      try {
        m = JSON.parse(ev.data);
      } catch {
        return;
      }
      if (m.type === 'sample') {
        onSample(m);
        st.trail.push(matVec(qMat(st.q), mul(norm(m.a), clamp(ACCEL_SCALE * len(m.a), 0.8, 5.5))));
        if (st.trail.length > 90) st.trail.shift();
      } else if (m.type === 'config') {
        st.periodMs = m.periodMs || 20;
      } else if (m.type === 'status') {
        st.rateHz = m.rateHz || 0;
        st.periodMs = m.periodMs || st.periodMs;
        st.count = m.count || 0;
        setStatus(m.serial, m.detail);
        if (m.latest && st.count === 0) onSample(m.latest);
      }
    };
    es.onerror = () => setStatus('waiting', 'web server connection lost — retrying…');
  }

  /* ------------------------------------------------------------ interaction */

  let drag = null;

  scene.addEventListener('pointerdown', (e) => {
    drag = { x: e.clientX, y: e.clientY, yaw: cam.yaw, pitch: cam.pitch };
    scene.classList.add('dragging');
    scene.setPointerCapture(e.pointerId);
  });

  scene.addEventListener('pointermove', (e) => {
    if (!drag) return;
    cam.yaw = drag.yaw - (e.clientX - drag.x) * 0.008;
    cam.pitch = clamp(drag.pitch + (e.clientY - drag.y) * 0.006, -1.25, 1.35);
  });

  const endDrag = (e) => {
    drag = null;
    scene.classList.remove('dragging');
    if (e && e.pointerId !== undefined && scene.hasPointerCapture(e.pointerId)) {
      scene.releasePointerCapture(e.pointerId);
    }
  };
  scene.addEventListener('pointerup', endDrag);
  scene.addEventListener('pointercancel', endDrag);

  scene.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      cam.dist = clamp(cam.dist * (1 + Math.sign(e.deltaY) * 0.08), 5.5, 32);
    },
    { passive: false }
  );

  scene.addEventListener('dblclick', () => {
    cam.yaw = camHome.yaw;
    cam.pitch = camHome.pitch;
    cam.dist = camHome.dist;
  });

  window.addEventListener('resize', resize);

  /* ------------------------------------------------------------------- boot */

  resize();
  requestAnimationFrame(frame);
  connect();

  setInterval(hud, 80);
  setInterval(drawCharts, 100);
})();
