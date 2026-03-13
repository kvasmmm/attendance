const HOST_IP = window.location.hostname;
const PORT = window.location.port || '8000';
const API_BASE = `http://${HOST_IP}:${PORT}/professor`;

let currentSessionId = "";
let ws = null;

window.onload = async () => {
    try {
        const response = await fetch(`${API_BASE}/session/active`);
        const data = await response.json();

        if (data.active) {
            currentSessionId = data.session_id;

            document.getElementById('setupSection').style.display = 'none';
            document.getElementById('dashboardSection').style.display = 'block';
            document.getElementById('pinDisplay').innerText = data.pin;
            document.getElementById('exportCsv').href = `${API_BASE}/export/${currentSessionId}/csv`;

            const studentUrl = `http://${HOST_IP}:${PORT}/student.html?pin=${data.pin}`;
            new QRCode(document.getElementById("qrcode"), {
                text: studentUrl,
                width: 150,
                height: 150
            });

            data.students.forEach(student => addStudentToTable(student));
            connectWebSocket();
        }
    } catch (e) {
        console.error("Error checking active session:", e);
    }
};

async function startSession() {
    const response = await fetch(`${API_BASE}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: "QR" })
    });

    const data = await response.json();
    currentSessionId = data.session_id;

    document.getElementById('setupSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('pinDisplay').innerText = data.pin;
    document.getElementById('exportCsv').href = `${API_BASE}/export/${currentSessionId}/csv`;

    const studentUrl = `http://${HOST_IP}:${PORT}/student.html?pin=${data.pin}`;
    new QRCode(document.getElementById("qrcode"), {
        text: studentUrl,
        width: 150,
        height: 150
    });

    connectWebSocket();
}

function connectWebSocket() {
    ws = new WebSocket(`ws://${HOST_IP}:${PORT}/professor/ws`);
    const statusEl = document.getElementById('connectionStatus');

    ws.onopen = () => {
        statusEl.innerText = "● Live connected";
        statusEl.style.color = "green";
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "new_student") {
            addStudentToTable(data);
        } else if (data.event === "delete_student") {
            removeStudentFromTable(data.student_id);
        } else if (data.event === "edit_student") {
            updateStudentInTable(data.old_student_id, data.new_student_id, data.timestamp);
        }
    };

    ws.onclose = () => {
        statusEl.innerText = "● Disconnected";
        statusEl.style.color = "red";
    };
}

function addStudentToTable(data) {
    const tbody = document.getElementById('studentTableBody');
    const row = document.createElement('tr');
    row.id = `row-${data.student_id}`;

    const time = new Date(data.timestamp).toLocaleTimeString();

    const badgeHtml = data.manual_entry
        ? `<span class="badge" style="background: #dc3545;">Manual</span>`
        : `<span class="badge">Auto</span>`;

    row.innerHTML = `
        <td class="st-id"><strong>${data.student_id}</strong></td>
        <td class="st-time">${time}</td>
        <td>${data.ip} <br> ${badgeHtml}</td>
        <td>
            <button onclick="profEditStudent('${data.student_id}')" style="background:#ffc107; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Edit</button>
            <button onclick="profDeleteStudent('${data.student_id}')" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Del</button>
        </td>
    `;
    tbody.insertBefore(row, tbody.firstChild);

    const countEl = document.getElementById('studentCount');
    countEl.innerText = parseInt(countEl.innerText) + 1;
}

function removeStudentFromTable(studentId) {
    const row = document.getElementById(`row-${studentId}`);
    if (row) {
        row.remove();
        const countEl = document.getElementById('studentCount');
        countEl.innerText = Math.max(0, parseInt(countEl.innerText) - 1);
    }
}

function updateStudentInTable(oldId, newId, timestamp) {
    const row = document.getElementById(`row-${oldId}`);
    if (row) {
        row.id = `row-${newId}`;
        row.querySelector('.st-id').innerHTML = `<strong>${newId}</strong>`;
        row.querySelector('.st-time').innerText = new Date(timestamp).toLocaleTimeString();
        row.cells[3].innerHTML = `
            <button onclick="profEditStudent('${newId}')" style="background:#ffc107; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Edit</button>
            <button onclick="profDeleteStudent('${newId}')" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Del</button>
        `;
    }
}

async function profAddStudent() {
    const inputStr = document.getElementById('manualStudentId').value.trim();
    const errorDiv = document.getElementById('manualError');
    errorDiv.innerText = "";

    const idRegex = /^202\d{6}$/;
    if (!idRegex.test(inputStr)) {
        errorDiv.innerText = "Must be 9 digits starting with 202.";
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/session/${currentSessionId}/student/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: inputStr })
        });

        if (response.ok) {
            document.getElementById('manualStudentId').value = "";
        } else {
            const result = await response.json();
            errorDiv.innerText = result.detail || "Error adding student.";
        }
    } catch (e) {
        errorDiv.innerText = "Network error.";
    }
}

async function profDeleteStudent(studentId) {
    if (confirm(`Delete student ${studentId}?`)) {
        await fetch(`${API_BASE}/session/${currentSessionId}/student/${studentId}`, { method: 'DELETE' });
    }
}

async function profEditStudent(oldStudentId) {
    const newStudentId = prompt("Enter new Student ID:", oldStudentId);
    if (newStudentId && newStudentId !== oldStudentId) {
        await fetch(`${API_BASE}/session/${currentSessionId}/student`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_student_id: oldStudentId, new_student_id: newStudentId })
        });
    }
}

async function closeSession() {
    if (confirm("Are you sure you want to close this session? Students will no longer be able to submit.")) {
        await fetch(`${API_BASE}/session/${currentSessionId}/close`, { method: 'POST' });
        alert("Session closed.");
        document.querySelector('.close-btn').disabled = true;
        document.querySelector('.close-btn').style.background = '#ccc';
    }
}
