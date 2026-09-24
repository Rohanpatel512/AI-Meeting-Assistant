const uploadBtn = document.querySelector(".choose-file-btn");
const uploadBox = document.querySelector(".upload-box");
const fileInput = document.querySelector("#file-hidden-input");
const fileContent = document.querySelector(".file-content");
const removeBtn = document.querySelector(".remove-btn");
const summaryOutput = document.querySelector(".summary-container");
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
        });

        const data = await response.json();
        
        displayResponse(data);

        
    } catch(error) {
        alert("Error sending file to server: ", error)
    }
    
    // Get the size of the file 
    const size = (file.size / (1024 * 1024)).toFixed(2);
    const type = file.name.split(".")[2];
    const name = file.name;
    const timeUploaded = new Date();

    // Display the file that was uploaded to user 
    displayUploadedFile(size, type, name, getTimeAgo(timeUploaded));

}

function getTimeAgo(timeUploaded) {
    const seconds = Math.floor((Date.now() - timeUploaded.getTime()) / 1000);

    if(seconds < 60) {
        return "Uploaded just now";
    }

    const minutes = Math.floor(seconds / 60);

    if(minutes < 60) {
        return `Uploaded ${minutes} minutes${minutes == 1 ? "": "s"} ago`
    }

    const hours = Math.floor(minutes / 60);

    if(hours < 24) {
        return `Uploaded ${hours} hours${hours == 1 ? "": "s"} ago`
    }

    const days = Math.floor(hours / 24);

    if(days >= 1) {
        return `Uploaded ${days} days${days == 1 ? "": "s"} ago`
    }


}

function displayUploadedFile(size, type, name, time) {

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

    fileMetaDiv.textContent = `${size} MB • ${time}`;

    fileDetailDiv.appendChild(strongText);
    fileDetailDiv.appendChild(fileMetaDiv);

    fileContainer.appendChild(fileIconDiv);
    fileContainer.append(fileDetailDiv);

    fileContent.append(fileContainer);

}

async function displayResponse(response) {

    summaryOutput.innerHTML = "";

    for(const [key, value] of Object.entries(response)) {

        const box = document.createElement("div");
        box.className = "content-boxes";

        const subtitle = document.createElement("h2");
        box.appendChild(subtitle);

        summaryOutput.appendChild(box);

        // converts JSON key to title 
        const title = toTitle(key);

        await type(title, subtitle);

        if(typeof value === "string") {
            const content = document.createElement("p");
            box.appendChild(content);
            await type(value, content);

        } else if(Array.isArray(value)) {

            for(const item of value) {
                const content = document.createElement("p");
                box.appendChild(content);

                if(typeof item === "object" && item != "null") {
                    const text = Object.values(item).filter(value => value != null).join(" - ");

                    await type(text, content);
                } else {
                    await type(text, content);
                }

            }

        }

    }


}

function toTitle(key) {

    if(key == "overview") {
        return "Overview";
    } else if(key == "discussion_points") {
        return "Key Discussions & Points";
    } else if(key == "decisions") {
        return "Decisions";
    } else if(key == "tasks_and_deadlines") {
        return "Tasks & Deadlines"
    }

}

function type(text, container) {
    return new Promise((resolve) => {
        let index = 0;
        const interval = setInterval(() => {
            if(index < text.length) {
                container.textContent += text[index];
                index++;
            } else {
                clearInterval(interval);
                resolve();
            }
        }, 100);
    });
}