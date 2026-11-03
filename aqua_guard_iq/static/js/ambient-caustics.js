/**
 * AquaGuard IQ v2.5 - Ambient Water Caustics & Flowing Champagne Background
 * Implements the sophisticated warm palette:
 * - Primary: Warm ivory (#F8F5ED)
 * - Secondary: Champagne beige (#EAE1D2)
 * - Subtle champagne-colored atmosphere with soft organic water ripples
 */

(function () {
  const canvas = document.getElementById('causticsCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = 0;
  let height = 0;
  let animationFrameId = null;

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.min(width, 1920);
    canvas.height = Math.min(height, 1200);
  }
  window.addEventListener('resize', resize);
  resize();

  // Subtle wave harmonics for organic liquid surface ripples
  const waves = [
    { freqX: 0.0032, freqY: 0.0022, speed: 0.0005, amp: 22, phase: 0 },
    { freqX: 0.0052, freqY: 0.0038, speed: 0.0008, amp: 14, phase: 2.1 },
    { freqX: 0.0075, freqY: 0.0055, speed: 0.0011, amp: 9, phase: 4.2 }
  ];

  // Soft champagne water glints
  const glints = [];
  const glintCount = 24;
  for (let i = 0; i < glintCount; i++) {
    glints.push({
      x: Math.random() * 1920,
      y: Math.random() * 1200,
      r: 1.0 + Math.random() * 2.0,
      alpha: 0.15 + Math.random() * 0.35,
      speedY: -(0.1 + Math.random() * 0.25),
      speedX: (Math.random() - 0.5) * 0.15,
      pulseSpeed: 0.015 + Math.random() * 0.025,
      pulsePhase: Math.random() * Math.PI * 2
    });
  }

  let time = 0;

  function render() {
    time += 1;
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Dynamic transparent overlay: Subtle Champagne Sunlight Bloom & Living Water Caustics
    const bloomTop = ctx.createRadialGradient(w * 0.85, h * 0.18, 15, w * 0.85, h * 0.18, w * 0.42);
    bloomTop.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
    bloomTop.addColorStop(0.5, 'rgba(255, 252, 245, 0.15)');
    bloomTop.addColorStop(1, 'transparent');
    ctx.fillStyle = bloomTop;
    ctx.fillRect(0, 0, w, h);

    const bloomLeft = ctx.createRadialGradient(w * 0.18, h * 0.28, 20, w * 0.18, h * 0.28, w * 0.45);
    bloomLeft.addColorStop(0, 'rgba(255, 255, 255, 0.6)');
    bloomLeft.addColorStop(0.6, 'rgba(255, 250, 240, 0.18)');
    bloomLeft.addColorStop(1, 'transparent');
    ctx.fillStyle = bloomLeft;
    ctx.fillRect(0, 0, w, h);

    // 3. Delicate Liquid Water Ripple Folds (Simulating silk water ripples without heavy color)
    const stepY = 100;
    const countY = Math.ceil(h / stepY) + 2;

    for (let j = 0; j < countY; j++) {
      const baseY = j * stepY - 40;
      ctx.beginPath();
      ctx.moveTo(0, baseY);

      for (let x = 0; x <= w; x += 45) {
        let dy = 0;
        for (let k = 0; k < waves.length; k++) {
          const wv = waves[k];
          dy += Math.sin(x * wv.freqX + baseY * wv.freqY + time * wv.speed + wv.phase) * wv.amp;
        }
        ctx.lineTo(x, baseY + dy);
      }

      ctx.lineTo(w, h);
      ctx.lineTo(0, h);
      ctx.closePath();

      const isCrest = j % 2 === 0;
      const grad = ctx.createLinearGradient(0, baseY - 30, w, baseY + 50);

      if (isCrest) {
        grad.addColorStop(0, 'rgba(255, 255, 255, 0.08)');
        grad.addColorStop(1, 'rgba(245, 238, 226, 0.04)');
      } else {
        grad.addColorStop(0, 'rgba(230, 220, 205, 0.05)');
        grad.addColorStop(1, 'transparent');
      }

      ctx.fillStyle = grad;
      ctx.fill();
    }

    // 4. Subtle Champagne Water Glints
    for (let i = 0; i < glints.length; i++) {
      const g = glints[i];
      g.y += g.speedY;
      g.x += g.speedX;
      g.pulsePhase += g.pulseSpeed;

      if (g.y < -20) g.y = h + 20;
      if (g.x < -20) g.x = w + 20;
      if (g.x > w + 20) g.x = -20;

      const currentAlpha = g.alpha * (0.6 + 0.4 * Math.sin(g.pulsePhase));
      ctx.beginPath();
      ctx.arc(g.x, g.y, g.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, ' + currentAlpha + ')';
      ctx.fill();
    }

    animationFrameId = requestAnimationFrame(render);
  }

  render();

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    } else {
      render();
    }
  });
})();
