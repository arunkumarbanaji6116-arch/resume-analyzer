const resumeForm = document.querySelector('form');
const fileInput = document.getElementById('resume-file-input');
const previewContainer = document.getElementById('image-preview-container');
const previewImg = document.getElementById('image-preview');
const previewFilename = document.getElementById('preview-filename');
const dropzone = document.getElementById('resume-dropzone');

if (fileInput && previewContainer && previewImg) {
  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        if (previewFilename) previewFilename.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        previewContainer.style.display = 'flex';
      };
      reader.readAsDataURL(file);
    }
  });
}

if (resumeForm) {
  resumeForm.addEventListener('submit', () => {
    const button = resumeForm.querySelector('#analyze-btn') || resumeForm.querySelector('button');
    if (button) {
      button.textContent = 'Extracting text & reviewing with AI...';
      button.disabled = true;
      button.style.opacity = '0.75';
    }
  });
}
