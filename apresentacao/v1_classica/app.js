(() => {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const total = slides.length;
  const counterEl = document.getElementById("slide-counter");
  const progressEl = document.getElementById("progress-fill");
  const prevBtn = document.getElementById("btn-prev");
  const nextBtn = document.getElementById("btn-next");
  const overviewBtn = document.getElementById("btn-overview");
  const fullscreenBtn = document.getElementById("btn-fullscreen");
  const printBtn = document.getElementById("btn-print");

  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");
  const lightboxCap = document.getElementById("lightbox-cap");
  const lightboxClose = document.getElementById("lightbox-close");

  let current = 0;

  function parseHashIndex() {
    const match = window.location.hash.match(/slide-(\d+)/i);
    if (!match) return 0;
    const idx = parseInt(match[1], 10) - 1;
    return Number.isFinite(idx) && idx >= 0 && idx < total ? idx : 0;
  }

  function updateScale() {
    if (document.body.classList.contains("overview-mode")) return;
    const padW = 48;
    const padH = 92;
    const availW = Math.max(320, window.innerWidth - padW);
    const availH = Math.max(200, window.innerHeight - padH);
    const scale = Math.min(availW / 1280, availH / 720, 1.45);
    document.documentElement.style.setProperty("--slide-scale", scale.toFixed(4));
  }

  function renderSlide(index, updateHash = true) {
    current = Math.max(0, Math.min(total - 1, index));
    slides.forEach((s, i) => {
      s.classList.toggle("active", i === current);
    });
    if (counterEl) {
      counterEl.textContent = `${current + 1} / ${total}`;
    }
    if (progressEl) {
      progressEl.style.width = `${((current + 1) / total) * 100}%`;
    }
    if (prevBtn) prevBtn.disabled = current === 0;
    if (nextBtn) nextBtn.disabled = current === total - 1;

    if (updateHash) {
      history.replaceState(null, "", `#slide-${current + 1}`);
    }
  }

  function toggleOverview(forceState) {
    const nextState =
      typeof forceState === "boolean"
        ? forceState
        : !document.body.classList.contains("overview-mode");
    document.body.classList.toggle("overview-mode", nextState);
    if (overviewBtn) {
      overviewBtn.textContent = nextState ? "Modo Slide (G)" : "Grade (G)";
    }
    if (!nextState) {
      updateScale();
    }
  }

  function openLightbox(imgEl) {
    if (!lightbox || !lightboxImg) return;
    lightboxImg.src = imgEl.src;
    lightboxImg.alt = imgEl.alt || "";
    const fig = imgEl.closest(".fig-frame, .chart-card");
    const cap = fig ? fig.querySelector(".fig-caption, .chart-caption, .chart-takeaway") : null;
    lightboxCap.textContent = cap ? cap.textContent : imgEl.alt || "";
    lightbox.classList.add("open");
  }

  function closeLightbox() {
    if (lightbox) lightbox.classList.remove("open");
  }

  if (prevBtn) prevBtn.addEventListener("click", () => renderSlide(current - 1));
  if (nextBtn) nextBtn.addEventListener("click", () => renderSlide(current + 1));
  if (overviewBtn) overviewBtn.addEventListener("click", () => toggleOverview());
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      const wasOverview = document.body.classList.contains("overview-mode");
      if (wasOverview) toggleOverview(false);
      window.print();
    });
  }

  if (fullscreenBtn) {
    fullscreenBtn.addEventListener("click", () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
    });
  }

  slides.forEach((slide, idx) => {
    slide.addEventListener("click", (e) => {
      if (document.body.classList.contains("overview-mode")) {
        e.preventDefault();
        renderSlide(idx);
        toggleOverview(false);
      }
    });
  });

  document.querySelectorAll(".fig-frame img, .chart-card img").forEach((img) => {
    img.addEventListener("click", (e) => {
      if (document.body.classList.contains("overview-mode")) return;
      e.stopPropagation();
      openLightbox(img);
    });
  });

  if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
  if (lightbox) {
    lightbox.addEventListener("click", (e) => {
      if (e.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (lightbox && lightbox.classList.contains("open")) {
      if (e.key === "Escape") closeLightbox();
      return;
    }

    if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") {
      if (document.body.classList.contains("overview-mode")) return;
      e.preventDefault();
      renderSlide(current + 1);
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      if (document.body.classList.contains("overview-mode")) return;
      e.preventDefault();
      renderSlide(current - 1);
    } else if (e.key === "Home") {
      e.preventDefault();
      renderSlide(0);
    } else if (e.key === "End") {
      e.preventDefault();
      renderSlide(total - 1);
    } else if (e.key === "g" || e.key === "G") {
      e.preventDefault();
      toggleOverview();
    } else if (e.key === "f" || e.key === "F") {
      e.preventDefault();
      fullscreenBtn?.click();
    } else if (e.key === "Escape" && document.body.classList.contains("overview-mode")) {
      toggleOverview(false);
    }
  });

  window.addEventListener("resize", updateScale);
  window.addEventListener("hashchange", () => renderSlide(parseHashIndex(), false));

  updateScale();
  renderSlide(parseHashIndex(), false);
})();
