/* ============================================================
   SRDS Lost & Found - main.js v4
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const sunSVG  = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
  const moonSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

  /* ===================== PAGE TRANSITIONS ===================== */
  // Fade + lift on exit, fade + drop on enter
  // ── PAGE TRANSITION CURTAIN ──────────────────────────────
  // A fixed dark overlay that fades out on load and fades in on navigation.
  // Using hardcoded hex so CSS variables don't need to resolve first.
  const isDark = !document.body.classList.contains('light-mode');
  const curtain = document.createElement('div');
  curtain.id = 'page-curtain';
  Object.assign(curtain.style, {
    position:   'fixed',
    inset:      '0',
    zIndex:     '9999',
    background: '#05091a',
    opacity:    '1',
    transition: 'none',
    pointerEvents: 'none',
  });
  document.body.appendChild(curtain);

  // Tick twice so the browser registers opacity:1 before we animate to 0
  requestAnimationFrame(() => requestAnimationFrame(() => {
    curtain.style.transition = 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
    curtain.style.opacity = '0';
  }));

  function navigateTo(dest) {
    curtain.style.transition = 'opacity 0.35s cubic-bezier(0.4, 0, 1, 1)';
    curtain.style.opacity = '1';
    curtain.style.pointerEvents = 'all';
    setTimeout(() => { window.location.href = dest; }, 360);
  }

  document.querySelectorAll('a').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (link.target === '_blank') return;
    if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript')) return;
    link.addEventListener('click', e => {
      const dest = link.href;
      if (!dest || dest === window.location.href) return;
      try {
        const u = new URL(dest);
        if (u.hash && u.pathname === window.location.pathname) return;
        // Only intercept same-origin links
        if (u.origin !== window.location.origin) return;
      } catch { return; }
      e.preventDefault();
      navigateTo(dest);
    });
  });

  /* ===================== SCROLL REVEAL ===================== */
  // All .reveal elements start invisible in CSS.
  // We fire the observer with a generous rootMargin so animations
  // begin WELL before the element reaches the viewport - giving the
  // appearance of content rising up smoothly as you approach it.
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Small stagger based on position in its sibling group
          const siblings = Array.from(entry.target.parentElement?.children || []);
          const idx = siblings.filter(el => el.classList.contains('reveal')).indexOf(entry.target);
          const delay = Math.min(idx * 55, 200);
          setTimeout(() => entry.target.classList.add('visible'), delay);
          obs.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0,
      rootMargin: '0px 0px 160px 0px'  // fire 160px before bottom of viewport
    });
    reveals.forEach(el => obs.observe(el));
  }

  /* ===================== SPOTLIGHT CURSOR ===================== */
  const spotlight = document.getElementById('cursorSpotlight');
  if (spotlight && window.innerWidth > 900) {
    let tx = window.innerWidth / 2, ty = window.innerHeight / 2;
    let cx = tx, cy = ty;
    let running = true;

    document.addEventListener('mousemove', e => { tx = e.clientX; ty = e.clientY; }, { passive: true });

    const follow = () => {
      if (!running) return;
      cx += (tx - cx) * 0.06;
      cy += (ty - cy) * 0.06;
      spotlight.style.transform = `translate(calc(-50% + ${cx}px), calc(-50% + ${cy}px))`;
      requestAnimationFrame(follow);
    };
    spotlight.style.top = '0';
    spotlight.style.left = '0';
    follow();

    document.querySelectorAll('a, button, .card').forEach(el => {
      el.addEventListener('mouseenter', () => {
        spotlight.style.background = 'radial-gradient(circle, rgba(61,114,200,0.12) 0%, rgba(61,114,200,0.04) 40%, transparent 70%)';
      }, { passive: true });
      el.addEventListener('mouseleave', () => {
        spotlight.style.background = 'radial-gradient(circle, rgba(61,114,200,0.065) 0%, rgba(61,114,200,0.025) 40%, transparent 70%)';
      }, { passive: true });
    });

    document.addEventListener('visibilitychange', () => { running = !document.hidden; if (running) follow(); });
  } else {
    if (spotlight) spotlight.style.display = 'none';
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

  /* ===================== PARTICLES ===================== */
  const particleContainer = document.querySelector('.particles');
  if (particleContainer) {
    const count = window.innerWidth < 640 ? 6 : 12;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('div');
      p.classList.add('particle');
      const size = Math.random() * 2.5 + 1;
      p.style.cssText = `left:${Math.random()*100}%;width:${size}px;height:${size}px;opacity:${Math.random()*0.4+0.05};animation-duration:${Math.random()*25+20}s;animation-delay:${Math.random()*-30}s;`;
      particleContainer.appendChild(p);
    }
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
            el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
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
  if (saved === 'light') { document.body.classList.add('light-mode'); if (themeBtn) themeBtn.innerHTML = moonSVG; }
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      localStorage.setItem('srds-theme', isLight ? 'light' : 'dark');
      themeBtn.innerHTML = isLight ? moonSVG : sunSVG;
    });
  }

  /* ===================== BOOKMARKS ===================== */
  const getBookmarks  = () => JSON.parse(localStorage.getItem('srds-bookmarks') || '[]');
  const saveBookmarks = (arr) => localStorage.setItem('srds-bookmarks', JSON.stringify(arr));
  const svgBM  = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" style="width:13px;height:13px"><path d="M4 2h8a1 1 0 0 1 1 1v10l-5-3-5 3V3a1 1 0 0 1 1-1z"/></svg>';
  const svgBMS = '<svg viewBox="0 0 16 16" fill="currentColor" stroke="none" style="width:13px;height:13px"><path d="M4 2h8a1 1 0 0 1 1 1v10l-5-3-5 3V3a1 1 0 0 1 1-1z"/></svg>';

  const updateBookmarkBadge = () => {
    const badge = document.querySelector('.bookmark-count');
    if (badge) { const c = getBookmarks().length; badge.textContent = c; badge.style.display = c > 0 ? 'flex' : 'none'; }
  };

  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const id = btn.dataset.id;
    if (getBookmarks().includes(id)) { btn.classList.add('saved'); btn.innerHTML = svgBMS; }
    btn.addEventListener('click', () => {
      let bm = getBookmarks();
      if (bm.includes(id)) {
        bm = bm.filter(x => x !== id);
        btn.classList.remove('saved'); btn.innerHTML = svgBM;
        showToast('Bookmark removed');
      } else {
        bm.push(id);
        btn.classList.add('saved'); btn.innerHTML = svgBMS;
        showToast('Saved');
      }
      saveBookmarks(bm);
      updateBookmarkBadge();
    });
  });
  updateBookmarkBadge();

  /* ===================== FLASH AUTO-DISMISS ===================== */
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'all 0.5s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(120%)';
      setTimeout(() => el.remove(), 500);
    }, 4500);
  });

  /* ===================== TOAST ===================== */
  window.showToast = (msg, type = 'success') => {
    const container = document.querySelector('.flash-container') || (() => {
      const c = document.createElement('div'); c.className = 'flash-container';
      document.body.appendChild(c); return c;
    })();
    const toast = document.createElement('div');
    toast.className = `flash ${type}`;
    toast.innerHTML = msg;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'all 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(120%)';
      setTimeout(() => toast.remove(), 400);
    }, 2800);
  };

  /* ===================== PARALLAX HERO ===================== */
  const heroBg = document.querySelector('.hero-bg');
  if (heroBg) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          heroBg.style.transform = `translateY(${window.scrollY * 0.28}px)`;
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
          field.style.boxShadow = '0 0 0 3px rgba(220,38,38,0.18)';
          valid = false;
          field.addEventListener('input', () => { field.style.borderColor = ''; field.style.boxShadow = ''; }, { once: true });
        }
      });
      if (!valid) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });
  });

});
