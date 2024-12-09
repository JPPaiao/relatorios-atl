const nav = document.getElementById('nav')
const gja = document.getElementById('gja')
const pga = document.getElementById('pga')

nav.addEventListener('click', renderTable)
gja.addEventListener('click', renderTable)
pga.addEventListener('click', renderTable)


function calcularDatasPadrao() {
  const hoje = new Date()
  
  const formatarData = (data) => {
    const dia = String(data.getDate()).padStart(2, '0')
    const mes = String(data.getMonth() + 1).padStart(2, '0') // getMonth() é zero-based
    const ano = data.getFullYear()
    // return `${dia}/${mes}/${ano}`
    return `${ano}-${mes}-${dia}`
  }

  // Data do mês atual (ano, mês e dia atual como padrão)
  const dataAtual = new Date()
  const dataAtualFormatada = formatarData(dataAtual)

  // Data de dois meses atrás
  const dataPassada = new Date()
  dataPassada.setMonth(dataPassada.getMonth() - 2)
  const dataPassadaFormatada = formatarData(dataPassada)

  return { dataAtualFormatada, dataPassadaFormatada }
}

document.addEventListener("DOMContentLoaded", () => {
  const datasPadrao = calcularDatasPadrao()

  document.getElementById("month-current").value = datasPadrao.dataPassadaFormatada
  document.getElementById("month-pass").value = datasPadrao.dataAtualFormatada
})


function selectButton(button) {
  // Remove a classe 'selected' de todos os botões
  let buttons = document.querySelectorAll('.button-restart')
  buttons.forEach(btn => btn.classList.remove('selected'))
  
  // Adiciona a classe 'selected' apenas ao botão clicado
  button.classList.add('selected')
}



