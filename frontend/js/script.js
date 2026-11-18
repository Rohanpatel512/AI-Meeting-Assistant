const uploadBtn = document.querySelector(".choose-file-btn");
const uploadBox = document.querySelector(".upload-box");
const fileInput = document.querySelector("#file-hidden-input");
const fileContent = document.querySelector(".file-content");
const removeBtn = document.querySelector(".remove-btn");
const summaryOutput = document.querySelector(".summary-container");
const pdfButton = document.querySelector(".pdf-button");
const copyButton = document.querySelector(".copy-button");
const status_text = document.querySelector(".status-text");
const summarizeBtn = document.querySelector(".summarize-btn");
const API_BASED_URL = window.APP_CONFIG?.API_BASE_URL ?? "";
let file = null;
let meetingSummary = null;
let uploadedFileTimes = [];
let isSummaryLocked = false;

import { generatePDF } from "./pdf.js";

copyButton.addEventListener("click", async () => {
    if (!meetingSummary || isSummaryLocked) return;

    const text = summaryOutput.innerText;

    try {
        await navigator.clipboard.writeText(text);
        copyButton.textContent = "Copied!";
        setTimeout(() => copyButton.textContent = "Copy", 2000);
    } catch(error) {
        console.error("Failed to copy to clipboard");
    }
});

pdfButton.addEventListener("click", () => {
    if (!meetingSummary || isSummaryLocked) return;
    generatePDF(meetingSummary);
})

uploadBtn.addEventListener("click", () => {
    if (isSummaryLocked) return;
    fileInput.click();
});

fileInput.addEventListener("change", () => {
    if (isSummaryLocked) return;
    file = fileInput.files[0];
    // Get the size of the file 
    const size = (file.size / (1024 * 1024)).toFixed(2);
    const type = file.name.split(".")[2];
    const name = file.name;
    const timeUploaded = new Date();

    // Display the file that was uploaded to user 
    uploadedFileTimes.push([size, timeUploaded.getMinutes()]);
    displayUploadedFile(size, type, name, "Uploaded just now");
    refreshActionState();
});

uploadBox.addEventListener('dragover', (e) => {
    if (isSummaryLocked) {
        e.preventDefault();
        e.stopPropagation();
        return;
    }

    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    uploadBox.style.borderColor = '#000'
});

uploadBox.addEventListener('dragleave', (e) => {
    if (isSummaryLocked) return;
    uploadBox.style.borderColor = '#cfd4e3'
});

uploadBox.addEventListener('drop', (e) => {
    if (isSummaryLocked) {
        e.preventDefault();
        e.stopPropagation();
        return;
    }

    e.preventDefault();
    file = e.dataTransfer.files[0];

    const size = (file.size / (1024 * 1024)).toFixed(2);
    const type = file.name.split(".")[2];
    const name = file.name;
    const timeUploaded = new Date();

    // Display the file that was uploaded to user 
    uploadedFileTimes.push([size, timeUploaded.getMinutes()]);
    displayUploadedFile(size, type, name, "Uploaded just now");
    uploadBox.style.borderColor = '#cfd4e3';
    refreshActionState();
});

removeBtn.addEventListener('click', () => {
    if (isSummaryLocked) return;
    const child = fileContent.children[0];
    child.remove();
    file = null;
    refreshActionState();
});

summarizeBtn.addEventListener("click", async () => {
    if (isSummaryLocked) return;

    if(!file) {
        alert("Please upload a file before summarizing.");
        return;
    }

    isSummaryLocked = true;
    lockButtons(true);
    console.log("Locked: ", summarizeBtn.disabled);
    await sendFile(file);
})

setInterval(updateUploadTime, 60000);

async function sendFile(file) {
    updateStatusMessage("Uploading file...");
    if(!file) {
        isSummaryLocked = false;
        refreshActionState();
        return;
    }

    const formData = new FormData();
    formData.append("file", file)

    try {
        const refreshOk = await ensureSessionFresh();
        if(!refreshOk) {
            window.location.href = "index.html";
            return;
        }


        updateStatusMessage("Analyzing transcript...");
        const response = await fetch(`${API_BASED_URL}/meeting/summarize`, {
            method: "POST",
            credentials: 'include',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "An error occurred while processing the transcript.");
        }

        updateStatusMessage("Generating Summary...");

        meetingSummary = data

        await displayResponse(data);
        updateStatusMessage("");

    } catch(error) {
        updateStatusMessage("");
        alert(error.message);
    } finally {
        isSummaryLocked = false;
        lockButtons(false);
        refreshActionState();
    }

}

