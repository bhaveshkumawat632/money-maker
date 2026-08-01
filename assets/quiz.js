// Money Quiz Widget — interactive Hindi/English financial literacy quiz
(function(){
  var quizzes = [
    {q:"SIP ka full form kya hai?",opts:["Systematic Investment Plan","Single Income Program","Stock Investment Process","Savings Insurance Plan"],ans:0},
    {q:"EPF ka full form kya hai?",opts:["Employee Provident Fund","Extra Profit Fund","Economic Production Fund","Emergency Pension Fund"],ans:0},
    {q:"Nifty 50 kis exchange ka index hai?",opts:["NSE","BSE","MCX","NCDEX"],ans:0},
    {q:"Mutual fund mein 'NAV' ka matlab kya hai?",opts:["Net Asset Value","New Annual Value","National Asset Vault","Net Annual Volume"],ans:0},
    {q:"FD mein 'FD' ka matlab kya hai?",opts:["Fixed Deposit","Flexible Deposit","First Deposit","Financial Document"],ans:0},
    {q:"STT ka full form kya hai?",opts:["Securities Transaction Tax","Stock Trade Tax","Saving Tax Threshold","Securities Transfer Tax"],ans:0},
    {q:"Credit card bill kholne par late fee kaise hota hai?",opts:["Interest lagta hai","Discount milti hai","Kuch nahi","Cashback milta hai"],ans:0},
    {q:"Best saving scheme India mein kaunsa hai?",opts:["PPF","Credit Card","Personal Loan","Car Loan"],ans:0},
    {q:"SBI ka full form kya hai?",opts:["State Bank of India","Secure Bank of India","State Banking International","Savings Bank India"],ans:0},
    {q:"PDD ka full form kya hai?",opts:["Public Provident Fund","Personal Pension Deposit","Private Profit Document","Public Profit Dividend"],ans:0}
  ];
  var container = document.getElementById('quiz-box');
  var idx = 0, score = 0;
  if(!container) return;
  function loadQ(){
    if(idx>=quizzes.length){
      container.innerHTML = '<div class="quiz-result"><h3>'+(document.documentElement.lang==='hi'?'Quiz Complete!':'Quiz Complete!')+'</h3><p>'+(document.documentElement.lang==='hi'?'Tumhara score:':'Your score: ')+score+' / '+quizzes.length+'</p><button onclick="location.reload()">'+(document.documentElement.lang==='hi'?'Dobara karo':'Play Again')+'</button></div>';
      return;
    }
    var q = quizzes[idx];
    var h = '<div class="quiz-question">'+(document.documentElement.lang==='hi'?'Sawaal '+(idx+1)+': ':'Question '+(idx+1)+': ')+q.q+'</div><div class="quiz-opts">';
    q.opts.forEach(function(opt,i){
      h += '<button class="quiz-opt" data-i="'+i+'">'+opt+'</button>';
    });
    h += '</div><div class="quiz-info">'+(document.documentElement.lang==='hi'?('Sawaal '+(idx+1)+' of '+quizzes.length):('Question '+(idx+1)+' of '+quizzes.length))+'</div>';
    container.innerHTML = h;
    container.querySelectorAll('.quiz-opt').forEach(function(btn){
      btn.addEventListener('click', function(){
        var chosen = parseInt(this.getAttribute('data-i'));
        if(chosen===quizzes[idx].ans) score++;
        idx++; loadQ();
      });
    });
  }
  loadQ();
})();
