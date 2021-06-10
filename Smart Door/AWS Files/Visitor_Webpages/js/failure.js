window.onload = function(){
    validPage = localStorage.getItem("submitOTP");
    if(validPage == "false"){
        window.location.href = "index.html";
    }
    localStorage.setItem("submitOTP", "false");
}