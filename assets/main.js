/* ============================================
   PAISA POCKET — Main Interactions
   3D card tilt • Scroll reveal • Smooth UX
   ============================================ */

(function(){
  'use strict';

  var ticking = false;
  function rafTick(fn){
    if(!ticking){
      ticking = true;
      requestAnimationFrame(function(){
        fn();
        ticking = false;
      });
    }
  }

  function initTilt(){
    document.querySelectorAll('.card, .product-card').forEach(function(el){
      el.style.willChange = 'transform';
      el.addEventListener('mousemove', function(e){
        var rect = el.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var cx = rect.width / 2;
        var cy = rect.height / 2;
        var rotX = ((y - cy) / cy) * -6;
        var rotY = ((x - cx) / cx) * 6;
        el.style.transform = 'perspective(900px) rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg) translateY(-6px) scale(1.01)';
        el.style.boxShadow = '0 20px 40px rgba(0,0,0,.35)';
      });
      el.addEventListener('mouseleave', function(){
        el.style.transform = '';
        el.style.boxShadow = '';
        el.style.willChange = 'auto';
      });
    });
  }

  function initReveal(){
    if(!('IntersectionObserver' in window)) return;
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {threshold:0.08, rootMargin:'0px 0px -30px 0px'});

    document.querySelectorAll(
      '.card, .product-card, .quiz-card, .tool-card, .newsletter-card, .dashboard-hook, .section-header, .cta-section'
    ).forEach(function(el){
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  function animateCounters(){
    document.querySelectorAll('[data-count]').forEach(function(el){
      var target = parseInt(el.getAttribute('data-count'),10);
      var duration = 1400;
      var start = null;
      function step(ts){
        if(!start) start = ts;
        var progress = Math.min((ts - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(eased * target).toLocaleString('en-IN');
        if(progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  function initNavShadow(){
    var header = document.querySelector('header.site');
    if(!header) return;
    window.addEventListener('scroll', function(){
      rafTick(function(){
        if(window.scrollY > 20){
          header.classList.add('scrolled');
        } else {
          header.classList.remove('scrolled');
        }
      });
    }, {passive:true});
  }

  function initAll(){
    initTilt();
    initReveal();
    initNavShadow();
    animateCounters();
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
