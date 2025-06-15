let lastMessage = "";
let lastSpokenTime = 0;
const repeatDelay = 5000;

function speak(text) {
    const synth = window.speechSynthesis;

    // Fix: cancel any pending/ongoing utterance
    if (synth.speaking || synth.pending) {
        synth.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    synth.speak(utterance);
}

function fetchFeedback() {
    fetch("/feedback")
        .then(response => response.json())
        .then(data => {
            const currentTime = Date.now();
            const message = data.message;

            if (!message) return;

            const isNewMessage = message !== lastMessage;
            const isDelayPassed = (currentTime - lastSpokenTime) > repeatDelay;

            if (isNewMessage || isDelayPassed) {
                speak(message);
                lastMessage = message;
                lastSpokenTime = currentTime;
            }
        });
}

// Voice requires user interaction in some browsers
window.addEventListener("click", () => {
    if (speechSynthesis.paused) {
        speechSynthesis.resume();
    }
}, { once: true });

setInterval(fetchFeedback, 1000);
