const form = document.getElementById('form');
const username = document.getElementById('username');
const password = document.getElementById('password');
const email = document.getElementById('e-mail');
const confirming = document.getElementById('confirm');
var success = 0;//count whether the register operation is successful or not, 4 success in total

form.addEventListener('submit', e => {
    e.preventDefault();
    RegisterCheck();
})

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

const setBack = element => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector('.error-message');
    errorDisplay.innerText = '';
    inputControl.classList.remove('error-message');
    inputControl.classList.remove('success');
}

const isValidpassword = password => {
    const regularexpression = /^(?=.*[a-z])(?=.*\d)(?=.*[A-Z])[^]{8,16}$/;
    return regularexpression.test(password);
}

const isValidemail = email => {
    const regularexpression = /^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z0-9]+$/;
    return regularexpression.test(email);
}

function validateInputs() {
    const passwordValue = password.value.trim();
    const usernameValue = username.value.trim();
    const emailValue = email.value.trim();
    const confirmValue = confirming.value.trim();
    if (usernameValue === '') {
        setError(username, 'Username is required.');
    } else {
        setSuccess(username);
        success++;
    }
    if (passwordValue === '') {
        setError(password, 'Password is required.');
    } else if (!isValidpassword(passwordValue)) {
        setError(password, 'Password must have numbers,\n upper and lower case letters,\n 8-16 characters.');
    } else {
        setSuccess(password);
        success++;
    }
    if (emailValue === '') {
        setError(email, 'E-mail is required.')
    } else if (!isValidemail(emailValue)) {
        setError(email, 'Invalid email is provided.')
    } else {
        setSuccess(email);
        success++;
    }
    if (confirmValue == passwordValue && confirmValue != '') {
        setSuccess((confirming));
        success++;
    } else if (confirmValue === '') {
        setError(confirming, 'confirm password is required.');
    } else {
        setError(confirming, 'Second password input is different.');
    }
}

function formReset()//reset the whole page
{
    document.getElementById("form").reset();
    //remove the changed class name of four input boxes
    setBack(username);
    setBack(email);
    setBack(password);
    setBack(confirming);
}

function RegisterCheck() {
    success = 0;//check success is successful or not
    validateInputs();
    if (success != 4)//if not successful, retrun false
        return false;
    else {
        form.submit();//submit the form and let app to render new page
        return true;
    }
}