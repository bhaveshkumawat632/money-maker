function calcSavings() {
  var m = +document.getElementById('sc-monthly').value || 0;
  var y = +document.getElementById('sc-years').value || 0;
  var r = (+document.getElementById('sc-rate').value || 0) / 100 / 12;
  var n = y * 12;
  var fv = 0;
  if (r === 0) { fv = m * n; } else { fv = m * ((Math.pow(1 + r, n) - 1) / r) * (1 + r); }
  var amt = Math.round(fv).toLocaleString('en-IN');
  document.getElementById('sc-result').textContent = '{r1}'.replace('{{AMT}}', amt);
  if (window.navigator && navigator.sendBeacon) navigator.sendBeacon('/t.gif?e=calc');
}
function trackLead(e) { if (navigator.sendBeacon) navigator.sendBeacon('/t.gif?e=lead'); return true; }

/* SIP vs FD vs Gold Calculator */
function fmtINR(n) {
  if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2) + ' Cr';
  if (n >= 1e5) return '₹' + (n / 1e5).toFixed(2) + ' L';
  if (n >= 1e3) return '₹' + (n / 1e3).toFixed(2) + ' K';
  return '₹' + Math.round(n).toLocaleString('en-IN');
}
function fmtINRFull(n) {
  return '₹' + Math.round(n).toLocaleString('en-IN');
}
function calcCompare() {
  var m = parseFloat(document.getElementById('cmp-monthly').value) || 0;
  var y = parseInt(document.getElementById('cmp-years').value) || 0;
  var sipRate = parseFloat(document.getElementById('cmp-sip-rate').value) || 0;
  var fdRate = parseFloat(document.getElementById('cmp-fd-rate').value) || 0;
  var goldRate = parseFloat(document.getElementById('cmp-gold-rate').value) || 0;

  if (!m || !y) {
    document.getElementById('cmp-result').innerHTML = '<div class="cmp-warn">कृपया सभी फील्ड भरें।</div>';
    return;
  }

  var totalInvested = m * 12 * y;

  // SIP: monthly contributions with monthly rate
  var sipMonthlyRate = sipRate / 100 / 12;
  var sipN = y * 12;
  var sipFV = 0;
  if (sipMonthlyRate === 0) {
    sipFV = totalInvested;
  } else {
    sipFV = m * ((Math.pow(1 + sipMonthlyRate, sipN) - 1) / sipMonthlyRate) * (1 + sipMonthlyRate);
  }
  var sipProfit = sipFV - totalInvested;

  // FD: lump sum at annual compounding
  var fdFV = totalInvested * Math.pow(1 + fdRate / 100, y);
  var fdProfit = fdFV - totalInvested;

  // Gold: lump sum at annual appreciation
  var goldFV = totalInvested * Math.pow(1 + goldRate / 100, y);
  var goldProfit = goldFV - totalInvested;

  var results = [
    { name: 'SIP', fv: sipFV, profit: sipProfit, rate: sipRate, color: '#5b8cff' },
    { name: 'FD', fv: fdFV, profit: fdProfit, rate: fdRate, color: '#22d3a8' },
    { name: 'Gold', fv: goldFV, profit: goldProfit, rate: goldRate, color: '#ffb020' }
  ];
  results.sort(function(a, b) { return b.fv - a.fv; });
  var winner = results[0];

  var bars = results.map(function(r) {
    var pct = Math.max(5, Math.round((r.fv / winner.fv) * 100));
    var isWinner = r.name === winner.name;
    return '<div class="cmp-bar-row">' +
      '<div class="cmp-bar-label">' +
        '<span class="cmp-name" style="color:' + r.color + '">' + r.name + '</span>' +
        '<span class="cmp-rate">' + r.rate + '% p.a.</span>' +
        (isWinner ? '<span class="cmp-badge">🏆 विजेता</span>' : '') +
      '</div>' +
      '<div class="cmp-bar-track">' +
        '<div class="cmp-bar-fill" style="width:' + pct + '%;background:' + r.color + '"></div>' +
      '</div>' +
      '<div class="cmp-bar-values">' +
        '<div><strong>' + fmtINR(r.fv) + '</strong><br><small>कुल राशि</small></div>' +
        '<div class="cmp-profit"><strong>' + fmtINR(r.profit) + '</strong><br><small>लाभ</small></div>' +
      '</div>' +
    '</div>';
  }).join('');

  var html = '<div class="cmp-summary">कुल निवेश: <strong>' + fmtINRFull(totalInvested) + '</strong> · ' + m + ' x ' + y + ' महीने</div>' +
    '<div class="cmp-bars">' + bars + '</div>' +
    '<div class="cmp-cta">' +
      '<p>📈 <strong>' + winner.name + '</strong> सबसे ज़्यादा लाभ देता है — इस सेंटिरी में <strong>' + fmtINR(winner.profit) + '</strong> का फायदा!</p>' +
      '<a class="affbtn" href="https://www.amazon.in/s?k=mutual+fund+investment+books" target="_blank" rel="noopener sponsored" onclick="trackLead(event)">📚 Amazon पर निवेश बुक्स देखें</a>' +
    '</div>';

  document.getElementById('cmp-result').innerHTML = html;
  if (window.navigator && navigator.sendBeacon) navigator.sendBeacon('/t.gif?e=compare');
}
