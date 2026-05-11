/* ===== Produce AI 2026 — Main JS ===== */

/* ===== IMAGE PREVIEW ===== */
function previewImage(event) {
  var file = event.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function (e) {
    var img  = document.getElementById("previewImg");
    var text = document.getElementById("uploadText");
    var btn  = document.getElementById("analyzeBtn");
    if (img)  { img.src = e.target.result; img.classList.remove("hidden"); }
    if (text) text.classList.add("hidden");
    if (btn)  btn.disabled = false;
  };
  reader.readAsDataURL(file);
}

/* ===== APP INIT ===== */
document.addEventListener("DOMContentLoaded", function () {

  var captureCanvas = document.createElement("canvas");
  var captureCtx = captureCanvas.getContext("2d");
  var cameraStream = null;
  var currentFacingMode = "environment";

  var useCameraBtn      = document.getElementById("useCameraBtn");
  var cameraPanel       = document.getElementById("cameraPanel");
  var cameraVideo       = document.getElementById("cameraVideo");
  var cameraFlipBtn     = document.getElementById("cameraFlipBtn");
  var cameraCaptureBtn  = document.getElementById("cameraCaptureBtn");
  var cameraRetakeBtn   = document.getElementById("cameraRetakeBtn");
  var cameraCloseBtn    = document.getElementById("cameraCloseBtn");
  var cameraStatus      = document.getElementById("cameraStatus");
  var cameraQualityHint = document.getElementById("cameraQualityHint");
  var imageSourceInput  = document.getElementById("imageSource");

  function setHidden(el, hidden) {
    if (!el) return;
    if (hidden) el.classList.add("hidden");
    else el.classList.remove("hidden");
  }

  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(function (t) { t.stop(); });
      cameraStream = null;
    }
    if (cameraVideo) cameraVideo.srcObject = null;
  }

  function setCameraStatus(text) {
    if (cameraStatus) cameraStatus.textContent = text || "";
  }

  function setQualityHint(text, level) {
    if (!cameraQualityHint) return;
    cameraQualityHint.textContent = text || "";
    cameraQualityHint.classList.remove("camera-quality-ok","camera-quality-warn","camera-quality-bad");
    if (level) cameraQualityHint.classList.add(level);
  }

  function analyzeQuality() {
    if (!captureCanvas.width || !captureCanvas.height) return;
    var imageData = captureCtx.getImageData(0, 0, captureCanvas.width, captureCanvas.height);
    var data = imageData.data;
    var len = data.length;
    var step = 32;
    var sum = 0;
    var sumSq = 0;
    var count = 0;
    for (var i = 0; i < len; i += step) {
      var r = data[i];
      var g = data[i + 1];
      var b = data[i + 2];
      var y = 0.299 * r + 0.587 * g + 0.114 * b;
      sum += y;
      sumSq += y * y;
      count++;
    }
    if (!count) return;
    var mean = sum / count;
    var variance = sumSq / count - mean * mean;
    var message = "";
    var level = "";
    if (mean < 45) {
      message = "Image looks very dark. Try moving to better light.";
      level = "camera-quality-bad";
    } else if (mean < 75) {
      message = "Image is a bit dark. Results may be less accurate.";
      level = "camera-quality-warn";
    } else {
      message = "Lighting looks good.";
      level = "camera-quality-ok";
    }
    if (variance < 220) {
      if (message) message += " ";
      message += "Image may be slightly blurry. Hold the camera steady.";
      if (level !== "camera-quality-bad") level = "camera-quality-warn";
    }
    setQualityHint(message, level);
  }

  function startCamera(facingMode) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraStatus("Camera not supported in this browser.");
      return;
    }
    var mode = facingMode || currentFacingMode;
    var constraints = {
      video: {
        facingMode: { ideal: mode },
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    };
    setCameraStatus("Starting camera…");
    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
      cameraStream = stream;
      if (cameraVideo) cameraVideo.srcObject = stream;
      currentFacingMode = mode;
      setCameraStatus("");
      if (cameraPanel) {
        setHidden(cameraPanel, false);
        cameraPanel.setAttribute("aria-hidden", "false");
      }
      if (cameraRetakeBtn) setHidden(cameraRetakeBtn, true);
      setQualityHint("", "");
    }).catch(function () {
      setCameraStatus("Unable to access camera. Check permissions.");
    });
  }

  if (useCameraBtn && cameraPanel && cameraVideo) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      useCameraBtn.disabled = true;
      useCameraBtn.textContent = "Camera not supported";
    } else {
      useCameraBtn.addEventListener("click", function () {
        if (cameraStream) {
          setHidden(cameraPanel, false);
          cameraPanel.setAttribute("aria-hidden", "false");
        } else {
          startCamera();
        }
      });
    }
  }

  if (cameraCloseBtn && cameraPanel) {
    cameraCloseBtn.addEventListener("click", function () {
      stopCamera();
      setHidden(cameraPanel, true);
      cameraPanel.setAttribute("aria-hidden", "true");
      setCameraStatus("");
      setQualityHint("", "");
    });
  }

  if (cameraFlipBtn) {
    cameraFlipBtn.addEventListener("click", function () {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
      var next = currentFacingMode === "environment" ? "user" : "environment";
      stopCamera();
      startCamera(next);
    });
  }

  /* ----- DRAG & DROP ----- */
  var zone      = document.getElementById("dropZone");
  var fileInput = document.getElementById("fileInput");
  if (zone && fileInput) {
    zone.addEventListener("dragover", function (e) {
      e.preventDefault(); zone.classList.add("dragging");
    });
    zone.addEventListener("dragleave", function () {
      zone.classList.remove("dragging");
    });
    zone.addEventListener("drop", function (e) {
      e.preventDefault(); zone.classList.remove("dragging");
      var file = e.dataTransfer.files[0];
      if (file) { fileInput.files = e.dataTransfer.files; previewImage({ target: { files: [file] } }); }
    });
  }

  if (cameraCaptureBtn && cameraVideo && fileInput) {
    cameraCaptureBtn.addEventListener("click", function () {
      if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) return;
      var vw = cameraVideo.videoWidth;
      var vh = cameraVideo.videoHeight;
      var maxSide = 1024;
      var scale = Math.min(maxSide / vw, maxSide / vh, 1);
      var cw = Math.round(vw * scale);
      var ch = Math.round(vh * scale);
      captureCanvas.width = cw;
      captureCanvas.height = ch;
      captureCtx.drawImage(cameraVideo, 0, 0, cw, ch);
      analyzeQuality();
      captureCanvas.toBlob(function (blob) {
        if (!blob) return;
        var file = new File([blob], "camera.jpg", { type: "image/jpeg" });
        var dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        previewImage({ target: fileInput });
        if (cameraRetakeBtn) setHidden(cameraRetakeBtn, false);
        if (imageSourceInput) imageSourceInput.value = "camera";
      }, "image/jpeg", 0.9);
    });
  }

  if (cameraRetakeBtn && fileInput) {
    cameraRetakeBtn.addEventListener("click", function () {
      var img  = document.getElementById("previewImg");
      var text = document.getElementById("uploadText");
      var btn  = document.getElementById("analyzeBtn");
      if (img) { img.src = ""; img.classList.add("hidden"); }
      if (text) text.classList.remove("hidden");
      if (btn) btn.disabled = true;
      fileInput.value = "";
      setQualityHint("", "");
      if (imageSourceInput) imageSourceInput.value = "upload";
    });
  }

  /* ----- FORM + SCAN OVERLAY ----- */
  var form = document.getElementById("predictForm");
  if (form) {
    form.addEventListener("submit", function () {
      var overlay = document.getElementById("scanOverlay");
      var btn     = document.getElementById("analyzeBtn");
      var btnText = document.getElementById("btnText");
      if (btn)     btn.disabled = true;
      if (btnText) btnText.textContent = "Analyzing…";
      if (overlay) { overlay.classList.add("active"); overlay.setAttribute("aria-hidden","false"); }
      var steps = document.querySelectorAll(".scan-step");
      var bar   = document.getElementById("scanProgressBar");
      steps.forEach(function (step, i) {
        setTimeout(function () {
          step.classList.add("done");
          if (bar) bar.style.width = ((i + 1) / steps.length * 100) + "%";
        }, i * 700 + 400);
      });
    });
  }

  /* ----- AI INSIGHTS COLLAPSIBLE ----- */
  var insightsTrigger = document.getElementById("insightsTrigger");
  var insightsPanel   = document.getElementById("insightsPanel");
  if (insightsTrigger && insightsPanel) {
    insightsTrigger.addEventListener("click", function () {
      var isOpen = insightsPanel.classList.toggle("open");
      insightsTrigger.setAttribute("aria-expanded", isOpen);
    });
  }

  /* ----- ANIMATE BARS ----- */
  document.querySelectorAll(".stat-bar-fill, .bar-value").forEach(function (el) {
    var w = el.getAttribute("data-width");
    if (w) {
      el.style.width = "0%";
      setTimeout(function () { el.style.width = w; }, 150);
    }
  });

  /* ----- STOP SCAN LINE AFTER 2s ----- */
  var resultImgWrap = document.getElementById("resultImageWrap");
  if (resultImgWrap) {
    setTimeout(function () { resultImgWrap.classList.remove("scanning"); }, 2000);
  }

});
