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
      const isImage = file.type && file.type.startsWith('image/');
      const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
      const isDocx = file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc');

      if (isImage) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewImg.src = e.target.result;
          previewImg.style.display = 'block';
          if (previewFilename) previewFilename.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
          previewContainer.style.display = 'flex';
        };
        reader.readAsDataURL(file);
      } else {
        previewImg.style.display = 'none';
        previewImg.src = '';
        const badge = isPdf ? '📄 PDF Document: ' : isDocx ? '📝 Word Document: ' : '📄 ';
        if (previewFilename) previewFilename.textContent = `${badge}${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        previewContainer.style.display = 'flex';
      }
    } else {
      previewContainer.style.display = 'none';
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
