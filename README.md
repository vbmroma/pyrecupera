Data Recovery Tool - Enterprise Edition

Uma ferramenta avançada de análise forense e extração de dados (recuperação lógica e física), desenvolvida inteiramente em Python. Com uma interface gráfica intuitiva, este software permite desde a cópia estruturada de arquivos existentes até o *File Carving* profundo para resgatar arquivos deletados ou partições formatadas direto do disco bruto.

Funcionalidades Principais

- **Modo Estruturado (Recuperação Lógica):** Mapeia e copia a árvore de diretórios preservando a estrutura original. Útil para backup de discos corrompidos onde os arquivos ainda estão logicamente acessíveis.
- **Busca Profunda (File Carving):** Lê o disco em nível físico (Raw File Carving) utilizando *Magic Numbers* (assinaturas hexadecimais) para encontrar e recuperar arquivos apagados ou formatados.
- **Formatos Suportados na Busca Profunda:**
  - **Imagens:** JPG (com extração de data EXIF para nomeação) e PNG.
  - **Documentos:** PDFs.
  - **Pacote Office:** Modernos (.docx, .xlsx, .pptx, arquivos .zip) e Antigos (.doc, .xls, .ppt) com análise heurística OLE2/ZIP para identificar a extensão correta.
  - **Vídeos:** MP4 e MKV.
- **Análise de Relatório MFT (Ghost Reader Forense):** Varre cabeçalhos MFT da tabela do Windows para extrair os nomes originais e offsets de arquivos/pastas que foram apagados, gerando um relatório forense detalhado (`Relatorio_Forense_Apagados.txt`).
- **Smart Carving:** Mecanismos de segurança para evitar arquivos gigantes (*Slack Space Detection* através de blocos `\x00` e detecção de *Footers*).
- **Monitoramento em Tempo Real:**
  - Barra de progresso responsiva (Threads separadas da UI).
  - Logs detalhados da operação.
  - Pré-visualização Hexadecimal contínua (Live Preview) dos blocos em análise.
- **Banco de Assinaturas Dinâmico:** Utiliza um arquivo `assinaturas.json` customizável para adicionar novos *Magic Numbers* sem alterar o código principal.

Avisos Importantes de Segurança

1. **Execute como Administrador/Root:** Para ler o disco fisicamente (ex: `\\.\E:` ou `/dev/sdb`), o Python **precisa** de privilégios elevados. Se executado sem permissão, a varredura profunda falhará.
2. **NUNCA salve no disco que está sendo recuperado!** Salvar arquivos na mesma unidade que você está tentando recuperar vai sobrescrever dados apagados e destruí-los para sempre. Sempre selecione uma *Pasta de Destino* em um disco/pendrive diferente.

Pré-requisitos

A ferramenta não depende de bibliotecas de terceiros complexas, facilitando a execução. As bibliotecas usadas são nativas do Python:
- Python 3.7+
- `tkinter` (Geralmente embutido no Python no Windows. No Linux pode ser necessário instalar: `sudo apt install python3-tk`).

Como Usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/vbmroma/pyrecupera.git
   cd SEU_REPOSITORIO
   ```

2. Execute o script como **Administrador**:
   - **Windows:** Abra o Prompt de Comando (CMD) ou PowerShell como Administrador e execute:
     ```bash
     python recuperador.py
     ```
   - **Linux/Mac:** 
     ```bash
     sudo python3 recuperador.py
     ```

3. Na interface do programa:
   - **Unidade do Disco:** Informe a letra (Ex: `E:`) ou o caminho físico (`\\.\PhysicalDrive1`).
   - **Pasta de Destino:** Escolha a pasta (em outro disco) onde os arquivos serão salvos.
   - Escolha o modo de operação (Estruturado ou Busca Profunda escolhendo os filtros).
   - Clique em **Iniciar Recuperação**.

Arquitetura e Padrões (Technical Details)

- **Assinaturas (Magic Numbers):** O programa busca cabeçalhos hexadecimais específicos na leitura bruta de blocos de `4096 bytes`. Quando encontra (ex: `ffd8ff` para JPG), ele inicia a extração até atingir o rodapé (`ffd9`) ou o tamanho máximo permitido no JSON.
- **Concorrência Segura:** Utiliza a biblioteca `threading` para realizar a I/O pesada de leitura de disco fora da Main Thread, evitando o congelamento da interface do `tkinter`. As atualizações de interface (*Progress bar, Logs, Preview Hex*) são despachadas seguramente de volta à Main Thread via `self.root.after()`.
- **Tipagem Robusta:** Código documentado e implementado usando a biblioteca `typing` (Dict, Any, Optional) para facilitar manutenção.

Contribuição

Contribuições são bem-vindas! Se você quiser adicionar suporte a novos formatos de arquivo, melhorar a precisão do File Carving ou aprimorar a leitura MFT, fique à vontade para abrir uma *Issue* ou enviar um *Pull Request*.

1. Faça um Fork do projeto.
2. Crie uma Branch para sua feature (`git checkout -b feature/NovoFormato`).
3. Faça o Commit de suas mudanças (`git commit -m 'Adiciona suporte a PDF e ZIP'`).
4. Faça o Push para a Branch (`git push origin feature/NovoFormato`).
5. Abra um Pull Request.

Aviso Legal

Esta ferramenta foi desenvolvida para fins educacionais, de pesquisa em Segurança da Informação (Forense) e recuperação pessoal de dados de forma lícita. 
O autor não se responsabiliza pelo mau uso da ferramenta ou por perdas de dados resultantes do seu uso inadequado (como a sobrescrita acidental).
