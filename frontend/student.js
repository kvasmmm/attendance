let editTimer = null;
let timeLeft = 5;
const HOST_IP = window.location.hostname;
const PORT = window.location.port || '8000';
const API_URL = `http://${HOST_IP}:${PORT}/student`;

const pinInput = document.getElementById('pinInput');
const studentIdInput = document.getElementById('studentIdInput');
const submitBtn = document.getElementById('submitBtn');
const statusMsg = document.getElementById('statusMessage');
const successMsg = document.getElementById('successMessage');

let currentSessionId = "";
let savedStudentId = "";
const baseUrl = window.location.origin + window.location.pathname;
let qrcodeObj = null;

qrcodeObj = new QRCode(document.getElementById("studentQrCode"), {
    text: baseUrl,
    width: 150,
    height: 150
});

function startEditTimer(startSeconds = 5) {
    timeLeft = startSeconds;
    submitBtn.disabled = false;
    submitBtn.innerText = `Edit Submission (${timeLeft}s)`;
    submitBtn.style.background = "#ffc107";
    submitBtn.style.color = "#000";

    clearInterval(editTimer);

    editTimer = setInterval(() => {
        timeLeft--;
        if (timeLeft > 0) {
            submitBtn.innerText = `Edit Submission (${timeLeft}s)`;
        } else {
            clearInterval(editTimer);
            submitBtn.innerText = "Locked 🔒";
            submitBtn.style.background = "#6c757d";
            submitBtn.style.color = "white";
            submitBtn.disabled = true;
            studentIdInput.disabled = true;
        }
    }, 1000);
}

function updateShareQR() {
    const currentPin = pinInput.value.trim();
    let shareUrl = baseUrl;

    if (currentPin) {
        shareUrl += `?pin=${currentPin}`;
    }

    qrcodeObj.clear();
    qrcodeObj.makeCode(shareUrl);
}

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('pin')) {
    const currentPinFromUrl = urlParams.get('pin');
    pinInput.value = currentPinFromUrl;
    pinInput.style.display = 'none';
}

updateShareQR();
pinInput.addEventListener('input', updateShareQR);

function checkLocalStorage() {
    const savedDataStr = localStorage.getItem('attendance_data');
    const urlParams = new URLSearchParams(window.location.search);
    const currentPinFromUrl = urlParams.get('pin');

    if (savedDataStr) {
        const savedData = JSON.parse(savedDataStr);

        if (currentPinFromUrl && savedData.pin !== currentPinFromUrl) {
            studentIdInput.value = savedData.student_id;
            localStorage.removeItem('attendance_data');
        } else {
            studentIdInput.value = savedData.student_id;
            savedStudentId = savedData.student_id;
            successMsg.style.display = 'block';
            studentIdInput.disabled = true;

            if (savedData.timestamp) {
                const elapsed = Math.floor((Date.now() - savedData.timestamp) / 1000);
                if (elapsed < 5) {
                    startEditTimer(5 - elapsed);
                } else {
                    submitBtn.innerText = "Locked 🔒";
                    submitBtn.style.background = "#6c757d";
                    submitBtn.style.color = "white";
                    submitBtn.disabled = true;
                }
            } else {
                submitBtn.innerText = "Locked 🔒";
                submitBtn.disabled = true;
            }
        }
    }
}

checkLocalStorage();

fetch(`${API_URL}/me`)
    .then(res => res.json())
    .then(data => {
        document.getElementById('ipDisplay').innerText = data.ip;
    })
    .catch(() => document.getElementById('ipDisplay').innerText = "Unknown");

const deviceStr = navigator.userAgent + screen.width + screen.height + navigator.hardwareConcurrency;
let hash = 0;
for (let i = 0; i < deviceStr.length; i++) {
    hash = ((hash << 5) - hash) + deviceStr.charCodeAt(i);
    hash |= 0;
}

const pseudoMac = Math.abs(hash).toString(16).toUpperCase().padStart(8, '0');
const formattedMac = pseudoMac.match(/.{1,2}/g).join(':');
document.getElementById('macDisplay').innerText = formattedMac;

async function submitAttendance() {
    if (submitBtn.innerText.includes("Edit Submission")) {
        clearInterval(editTimer);
        studentIdInput.disabled = false;
        submitBtn.innerText = "Save Changes";
        submitBtn.style.background = "#0056b3";
        submitBtn.style.color = "white";
        successMsg.style.display = 'none';
        studentIdInput.focus();
        return;
    }

    const pin = pinInput.value.trim();
    const studentId = studentIdInput.value.trim();
    statusMsg.innerText = "";

    if (!pin || !studentId) {
        statusMsg.innerText = "Please fill all fields.";
        return;
    }

    const idRegex = /^202\d{6}$/;
    if (!idRegex.test(studentId)) {
        statusMsg.innerText = "Invalid Student ID.";
        return;
    }

    submitBtn.disabled = true;

    const isEditMode = (submitBtn.innerText === "Save Changes");
    const endpoint = isEditMode ? '/edit' : '/submit';
    const payload = isEditMode
        ? { old_student_id: savedStudentId, new_student_id: studentId, pin: pin }
        : { student_id: studentId, pin: pin };

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: isEditMode ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            localStorage.setItem('attendance_data', JSON.stringify({
                student_id: studentId,
                pin: pin,
                session_id: result.session_id || currentSessionId,
                timestamp: Date.now()
            }));
            successMsg.style.display = 'block';
            studentIdInput.disabled = true;
            savedStudentId = studentId;

            startEditTimer(5);
        } else {
            statusMsg.innerText = result.detail || "Error occurred.";
            submitBtn.disabled = false;
        }
    } catch (e) {
        statusMsg.innerText = "Network error. Please try again.";
        submitBtn.disabled = false;
    }
}
