/* ============================================================
   SRDS Lost & Found — main.js
   Features: Custom cursor, scroll reveals, particles,
   page transitions, dark/light mode, bookmarks, counter animations
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ===================== CUSTOM CURSOR ===================== */
  const cursor = document.querySelector('.cursor');
  const ring   = document.querySelector('.cursor-ring');

  if (cursor && ring && window.innerWidth > 640) {
    let mx = 0, my = 0, rx = 0, ry = 0;

    document.addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY;
      cursor.style.left = mx + 'px';
      cursor.style.top  = my + 'px';
    });

    // Smooth ring follow
    const followRing = () => {
      rx += (mx - rx) * 0.12;
      ry += (my - ry) * 0.12;
      ring.style.left = rx + 'px';
      ring.style.top  = ry + 'px';
      requestAnimationFrame(followRing);
    };
    followRing();

    // Scale on interactive elements
    const interactives = document.querySelectorAll('a, button, .card, .bookmark-btn, input, select, textarea');
    interactives.forEach(el => {
      el.addEventListener('mouseenter', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(2)';
        cursor.style.opacity = '0.5';
      });
      el.addEventListener('mouseleave', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(1)';
        cursor.style.opacity = '1';
      });
    });
  }

  /* ===================== NAV SCROLL ===================== */
  const nav = document.querySelector('nav');
  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ===================== MOBILE NAV ===================== */
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    // Close on link click
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
  }

  /* ===================== PARTICLES ===================== */
  const particleContainer = document.querySelector('.particles');
  if (particleContainer) {
    const count = window.innerWidth < 640 ? 20 : 45;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('div');
      p.classList.add('particle');
      const size = Math.random() * 3 + 1;
      p.style.cssText = `
        left: ${Math.random() * 100}%;
        width: ${size}px;
        height: ${size}px;
        opacity: ${Math.random() * 0.5 + 0.1};
        animation-duration: ${Math.random() * 20 + 15}s;
        animation-delay: ${Math.random() * -25}s;
      `;
      particleContainer.appendChild(p);
    }
  }

  /* ===================== SCROLL REVEAL ===================== */
  const reveals = document.querySelectorAll('.reveal');
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  reveals.forEach(el => revealObs.observe(el));

  /* ===================== COUNTER ANIMATION ===================== */
  const counters = document.querySelectorAll('.stat-number[data-target]');
  const counterObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        const duration = 1800;
        const start = performance.now();
        const animate = (now) => {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          // Ease out cubic
          const eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(eased * target);
          if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
        counterObs.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(el => counterObs.observe(el));

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
      themeBtn.style.transform = 'rotate(360deg)';
      setTimeout(() => themeBtn.style.transform = '', 400);
    });
  }

  /* ===================== BOOKMARKS ===================== */
  const getBookmarks = () => JSON.parse(localStorage.getItem('srds-bookmarks') || '[]');
  const saveBookmarks = (arr) => localStorage.setItem('srds-bookmarks', JSON.stringify(arr));

  const updateBookmarkBadge = () => {
    const badge = document.querySelector('.bookmark-count');
    if (badge) {
      const count = getBookmarks().length;
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  };

  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    const id = btn.dataset.id;
    const bookmarks = getBookmarks();
    if (bookmarks.includes(id)) { btn.classList.add('saved'); btn.textContent = '🔖'; }

    btn.addEventListener('click', () => {
      let bm = getBookmarks();
      if (bm.includes(id)) {
        bm = bm.filter(x => x !== id);
        btn.classList.remove('saved');
        btn.textContent = '🏷️';
        showToast('Bookmark removed', 'info');
      } else {
        bm.push(id);
        btn.classList.add('saved');
        btn.textContent = '🔖';
        showToast('Item bookmarked! Check your saved items.', 'success');
        // Bounce animation
        btn.style.transform = 'scale(1.4)';
        setTimeout(() => btn.style.transform = '', 300);
      }
      saveBookmarks(bm);
      updateBookmarkBadge();
    });
  });
  updateBookmarkBadge();

  /* ===================== PAGE TRANSITIONS ===================== */
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed; inset: 0; background: var(--navy-mid);
    z-index: 9000; pointer-events: none;
    transform: scaleY(0); transform-origin: bottom;
    transition: transform 0.35s cubic-bezier(0.76, 0, 0.24, 1);
  `;
  document.body.appendChild(overlay);

  document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="mailto"])').forEach(link => {
    if (!link.href || link.href.startsWith('javascript')) return;
    link.addEventListener('click', e => {
      const dest = link.href;
      if (dest === window.location.href) return;
      e.preventDefault();
      overlay.style.transformOrigin = 'bottom';
      overlay.style.transform = 'scaleY(1)';
      setTimeout(() => { window.location.href = dest; }, 350);
    });
  });

  // Reveal on load
  overlay.style.transformOrigin = 'top';
  overlay.style.transform = 'scaleY(1)';
  requestAnimationFrame(() => {
    setTimeout(() => { overlay.style.transform = 'scaleY(0)'; }, 50);
  });

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
      const c = document.createElement('div');
      c.className = 'flash-container';
      document.body.appendChild(c);
      return c;
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

  /* ===================== SMOOTH PARALLAX HERO ===================== */
  const heroBg = document.querySelector('.hero-bg');
  if (heroBg) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      heroBg.style.transform = `translateY(${y * 0.4}px)`;
    }, { passive: true });
  }

  /* ===================== SEARCH KEYBOARD SHORTCUT ===================== */
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.getElementById('searchInput');
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      } else {
        window.location.href = '/items';
      }
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
          field.addEventListener('input', () => {
            field.style.borderColor = '';
            field.style.boxShadow = '';
          }, { once: true });
        }
      });
      if (!valid) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });
  });

  /* ===================== STATS SECTION HOVER ===================== */
  document.querySelectorAll('.stat-box').forEach(box => {
    box.addEventListener('mouseenter', () => {
      box.style.boxShadow = '0 0 24px var(--accent-glow)';
    });
    box.addEventListener('mouseleave', () => {
      box.style.boxShadow = '';
    });
  });

});
