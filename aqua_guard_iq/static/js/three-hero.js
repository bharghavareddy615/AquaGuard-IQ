/**
 * AquaGuard IQ v2.5 - Photorealistic 3D Water Purifier Assembly
 * Powered by Three.js (r128) & GLTFLoader
 * 
 * Features:
 * - Loads official binary GLB model (water_purifier_cartridge.glb)
 * - Precision CNC lathe-threaded stainless steel connectors with specular reflections
 * - Dual-walled crystal acrylic pressure vessel (Physical Glass Refraction IOR 1.52)
 * - Internal Diamond-Pattern RO Filtration Membrane (high-res texture mapping)
 * - Organic transparent turquoise liquid water splash stream (Physical Water IOR 1.333)
 * - Continuous smooth 3D local Y-axis rotation (12-15s per revolution)
 * - Subtle floating buoyancy & responsive cursor parallax
 */

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('hero-webgl-canvas');
  if (!container) return;

  if (typeof THREE === 'undefined') {
    console.warn('Three.js library not loaded');
    return;
  }

  // 1. Scene Setup
  const scene = new THREE.Scene();
  let width = container.clientWidth || 650;
  let height = container.clientHeight || 620;

  const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 1000);
  camera.position.set(0, 0, 18.0);

  const renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance'
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.32;
  renderer.outputEncoding = THREE.sRGBEncoding;

  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  // 2. Studio Environment Lighting
  const ambientLight = new THREE.AmbientLight(0xfffbf5, 1.35);
  scene.add(ambientLight);

  // Key Studio Light (Warm Ivory Highlight)
  const keyLight = new THREE.DirectionalLight(0xfffcf7, 2.8);
  keyLight.position.set(12, 16, 14);
  scene.add(keyLight);

  // Turquoise / Cyan Rim Light (Accentuating Acrylic & Liquid Edges)
  const rimLight = new THREE.DirectionalLight(0x00d2ff, 2.2);
  rimLight.position.set(-12, -6, 8);
  scene.add(rimLight);

  // Soft Front Fill Light
  const fillLight = new THREE.DirectionalLight(0xe2e8f0, 1.4);
  fillLight.position.set(0, -8, 12);
  scene.add(fillLight);

  // Internal Core Point Light (Luminance inside the RO Cartridge)
  const coreLight = new THREE.PointLight(0x38bdf8, 1.8, 16);
  coreLight.position.set(0, 0, 0);
  scene.add(coreLight);

  // 3. Hierarchy & Coordinate System
  const pivotRoot = new THREE.Group();
  pivotRoot.position.set(0.65, -0.15, 0);
  pivotRoot.rotation.z = -0.52; // ~-30° studio diagonal tilt
  pivotRoot.rotation.x = 0.22;  // Slight forward tilt
  pivotRoot.rotation.y = 0.26;  // Oblique 3D angle
  scene.add(pivotRoot);

  const floatingGroup = new THREE.Group();
  pivotRoot.add(floatingGroup);

  // Unified 3D Rotation Group
  const purifierSpinGroup = new THREE.Group();
  floatingGroup.add(purifierSpinGroup);

  // 4. Load High-Resolution Diamond RO Texture
  const textureLoader = new THREE.TextureLoader();
  const diamondTex = textureLoader.load('/static/textures/ro_membrane_diamond.png', (tex) => {
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(4, 3);
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  });

  // 5. Materials Library for GLB Model Parts
  // Polished Stainless Steel (Top & Bottom Caps, Fine Lathe Threads, Flanges)
  const steelMat = new THREE.MeshPhysicalMaterial({
    color: 0xe2ebf5,
    metalness: 0.96,
    roughness: 0.15,
    reflectivity: 0.98,
    clearcoat: 0.8,
    clearcoatRoughness: 0.08
  });

  // Precision Slim Compression Collars
  const collarMat = new THREE.MeshPhysicalMaterial({
    color: 0xf1f5f9,
    metalness: 0.98,
    roughness: 0.12,
    reflectivity: 1.0,
    clearcoat: 1.0
  });

  // Crystal-Clear Acrylic Pressure Vessel (Optical Glass Refraction)
  const acrylicGlassMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transmission: 0.94,
    opacity: 1.0,
    transparent: true,
    roughness: 0.04,
    metalness: 0.02,
    ior: 1.52,
    reflectivity: 0.92,
    clearcoat: 1.0,
    clearcoatRoughness: 0.02,
    depthWrite: false
  });

  // Internal RO Membrane Filtration Core
  const membraneMat = new THREE.MeshStandardMaterial({
    map: diamondTex,
    bumpMap: diamondTex,
    bumpScale: 0.04,
    roughness: 0.38,
    metalness: 0.32,
    color: 0xffffff,
    emissive: 0x052e42,
    emissiveIntensity: 0.22
  });

  // Central Stainless Steel Permeate Lumen Tube
  const lumenMat = new THREE.MeshStandardMaterial({
    color: 0xd8e2ec,
    metalness: 0.92,
    roughness: 0.22
  });

  // Realistic Transparent Aqua Liquid Splash Ribbon
  const aquaSplashMat = new THREE.MeshPhysicalMaterial({
    color: 0x00d2ff,
    emissive: 0x005577,
    emissiveIntensity: 0.14,
    transmission: 0.88,
    opacity: 0.92,
    transparent: true,
    roughness: 0.05,
    ior: 1.333,
    reflectivity: 0.96,
    clearcoat: 1.0,
    clearcoatRoughness: 0.03
  });

  // 6. Floating Liquid Droplet Spheres (Complementing the splash)
  const dropletMat = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    transmission: 0.92,
    roughness: 0.03,
    ior: 1.333,
    transparent: true,
    opacity: 0.95
  });

  const droplets = [];
  const dropletGroup = new THREE.Group();
  for (let i = 0; i < 35; i++) {
    const radius = 0.04 + Math.random() * 0.10;
    const dropGeo = new THREE.SphereGeometry(radius, 14, 14);
    const dropMesh = new THREE.Mesh(dropGeo, dropletMat);

    const angle = Math.random() * Math.PI * 2.8 - 0.5;
    const y = 4.2 - (i / 35) * 8.4 + (Math.random() - 0.5) * 0.5;
    const r = 1.75 + (Math.random() - 0.5) * 0.6;
    dropMesh.position.set(r * Math.cos(angle), y, r * Math.sin(angle));
    dropletGroup.add(dropMesh);

    droplets.push({
      mesh: dropMesh,
      basePos: dropMesh.position.clone(),
      phase: Math.random() * Math.PI * 2,
      speed: 1.0 + Math.random() * 1.5,
      amp: 0.08 + Math.random() * 0.12
    });
  }
  floatingGroup.add(dropletGroup);

  // 7. Load the Detailed 3D GLB Model using GLTFLoader
  let isGlbLoaded = false;

  if (typeof THREE.GLTFLoader !== 'undefined') {
    const loader = new THREE.GLTFLoader();
    loader.load(
      '/static/models/water_purifier_cartridge.glb',
      (gltf) => {
        const model = gltf.scene;

        // Traverse and assign materials based on part names
        model.traverse((child) => {
          if (child.isMesh) {
            const name = child.name || '';
            if (name.includes('TopCap') || name.includes('BottomCap')) {
              child.material = steelMat;
            } else if (name.includes('AcrylicHousing')) {
              child.material = acrylicGlassMat;
            } else if (name.includes('InternalROMembrane')) {
              child.material = membraneMat;
            } else if (name.includes('PermeateCollector')) {
              child.material = lumenMat;
            } else if (name.includes('AccentRing')) {
              child.material = collarMat;
            } else if (name.includes('AquaLiquidSplash')) {
              child.material = aquaSplashMat;
            } else {
              child.material = steelMat;
            }
            child.castShadow = false;
            child.receiveShadow = false;
          }
        });

        purifierSpinGroup.add(model);
        isGlbLoaded = true;
        console.log('AquaGuard IQ: GLB Product Model successfully loaded and configured');
      },
      undefined,
      (error) => {
        console.error('Failed to load GLB model:', error);
      }
    );
  } else {
    console.warn('THREE.GLTFLoader not available');
  }

  // 8. Interactive Cursor Parallax
  const heroSection = document.getElementById('hero-landing');
  let targetParallaxX = 0;
  let targetParallaxY = 0;
  let currentParallaxX = 0;
  let currentParallaxY = 0;

  if (heroSection) {
    heroSection.addEventListener('mousemove', (e) => {
      const rect = heroSection.getBoundingClientRect();
      targetParallaxX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.35;
      targetParallaxY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.35;
    });

    heroSection.addEventListener('mouseleave', () => {
      targetParallaxX = 0;
      targetParallaxY = 0;
    });
  }

  // 9. Animation Loop (Smooth 12-15s Full Revolution & Gentle Floating)
  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsedTime = clock.getElapsedTime();

    // A. CONTINUOUS SMOOTH 3D Y-AXIS ROTATION
    // Speed: 0.46 rad/s -> ~13.6 seconds per full 360-degree revolution
    purifierSpinGroup.rotation.y += delta * 0.46;

    // B. SUBTLE FLOATING BUOYANCY MOVEMENT
    floatingGroup.position.y = Math.sin(elapsedTime * 1.15) * 0.09;
    floatingGroup.position.x = Math.cos(elapsedTime * 0.85) * 0.03;
    floatingGroup.rotation.z = Math.sin(elapsedTime * 0.75) * 0.015;

    // C. LIQUID DROPLETS BOBBING
    for (let i = 0; i < droplets.length; i++) {
      const d = droplets[i];
      d.mesh.position.y = d.basePos.y + Math.sin(elapsedTime * d.speed + d.phase) * d.amp;
    }

    // D. SMOOTH CURSOR PARALLAX
    currentParallaxX += (targetParallaxX - currentParallaxX) * 0.05;
    currentParallaxY += (targetParallaxY - currentParallaxY) * 0.05;

    pivotRoot.rotation.x = 0.22 - currentParallaxY;
    pivotRoot.rotation.y = 0.26 + currentParallaxX;

    renderer.render(scene, camera);
  }

  animate();

  // 10. Responsive Window Resizing
  window.addEventListener('resize', () => {
    if (!container) return;
    width = container.clientWidth;
    height = container.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  });
});
