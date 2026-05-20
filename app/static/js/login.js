const form = document.getElementById('form');
const username = document.getElementById('username');
const password = document.getElementById('password');
const button = document.getElementById('toggle');
const body = document.querySelector('body');
const signup = document.querySelector('.signup');
const container = document.querySelector('.container');
const footer = document.querySelector('.footer');
let success = 0;//mark whether the register is successful

form.addEventListener('submit', e => {
    e.preventDefault();
    LoginCheck();//run validation fuctions every time we submit
})


button.onclick = function () {
    button.classList.toggle('dark');
    body.classList.toggle('dark');
    form.classList.toggle('dark');
    signup.classList.toggle('dark');
    container.classList.toggle('dark');
    footer.classList.toggle('dark');
}
const setError = (element, message) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector('.error-message');
    errorDisplay.innerText = message;
    inputControl.classList.add('error-message');
    inputControl.classList.remove('success');
}

const setSuccess = element => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector('.error-message');
    errorDisplay.innerText = '';
    inputControl.classList.add('success');
    inputControl.classList.remove('error-message');
}

const isValidpassword = password => {
    const regularexpression = /^(?=.*[a-z])(?=.*\d)(?=.*[A-Z])[^]{8,16}$/;
    return regularexpression.test(password);
}

function validateInputs() {
    const passwordValue = password.value.trim();//eliminate the spaces in the inputs
    const usernameValue = username.value.trim();
    if (usernameValue === '') {
        setError(username, 'Username is required');
    } else {
        setSuccess(username);
        success++;
    }
    if (passwordValue === '') {
        setError(password, 'Password is required');
    } else if (!isValidpassword(passwordValue)) {
        setError(password, 'Password must have numbers, upper and lower case letters, 8-16 characters');
    } else {
        setSuccess(password);
        success++;
    }
}

function LoginCheck() {
    success = 0;//check success is successful or not
    validateInputs();
    if (success != 2)//if not successful, retrun false
        return false;
    else {
        form.submit();//submit the form and let app to render new page
        return true;
    }
}