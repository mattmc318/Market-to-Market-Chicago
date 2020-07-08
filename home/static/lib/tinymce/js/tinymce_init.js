tinymce.init({
  selector: '#id_body',
  mobile: {theme: 'mobile'},
  themes: 'modern',
  height: 480,
  menubar: false,
  plugins: [
    'autosave advlist autolink lists link image charmap print preview',
    'spellchecker searchreplace visualblocks code fullscreen',
    'insertdatetime media table paste help wordcount anchor'
  ],
  toolbar: 'undo redo | formatselect | ' +
    'bold italic underline link backcolor | alignleft aligncenter ' +
    'alignright alignjustify | bullist numlist outdent indent | ' +
    'removeformat spellchecker | help',
});