function toggleTheme(){
  const d=document.documentElement;
  const cur=d.getAttribute("data-theme")||"";
  const next=cur==="light"?"":"light";
  if(next){d.setAttribute("data-theme","light");d.querySelector(".theme-toggle").textContent="☀️"}else{d.removeAttribute("data-theme");d.querySelector(".theme-toggle").textContent="🌙"}
  localStorage.setItem("theme",next);
}
// Restore saved theme
if(localStorage.getItem("theme")==="light"){
  document.documentElement.setAttribute("data-theme","light");
  document.querySelector(".theme-toggle").textContent="☀️";
}