async function renderTable(e) {
  const dataAtual = document.getElementById("month-current").value
  const dataPassada = document.getElementById("month-pass").value

  // Extrai o mês e o ano das datas selecionadas
  const mesAnoAtual = dataAtual.split("-") // Extrai [YYYY, MM]
  const mesAnoPassado = dataPassada.split("-") // Extrai [YYYY, MM]

  // Monta o intervalo de meses para enviar para o servidor (formato YYYY-MM a YYYY-MM)
  const meses = `${mesAnoPassado[2]}-${mesAnoPassado[1]}-${mesAnoPassado[0]}_${mesAnoAtual[2]}-${mesAnoAtual[1]}-${mesAnoAtual[0]}`

  const data = await fetch(`/read_sheet/${e.target.name}?months=${meses}`).then(d => d.json())
  let dataFormat = {
    colmns: [],
    data: []
  } 

  const dados_linhas = []
  
  if (data != null) {
    const totalRows = Object.keys(data).length
    if (dataFormat.data.length > 0) {
      dataFormat.data = []
    }

    for (let i=0; i<totalRows; i++) {
      dados_linhas.push({
        'UNIDADE': data[i]['UNIDADE'] || '',
        'TIPO': data[i]['TIPO'] || '',
        'OWNER': data[i]['OWNER'] || '',
        'ENTRADA': data[i]['ENTRADA'] || '',
        'CNPJ_AGENDADO': data[i]['CNPJ AGENDADO'] || '',
        'CNPJ_HBL': data[i]['CNPJ HBL'] || '',
        'TRANSPORTADORA': data[i]['TRANSPORTADORA'] || '',
        'CNPJ_TRANSPORTADORA': data[i]['CNPJ TRANSPORTADORA'] || '',
        'VALORES': data[i]['VALORES'] || '',
        'OBS': data[i]['OBS'] || '',
        'DATA_PAG': data[i]['DATA. PAG'] || '',
        'NF': data[i]['NF'] || '',
        'TERMO': data[i]['TERMO'] || '',
        'DOCUMENTACAO': data[i]['DOCUMENTACAO'] || '',
        'ISENTO': data[i]['ISENTO'] || '',
        'V_ISENTO': data[i]['V. ISENTO'] || '',
        'OBS_SAC': data[i]['OBS SAC'] || '',
        'SAC': data[i]['SAC'] || '',
      })
    }
  }

  if (dataFormat.colmns.length <= 0) {
    dataFormat.colmns = [
      { title: 'UNIDADE', data: 'UNIDADE' },
      { title: 'TIPO', data: 'TIPO' },
      { title: 'OWNER', data: 'OWNER' },
      { title: 'ENTRADA', data: 'ENTRADA' },
      { title: 'CNPJ AGENDADO', data: 'CNPJ_AGENDADO' }, 
      { title: 'CNPJ HBL', data: 'CNPJ_HBL' },
      { title: 'TRANSPORTADORA', data: 'TRANSPORTADORA' },
      { title: 'CNPJ TRANSPORTADORA', data: 'CNPJ_TRANSPORTADORA' },
      { title: 'VALORES', data: 'VALORES' },
      { title: 'OBS', data: 'OBS' },
      { title: 'DATA. PAG', data: 'DATA_PAG' },
      { title: 'NF', data: 'NF' },
      { title: 'TERMO', data: 'TERMO' },
      { title: 'DOCUMENTAÇÃO', data: 'DOCUMENTACAO' },
      { title: 'ISENTO', data: 'ISENTO' },
      { title: 'V. ISENTO', data: 'V_ISENTO' },
      { title: 'OBS SAC', data: 'OBS_SAC' },
      { title: 'SAC', data: 'SAC' }
    ]
  }

  dataFormat.data = dados_linhas

  function formatDate(data) {
    if (!data) return ''

    // Se a entrada contém data e hora
    if (data.includes('-') && data.includes(':') && data.length >= 19) {
        const [datePart, timePart] = data.split(' ') // Separa a data e a hora
        const [year, month, day] = datePart.split('-') // Divide a data no formato 'YYYY-MM-DD'
        return `${day}/${month}/${year} ${timePart}` // Retorna no formato 'DD/MM/YYYY HH:MM:SS'
    }

    // Se a entrada contém apenas a data
    if (data.includes('-') && data.length === 10) {
        const [year, month, day] = data.split('-') // Divide a data no formato 'YYYY-MM-DD'
        return `${day}/${month}/${year}` // Retorna no formato 'DD/MM/YYYY'
    }

    // Caso não seja uma data válida, retorna como está
    return data
}

  const table = $('#table-container').DataTable({
    data: dataFormat.data,
    columns: dataFormat.colmns,
    colReorder: true,
    displayLength: 100,
    scrollX: '98%',
    scrollY: '60vh',
    scrollCollapse: true,
    destroy: true,
    info: false,
    order: [[3, 'desc']],
    fixedColumns: {
      start: 1,
    },
    layout: {
      topStart: {
        buttons: ['copy', 'csv', 'pdf', 'print',
          {
            extend: 'excelHtml5',
            autoFilter: true,
            title: `Download_${e.target.name}_${meses}`
          },
        ]
      }
    },
    columnDefs: [
      {
        target: 3,
        render: (data, type, row) => {
          return formatDate(data)
        }
      },
      {
        target: 8,
        render: DataTable.render.number(null, null, 0, 'R$ ')
      },
      {
        target: 10,
        render: (data, type, row) => {
          return formatDate(data)
        }
      },
      {
        target: 13,
        render: DataTable.render.number(null, null, 0, 'R$ ')
      },
    ],
    initComplete: function () {
      this.api()
          .columns()
          .every(function () {
              let column = this
              let title = column.footer().textContent

              // Create input element
              let input = document.createElement('input')
              input.style = 'width: 76px'
              input.style = 'font-size: 12px'
              input.placeholder = title;
              column.footer().replaceChildren(input)

              // Event listener for user input
              input.addEventListener('keyup', () => {
                  if (column.search() !== this.value) {
                      column.search(input.value).draw()
                  }
              })
          })
    }
  })
}

