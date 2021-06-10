var botui = new BotUI('concierge');
var apigClient = apigClientFactory.newClient();

function Hello () {
  botui.message.bot({
    content: 'Welcome to the dining concierge service. What can I help you today? You can say restaurant recommendations.'
  });
  WaitForMessage();
}

function ProcessMessage(msg) {
    var params = {};
    var body = {
        "message":msg
    };
    var additionalParams = {
        headers: {},
        queryParams: {}
    };
    apigClient.chatbotPost(params,body,additionalParams)
        .then(function(result){
            botui.message.bot({
                content: result.data
            });
        }).catch( function(err){
            console.log(err);
        });

}
function WaitForMessage () {
  botui.action.text({
    action: {
      placeholder: 'Enter your text here'
    }
  }).then(function (res) { // will be called when it is submitted.
    ProcessMessage(res);
    WaitForMessage();
  });
}

Hello()
