const uploadBtn = document.querySelector(".choose-file-btn");
const uploadBox = document.querySelector(".upload-box");
const fileInput = document.querySelector("#file-hidden-input");
const fileContent = document.querySelector(".file-content");
const removeBtn = document.querySelector(".remove-btn");
const summaryOutput = document.querySelector(".summary-container");
const API_BASED_URL = window.APP_CONFIG?.API_BASE_URL ?? "";

/*
const testResponse = {
    decisions: [
        {
            text: "Marketing team will avoid using the analytics tab until backend fix.",
            rationale: "Analytics tab likely to cause timeout due to ongoing database refactor."
        },
        {
            text: "Code freeze is set for September 25th.",
            rationale: "To allow full week of QA before release."
        },
        {
            text: "Ad sets launch on October 1st if budget approved.",
            rationale: "Maintaining launch schedule."
        },
        {
            text: "Status check meeting on Friday.",
            rationale: "To review progress."
        },
        {
            text: "Critical bugs will be logged in Jira with the Launch-Blocker tag.",
            rationale: "Ensure visibility to backend team."
        }
    ],

    discussion_points: [
        {
            text: "Beta build status: stable core workflow, new dashboard, analytics tab problematic; fix expected by Friday."
        },
        {
            text: "Marketing campaign readiness: ad copy, landing page, need sign-off by Thursday; ad launch on October 1st."
        },
        {
            text: "Finance approval status: request submitted Monday, finance out until Wednesday, follow up Thursday."
        },
        {
            text: "Code freeze target: September 25th; QA testing week; public release October 1st."
        },
        {
            text: "Bug logging protocol: use Jira Launch-Blocker tag for critical issues found during demo recording."
        },
        {
            text: "Next status check meeting scheduled for Friday."
        }
    ],

    overview: "Team aligned on Q4 product launch, addressing beta build readiness, marketing campaign schedule, finance approval timeline, code freeze, bug logging protocol, and next status check.",

    tasks_and_deadlines: [
        {
            task: "Fix analytics tab bug",
            assignee: "Elena",
            deadline: "Friday"
        },
        {
            task: "Follow up with finance for budget approval",
            assignee: "James",
            deadline: "Thursday"
        },
        {
            task: "Implement code freeze",
            assignee: null,
            deadline: "2026-09-25"
        },
        {
            task: "Record onboarding flow and main dashboard demos, avoid analytics tab",
            assignee: "Marketing team",
            deadline: "End of week"
        },
        {
            task: "Log critical bugs in Jira with Launch-Blocker tag",
            assignee: null,
            deadline: "Immediate"
        },
        {
            task: "Schedule status check meeting on Friday",
            assignee: "Sarah",
            deadline: "Friday"
        }
    ]
};

window.addEventListener('load', () => {
    displayResponse(testResponse);
});
*/


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