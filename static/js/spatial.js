// Spatial UI Dynamic Specular Lighting & 3D Tilt Engine + Universal Dropzone Controller
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.workspace-card, .panel, .auth-card, .features article, .phase-card, .interview-header-card');

  cards.forEach(card => {
    card.classList.add('spatial-glow-surface');

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);

      // Apply 3D perspective tilt on workspace cards
      if (card.classList.contains('workspace-card')) {
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -5;
        const rotateY = ((x - centerX) / centerX) * 5;

        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px) scale3d(1.015, 1.015, 1.015)`;
      }
    });

    card.addEventListener('mouseleave', () => {
      if (card.classList.contains('workspace-card')) {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0) scale3d(1, 1, 1)';
      }
    });
  });

  // Universal Dropzone Controller (Tap Logo to Upload)
  initUploadDropzones();

  // Universal Theme Controller (Dark / Light toggle)
  initThemeController();

  // Zero-Latency Navigation & Instant Prefetch Engine
  initZeroLatencyNavigation();

  // Instant Form Submit Feedback
  initInstantFormFeedback();
});

function initThemeController() {
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const sunIcon = document.getElementById("theme-icon-sun");
  const moonIcon = document.getElementById("theme-icon-moon");

  function updateThemeIcons(isDark) {
    if (sunIcon) {
      sunIcon.style.display = isDark ? "block" : "none";
    }
    if (moonIcon) {
      moonIcon.style.display = isDark ? "none" : "block";
    }
    if (themeToggleBtn) {
      const label = isDark ? "Switch to light theme" : "Switch to dark theme";
      themeToggleBtn.setAttribute("title", label);
      themeToggleBtn.setAttribute("aria-label", label);
    }
  }

  // Determine theme state on load
  const isCurrentlyDark = document.documentElement.classList.contains("dark");
  updateThemeIcons(isCurrentlyDark);

  if (themeToggleBtn) {
    // Avoid double listeners
    if (themeToggleBtn.dataset.bound === "true") return;
    themeToggleBtn.dataset.bound = "true";

    themeToggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const willBeDark = !document.documentElement.classList.contains("dark");
      if (willBeDark) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("careerforge_theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("careerforge_theme", "light");
      }
      updateThemeIcons(willBeDark);
    });
  }
}

function initUploadDropzones() {
  const dropzones = document.querySelectorAll('.upload-dropzone');

  dropzones.forEach(zone => {
    const fileInput = zone.querySelector('input[type="file"]');
    if (!fileInput) return;

    const badge = zone.querySelector('.dropzone-icon-badge');
    let statusContainer = zone.querySelector('.dropzone-file-status');
    if (!statusContainer) {
      statusContainer = document.createElement('div');
      statusContainer.className = 'dropzone-file-status';
      zone.appendChild(statusContainer);
    }

    const formatBytes = (bytes) => {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const updateFileDisplay = (file) => {
      if (!file) {
        statusContainer.innerHTML = '';
        zone.classList.remove('has-file');
        return;
      }
      zone.classList.add('has-file');
      const ext = file.name ? file.name.split('.').pop().toLowerCase() : '';
      let chipIconHtml = '✓';
      if (ext === 'pdf') chipIconHtml = '📄';
      else if (ext === 'docx' || ext === 'doc') chipIconHtml = '📝';

      statusContainer.innerHTML = `
        <div class="selected-file-chip">
          <div class="chip-icon">${chipIconHtml}</div>
          <div class="chip-details">
            <span class="chip-name" title="${file.name}">${file.name}</span>
            <span class="chip-size">${formatBytes(file.size)}</span>
          </div>
          <button type="button" class="chip-remove-btn" title="Remove selected file" aria-label="Remove file">&times;</button>
        </div>
      `;

      // If file is an image, preview thumbnail in chip icon
      if (file.type && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const icon = statusContainer.querySelector('.chip-icon');
          if (icon && e.target && e.target.result) {
            icon.innerHTML = `<img src="${e.target.result}" alt="Preview" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
          }
        };
        reader.readAsDataURL(file);
      }

      const removeBtn = statusContainer.querySelector('.chip-remove-btn');
      if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          fileInput.value = '';
          updateFileDisplay(null);
          const imgPreviewContainer = zone.querySelector('#image-preview-container');
          if (imgPreviewContainer) {
            imgPreviewContainer.style.display = 'none';
          }
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        });
      }
    };

    // Tap on logo badge triggers file chooser
    if (badge) {
      badge.setAttribute('role', 'button');
      badge.setAttribute('tabindex', '0');
      badge.setAttribute('title', 'Tap logo to upload');
      badge.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
      });
      badge.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          fileInput.click();
        }
      });
    }

    // Clicking anywhere inside dropzone (except interactive elements) triggers file input
    zone.addEventListener('click', (e) => {
      if (e.target.closest('.chip-remove-btn') || e.target.closest('button') || e.target.closest('a')) {
        return;
      }
      fileInput.click();
    });

    // File selected via dialog
    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      updateFileDisplay(file);
    });

    // Drag and drop support
    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.add('drag-active');
    });

    zone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.remove('drag-active');
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.remove('drag-active');
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        const file = fileInput.files[0];
        updateFileDisplay(file);
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });
}

