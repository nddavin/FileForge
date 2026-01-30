import React, { useEffect, useRef } from 'react';

export function GlowingSphere3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    // Mouse position
    let mouseX = width / 2;
    let mouseY = height / 2;
    let targetRotationX = 0;
    let targetRotationY = 0;
    let currentRotationX = 0;
    let currentRotationY = 0;

    // Sphere parameters
    const sphereRadius = 150;
    const segments = 32;
    const rings = 24;
    const rotationSpeed = 0.005;
    const glowLayers = 6;

    // Generate sphere vertices
    function generateSphere() {
      const vertices: { x: number; y: number; z: number }[] = [];
      const indices: number[] = [];

      for (let ring = 0; ring <= rings; ring++) {
        const theta = (ring * Math.PI) / rings;
        const sinTheta = Math.sin(theta);
        const cosTheta = Math.cos(theta);

        for (let segment = 0; segment <= segments; segment++) {
          const phi = (segment * 2 * Math.PI) / segments;
          const sinPhi = Math.sin(phi);
          const cosPhi = Math.cos(phi);

          const x = cosPhi * sinTheta;
          const y = cosTheta;
          const z = sinPhi * sinTheta;

          vertices.push({ x, y, z });
        }
      }

      for (let ring = 0; ring < rings; ring++) {
        for (let segment = 0; segment < segments; segment++) {
          const first = ring * (segments + 1) + segment;
          const second = first + segments + 1;

          indices.push(first, second, first + 1);
          indices.push(second, second + 1, first + 1);
        }
      }

      return { vertices, indices };
    }

    const sphere = generateSphere();

    // Project 3D to 2D
    function project(vertex: { x: number; y: number; z: number }, rotationX: number, rotationY: number) {
      let x = vertex.x;
      let y = vertex.y;
      let z = vertex.z;

      // Rotate around X axis
      const cosX = Math.cos(rotationX);
      const sinX = Math.sin(rotationX);
      const tempY = y * cosX - z * sinX;
      const tempZ = y * sinX + z * cosX;
      y = tempY;
      z = tempZ;

      // Rotate around Y axis
      const cosY = Math.cos(rotationY);
      const sinY = Math.sin(rotationY);
      const tempX = x * cosY - z * sinY;
      const tempZ2 = x * sinY + z * cosY;
      x = tempX;
      z = tempZ2;

      // Perspective projection
      const perspective = 500;
      const scale = perspective / (perspective + z * sphereRadius);

      return {
        x: x * sphereRadius * scale + width / 2,
        y: y * sphereRadius * scale + height / 2,
        z: z,
        scale: scale
      };
    }

    // Check if a face is visible (backface culling)
    function isFaceVisible(v1: { x: number; y: number }, v2: { x: number; y: number }, v3: { x: number; y: number }) {
      return (v2.x - v1.x) * (v3.y - v1.y) - (v2.y - v1.y) * (v3.x - v1.x) < 0;
    }

    let animationId: number;

    // Draw function
    function draw() {
      ctx.fillStyle = 'rgba(10, 10, 26, 1)';
      ctx.fillRect(0, 0, width, height);

      // Add subtle background glow
      const gradient = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, 400);
      gradient.addColorStop(0, 'rgba(100, 150, 255, 0.1)');
      gradient.addColorStop(1, 'rgba(10, 10, 26, 0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);

      // Smooth rotation interpolation
      currentRotationX += (targetRotationX - currentRotationX) * 0.05;
      currentRotationY += (targetRotationY - currentRotationY) * 0.05;

      // Auto rotation
      currentRotationY += rotationSpeed;

      // Project all vertices
      const projected = sphere.vertices.map(v => project(v, currentRotationX, currentRotationY));

      // Calculate center of sphere for mouse interaction
      const centerX = width / 2;
      const centerY = height / 2;

      // Calculate distance from mouse to sphere center
      const mouseDistance = Math.sqrt(Math.pow(mouseX - centerX, 2) + Math.pow(mouseY - centerY, 2));

      // Calculate mouse influence on rotation
      const mouseInfluenceX = (mouseX - centerX) / width * 2;
      const mouseInfluenceY = (mouseY - centerY) / height * 2;
      targetRotationX += mouseInfluenceY * 0.002;
      targetRotationY += mouseInfluenceX * 0.002;

      // Draw glow layers
      for (let layer = glowLayers; layer > 0; layer--) {
        const glowScale = 1 + layer * 0.08;
        const glowOpacity = 0.03 * (glowLayers - layer + 1);

        ctx.strokeStyle = `rgba(100, 180, 255, ${glowOpacity})`;
        ctx.lineWidth = 2;

        for (let i = 0; i < sphere.indices.length; i += 3) {
          const v1 = projected[sphere.indices[i]];
          const v2 = projected[sphere.indices[i + 1]];
          const v3 = projected[sphere.indices[i + 2]];

          if (v1.z < 0.5 && v2.z < 0.5 && v3.z < 0.5) {
            // Scale positions for glow effect
            const gx1 = (v1.x - centerX) * glowScale + centerX;
            const gy1 = (v1.y - centerY) * glowScale + centerY;
            const gx2 = (v2.x - centerX) * glowScale + centerX;
            const gy2 = (v2.y - centerY) * glowScale + centerY;
            const gx3 = (v3.x - centerX) * glowScale + centerX;
            const gy3 = (v3.y - centerY) * glowScale + centerY;

            ctx.beginPath();
            ctx.moveTo(gx1, gy1);
            ctx.lineTo(gx2, gy2);
            ctx.lineTo(gx3, gy3);
            ctx.closePath();
            ctx.stroke();
          }
        }
      }

      // Store face depths for sorting
      const faces: { v1: ReturnType<typeof project>; v2: ReturnType<typeof project>; v3: ReturnType<typeof project>; avgZ: number; avgScale: number }[] = [];

      for (let i = 0; i < sphere.indices.length; i += 3) {
        const v1 = projected[sphere.indices[i]];
        const v2 = projected[sphere.indices[i + 1]];
        const v3 = projected[sphere.indices[i + 2]];

        const avgZ = (v1.z + v2.z + v3.z) / 3;
        const avgScale = (v1.scale + v2.scale + v3.scale) / 3;

        faces.push({ v1, v2, v3, avgZ, avgScale });
      }

      // Sort faces by depth (back to front)
      faces.sort((a, b) => a.avgZ - b.avgZ);

      // Draw faces
      faces.forEach(face => {
        if (face.avgZ < 0.5) {
          // Calculate lighting based on position
          const lighting = Math.max(0.2, (face.avgZ + 1) / 2);
          
          // Calculate color based on mouse distance
          const mouseFactor = Math.max(0, 1 - mouseDistance / 400);
          const baseR = Math.floor(100 + mouseFactor * 100);
          const baseG = Math.floor(150 + mouseFactor * 80);
          const baseB = 255;

          const r = Math.floor(baseR * lighting);
          const g = Math.floor(baseG * lighting);
          const b = Math.floor(baseB * lighting);

          // Check if face should be drawn
          if (isFaceVisible(face.v1, face.v2, face.v3)) {
            // Create gradient for each face
            const gradient = ctx.createLinearGradient(face.v1.x, face.v1.y, face.v3.x, face.v3.y);
            
            const alpha = 0.7 + face.avgScale * 0.3;
            gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha})`);
            gradient.addColorStop(0.5, `rgba(${r - 20}, ${g - 20}, ${b - 20}, ${alpha * 0.8})`);
            gradient.addColorStop(1, `rgba(${r - 40}, ${g - 40}, ${b - 40}, ${alpha * 0.6})`);

            ctx.beginPath();
            ctx.moveTo(face.v1.x, face.v1.y);
            ctx.lineTo(face.v2.x, face.v2.y);
            ctx.lineTo(face.v3.x, face.v3.y);
            ctx.closePath();
            ctx.fillStyle = gradient;
            ctx.fill();

            // Add subtle stroke
            ctx.strokeStyle = `rgba(${r + 50}, ${g + 50}, ${b + 50}, ${alpha * 0.3})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      });

      // Draw core glow
      const coreGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, sphereRadius * 1.5);
      const coreAlpha = 0.15 + Math.sin(Date.now() * 0.003) * 0.05;
      coreGradient.addColorStop(0, `rgba(150, 200, 255, ${coreAlpha})`);
      coreGradient.addColorStop(0.5, `rgba(100, 150, 255, ${coreAlpha * 0.5})`);
      coreGradient.addColorStop(1, 'rgba(100, 150, 255, 0)');

      ctx.fillStyle = coreGradient;
      ctx.fillRect(0, 0, width, height);

      animationId = requestAnimationFrame(draw);
    }

    // Event listeners
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      mouseX = e.touches[0].clientX;
      mouseY = e.touches[0].clientY;
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    window.addEventListener('resize', handleResize);

    // Start animation
    draw();

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div style={{ 
      position: 'relative', 
      width: '100%', 
      height: '100vh', 
      background: 'linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%)',
      overflow: 'hidden'
    }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />
      <div style={{
        position: 'absolute',
        bottom: '30px',
        left: '50%',
        transform: 'translateX(-50%)',
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: '14px',
        textAlign: 'center',
        pointerEvents: 'none',
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
      }}>
        Move your mouse to interact with the sphere
      </div>
    </div>
  );
}

export default GlowingSphere3D;
