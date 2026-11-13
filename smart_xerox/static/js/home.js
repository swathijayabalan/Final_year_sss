if (window.pdfjsLib) {
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
}
document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("document");
  if (!fileInput) return;
  const copiesInput = document.getElementById("copies");
  const typeInput = document.getElementById("print_type");
  const sidesInput = document.getElementById("sides");
  const amount = document.getElementById("amount");
  const info = document.getElementById("pageInfo");
  const fileName = document.getElementById("fileName");
  let pages = 0;
  function update() {
    const copies = Number(copiesInput.value);
    if (!pages || !Number.isInteger(copies) || copies < 1 || copies > 100) {
      amount.textContent = "₹0.00";
      return;
    }
    const key = typeInput.value + "_" + sidesInput.value;
    const rates = {bw_single: 2, bw_double: 3, color_single: 5, color_double: 8};
    const units = sidesInput.value === "double" ? Math.ceil(pages / 2) : pages;
    const rate = rates[key];
    amount.textContent = "₹" + (units * copies * rate).toFixed(2);
    info.textContent = `${pages} PDF pages · ${copies} copies · ₹${rate} per ${sidesInput.value === "double" ? "sheet" : "page"}`;
  }
  fileInput.addEventListener("change", async () => {
    pages = 0;
    amount.textContent = "₹0.00";
    const file = fileInput.files[0];
    if (!file) return;
    fileName.textContent = file.name;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size > 10 * 1024 * 1024) {
      alert("Choose a PDF file of 10 MB or smaller.");
      fileInput.value = "";
      fileName.textContent = "Drag your file here or browse";
      return;
    }
    if (!window.pdfjsLib) {
      info.textContent = "PDF preview library unavailable. Submit to calculate on the server.";
      return;
    }
    info.textContent = "Reading PDF pages…";
    try {
      const pdf = await pdfjsLib.getDocument({data: await file.arrayBuffer()}).promise;
      pages = pdf.numPages;
      update();
    } catch (e) {
      info.textContent = "Could not preview this PDF. Submit to let the server validate it.";
    }
  });
  [copiesInput, typeInput, sidesInput].forEach(el => {
    el.addEventListener("input", update);
    el.addEventListener("change", update);
  });
  document.getElementById("printForm").addEventListener("submit", () => {
    const button = document.getElementById("submitButton");
    button.disabled = true;
    button.textContent = "Creating your order…";
  });
});