// ==========================================================================
// Zero-Latency Navigation & Instant Prefetch Engine
// ==========================================================================

function initZeroLatencyNavigation() {
  // 1. Register Service Worker for 0ms Asset Serving
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }

  const prefetchedUrls = new Set();
  const currentOrigin = window.location.origin;

  function canPrefetch(urlStr) {
    if (!urlStr) return false;
    try {
      const url = new URL(urlStr, currentOrigin);
      if (url.origin !== currentOrigin) return false;
      if (url.pathname === window.location.pathname) return false;
      if (url.pathname.includes('logout') || url.pathname.includes('download') || url.pathname.includes('delete')) return false;
      if (url.hash && url.pathname === window.location.pathname) return false;
      return true;
    } catch (e) {
      return false;
    }
  }

  function prefetch(urlStr) {
    if (!canPrefetch(urlStr)) return;
    const url = new URL(urlStr, currentOrigin).pathname;
    if (prefetchedUrls.has(url)) return;
    prefetchedUrls.add(url);

    // Native link prefetch
    const linkEl = document.createElement('link');
    linkEl.rel = 'prefetch';
    linkEl.href = url;
    linkEl.as = 'document';
    document.head.appendChild(linkEl);

    // Low-priority HTTP cache warm-up
    if ('fetch' in window) {
      fetch(url, { priority: 'low', credentials: 'same-origin' }).catch(() => {});
    }
  }

  // Idle background prefetch of core workspace tools
  const idlePrefetch = () => {
    const coreRoutes = ['/dashboard', '/builder', '/interview', '/jobs'];
    coreRoutes.forEach((route) => {
      if (route !== window.location.pathname) {
        prefetch(route);
      }
    });
  };

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(idlePrefetch, { timeout: 1500 });
  } else {
    setTimeout(idlePrefetch, 800);
  }

  // Instant hover & touch anticipation (fires ~150ms before click)
  document.addEventListener('mouseover', (e) => {
    const link = e.target.closest('a[href]');
    if (link && canPrefetch(link.href)) {
      prefetch(link.href);
    }
  }, { passive: true });

  document.addEventListener('touchstart', (e) => {
    const link = e.target.closest('a[href]');
    if (link && canPrefetch(link.href)) {
      prefetch(link.href);
    }
  }, { passive: true });
}

function initInstantFormFeedback() {
  document.querySelectorAll('form').forEach((form) => {
    if (form.dataset.instantFeedbackBound === 'true') return;
    form.dataset.instantFeedbackBound = 'true';

    form.addEventListener('submit', () => {
      const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.style.opacity = '0.92';
        submitBtn.style.pointerEvents = 'none';
        if (submitBtn.tagName.toLowerCase() === 'button') {
          const setBtnState = (text) => {
            submitBtn.innerHTML = '<span style="display:inline-flex; align-items:center; justify-content:center; gap:8px;">' +
              '<svg style="animation: spin 0.75s linear infinite;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>' +
              text + '</span>';
          };
          setBtnState('⚡ Reading & parsing document...');
          setTimeout(() => setBtnState('⚡ Matching competencies & skills...'), 1100);
          setTimeout(() => setBtnState('⚡ Synthesizing ATS score...'), 2400);
        }
      }
    });
  });
}

