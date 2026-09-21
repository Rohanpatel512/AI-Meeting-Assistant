const uploadBtn = document.querySelector(".choose-file-btn");
const uploadBox = document.querySelector(".upload-box");
const fileInput = document.querySelector("#file-hidden-input");
const fileContent = document.querySelector(".file-content");
const removeBtn = document.querySelector(".remove-btn");
const API_BASED_URL = window.APP_CONFIG?.API_BASE_URL ?? "";


uploadBtn.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", () => {
    sendFile(fileInput.files[0]);
});

uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    uploadBox.style.borderColor = '#000'
});

uploadBox.addEventListener('dragleave', (e) => {
    uploadBox.style.borderColor = '#cfd4e3'
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    sendFile(e.dataTransfer.files[0]);
    uploadBox.style.borderColor = '#cfd4e3';
});

removeBtn.addEventListener('click', () => {
    const child = fileContent.children[0];
    child.remove();
});


async function sendFile(file) {

    if(!file) {
        return;
    }

    const formData = new FormData();
    formData.append("file", file)

    try {
        const response = await fetch(`${API_BASED_URL}/meeting/summarize`, {
            method: "POST",
            body: formData
        })
    } catch(error) {
        alert("Error sending file to server: ", error)
    }
    
    // Get the size of the file 
    const size = (file.size / (1024 * 1024)).toFixed(2);
    const type = file.name.split(".")[2];
    const name = file.name;

    // Display the file that was uploaded to user 
    displayUploadedFile(size, type, name);

}

function displayUploadedFile(size, type, name) {

    const fileContainer = document.createElement('div');
    const fileIconDiv = document.createElement('div');
    const fileDetailDiv = document.createElement('div');
    const fileMetaDiv = document.createElement('div');

    const strongText = document.createElement('strong');

    fileContainer.className = 'file-container';
    fileDetailDiv.className = "file-details";
    fileIconDiv.className = "file-icon";
    fileMetaDiv.className = "file-meta";

    
    if(type == "txt") {
        fileIconDiv.textContent = 'TXT';
    } else {
        fileIconDiv.textContent = 'DOCX';
    }

    strongText.textContent = name;

    fileMetaDiv.textContent = `${size} MB • Uploaded just now`;

    fileDetailDiv.appendChild(strongText);
    fileDetailDiv.appendChild(fileMetaDiv);

    fileContainer.appendChild(fileIconDiv);
    fileContainer.append(fileDetailDiv);

    fileContent.append(fileContainer);

}