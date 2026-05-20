//forn end check for edit an assessment
const form = document.getElementById('editIn');
const module = document.getElementById('create-list-input');
const assessment = document.getElementById('create-task-input');
const description = document.getElementById('floatingTextarea2')
const ddl = $('#daed').val();
const reminder = $('#remind').val();


form.addEventListener('submit', e => {
    e.preventDefault();
    CheckEdit();
})
const setError = (element, message) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector('.error-message');
    errorDisplay.innerText = message;
    inputControl.classList.add('error-message');
}

//real time functions and variables
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
var now = year + "-" + addZero(month) + "-" + addZero(date) + "T" + addZero(hour) + ":" + addZero(min);

function CheckEdit() {
    const modulevalue = module.value.trim();
    const assvalue = assessment.value.trim();
    const describe = description.value.trim();
    if (modulevalue === '') {
        setError(module, "Module must be entered!");
    } else if (assvalue === '') {
        setError(assessment, "Assessment must be entered!");
    } else if(describe === ''){
        setError(description,"Description must not be empty!")
    }
    else {
        form.submit();
    }
}