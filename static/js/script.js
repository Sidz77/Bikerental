// Show the scroll button when user scrolls down
window.addEventListener("scroll", function () {
    let scrollToTopBtn = document.getElementById("scrollToTop");
    if (window.scrollY > 300) {
        scrollToTopBtn.style.display = "block";
    } else {
        scrollToTopBtn.style.display = "none";
    }
});

// Scroll back to top when button is clicked
document.getElementById("scrollToTop").addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
});

document.addEventListener("DOMContentLoaded", function () {
    const counters = document.querySelectorAll(".counter");
    const statsSection = document.querySelector("#statsSection");
    let started = false; // To prevent re-triggering

    function startCounters() {
        counters.forEach(counter => {
            let target = +counter.getAttribute("data-target");
            let count = 0;
            let increment = Math.ceil(target / 100); // Smooth counting effect

            let updateCounter = setInterval(() => {
                count += increment;
                if (count >= target) {
                    counter.innerText = target + "+";
                    clearInterval(updateCounter);
                } else {
                    counter.innerText = count;
                }
            }, 30); // Speed of counting
        });
    }

    let observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !started) {
                startCounters();
                started = true; // Run only once
            }
        });
    }, { threshold: 0.5 });

    observer.observe(statsSection);
});

