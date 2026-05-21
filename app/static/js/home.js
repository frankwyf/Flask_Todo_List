//deal with the deadline date
var today = new Date();
var year = today.getFullYear();
var month = today.getMonth() + 1;
var date = today.getDate();
var hour = today.getHours();
var min = today.getMinutes();

//make up for month and date if it is not two-digits
function addZero(num) {
    return num < 10 ? '0' + num : num;
}

$(document).ready(function () {
    document.getElementById('setdead').setAttribute("value",
        year + "-" + addZero(month) + "-" + addZero(date) + "T" + addZero(hour) + ":" + addZero(min));
    document.getElementById('setremind').setAttribute("value",
        year + "-" + addZero(month) + "-" + addZero(date) + "T" + addZero(hour) + ":" + addZero(min));
});

//front end check for new assessment adding
const form = document.getElementById('form');
const module = document.getElementById('create-list-input');
const assessment = document.getElementById('create-task-input');


if (form && module && assessment) {
    form.addEventListener('submit', e => {
        e.preventDefault();
        const modulevalue = module.value.trim();
        const assvalue = assessment.value.trim();
        if (modulevalue === '') {
            setError(module, "Module must be entered!");
        } else if (assvalue === '') {
            setError(assessment, "Assessment must be entered!");
        } else {
            form.submit();
        }
    })
}
const setError = (element, message) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector('.error-message');
    errorDisplay.innerText = message;
    inputControl.classList.add('error-message');
}

// Configure weather widget only if a key is provided by backend config.
if (window.WEATHER_WIDGET_KEY) {
    WIDGET = {
        "CONFIG": {
            "layout": "1",
            "width": "400",
            "height": "120",
            "background": "1",
            "dataColor": "FFFFFF",
            "language": "en",
            "borderRadius": "5",
            "key": window.WEATHER_WIDGET_KEY
        }
    }
}


//log out a user
function logout() {
    //sent a modal to tell the user that he/she has been logged out
    window.location.href = "http://127.0.0.1:5000/newlogin"
}

//show toast for more message
var liveToastBtn = document.querySelector("#liveToastBtn");
if (liveToastBtn) {
    liveToastBtn.onclick = function () {
        new bootstrap.Toast(document.querySelector('.toast')).show();
        window.setTimeout(function () {
            $(".toast").removeClass("show");
        }, 5000);
    }
}

var inTaskBtn = document.querySelector("#intask");
if (inTaskBtn) {
    inTaskBtn.onclick = function () {
        new bootstrap.Toast(document.querySelector('.toast')).show();
    }
}

//log out popover
var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
return new bootstrap.Popover(popoverTriggerEl)
})


