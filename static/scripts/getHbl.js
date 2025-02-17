// const navHbl = document.getElementById('get-hbl-nav')
// const gjaHbl = document.getElementById('get-hbl-gja')
// const pgaHbl = document.getElementById('get-hbl-pga')

// navHbl.addEventListener('click', getHbls)
// gjaHbl.addEventListener('click', getHbls)

document.getElementById('get-hbl').addEventListener('click', (e) => {
  if (depot === null) {
    Swal.fire({
      title: 'Escolha um Depot primeiro',
      icon: 'error'
    })
  } else {
    getHbls(e)
  }
})

function getHbls(e) {
  Swal.fire({
    title: `Buscar HBLs de ${depot.toUpperCase()}`,
    html: `
      <form id="upload-form" action="/create_sheet" method="POST" enctype="multipart/form-data">
        <div class="upload-container">
          <div class="drop-zone" id="drop-zone">
            <p>Arraste e solte seus arquivos aqui, ou <span class="upload-link">clique para selecionar</span></p>
            <input type="file" id="file-hbl" class="file-upload-input" name="file-hbl">
          </div>
          <ul id="file-list"></ul>

          <div id="progress-container">
            <div id="progress-bar"></div>
          </div>

          <div class="progress-info">
            <button type="submit" id="uploadBtn" disabled>Enviar</button>
            <span class="percentage" id="upload-percentage">0%</span>
          </>
        </div>
      </form>
    `,
    width: '600px',
    showCloseButton: true,
    showConfirmButton: false,
    allowOutsideClick: false,
    allowEscapeKey: false,
    allowEnterKey: false,
    didOpen: () => {
      const dropZone = document.getElementById('drop-zone')
      const fileInput = document.getElementById('file-hbl')
      const fileList = document.getElementById('file-list')
      const progressContainer = document.getElementById('progress-container')
      const progressBar = document.getElementById('progress-bar')
      const uploadBtn = document.getElementById('uploadBtn')
      const uploadPercentage = document.getElementById('upload-percentage')
      const uploadForm = document.getElementById('upload-form')

      let fileHbl = null // Variável para armazenar o arquivo selecionado
      function preventDefaults(e) {
        e.preventDefault()
        e.stopPropagation()
      }

      // Abrir seletor de arquivos ao clicar na área
      dropZone.addEventListener('click', () => fileInput.click())


      if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
          dropZone.addEventListener(eventName, preventDefaults)
        })
      }

      // Estilizar ao arrastar sobre a área
      dropZone.addEventListener('dragover', () => dropZone.classList.add('dragging'))
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragging'))

      // Manipular arquivos arrastados
      dropZone.addEventListener('drop', (e) => {
        dropZone.classList.remove('dragging')

        if (e.dataTransfer && e.dataTransfer.files.length) {
          fileHbl = e.dataTransfer.files[0] // Pegar o único arquivo
          handleFile(fileHbl)
        } else {
          console.error("Vazio")
        }
      })

      // Manipular arquivos selecionados via seletor
      fileInput.addEventListener('change', () => {
        fileHbl = fileInput.files[0] // Pegar o único arquivo
        handleFile(fileHbl)
      })

      // Função para processar e listar o arquivo
      function handleFile(selectedFile) {
        fileList.innerHTML = '' // Limpa a lista anterior
        const li = document.createElement('li')
        li.textContent = selectedFile.name
        fileList.appendChild(li)

        // Habilita o botão de upload
        if (selectedFile) {
          uploadBtn.disabled = false
        }
      }

      async function handleUpload() {
        const formData = new FormData()
        formData.append('file', fileHbl)  // Anexar o arquivo corretamente no campo 'file'
        uploadBtn.disabled = true
        link = document.createElement('a')

        try {
          
          console.log(depot)
          const data = await fetch(`/get-hbl/${depot}`, {
            method: 'POST',
            body: formData
          })
          .catch(error => {
            Swal.fire({
            title: 'Erro ao enviar o arquivo!',
              icon: 'error'
            })
            console.error('Erro no upload do arquivo:', error)
          })

          if (!data.ok) {
            throw new Error('Erro durante o envio do arquivo.')
          }


          const contentDisposition = data.headers.get('Content-Disposition')
          let filename = 'arquivo_processado.xlsx'

          if (contentDisposition && contentDisposition.includes('filename=')) {
            const match = contentDisposition.match(/filename="(.+?)"/)
            if (match && match[1]) {
                filename = match[1]
            }
          }

          // Obter a resposta do servidor (link para download)
          const blob = await data.blob()
          const downloadUrl = window.URL.createObjectURL(blob)

          Swal.fire({
              title: 'Arquivo enviado com sucesso!',
              html: 'Clique no botão abaixo para baixar o arquivo processado.',
              icon: 'success',
              showCloseButton: true,
          }).then(() => {
              // Acionar o download automaticamente após clicar em "OK"
              const downloadLink = document.createElement('a')
              downloadLink.href = downloadUrl
              downloadLink.download = filename; // Usar o nome do arquivo do servidor
              document.body.appendChild(downloadLink); // Necessário para Firefox
              downloadLink.click();
              document.body.removeChild(downloadLink);
          })
        } catch (e) {
          console.error("Erro ao realizar o upload:", e)
          Swal.fire({
              title: 'Erro durante o upload!',
              text: 'Não foi possível enviar o arquivo',
              icon: 'error'
          })
        }
      }

      uploadForm.addEventListener('submit', (e) => {
        e.preventDefault()  // Impede o envio padrão do formulário
        handleUpload()  // Envia o arquivo e inicia o monitoramento do progresso
      })
    }
  })
}