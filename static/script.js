document.addEventListener("DOMContentLoaded", () => {
    
    // --- Custom Cursor Logic ---
    const cursor = document.getElementById("custom-cursor");
    
    // Smooth trailing cursor position
    document.addEventListener("mousemove", (e) => {
        requestAnimationFrame(() => {
            if (cursor) {
                cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
            }
        });
    });

    // Add hovering effect when over interactive elements
    const interactiveElements = document.querySelectorAll('button, .theme-toggle, .audio-toggle, .sms-pill-btn, .sms-card-btn, a');
    interactiveElements.forEach(el => {
        el.addEventListener("mouseenter", () => {
            document.body.classList.add("hovering");
        });
        el.addEventListener("mouseleave", () => {
            document.body.classList.remove("hovering");
        });
    });

    // --- Theme Toggle Logic ---
    const themeToggle = document.getElementById("theme-toggle");
    const htmlEl = document.documentElement;
    
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            if (htmlEl.classList.contains("dark-mode")) {
                htmlEl.classList.remove("dark-mode");
                htmlEl.classList.add("light-mode");
            } else {
                htmlEl.classList.remove("light-mode");
                htmlEl.classList.add("dark-mode");
            }
        });
    }

    // --- Dual SMS Gateway Copy & Launch Logic ---
    const smsButtons = document.querySelectorAll(".sms-pill-btn, .sms-card-btn");
    const copyFeedback = document.getElementById("copy-feedback");
    let feedbackTimer;

    smsButtons.forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const phone = btn.getAttribute("data-phone");
            if (!phone) return;

            // Copy to clipboard
            try {
                await navigator.clipboard.writeText(phone);
                
                if (copyFeedback) {
                    copyFeedback.textContent = `Copied ${phone}! Send any SMS from your phone with zero internet required.`;
                    copyFeedback.classList.add("show");
                    clearTimeout(feedbackTimer);
                    feedbackTimer = setTimeout(() => {
                        copyFeedback.classList.remove("show");
                    }, 3500);
                }

                const actionLabel = btn.querySelector(".action-label");
                if (actionLabel) {
                    const originalText = actionLabel.textContent;
                    actionLabel.textContent = "Copied!";
                    setTimeout(() => {
                        actionLabel.textContent = originalText;
                    }, 2200);
                }
            } catch (err) {
                console.warn("Clipboard write failed:", err);
            }

            // On desktop, prevent default sms: handler to avoid OS protocol errors,
            // while allowing native SMS apps to launch on mobile devices.
            const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
            if (!isMobile) {
                e.preventDefault();
            }
        });
    });

    // --- Audio Logic ---
    const bgAudio = document.getElementById("bg-audio");
    const audioToggle = document.getElementById("audio-toggle");
    const playIcon = document.getElementById("audio-icon-play");
    const pauseIcon = document.getElementById("audio-icon-pause");
    
    if (bgAudio && audioToggle) {
        bgAudio.volume = 0.4;
        let isPlaying = false;
        let fadeInterval;
        let isFadingOutForLoop = false;

        function fadeAudio(targetVolume, duration) {
            clearInterval(fadeInterval);
            const steps = 20;
            const stepTime = duration / steps;
            const volumeStep = (targetVolume - bgAudio.volume) / steps;
            
            fadeInterval = setInterval(() => {
                let newVolume = bgAudio.volume + volumeStep;
                if (newVolume < 0) newVolume = 0;
                if (newVolume > 1) newVolume = 1;
                
                bgAudio.volume = newVolume;
                
                if ((volumeStep > 0 && bgAudio.volume >= targetVolume) || 
                    (volumeStep < 0 && bgAudio.volume <= targetVolume)) {
                    bgAudio.volume = targetVolume;
                    clearInterval(fadeInterval);
                }
            }, stepTime);
        }

        audioToggle.addEventListener("click", (e) => {
            e.stopPropagation(); // Prevent this click from triggering document interact
            if (!isPlaying) {
                bgAudio.volume = 0;
                bgAudio.play();
                fadeAudio(0.2, 1000);
                if (playIcon) playIcon.style.display = "none";
                if (pauseIcon) pauseIcon.style.display = "block";
                isPlaying = true;
                isFadingOutForLoop = false;
            } else {
                fadeAudio(0, 1000);
                setTimeout(() => { bgAudio.pause(); }, 1000);
                if (playIcon) playIcon.style.display = "block";
                if (pauseIcon) pauseIcon.style.display = "none";
                isPlaying = false;
            }
        });

        bgAudio.addEventListener("timeupdate", () => {
            if (isPlaying && bgAudio.duration > 0) {
                const timeRemaining = bgAudio.duration - bgAudio.currentTime;
                if (timeRemaining <= 1.5 && !isFadingOutForLoop) {
                    isFadingOutForLoop = true;
                    fadeAudio(0, 1400); // Start fading out just before the track ends
                }
            }
        });
        
        bgAudio.addEventListener("ended", () => {
            if (isPlaying) {
                bgAudio.currentTime = 0;
                bgAudio.play();
                isFadingOutForLoop = false;
                fadeAudio(0.2, 1000); // Fade back in for the new loop
            }
        });

        // Attempt Autoplay
        const attemptAutoplay = async () => {
            try {
                bgAudio.volume = 0;
                await bgAudio.play();
                fadeAudio(0.2, 2000); // Gentle 2s fade in on load
                if (playIcon) playIcon.style.display = "none";
                if (pauseIcon) pauseIcon.style.display = "block";
                isPlaying = true;
                isFadingOutForLoop = false;
            } catch (err) {
                console.log("Autoplay blocked. Waiting for first interaction...");
                const startOnInteract = () => {
                    if (!isPlaying) {
                        bgAudio.volume = 0;
                        bgAudio.play();
                        fadeAudio(0.2, 2000);
                        if (playIcon) playIcon.style.display = "none";
                        if (pauseIcon) pauseIcon.style.display = "block";
                        isPlaying = true;
                        isFadingOutForLoop = false;
                    }
                    document.removeEventListener("click", startOnInteract);
                };
                document.addEventListener("click", startOnInteract);
            }
        };

        attemptAutoplay();
    }
});
