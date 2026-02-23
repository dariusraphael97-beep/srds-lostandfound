/* ============================================================
   SRDS Lost & Found — main.js v3 (memory-safe)
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ===================== CUSTOM CURSOR ===================== */
  const cursor = document.querySelector('.cursor');
  const ring   = document.querySelector('.cursor-ring');

  if (cursor && ring && window.innerWidth > 900) {
    let mx = 0, my = 0, rx = 0, ry = 0;
    let rafId = null;
    let isVisible = true;

    document.addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY;
      cursor.style.left = mx + 'px';
      cursor.style.top  = my + 'px';
    }, { passive: true });

    const followRing = () => {
      if (!isVisible) return; // stop when tab hidden
      rx += (mx - rx) * 0.12;
      ry += (my - ry) * 0.12;
      ring.style.left = rx + 'px';
      ring.style.top  = ry + 'px';
      rafId = requestAnimationFrame(followRing);
    };
    rafId = requestAnimationFrame(followRing);

    // Pause when tab is hidden to prevent memory leak
    document.addEventListener('visibilitychange', () => {
      isVisible = !document.hidden;
      if (isVisible && !rafId) rafId = requestAnimationFrame(followRing);
    });

    document.querySelectorAll('a, button, .card, input, select, textarea').forEach(el => {
      el.addEventListener('mouseenter', () => { cursor.style.transform = 'translate(-50%,-50%) scale(2)'; cursor.style.opacity = '0.5'; });
      el.addEventListener('mouseleave', () => { cursor.style.transform = 'translate(-50%,-50%) scale(1)'; cursor.style.opacity = '1'; });
    });
  } else {
    // Hide cursor elements on mobile/tablet — they cause layout issues
    if (cursor) cursor.style.display = 'none';
    if (ring)   ring.style.display   = 'none';
  }

  /* ===================== NAV SCROLL ===================== */
  const nav = document.querySelector('nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ===================== MOBILE NAV ===================== */
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
  }

  /* ===================== PARTICLES (reduced, CSS-only) ===================== */
  const particleContainer = document.querySelector('.particles');
  if (particleContainer) {
    // Max 12 particles (was 45) — enough for the effect, won't crash
    const count = window.innerWidth < 640 ? 6 : 12;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('div');
      p.classList.add('particle');
      const size = Math.random() * 2.5 + 1;
      p.style.cssText = `left:${Math.random()*100}%;width:${size}px;height:${size}px;opacity:${Math.random()*0.4+0.05};animation-duration:${Math.random()*25+20}s;animation-delay:${Math.random()*-30}s;`;
      particleContainer.appendChild(p);
    }
  }

  /* ===================== SCROLL REVEAL ===================== */
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const revealObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObs.unobserve(entry.target); // unobserve immediately — no ongoing work
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
    reveals.forEach(el => revealObs.observe(el));
  }

  /* ===================== COUNTER ANIMATION ===================== */
  const counters = document.querySelectorAll('.stat-number[data-target]');
  if (counters.length) {
    const counterObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.dataset.target, 10);
          const start = performance.now();
          const animate = (now) => {
            const p = Math.min((now - start) / 1600, 1);
            el.textContent = Math.round((1 - Math.pow(1-p, 3)) * target);
            if (p < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
          counterObs.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => counterObs.observe(el));
  }

  /* ===================== DARK / LIGHT TOGGLE ===================== */
  const themeBtn = document.getElementById('themeToggle');
  const saved = localStorage.getItem('srds-theme');
  if (saved === 'light') { document.body.classList.add('light-mode'); if (themeBtn) themeBtn.textContent = '🌙'; }
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      localStorage.setItem('srds-theme', isLight ? 'light' : 'dark');
      themeBtn.textContent = isLight ? '🌙' : '☀️';
    });
  }

  /* ===================== BOOKMARKS ===================== */
  const getBookmarks  = () => JSON.parse(localStorage.getItem('srds-bookmarks') || '[]');
  const saveBookmarks = (arr) => localStorage.setItem('srds-bookmarks', JSON.stringify(arr));

  const updateBookmarkBadge = () => {
    const badge = document.querySelector('.bookmark-count');
    if (badge) { const c = getBookmarks().length; badge.textContent = c; badge.style.display = c > 0 ? 'flex' : 'none'; }
  };

  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const id = btn.dataset.id;
    if (getBookmarks().includes(id)) { btn.classList.add('saved'); btn.textContent = '🔖'; }
    btn.addEventListener('click', () => {
      let bm = getBookmarks();
      if (bm.includes(id)) {
        bm = bm.filter(x => x !== id);
        btn.classList.remove('saved'); btn.textContent = '🏷️';
        showToast('Bookmark removed', 'info');
      } else {
        bm.push(id);
        btn.classList.add('saved'); btn.textContent = '🔖';
        showToast('Item bookmarked!', 'success');
      }
      saveBookmarks(bm);
      updateBookmarkBadge();
    });
  });
  updateBookmarkBadge();

  /* ===================== PAGE TRANSITIONS ===================== */
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:var(--navy-mid);z-index:9000;pointer-events:none;transform:scaleY(0);transform-origin:bottom;transition:transform 0.3s cubic-bezier(0.76,0,0.24,1);';
  document.body.appendChild(overlay);

  document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="mailto"])').forEach(link => {
    if (!link.href || link.href.startsWith('javascript')) return;
    link.addEventListener('click', e => {
      if (link.href === window.location.href) return;
      e.preventDefault();
      const dest = link.href;
      overlay.style.transformOrigin = 'bottom';
      overlay.style.transform = 'scaleY(1)';
      setTimeout(() => { window.location.href = dest; }, 300);
    });
  });

  overlay.style.transformOrigin = 'top';
  overlay.style.transform = 'scaleY(1)';
  requestAnimationFrame(() => setTimeout(() => { overlay.style.transform = 'scaleY(0)'; }, 50));

  /* ===================== FLASH AUTO-DISMISS ===================== */
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'all 0.5s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(120%)';
      setTimeout(() => el.remove(), 500);
    }, 4500);
  });

  /* ===================== TOAST HELPER ===================== */
  window.showToast = (msg, type = 'success') => {
    const container = document.querySelector('.flash-container') || (() => {
      const c = document.createElement('div'); c.className = 'flash-container';
      document.body.appendChild(c); return c;
    })();
    const toast = document.createElement('div');
    toast.className = `flash ${type}`;
    toast.innerHTML = `${type === 'success' ? '✓' : 'ℹ'} ${msg}`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'all 0.5s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(120%)';
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  };

  /* ===================== PARALLAX HERO (throttled) ===================== */
  const heroBg = document.querySelector('.hero-bg');
  if (heroBg) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          heroBg.style.transform = `translateY(${window.scrollY * 0.3}px)`;
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  /* ===================== KEYBOARD SHORTCUTS ===================== */
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const s = document.getElementById('searchInput');
      if (s) { s.focus(); s.select(); } else window.location.href = '/items';
    }
  });

  /* ===================== FORM VALIDATION ===================== */
  document.querySelectorAll('form[data-validate]').forEach(form => {
    form.addEventListener('submit', e => {
      let valid = true;
      form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
          field.style.borderColor = 'var(--error)';
          field.style.boxShadow = '0 0 0 4px rgba(239,68,68,0.2)';
          valid = false;
          field.addEventListener('input', () => { field.style.borderColor = ''; field.style.boxShadow = ''; }, { once: true });
        }
      });
      if (!valid) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });
  });

});
