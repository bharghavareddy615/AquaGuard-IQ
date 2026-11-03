/**
 * AquaGuard IQ - 3D Interactive WebGL RO Filter & Water Swirling Vortex
 * Enterprise-Grade v2.0 Production Prototype | AtomQUEST Track 2
 * Inspired by image_3.png visual standard
 */

(function () {
  let scene, camera, renderer, animationFrameId;
  let filterGroup, vortexParticles, orbitalRingsGroup;
  let mouseX = 0, mouseY = 0;
  let targetRotationX = 0.2, targetRotationY = -0.4;
  let container;
  let isWebGLAvailable = true;

  // Particle vortex parameters
  const PARTICLE_COUNT = 1400;
  let particlePositions, particleVelocities;

  document.addEventListener('DOMContentLoaded', () => {
    container = document.getElementById('canvas-3d-container');
    if (!container) return;

    try {
      initThreeScene();
      animate();
    } catch (err) {
      console.warn("WebGL initialization fallback to 2D canvas:", err);
      init2DFallback();
    }

    window.addEventListener('resize', onWindowResize);
    window.addEventListener('mousemove', onMouseMove);
  });

  function initThreeScene() {
    if (typeof THREE === 'undefined') {
      throw new Error("Three.js not loaded");
    }

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 550;

    // 1. Scene & Camera
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 16);

    // 2. WebGL Renderer
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0x06b6d4, 0.8);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 2.5);
    dirLight1.position.set(10, 15, 10);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x10b981, 1.8);
    dirLight2.position.set(-10, -10, 10);
    scene.add(dirLight2);

    const pointLight = new THREE.PointLight(0x22d3ee, 3, 20);
    pointLight.position.set(0, 0, 5);
    scene.add(pointLight);

    // 4. Construct 3D Filter Group (Casing + Membrane + Fittings)
    filterGroup = new THREE.Group();

    // Outer Glass Casing (Transparent Cylinder)
    const glassGeo = new THREE.CylinderGeometry(1.65, 1.65, 8.5, 36, 1, true);
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0x67e8f9,
      emissive: 0x083344,
      emissiveIntensity: 0.3,
      metalness: 0.1,
      roughness: 0.15,
      transparent: true,
      opacity: 0.38,
      transmission: 0.75,
      depthWrite: false,
      wireframe: false
    });
    const glassCasing = new THREE.Mesh(glassGeo, glassMat);
    filterGroup.add(glassCasing);

    // Outer Edge Glowing Wireframe Casing
    const glassEdges = new THREE.EdgesGeometry(glassGeo);
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.4
    });
    const glassWire = new THREE.LineSegments(glassEdges, lineMat);
    filterGroup.add(glassWire);

    // Inner Membrane Core (Cylindrical Filter Core with fine cross-weave)
    const coreGeo = new THREE.CylinderGeometry(1.18, 1.18, 7.8, 32, 24);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x0e7490,
      emissive: 0x06b6d4,
      emissiveIntensity: 0.6,
      wireframe: true,
      transparent: true,
      opacity: 0.65
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    filterGroup.add(coreMesh);

    // Inner Central Lumen Rod
    const rodGeo = new THREE.CylinderGeometry(0.35, 0.35, 8.8, 16);
    const rodMat = new THREE.MeshStandardMaterial({
      color: 0xe0f2fe,
      metalness: 0.85,
      roughness: 0.2
    });
    const rodMesh = new THREE.Mesh(rodGeo, rodMat);
    filterGroup.add(rodMesh);

    // Filter Top Cap & Nipple Fitting
    const capTopGeo = new THREE.CylinderGeometry(1.5, 1.7, 0.8, 32);
    const capMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.5,
      roughness: 0.3
    });
    const capTop = new THREE.Mesh(capTopGeo, capMat);
    capTop.position.y = 4.65;
    filterGroup.add(capTop);

    // Top Quick-Connect Nozzle
    const nozzleGeo = new THREE.CylinderGeometry(0.45, 0.45, 1.0, 16);
    const nozzleMesh = new THREE.Mesh(nozzleGeo, rodMat);
    nozzleMesh.position.y = 5.4;
    filterGroup.add(nozzleMesh);

    // Nozzle ribbed rings
    const ringGeo1 = new THREE.TorusGeometry(0.55, 0.08, 12, 24);
    const ring1 = new THREE.Mesh(ringGeo1, rodMat);
    ring1.rotation.x = Math.PI / 2;
    ring1.position.y = 5.3;
    filterGroup.add(ring1);

    // Filter Bottom Cap & Drain Fitting
    const capBottomGeo = new THREE.CylinderGeometry(1.7, 1.4, 0.8, 32);
    const capBottom = new THREE.Mesh(capBottomGeo, capMat);
    capBottom.position.y = -4.65;
    filterGroup.add(capBottom);

    const nozzleBottom = new THREE.Mesh(nozzleGeo, rodMat);
    nozzleBottom.position.y = -5.4;
    filterGroup.add(nozzleBottom);

    // 5. Orbital Neon Holographic Rings (from image_3.png)
    orbitalRingsGroup = new THREE.Group();

    // Central glowing cyan orbital ring
    const orbitGeo1 = new THREE.TorusGeometry(2.6, 0.045, 16, 64);
    const orbitMat1 = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.85
    });
    const orbitRing1 = new THREE.Mesh(orbitGeo1, orbitMat1);
    orbitRing1.rotation.x = Math.PI / 2.3;
    orbitRing1.rotation.y = 0.2;
    orbitRing1.position.y = 0.8;
    orbitalRingsGroup.add(orbitRing1);

    // Second inclined emerald orbital ring
    const orbitGeo2 = new THREE.TorusGeometry(3.1, 0.035, 16, 64);
    const orbitMat2 = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.75
    });
    const orbitRing2 = new THREE.Mesh(orbitGeo2, orbitMat2);
    orbitRing2.rotation.x = Math.PI / 2.1;
    orbitRing2.rotation.y = -0.3;
    orbitRing2.position.y = -0.4;
    orbitalRingsGroup.add(orbitRing2);

    // Third outer blue whisper ring
    const orbitGeo3 = new THREE.TorusGeometry(3.6, 0.025, 16, 64);
    const orbitMat3 = new THREE.MeshBasicMaterial({
      color: 0x3b82f6,
      transparent: true,
      opacity: 0.5
    });
    const orbitRing3 = new THREE.Mesh(orbitGeo3, orbitMat3);
    orbitRing3.rotation.x = Math.PI / 2.6;
    orbitRing3.position.y = 1.8;
    orbitalRingsGroup.add(orbitRing3);

    filterGroup.add(orbitalRingsGroup);

    // Tilt the entire filter assembly naturally like in image_3.png
    filterGroup.rotation.z = -0.38; // 22-degree diagonal tilt
    filterGroup.rotation.y = 0.35;
    filterGroup.position.set(0.6, 0, 0);
    scene.add(filterGroup);

    // 6. Swirling Water Vortex & Fluid Dynamic Particle System
    createWaterVortexParticles();
  }

  function createWaterVortexParticles() {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(PARTICLE_COUNT * 3);
    const colors = new Float32Array(PARTICLE_COUNT * 3);
    const sizes = new Float32Array(PARTICLE_COUNT);

    particlePositions = [];
    particleVelocities = [];

    const cyanColor = new THREE.Color(0x22d3ee);
    const blueColor = new THREE.Color(0x38bdf8);
    const emeraldColor = new THREE.Color(0x34d399);
    const whiteColor = new THREE.Color(0xffffff);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Helix and cylindrical distribution
      const theta = Math.random() * Math.PI * 2;
      const radius = 1.6 + Math.random() * 2.8;
      const height = (Math.random() - 0.5) * 13;

      const x = radius * Math.cos(theta);
      const y = height;
      const z = radius * Math.sin(theta);

      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;

      // Color variation (water cyan, sky blue, highlights)
      let c;
      const rand = Math.random();
      if (rand < 0.5) c = cyanColor;
      else if (rand < 0.8) c = blueColor;
      else if (rand < 0.93) c = emeraldColor;
      else c = whiteColor;

      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;

      sizes[i] = 0.08 + Math.random() * 0.16;

      // Velocity data
      particlePositions.push({
        radius: radius,
        theta: theta,
        y: y,
        speedTheta: 0.015 + Math.random() * 0.025,
        speedY: 0.03 + Math.random() * 0.04
      });
    }

    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Particle sprite using canvas gradient
    const sprite = createParticleTexture();
    const mat = new THREE.PointsMaterial({
      size: 0.28,
      vertexColors: true,
      map: sprite,
      transparent: true,
      opacity: 0.88,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    vortexParticles = new THREE.Points(geo, mat);
    // Align vortex with filter group tilt
    vortexParticles.rotation.z = -0.38;
    vortexParticles.position.set(0.6, 0, 0);
    scene.add(vortexParticles);
  }

  function createParticleTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
    grad.addColorStop(0.2, 'rgba(34, 211, 238, 0.9)');
    grad.addColorStop(0.6, 'rgba(6, 182, 212, 0.3)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 64, 64);

    const texture = new THREE.Texture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  function onMouseMove(e) {
    // Normalized coordinates (-1 to 1)
    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;

    targetRotationY = 0.35 + mouseX * 0.3;
    targetRotationX = -0.38 + mouseY * 0.2;
  }

  function onWindowResize() {
    if (!container || !camera || !renderer) return;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 550;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  function animate() {
    animationFrameId = requestAnimationFrame(animate);

    const time = performance.now() * 0.001;

    // 1. Smoothly tilt the filter based on cursor
    if (filterGroup) {
      filterGroup.rotation.y += (targetRotationY - filterGroup.rotation.y) * 0.05;
      filterGroup.rotation.z += (targetRotationX - filterGroup.rotation.z) * 0.05;

      // Gentle floating buoyancy
      filterGroup.position.y = Math.sin(time * 1.5) * 0.15;
    }

    // 2. Rotate orbital rings at varying velocities
    if (orbitalRingsGroup) {
      orbitalRingsGroup.children.forEach((ring, idx) => {
        ring.rotation.z += 0.008 * (idx % 2 === 0 ? 1 : -1);
      });
    }

    // 3. Update particle vortex dynamics
    if (vortexParticles && particlePositions) {
      const positions = vortexParticles.geometry.attributes.position.array;

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const p = particlePositions[i];

        // Orbit around cylinder
        p.theta += p.speedTheta;
        p.y += p.speedY;

        // Reset if flow shoots past top
        if (p.y > 7.0) {
          p.y = -7.0;
          p.radius = 1.6 + Math.random() * 2.8;
        }

        positions[i * 3] = p.radius * Math.cos(p.theta);
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.radius * Math.sin(p.theta);
      }

      vortexParticles.geometry.attributes.position.needsUpdate = true;
      vortexParticles.position.y = filterGroup ? filterGroup.position.y : 0;
      vortexParticles.rotation.y = filterGroup ? filterGroup.rotation.y : 0;
    }

    renderer.render(scene, camera);
  }

  // Fallback 2D Canvas if WebGL is unavailable
  function init2DFallback() {
    if (!container) return;
    container.innerHTML = '<canvas id="fallback-canvas" style="width:100%; height:100%;"></canvas>';
    const canvas = document.getElementById('fallback-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    canvas.width = container.clientWidth || 600;
    canvas.height = container.clientHeight || 550;

    let angle = 0;
    function draw2D() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width * 0.55;
      const cy = canvas.height * 0.5;

      // Filter cylinder silhouette
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-0.35);

      // Glass body
      const grad = ctx.createLinearGradient(-40, 0, 40, 0);
      grad.addColorStop(0, 'rgba(6, 182, 212, 0.4)');
      grad.addColorStop(0.5, 'rgba(255, 255, 255, 0.2)');
      grad.addColorStop(1, 'rgba(2, 132, 199, 0.4)');
      ctx.fillStyle = grad;
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 2;
      ctx.strokeRect(-45, -150, 90, 300);
      ctx.fillRect(-45, -150, 90, 300);

      // Orbital circles
      angle += 0.02;
      ctx.beginPath();
      ctx.ellipse(0, 0, 110, 35, 0.4, 0, Math.PI * 2);
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.restore();
      requestAnimationFrame(draw2D);
    }
    draw2D();
  }
})();

