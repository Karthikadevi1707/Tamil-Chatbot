if(!localStorage.getItem("loggedUser")){
window.location="index.html";
}

let chatArea=document.getElementById("chatArea");
let historyDiv=document.getElementById("history");

function sendMessage(){
let text=userInput.value.trim();
if(!text) return;

addUserMessage(text);
addHistory(text);

let answer=generateAnswer(text);
aiTyping(answer);

userInput.value="";
}

function generateAnswer(text){

if(text.includes("கட்டுரை")){
return `📌 அறிமுகம்

${text} பற்றிய விரிவான விளக்கம்.

🔹 முக்கிய பகுதி 1
இதன் முக்கிய அம்சங்கள் விளக்கம்.

🔹 முக்கிய பகுதி 2
மேலும் விரிவான தகவல்கள்.

✅ முடிவு
இதனால் ${text} பற்றிய கட்டுரை நிறைவடைகிறது.`;
}

return `${text} பற்றிய சுருக்கமான விளக்கம்:

• முக்கிய அம்சம் 1  
• முக்கிய அம்சம் 2  
• முக்கிய அம்சம் 3`;
}

function aiTyping(answer){

let div=document.createElement("div");
div.className="message";

let copy=document.createElement("span");
copy.innerText="📋";
copy.className="copy-btn";
copy.onclick=()=>navigator.clipboard.writeText(answer);

div.appendChild(copy);
chatArea.appendChild(div);

let i=0;
let interval=setInterval(()=>{
div.innerHTML+=answer.charAt(i);
i++;
if(i>=answer.length) clearInterval(interval);
},15);

chatArea.scrollTop=chatArea.scrollHeight;
}

function addUserMessage(text){
chatArea.innerHTML+=`<div class="message">👤 ${text}</div>`;
}

function addHistory(topic){
let id="his_"+Date.now();

let div=document.createElement("div");
div.className="history-item";
div.id=id;

div.innerHTML=`
<span>${topic}</span>
<button onclick="deleteHistory('${id}')">X</button>
`;

historyDiv.appendChild(div);
}

function deleteHistory(id){
document.getElementById(id).remove();
}

function handleFile(event){
let file=event.target.files[0];
if(!file) return;

if(file.type.startsWith("image/")){
let imgURL=URL.createObjectURL(file);
chatArea.innerHTML+=`<div class="message"><img src="${imgURL}" width="200"></div>`;

aiTyping("இந்த படத்தில் காணப்படும் பொருளின் விளக்கம்:\n\n• பொருள் அடையாளம்\n• பயன்பாடு\n• முக்கிய அம்சம்");
}

else if(file.type==="application/pdf"){
chatArea.innerHTML+=`<div class="message">📄 PDF Uploaded: ${file.name}</div>`;

aiTyping("இந்த PDF பற்றிய சுருக்கமான விளக்கம்:\n\n• முக்கிய தலைப்பு\n• உள்ளடக்கம்\n• பயன்பாடு");
}
}

function startVoice(){
let recognition=new webkitSpeechRecognition();
recognition.lang="ta-IN";
recognition.start();

recognition.onresult=function(e){
userInput.value=e.results[0][0].transcript;
}
}

function logout(){
localStorage.removeItem("loggedUser");
window.location="index.html";
}