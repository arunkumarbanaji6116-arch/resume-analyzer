// Spatial UI Dynamic Specular Lighting & 3D Tilt Engine
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.workspace-card, .panel, .auth-card, .features article, .phase-card, .interview-header-card');

  cards.forEach(card => {
    card.classList.add('spatial-glow-surface');

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      card.style.setProperty('--mouse-x', ${x}px);
      card.style.setProperty('--mouse-y', ${y}px);

      // Apply 3D perspective tilt on workspace cards
      if (card.classList.contains('workspace-card')) {
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -5;
        const rotateY = ((x - centerX) / centerX) * 5;

        card.style.transform = perspective(1000px) rotateX(deg) rotateY(deg) translateY(-8px) scale3d(1.015, 1.015, 1.015);
      }
    });

    card.addEventListener('mouseleave', () => {
      if (card.classList.contains('workspace-card')) {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0) scale3d(1, 1, 1)';
      }
    });
  });
});
