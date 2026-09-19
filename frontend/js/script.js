const uploadBtn = document.querySelector(".choose-file-btn");
const fileInput = document.querySelector("#file-hidden-input");
const API_BASED_URL = window.APP_CONFIG?.API_BASE_URL ?? "";


uploadBtn.addEventListener("click", () => {
    fileInput.click();
})

fileInput.addEventListener("change", () => {
    sendFile();
})

async function sendFile() {

     // If user has selected a file 
    if(fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append("file", fileInput.files[0])
        try {
            const response = await fetch(`${API_BASED_URL}/meeting/summarize`, {
                method: "POST",
                body: formData
            })
        } catch(error) {
            alert("Error sending file to server: ", error)
        }
    }
}