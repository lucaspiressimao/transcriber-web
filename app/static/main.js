if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(() => console.log("✅ Service Worker registrado"))
        .catch(err => console.error("❌ Falha ao registrar SW:", err));
}

let deferredPrompt;
const installBtn = document.createElement('button');
installBtn.textContent = "📲 Instalar app";
installBtn.style.position = "fixed";
installBtn.style.bottom = "20px";
installBtn.style.right = "20px";
installBtn.style.zIndex = 1000;
installBtn.style.padding = "10px 16px";
installBtn.style.border = "none";
installBtn.style.borderRadius = "8px";
installBtn.style.backgroundColor = "#2d2d2d";
installBtn.style.color = "#fff";
installBtn.style.cursor = "pointer";
installBtn.style.fontSize = "16px";
installBtn.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.body.appendChild(installBtn);
});

installBtn.addEventListener('click', () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('Usuário aceitou instalar');
            } else {
                console.log('Usuário recusou');
            }
            deferredPrompt = null;
            installBtn.remove();
        });
    }
});

function getCookie(name) {
    const cookies = document.cookie.split("; ");
    for (let cookie of cookies) {
        const [key, value] = cookie.split("=");
        if (key === name) return decodeURIComponent(value);
    }
    return null;
}

document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const loader = document.getElementById("loader");
    const fileInput = document.getElementById("file-input");
    const transcriptionElement = document.getElementById("transcription");
    const emailChecked = document.getElementById('send_email');

    const sendEmail = getCookie("send_email");
    if (sendEmail) {
        document.getElementById("send_email").checked = true;
    }

    emailChecked?.addEventListener('change', function () {
        if (emailChecked.checked) {
            document.cookie = "send_email=true; path=/";
        } else {
            document.cookie = "send_email=; path=/";
        }
    });

    uploadForm?.addEventListener("submit", async function (e) {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;

        loader.style.display = "flex";
        transcriptionElement.innerText = "";

        const emailInput = document.getElementById('email');
        const sendEmailCheckbox = document.getElementById('send_email');

        const formData = new FormData();
        formData.append("file", file);
        formData.append("email", emailInput.value);
        formData.append("send_email", sendEmailCheckbox.checked ? "true" : "false");

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            const text = await response.text();
            if (!response.ok) throw new Error(text);

            document.open();
            document.write(text);
            document.close();
        } catch (err) {
            loader.innerHTML = `<div style="color:red;">❌ Erro ao transcrever: ${err.message}</div>`;
            setTimeout(() => loader.style.display = "none", 3000);
        }
    });
});

function setLang(lang) {
    document.cookie = "lang=" + lang + "; path=/";
    window.location.reload();
}

function copyTranscription() {
    const texto = document.getElementById("transcription").innerText;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(texto).then(() => {
            alert("✅ Transcrição copiada!");
        }).catch(err => {
            alert("Erro ao copiar: " + err);
        });
    } else {
        const textArea = document.createElement("textarea");
        textArea.value = texto;
        textArea.style.position = "fixed";
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const success = document.execCommand("copy");
            alert(success ? "✅ Copiado com sucesso" : "Erro ao copiar");
        } catch (err) {
            alert("Erro ao copiar: " + err);
        }

        document.body.removeChild(textArea);
    }
}