async function ensureSessionFresh() {
    try {
        const response = await fetch(`${API_BASED_URL}/user/refresh`, {
            method: "POST",
            credentials: 'include'
        });

        if (!response.ok) {
            return false;
        }

        return true;
    } catch (error) {
        console.error("Session refresh check failed:", error);
        return false;
    }
}

function updateUploadTime() {

    const currentTime = new Date().getMinutes();

    if(uploadedFileTimes.length == 0) {
        return;
    }

    for(var i = 0; i < uploadedFileTimes.length; i++) {
        let diff = currentTime - uploadedFileTimes[i][1];
        let size = uploadedFileTimes[i][0];

        if(diff % 60 == 0) {

            let time = `Uploaded ${diff / 60} hour${diff == 1 ? "": "s"} ago`;
            fileContent.children[i].children[1].children[1].textContent = `${size} MB • ${time}`;

        } else if(diff < 60) {

            let time = `Uploaded ${diff} minute${diff == 1 ? "": "s"} ago`;
            fileContent.children[i].children[1].children[1].textContent = `${size} MB • ${time}`;
        }
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

    for (const [key, value] of Object.entries(response)) {
        const box = document.createElement("div");
        box.className = "content-boxes";
        summaryOutput.appendChild(box);

        const subtitle = document.createElement("h2");
        subtitle.textContent = "";
        box.appendChild(subtitle);

        const title = toTitle(key);
        await type(title, subtitle);

        if (typeof value === "string") {
            const content = document.createElement("p");
            content.textContent = "";
            box.appendChild(content);
            await type(value, content);

        } else if (Array.isArray(value)) {
            const list = document.createElement("ul");
            list.className = "summary-list";
            box.appendChild(list);

            for (const item of value) {
                const listItem = document.createElement("li");
                listItem.className = "summary-item";
                listItem.textContent = "";
                list.appendChild(listItem);

                if (item !== null && typeof item === "object") {
                    const entries = Object.entries(item).filter(([_, itemValue]) => itemValue !== null);

                    for (const [entryKey, entryValue] of entries) {
                        const field = document.createElement("div");
                        field.className = `summary-${entryKey}`;
                        field.textContent = "";
                        listItem.appendChild(field);

                        if (entryKey === "text" || entryKey === "task" || entryKey === "rationale") {
                            await type(String(entryValue), field);
                        } else {
                            const label = entryKey
                                .replaceAll("_", " ")
                                .replace(/\b\w/g, char => char.toUpperCase());

                            await type(`${label}: ${entryValue}`, field);
                        }
                    }
                } else {
                    await type(String(item), listItem);
                }
            }
        }
    }
}

function toTitle(key) {

    if(key == "overview") {
        return "Overview";
    } else if(key == "discussion_points") {
        return "Key Discussions Points";
    } else if(key == "decisions") {
        return "Decisions";
    } else if(key == "tasks_and_deadlines") {
        return "Tasks & Deadlines"
    }

}

function type(text, container) {
    return new Promise((resolve) => {
        container.textContent = "";
        let index = 0;

        const interval = setInterval(() => {
            if (index < text.length) {
                container.textContent += text[index];
                index++;
            } else {
                clearInterval(interval);
                resolve();
            }
        }, 30);
    });
}

function lockButtons(disabled) {

    document.body.classList.toggle("summary-locking", disabled);


    uploadBtn.disabled = disabled;
    fileInput.disabled = disabled; 
    removeBtn.disabled = disabled; 
    summarizeBtn.disabled = disabled; 
    pdfButton.disabled = disabled; 
    copyButton.disabled = disabled; 


    uploadBox.style.pointerEvents = disabled ? "none" : "auto";
    uploadBox.style.opacity = disabled ? "0.7" : "1";

}

function updateStatusMessage(statusText) {
    status_text.innerText = statusText;
}

function refreshActionState() {
    const hasSummary = Boolean(meetingSummary);
    const canEditFile = !isSummaryLocked;

    uploadBtn.disabled = !canEditFile;
    fileInput.disabled = !canEditFile;
    removeBtn.disabled = !canEditFile;
    summarizeBtn.disabled = !canEditFile || !file;
    pdfButton.disabled = !canEditFile || !hasSummary;
    copyButton.disabled = !canEditFile || !hasSummary;

    uploadBox.style.pointerEvents = canEditFile ? "auto" : "none";
    uploadBox.style.opacity = canEditFile ? "1" : "0.7";
}

window.addEventListener("DOMContentLoaded", () => {
    refreshActionState();
});