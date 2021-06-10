window.onload = function(){
    localStorage.setItem("submitOTP", "false");
}

function setOTPsubmit() {
    localStorage.setItem("submitOTP", "true");
}

(function ($) {
    "use strict";

    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');

    $('.validate-form').on('submit',function(){
        var check = true;

        for(var i=0; i<input.length; i++) {
            if(validate(input[i]) == false){
                showValidate(input[i]);
                check=false;
            }
        }
        return check;
    });


    $('.validate-form .input100').each(function(){
        $(this).focus(function(){
           hideValidate(this);
        });
    });

    function showValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function hideValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).removeClass('alert-validate');
    } 

})(jQuery);

const customMessages = {
    valueMissing:    'Please enter your passcode',      
    patternMismatch: 'Passcode must contain only numbers',
    tooShort:   'Passcode must be a 6 digit number',
    tooLong:    'Passcode must be a 6 digit number',
}
  
function getCustomMessage (type, validity) {
    if (validity.typeMismatch) {
        return customMessages[`${type}Mismatch`]
    } else {
        for (const invalidKey in customMessages) {
            if (validity[invalidKey]) {
                return customMessages[invalidKey]
            }
        }
    }
}
  
var inputs = document.querySelectorAll('input, select, textarea')
inputs.forEach(function (input) {
    function checkValidity () {
        const message = input.validity.valid
        ? null
        : getCustomMessage(input.type, input.validity, customMessages)
        input.setCustomValidity(message || '')
    }
    input.addEventListener('input', checkValidity)
    input.addEventListener('invalid', checkValidity)
})

