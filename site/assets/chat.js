let chatCtx = [];
function toggleChat(){
  var b=document.getElementById("chat-box");
  b.style.display=b.style.display==="none"?"flex":"none";
}
async function sendChat(){
  var input=document.getElementById("chat-input");
  var msg=input.value.trim();
  if(!msg)return;
  var box=document.getElementById("chat-messages");
  box.innerHTML+='<div class="chat-msg user">'+htmlEncode(msg)+'</div>';
  input.value="";
  box.innerHTML+='<div class="chat-msg ai" id="chat-typing">Typing...</div>';
  box.scrollTop=box.scrollHeight;
  try{
    var res=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:msg,context:chatCtx})});
    var data=await res.json();
    var typing=document.getElementById("chat-typing");
    if(typing)typing.outerHTML='<div class="chat-msg ai">'+htmlEncode(data.reply||"Sorry, I could not process the question.")+'</div>';
    chatCtx.push({role:"user",content:msg},{role:"assistant",content:data.reply||""});
    if(chatCtx.length>10)chatCtx=chatCtx.slice(-10);
  }catch(e){
    var typing=document.getElementById("chat-typing");
    if(typing)typing.outerHTML='<div class="chat-msg ai">Network error — Ollama may be offline.</div>';
  }
  box.scrollTop=box.scrollHeight;
}
function htmlEncode(s){var d=document.createElement("div");d.textContent=s;return d.innerHTML;}
