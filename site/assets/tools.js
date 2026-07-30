function calcSavings(){{
  var m=+document.getElementById('sc-monthly').value||0;
  var y=+document.getElementById('sc-years').value||0;
  var r=(+document.getElementById('sc-rate').value||0)/100/12;
  var n=y*12; var fv=0;
  if(r===0){{fv=m*n;}} else {{fv=m*((Math.pow(1+r,n)-1)/r)*(1+r);}}
  var amt=Math.round(fv).toLocaleString();
  document.getElementById('sc-result').textContent='{r1}'.replace('{{AMT}}',amt);
  if(window.navigator&&navigator.sendBeacon)navigator.sendBeacon('/t.gif?e=calc');
}}
function trackLead(e){{ if(navigator.sendBeacon)navigator.sendBeacon('/t.gif?e=lead'); return true; }}
