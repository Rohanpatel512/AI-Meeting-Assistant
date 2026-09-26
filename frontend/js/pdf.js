function cleanPdfText(value) {
    return String(value ?? "")
        .replace(/[\u200B-\u200D]/g, "")
        .replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\uFEFF]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

export function generatePDF(meetingSummary) {
    if (!meetingSummary) {
        alert("No meeting summary available.");
        return;
    }

    const jspdfLib = window.jspdf;
    if (!jspdfLib || !jspdfLib.jsPDF) {
        alert("PDF library failed to load. Please refresh the page and try again.");
        return;
    }

    const { jsPDF } = jspdfLib;
    const doc = new jsPDF();

    // Page settings
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    const margin = 20;
    const contentWidth = pageWidth - margin * 2;

    let y = margin;

  
    function checkPageBreak(requiredHeight = 10) {
        if (y + requiredHeight > pageHeight - margin) {
            doc.addPage();
            y = margin;
            return true;
        }

        return false;
    }


    function addWrappedText(text, x, fontSize = 11, lineHeight = 6) {
        doc.setFontSize(fontSize);

        const cleanText = cleanPdfText(text);
        const lines = doc.splitTextToSize(cleanText || " ", contentWidth);

        for (const line of lines) {
            checkPageBreak(lineHeight);

            doc.text(line, x, y);
            y += lineHeight;
        }
    }


    function addSectionHeading(title) {
        checkPageBreak(20);

        y += 5;

        doc.setFont("helvetica", "bold");
        doc.setFontSize(15);

        doc.text(title, margin, y);

        y += 8;

        // Small divider line
        doc.setLineWidth(0.3);
        doc.line(margin, y, pageWidth - margin, y);

        y += 7;

        doc.setFont("helvetica", "normal");
    }

    function addBullet(text) {
        const cleanedText = cleanPdfText(text);

        if (!cleanedText) {
            return;
        }

        doc.setFont("helvetica", "normal");
        doc.setFontSize(11);

        const bulletX = margin;
        const textX = margin + 6;
        const bulletWidth = contentWidth - 6;

        const lines = doc.splitTextToSize(cleanedText, bulletWidth);

        checkPageBreak(lines.length * 6);

        doc.text("•", bulletX, y);

        for (let i = 0; i < lines.length; i++) {
            if (i > 0) {
                checkPageBreak(6);
                y += 6;
            }

            doc.text(lines[i], textX, y);
        }

        y += 7;
    }

    function addTask(taskItem) {
        let taskText;
        let deadline = null;

        if (typeof taskItem === "string") {
            taskText = taskItem;
        } else if (taskItem && typeof taskItem === "object") {
            taskText =
                taskItem.task ||
                taskItem.title ||
                taskItem.description ||
                "";

            deadline =
                taskItem.deadline ||
                taskItem.due_date ||
                taskItem.dueDate ||
                null;
        }

        if (!taskText) {
            return;
        }

        doc.setFont("helvetica", "normal");
        doc.setFontSize(11);

        let fullText = cleanPdfText(taskText);

        if (deadline) {
            fullText += ` — Deadline: ${cleanPdfText(deadline)}`;
        }

        addBullet(fullText);
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);

    doc.text("Meeting Summary", margin, y);

    y += 10;

    // Subtitle
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);

    doc.text(
        `Generated on ${new Date().toLocaleDateString()}`,
        margin,
        y
    );

    y += 10;

    // Divider
    doc.setLineWidth(0.5);
    doc.line(margin, y, pageWidth - margin, y);

    y += 10;

    addSectionHeading("Overview");

    if (meetingSummary.overview) {
        const overviewText = cleanPdfText(meetingSummary.overview);

        addWrappedText(
            overviewText,
            margin,
            11,
            6
        );
    } else {
        addWrappedText(
            "No overview provided.",
            margin,
            11,
            6
        );
    }

    addSectionHeading("Key Discussion Points");

    if (
        Array.isArray(meetingSummary.discussion_points) &&
        meetingSummary.discussion_points.length > 0
    ) {
        meetingSummary.discussion_points.forEach(point => {
            addBullet(point.text);
        });
    } else {
        addWrappedText(
            "No discussion points provided.",
            margin,
            11,
            6
        );
    }

    addSectionHeading("Tasks & Deadlines");

    if (
        Array.isArray(meetingSummary.tasks) &&
        meetingSummary.tasks.length > 0
    ) {
        meetingSummary.tasks.forEach(task => {
            addTask(task);
        });
    } else if (
        Array.isArray(meetingSummary.tasks_and_deadlines) &&
        meetingSummary.tasks_and_deadlines.length > 0
    ) {
        meetingSummary.tasks_and_deadlines.forEach(task => {
            addTask(task);
        });
    } else {
        addWrappedText(
            "No tasks or deadlines provided.",
            margin,
            11,
            6
        );
    }

    addSectionHeading("Decisions");

    if (
        Array.isArray(meetingSummary.decisions) &&
        meetingSummary.decisions.length > 0
    ) {
        meetingSummary.decisions.forEach(decision => {
            const decisionText = cleanPdfText(decision.text);
            const rationaleText = decision.rationale ? ` ${cleanPdfText(decision.rationale)}` : "";
            addBullet(decisionText + rationaleText);
        });
    } else {
        addWrappedText(
            "No decisions provided.",
            margin,
            11,
            6
        );
    }

    const totalPages = doc.internal.getNumberOfPages();

    for (let page = 1; page <= totalPages; page++) {
        doc.setPage(page);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);

        doc.text(
            `Page ${page} of ${totalPages}`,
            pageWidth - margin,
            pageHeight - 10,
            { align: "right" }
        );
    }

    doc.save("meeting-summary.pdf");
}