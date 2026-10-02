const loginEmail = document.querySelector('#login-email');
const loginPassword = document.querySelector("#login-password");
const loginButton = document.querySelector(".login-button");

const signupName = document.querySelector("#signup-name");
const signupEmail = document.querySelector("#signup-email");
const signupPassword = document.querySelector("#signup-password");
const signupConfirm = document.querySelector("#signup-confirm");
const signupButton = document.querySelector(".signup-button");

const API_BASED_URL = window.APP_CONFIG?.API_BASE_URL ?? "";

if (loginButton) {
    loginButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const email = loginEmail.value;
        const password = loginPassword.value;

        const credentials = JSON.stringify({ email, password });

        try {
            const response = await fetch(`${API_BASED_URL}/user/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: credentials
            });

            const data = await response.json();

            if (!response.ok || data.message !== "Login successful") {
                throw new Error(data.detail || data.message || "Invalid password or email.");
            }

            window.location.href = "dashboard.html";
        } catch (error) {
            alert(`${error.message}. Please try again.`);
        }
    });
}

if (signupButton) {
    signupButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const name = signupName.value;
        const email = signupEmail.value;
        const password = signupPassword.value;
        const confirmPassword = signupConfirm.value;

        const credentials = JSON.stringify({
            name,
            email,
            password,
            confirm_password: confirmPassword
        });

        try {
            const response = await fetch(`${API_BASED_URL}/user/signup`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: credentials
            });

            const data = await response.json();

            if (!response.ok || data.message !== "User created successfully") {
                throw new Error(data.detail || "Signup failed.");
            }

            alert("Signup successful! Please log in.");
            window.location.href = "index.html";
        } catch (error) {
            alert(error.message);
        }
    });
}

