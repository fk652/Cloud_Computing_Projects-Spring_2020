var apigClient = apigClientFactory.newClient();
var apiKey = 'iohtUQW8aw4wryoAVWg6B1Lxn28wIwx2aoTFRpe3'

function showMessage(messageType, message) {
  hideMessage();
  $('#' + messageType + ' span').html(message);
  $('#' + messageType).show();
}

function hideMessage() {
  $('#error').hide();
  $('#info').hide();
  $('#success').hide();
}



function uploadPhoto() {
  var filePath = document.getElementById('file-input').value;
  var file = document.getElementById('file-input').files[0];
  var fileExtension = filePath.split(".")[1];
  var reader = new FileReader();
  document.getElementById('file-input').value = "";
  if((filePath == "") || (!['png','jpg','jpeg'].includes(fileExtension))) {
    showMessage("error","Please upload a valid PNG/JPG file");
  } else {
    var params = {
      'bucket': 'cs9223g-photo-album',
      'key': filePath.split("\\").slice(-1)[0]};
    var body = {};
    var additionalParams = {
      headers: {
        'content-type': 'image/' + fileExtension,
        'x-api-key': apiKey
      },
      queryParams: {}
    };
    reader.onload = function (event) {
      body =  btoa(event.target.result);
      //console.log(body);
      return apigClient.uploadBucketKeyPut(params,body,additionalParams)
        .then(function(result){
          showMessage('success', 'Upload success!')
        })
        .catch(function(error){
          showMessage('error', 'Upload failed!')
          console.log(error);
        });
    }
    reader.readAsBinaryString(file);
  }
}

function getHtml(template) {
  return template.join('\n');
}

function searchPhotos() {
  var q = $('#transcript').val();
  if (q.length === 0) {
    showMessage('error','Search field cannot be empty!')
  } else {
    showMessage('info','Searching ' + q)
    var params = {
      'q': q};
    var body = {};
    var additionalParams = {
      headers: {
        'x-api-key': apiKey
      },
      queryParams: {}
    };
    apigClient.searchGet(params,body,additionalParams)
      .then(function(result){
        showMessage('info', 'Found ' + result.data.results.length + ' photos');
        showPhotos(result.data.results);
      })
      .catch(function(error){
        showMessage('error', 'Search failed!')
        console.log(error);
      });
  }

}

function showPhotos(data) {
  if (data.length === 0) {
    document.getElementById('viewer').innerHTML = '';
  }
  else {
    var photos = data.map(function(photo) {
      var photoUrl = photo.url;
      var photoKey = photoUrl.split('/').pop();
      return getHtml([
        '<div class="col-lg-3 col-md-4 col-6">',
        '<img src="' + photoUrl + '"/>',
        '</div>',
      ]);
    });
    var htmlTemplate = [
      '<div class="row">',
      getHtml(photos),
      '</div>',
    ]
    document.getElementById('viewer').innerHTML = getHtml(htmlTemplate);
  }
}