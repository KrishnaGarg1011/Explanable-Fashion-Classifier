// frontend/script.js

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const f = document.getElementById("fileInput").files[0];
  if (!f) return alert("Select an image first");
  const fd = new FormData();
  fd.append("image", f);
  const res = await fetch("/upload", { method: "POST", body: fd });
  const j = await res.json();
  alert("Saved as " + j.filename);
});

document.getElementById("classifyBtn").addEventListener("click", async () => {
  const f = document.getElementById("fileInput").files[0];
  if (!f) return alert("Select an image first");
  const fd = new FormData();
  fd.append("image", f);
  const res = await fetch("/predict", { method: "POST", body: fd });
  const j = await res.json();
  // update UI
  document.getElementById("result").style.display = "block";
  document.getElementById("preview").src = j.image_url;
  document.getElementById("label").innerText = "Label: " + j.label;
  document.getElementById("confidence").innerText = "Confidence: " + j.confidence.toFixed(3);
  document.getElementById("explanation").innerText = j.explanation;
  document.getElementById("cam").src = j.cam_url || '';
});
