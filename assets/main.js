/* ============================================
   PAISA POCKET — Main Interactions
   3D card tilt • Scroll reveal • Smooth UX
   ============================================ */

(function(){
  'use strict';

  // ---------- 3D Card Tilt ----------
  function initTilt(){
    document.querySelectorAll('.card, .product-card').forEach(function(el){
      el.addEventListener('mousemove', function(e){
        var rect = el.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var cx = rect.width / 2;
        var cy = rect.height / 2;
        var rotX = ((y - cy) / cy) * -8;
        var rotY = ((x - cx) / cx) * 8;
        el.style.transform = 'perspective(800px) rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg) translateY(-4px)';
      });
      el.addEventListener('mouseleave', function(){
        el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0px)';
      });
    });
  }

  // ---------- Scroll Reveal ----------
  function initReveal(){
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {threshold:0.1, rootMargin:'0px 0px -40px 0px'});

    document.querySelectorAll(
      '.card, .product-card, .quiz-card, .tool-card, .newsletter-card, .dashboard-hook, .section-header, .cta-section'
    ).forEach(function(el){
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  // ---------- Smooth counter animation ----------
  function animateCounters(){
    document.querySelectorAll('[data-count]').forEach(function(el){
      var target = parseInt(el.getAttribute('data-count'),10);
      var duration = 1500;
      var start = performance.now();
      function step(now){
        var progress = Math.min((now - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(eased * target).toLocaleString('en-IN');
        if(progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  // ---------- Sticky nav shadow on scroll ----------
  function initNavShadow(){
    var header = document.querySelector('header.site');
    if(!header) return;
    window.addEventListener('scroll', function(){
      if(window.scrollY > 20){
        header.style.boxShadow = '0 4px 30px rgba(0,0,0,.35)';
      } else {
        header.style.boxShadow = 'none';
      }
    }, {passive:true});
  }

  // ---------- Initialize ----------
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  function initAll(){
    initTilt();
    initReveal();
    initNavShadow();
    animateCounters();
  }

  // Expose for external use
  window.PaisaPocket = {
    refreshTilt: initTilt,
    refreshReveal: initReveal
  };
})();
