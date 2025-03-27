document.getElementById('update').addEventListener('click', (e) => {
  if (depot === null) {
    Swal.fire({
      title: 'Escolha um Depot primeiro',
      icon: 'error'
    })
  } else {
    upload(e)
  }
})

function upload(e) {
  Swal.fire({
    title: `Upload para ${depot.toUpperCase()}`,
    html: `
      <form id="upload-form" action="/create_sheet" method="POST" enctype="multipart/form-data">
        <div class="upload-container">
          <div class="drop-zone" id="drop-zone">
            <p>Arraste e solte seus arquivos aqui, ou <span class="upload-link">clique para selecionar</span></p>
            <input type="file" id="file-upload" class="file-upload-input" name="file">
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
      const fileInput = document.getElementById('file-upload')
      const fileList = document.getElementById('file-list')
      const progressContainer = document.getElementById('progress-container')
      const progressBar = document.getElementById('progress-bar')
      const uploadBtn = document.getElementById('uploadBtn')
      const uploadPercentage = document.getElementById('upload-percentage')
      const uploadForm = document.getElementById('upload-form')

      let file = null // Variável para armazenar o arquivo selecionado
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
          file = e.dataTransfer.files[0] // Pegar o único arquivo
          handleFile(file)
        } else {
          console.error("Vazio")
        }
      })

      // Manipular arquivos selecionados via seletor
      fileInput.addEventListener('change', () => {
        file = fileInput.files[0] // Pegar o único arquivo
        handleFile(file)
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

      
      // Função para iniciar o upload e monitorar o progresso
      async function handleUpload() {
        const formData = new FormData()
        formData.append('file', file)  // Anexar o arquivo corretamente no campo 'file'
        progressContainer.style.display = 'block'
        uploadBtn.disabled = true

        try {
          const data = await fetch(`/create_sheet/${depot}`, {
            method: 'POST',
            body: formData
          })

          const responseData = await data.json()
          requestId = responseData.request_id // Salvar o request_id

          console.log(`Upload iniciado. Request ID: ${requestId}`)

          const statusInterval = setInterval(async () => {
            const progressResponse = await fetch(`/progress/${requestId}`)
            .catch(e =>{
              Swal.fire({
                title: `<p>Erro no upload - ${e}<p>`,
                icon: 'error'
              })
              clearInterval(statusInterval)
            })
            console.log(progressResponse)
            
            if (progressResponse === undefined) {
              Swal.fire({
                title: `<p>Erro de servidor<p>`,
                icon: 'error'
              })
              clearInterval(statusInterval)
            }

            const dataProgress = await progressResponse.json()
            const progress = dataProgress.progress
  
            if (progress >= 100 || dataProgress.status === 'completed') {

              const link = document.createElement('a')
              link.href = `/download_processed_file/${requestId}`
  
              progressBar.style.width = `${progress}`
              uploadPercentage.textContent = `${progress}`
              uploadBtn.disabled = true
              fileList.innerHTML = ''
              progressContainer.style.display = 'block'
              
              clearInterval(statusInterval)
              Swal.fire({
                title: 'Processamento concluído!',
                text: "Deseja baixar o arquivo processado?",
                icon: 'success',
                showCancelButton: true,
                confirmButtonText: 'Baixar',
                cancelButtonText: 'Cancelar'
              })
              .then((result) => {
                if (result.isConfirmed) {
                  link.download = `${file.name}`
                  console.log(link)
                  link.click()
                  dataProgress.status = 'completed'
                }
              })
            } if (dataProgress.status === 'erro') {
              clearInterval(statusInterval)
              console.log('Erro no upload do arquivo:', dataProgress.erros)

              let errorListHTML = '<ul style="text-align: left;">'
              dataProgress.erros.forEach(erro => {
                errorListHTML += `<li><strong>Unidade:</strong> ${erro.unidade} | <strong>Data:</strong> ${erro.data} | <strong>Erro:</strong> ${erro.mensagem}</li>`
              })
              errorListHTML += '</ul>'

              Swal.fire({
                title: `Erro nos Remarks de ${depot.toUpperCase()} `,
                html: errorListHTML,
                icon: 'error'
              })
            } else {
              console.log(progress)
              progressBar.style.width = `${progress}%`
              uploadPercentage.textContent = `${progress}%`
            }
          }, 12000)
        } catch (error) {
          console.log(error)
          Swal.fire({
            title: `Erro no upload - ${error}`,
            icon: 'error'
          })
        }
      }

      // Manipular o envio do formulário
      uploadForm.addEventListener('submit', (e) => {
        e.preventDefault()  // Impede o envio padrão do formulário
        handleUpload()  // Envia o arquivo e inicia o monitoramento do progresso
      })
    }
  })
}
