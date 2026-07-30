function filterCards(q){{
  q=(q||'').toLowerCase();
  document.querySelectorAll('#card-grid .card').forEach(function(c){{
    var t=c.textContent.toLowerCase();
    c.style.display = t.indexOf(q)>=0 ? '' : 'none';
  }});
}}
function setCat(cat,btn){{
  document.querySelectorAll('#cat-chips .chip').forEach(function(b){{b.classList.remove('active');}});
  btn.classList.add('active');
  document.querySelectorAll('#card-grid .card').forEach(function(c){{
    c.style.display = (cat==='all'||c.dataset.cat===cat) ? '' : 'none';
  }});
}}
