
window.onload = function(){
    validPage = localStorage.getItem("submitOTP");
    if(validPage == "false"){
        window.location.href = "index.html";
    }
    localStorage.setItem("submitOTP", "false");

    const urlParams = new URLSearchParams(window.location.search);
    var name = urlParams.get("name");
    document.getElementById('greeting').innerHTML = 'Welcome back<br />'.concat(name);
}