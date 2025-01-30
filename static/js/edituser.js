// Function to show the pop-up
function openPopup() {
    document.getElementById("popup").classList.add("active");
}

// Function to close the pop-up
function closePopup() {
    document.getElementById("popup").classList.remove("active");
}

// Function to toggle the password visibility
function togglePassword() {
    var passwordSpan = document.getElementById("password");
    var storedPassword = passwordSpan.getAttribute("data-password");
    if (passwordSpan.textContent === "*******") {
        passwordSpan.textContent = storedPassword;  // Show actual password
    } 
    else {
        passwordSpan.textContent = "*******";  // Hide password
    }
}

// Function to show the pop-up
function OpenPopup() {
    document.getElementById("pop-up").classList.add("active");
}

// Function to close the pop-up
function ClosePopup() {
    document.getElementById("pop-up").classList.remove("active");
}

function opencontact() {
    document.getElementById("pop-contact").classList.add("active");
}

function closecontact() {
    document.getElementById("pop-contact").classList.remove("active");
}
