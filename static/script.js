document.addEventListener("DOMContentLoaded", () => {
    
    // --- Custom Cursor Logic ---
    const cursor = document.getElementById("custom-cursor");
    
    // Update cursor position
    document.addEventListener("mousemove", (e) => {
        requestAnimationFrame(() => {
            if (cursor) {
                cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
            }
        });
    });

    // Add hovering effect when over interactive elements
    const interactiveElements = document.querySelectorAll('button, .sms-card-btn, a');
    interactiveElements.forEach(el => {
        el.addEventListener("mouseenter", () => {
            document.body.classList.add("hovering");
        });
        el.addEventListener("mouseleave", () => {
            document.body.classList.remove("hovering");
        });
    });

    // --- Dual SMS Gateway Copy & Launch Logic ---
    const smsButtons = document.querySelectorAll(".sms-card-btn");
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
                    copyFeedback.textContent = `Copied ${phone}! Send any SMS from your phone to start chatting live.`;
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
                    }, 2000);
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
});
