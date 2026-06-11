import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import re
from typing import Dict, Any, Tuple, Optional

# 6. Banco de Dados Dinâmico de Assinaturas (Magic Numbers & Footers)
DEFAULT_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "jpg": {"header": "ffd8ff", "footer": "ffd9", "max_size": 10485760},
    "png": {"header": "89504e470d0a1a0a", "footer": "49454e44ae426082", "max_size": 10485760},
    "pdf": {"header": "255044462d", "footer": "2525454f46", "max_size": 20971520},
    "office_moderno_ou_zip": {"header": "504b0304", "footer": "", "max_size": 52428800},
    "office_antigo": {"header": "d0cf11e0a1b11ae1", "footer": "", "max_size": 20971520},
    "mp4": {"header": "66747970", "footer": "", "max_size": 104857600},
    "mkv": {"header": "1a45dfa3", "footer": "", "max_size": 104857600},
    "mft": {"header": "46494c4530", "footer": "", "max_size": 1024}
}

class RecuperadorApp:
    """
    Data Recovery Tool - Ferramenta avançada de análise forense e extração lógica/física.
    Implementa padrões Senior de tipagem, separação de UI e concorrência segura.
    """
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Data Recovery Tool - Enterprise Edition")
        self.root.geometry("800x650")
        
        # Variáveis de controle
        self.caminho_destino = tk.StringVar()
        self.caminho_drive = tk.StringVar(value="E:") # Padrão amigável
        self.rodando: bool = False

        # Filtros (Desmarcando Imagens e PDFs, e marcando Office por padrão)
        self.var_imagens = tk.BooleanVar(value=False)
        self.var_pdf = tk.BooleanVar(value=False)
        self.var_office = tk.BooleanVar(value=True)
        self.var_videos = tk.BooleanVar(value=False)
        self.var_mft = tk.BooleanVar(value=False)
        self.var_modo_logico = tk.BooleanVar(value=False)

        self._construir_interface()

    def _construir_interface(self):
        # Frame de Configuração
        frame_config = ttk.LabelFrame(self.root, text="Configurações de Leitura", padding=(10, 10))
        frame_config.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_config, text="Unidade do Disco:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame_config, textvariable=self.caminho_drive, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_config, text="(Ex: E: ou D:)", font=("Arial", 8)).grid(row=1, column=1, sticky="w")

        ttk.Label(frame_config, text="Pasta de Destino:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame_config, textvariable=self.caminho_destino, width=40, state="readonly").grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame_config, text="Procurar...", command=self.selecionar_destino).grid(row=2, column=2, padx=5, pady=5)

        # Modo Lógico
        self.chk_logico = ttk.Checkbutton(frame_config, text="Modo Estruturado (COPIA APENAS O QUE AINDA EXISTE - Não recupera deletados)", variable=self.var_modo_logico, command=self._toggle_filtros)
        self.chk_logico.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)

        # Frame de Filtros
        frame_filtros = ttk.LabelFrame(self.root, text="Busca Profunda (Recuperação de Apagados/Formatados)", padding=(10, 10))
        frame_filtros.pack(fill="x", padx=10, pady=5)

        self.chk_img = ttk.Checkbutton(frame_filtros, text="Imagens", variable=self.var_imagens)
        self.chk_img.pack(side="left", padx=10)
        self.chk_pdf = ttk.Checkbutton(frame_filtros, text="PDFs", variable=self.var_pdf)
        self.chk_pdf.pack(side="left", padx=10)
        self.chk_office = ttk.Checkbutton(frame_filtros, text="Pacote Office", variable=self.var_office)
        self.chk_office.pack(side="left", padx=10)
        self.chk_videos = ttk.Checkbutton(frame_filtros, text="Vídeos", variable=self.var_videos)
        self.chk_videos.pack(side="left", padx=10)
        self.chk_mft = ttk.Checkbutton(frame_filtros, text="Relatório MFT (Pastas Apagadas)", variable=self.var_mft)
        self.chk_mft.pack(side="left", padx=10)

        # 9. Frame de Pré-visualização Hexadecimal
        frame_preview = ttk.LabelFrame(self.root, text="Pré-visualização Hexadecimal (Live)", padding=(10, 5))
        frame_preview.pack(fill="x", padx=10, pady=5)
        self.text_hex = tk.Text(frame_preview, height=3, state="disabled", bg="#1e1e1e", fg="#00ff00", font=("Courier", 9))
        self.text_hex.pack(fill="both", expand=True)

        # Frame de Logs e Progresso
        frame_logs = ttk.LabelFrame(self.root, text="Monitoramento em Tempo Real", padding=(10, 10))
        frame_logs.pack(fill="both", expand=True, padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame_logs, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.text_log = tk.Text(frame_logs, height=10, state="disabled", bg="#f4f4f4")
        self.text_log.pack(fill="both", expand=True)

        # Botões de Ação
        frame_acoes = ttk.Frame(self.root)
        frame_acoes.pack(fill="x", padx=10, pady=10)

        self.btn_iniciar = ttk.Button(frame_acoes, text="Iniciar Recuperação", command=self.iniciar_thread)
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_parar = ttk.Button(frame_acoes, text="Parar", command=self.parar_recuperacao, state="disabled")
        self.btn_parar.pack(side="left", padx=5)

    def _toggle_filtros(self) -> None:
        estado = "disabled" if self.var_modo_logico.get() else "normal"
        self.chk_img.config(state=estado)
        self.chk_pdf.config(state=estado)
        self.chk_office.config(state=estado)
        self.chk_videos.config(state=estado)
        self.chk_mft.config(state=estado)

    def _alterar_estado_ui(self, is_running: bool) -> None:
        """Desacopla lógica visual para travar UI e evitar race conditions no Tkinter."""
        self.btn_iniciar.config(state="disabled" if is_running else "normal")
        self.btn_parar.config(state="normal" if is_running else "disabled")
        estado_filtros = "disabled" if (is_running or self.var_modo_logico.get()) else "normal"
        for chk in [self.chk_img, self.chk_pdf, self.chk_office, self.chk_videos, self.chk_mft]:
            chk.config(state=estado_filtros)
        self.chk_logico.config(state="disabled" if is_running else "normal")

    def selecionar_destino(self) -> None:
        pasta = filedialog.askdirectory()
        if pasta:
            self.caminho_destino.set(pasta)

    def atualizar_preview(self, hex_data: str) -> None:
        self.text_hex.config(state="normal")
        self.text_hex.delete(1.0, tk.END)
        self.text_hex.insert(tk.END, hex_data)
        self.text_hex.config(state="disabled")

    def log(self, mensagem: str) -> None:
        self.text_log.config(state="normal")
        self.text_log.insert(tk.END, mensagem + "\n")
        self.text_log.see(tk.END)
        self.text_log.config(state="disabled")

    def iniciar_thread(self) -> None:
        destino = self.caminho_destino.get()
        if not destino:
            messagebox.showwarning("Aviso", "Selecione uma pasta de destino.")
            return
            
        entrada = self.caminho_drive.get().strip()
        if not entrada:
            messagebox.showwarning("Aviso", "Informe o caminho do drive físico.")
            return

        self.rodando = True
        self._alterar_estado_ui(is_running=True)
        self.text_log.config(state="normal")
        self.text_log.delete(1.0, tk.END) # Limpa logs anteriores
        self.text_log.config(state="disabled")
        
        self.progress_var.set(0)
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')

        if self.var_modo_logico.get():
            if len(entrada) > 3 and not entrada[0].isalpha():
                messagebox.showwarning("Aviso", "O Modo Estruturado requer a letra da unidade (Ex: E:).")
                self.parar_recuperacao(silencioso=True)
                return
            threading.Thread(target=self.motor_logico, args=(entrada, destino), daemon=True).start()
        else:
            if not (self.var_imagens.get() or self.var_pdf.get() or self.var_office.get() or self.var_videos.get() or self.var_mft.get()):
                messagebox.showwarning("Aviso", "Selecione pelo menos um tipo de arquivo para buscar.")
                self.parar_recuperacao(silencioso=True)
                return
            threading.Thread(target=self.motor_de_busca, args=(entrada, destino), daemon=True).start()

    def parar_recuperacao(self, silencioso: bool = False) -> None:
        self.rodando = False
        self._alterar_estado_ui(is_running=False)
        if not silencioso:
            self.log("\n[!] Solicitação de parada recebida. Aguardando fim do ciclo atual...")

    def motor_logico(self, entrada: str, destino: str) -> None:
        """Motor de Recuperação Lógica e Estrutural Recursiva"""
        letra_drive = f"{entrada[0].upper()}:\\" if entrada[0].isalpha() else entrada

        self.log(f"[*] Iniciando Recuperação Estruturada em {letra_drive}")
        self.log("[*] Mapeando árvore de diretórios... (Aguarde)")
        
        self.root.after(0, lambda: self.progress_bar.config(mode="indeterminate"))
        self.root.after(0, self.progress_bar.start)

        try:
            total_arquivos = sum([len(files) for r, d, files in os.walk(letra_drive)])
            self.log(f"[*] Total mapeado: {total_arquivos} arquivos.")
            
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_bar.config(mode="determinate"))
            self.root.after(0, self.progress_var.set, 0)

            arquivos_copiados = 0
            for root_dir, dirs, files in os.walk(letra_drive):
                if not self.rodando: break
                
                # Calcula o espelho da pasta para criar no destino
                caminho_relativo = os.path.relpath(root_dir, letra_drive)
                pasta_destino = destino if caminho_relativo == "." else os.path.join(destino, caminho_relativo)
                os.makedirs(pasta_destino, exist_ok=True)

                for file in files:
                    if not self.rodando: break
                    src = os.path.join(root_dir, file)
                    dst = os.path.join(pasta_destino, file)

                    try:
                        shutil.copy2(src, dst)
                        arquivos_copiados += 1
                        if arquivos_copiados % 10 == 0 or arquivos_copiados == total_arquivos:
                            pct = (arquivos_copiados / total_arquivos) * 100 if total_arquivos > 0 else 100
                            self.root.after(0, self.progress_var.set, pct)
                            self.log(f"    -> [OK] {caminho_relativo}\\{file}")
                    except Exception as e:
                        self.log(f"    -> [ERRO] Falha em {file}: {str(e)}")

        except Exception as e:
            self.log(f"[ERRO FATAL] {str(e)}")
        finally:
            self.root.after(0, lambda: self.parar_recuperacao(silencioso=True))
            self.log("\n[*] Recuperação Estruturada concluída.")

    def _carregar_assinaturas_ativas(self) -> Dict[bytes, Tuple[str, Dict[str, Any]]]:
        """Heurística: Inicializa banco JSON e filtra com base nas selections da UI."""
        caminho_json = "assinaturas.json"
        if not os.path.exists(caminho_json):
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SIGNATURES, f, indent=4)
        with open(caminho_json, "r", encoding="utf-8") as f:
            sig_db = json.load(f)

        ativas = {}
        if self.var_imagens.get():
            ativas[bytes.fromhex(sig_db["jpg"]["header"])] = ("jpg", sig_db["jpg"])
            ativas[bytes.fromhex(sig_db["png"]["header"])] = ("png", sig_db["png"])
        if self.var_pdf.get():
            ativas[bytes.fromhex(sig_db["pdf"]["header"])] = ("pdf", sig_db["pdf"])
        if self.var_office.get():
            ativas[bytes.fromhex(sig_db["office_moderno_ou_zip"]["header"])] = ("office_moderno_ou_zip", sig_db["office_moderno_ou_zip"])
            ativas[bytes.fromhex(sig_db["office_antigo"]["header"])] = ("office_antigo", sig_db["office_antigo"])
        if self.var_videos.get():
            ativas[bytes.fromhex(sig_db["mp4"]["header"])] = ("mp4", sig_db["mp4"])
            ativas[bytes.fromhex(sig_db["mkv"]["header"])] = ("mkv", sig_db["mkv"])
        if self.var_mft.get():
            ativas[bytes.fromhex(sig_db["mft"]["header"])] = ("mft", sig_db["mft"])
        return ativas

    def _analisar_mft(self, chunk: bytes, offset_base: int, assinatura: bytes, destino: str) -> None:
        """Ghost Reader Forense: Decodifica MFT Headers para salvar pastas/arquivos deletados."""
        offset_busca = 0
        while True:
            idx_mft = chunk.find(assinatura, offset_busca)
            if idx_mft == -1: break
            
            amostra = chunk[idx_mft : idx_mft + 1024]
            if len(amostra) >= 24:
                flags = int.from_bytes(amostra[22:24], byteorder='little')
                is_in_use = (flags & 0x01)
                is_dir = (flags & 0x02)
                
                if not is_in_use:
                    nomes = re.findall(b'((?:[\x20-\x7E\xA0-\xFF]\x00){4,})', amostra)
                    if nomes:
                        nome_encontrado = max(nomes, key=len).decode('utf-16le', errors='ignore')
                        tipo_str = "PASTA APAGADA" if is_dir else "ARQUIVO APAGADO"
                        self.log(f"    -> [FORENSE] {tipo_str}: '{nome_encontrado}'")
                        
                        caminho_relatorio = os.path.join(destino, "Relatorio_Forense_Apagados.txt")
                        with open(caminho_relatorio, "a", encoding="utf-8") as f:
                            # Bugfix Senior: Correção de offset real usando offset_base do disco
                            f.write(f"[{tipo_str}] Nome original: {nome_encontrado} | Offset Disco: {offset_base + idx_mft}\n")
            
            offset_busca = idx_mft + 1024

    def _analisar_office(self, amostra: bytes, tipo_base: str) -> Optional[str]:
        """Heurística OLE2/ZIP para identificar formatos originais de escritório."""
        if tipo_base == 'office_moderno_ou_zip':
            if b'word/' in amostra or b'[Content_Types].xml' in amostra: return 'docx'
            if b'xl/' in amostra: return 'xlsx'
            if b'ppt/' in amostra: return 'pptx'
            return None
        elif tipo_base == 'office_antigo':
            amostra_limpa = amostra.replace(b'\x00', b'')
            if b'WordDocument' in amostra_limpa: return 'doc'
            if b'Workbook' in amostra_limpa or b'Book' in amostra_limpa: return 'xls'
            if b'PowerPoint' in amostra_limpa: return 'ppt'
            return 'doc'
        return tipo_base

    def _extrair_metadados(self, buffer_bytes: bytes, gravando_tipo: str, id_padrao: int) -> str:
        """Extração EXIF para atribuição semântica do arquivo recuperado."""
        nome_base = f"recuperado_{id_padrao}"
        if gravando_tipo == "jpg":
            exif = re.search(b"(20[0-2][0-9]:[0-1][0-9]:[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9])", buffer_bytes[:8192])
            if exif:
                data_str = exif.group(1).decode("ascii").replace(":", "-").replace(" ", "_")
                nome_base = f"foto_{data_str}"
        return nome_base

    def motor_de_busca(self, entrada: str, destino: str) -> None:
        """Motor Base de Recuperação Física (Raw File Carving e MFT Hunting)"""
        
        if len(entrada) <= 3 and entrada[0].isalpha():
            letra_drive = entrada[0].upper()
            drive_path = f"\\\\.\\{letra_drive}:"
            letra_sistema = f"{letra_drive}:\\"
        else:
            drive_path = entrada
            letra_sistema = None
            
        tamanho_chunk = 4096  # Lendo 4KB por vez
        
        try:
            assinaturas_ativas = self._carregar_assinaturas_ativas()
        except Exception as e:
            self.log(f"[ERRO] Falha ao ler JSON de assinaturas: {str(e)}")
            self.parar_recuperacao(silencioso=True)
            return

        self.log(f"[*] Abrindo dispositivo: {drive_path}")
        
        # Tenta descobrir o tamanho total do disco para a barra de progresso
        total_size = 0
        try:
            if letra_sistema:
                total_size = shutil.disk_usage(letra_sistema).total
            else:
                with open(drive_path, "rb") as f_temp:
                    f_temp.seek(0, 2) # Pula pro final do arquivo
                    total_size = f_temp.tell()
            self.log(f"[*] Tamanho estimado do disco: {total_size / (1024**3):.2f} GB")
        except Exception as e:
            self.log(f"[Aviso] Tamanho total indisponível. Progresso será indeterminado.")
            # Altera a barra para modo indeterminado (animada sem %)
            self.root.after(0, lambda: self.progress_bar.config(mode="indeterminate"))
            self.root.after(0, self.progress_bar.start)

        try:
            with open(drive_path, "rb") as drive:
                buffer_leitura = b""
                contagem_arquivos = 0
                gravando_tipo: Optional[str] = None
                gravando_configs: Optional[Dict[str, Any]] = None
                
                bytes_lidos = 0
                iteracao = 0
                
                while self.rodando:
                    chunk = drive.read(tamanho_chunk)
                    if not chunk:
                        self.log("[*] Fim do disco alcançado.")
                        if total_size > 0:
                            self.root.after(0, self.progress_var.set, 100.0)
                        break
                    
                    # Bugfix: Guardar offset atual antes de somar tamanho lido
                    offset_chunk_atual = bytes_lidos
                    bytes_lidos += len(chunk)
                    iteracao += 1
                    
                    if total_size > 0 and iteracao % 1024 == 0:
                        pct = (bytes_lidos / total_size) * 100
                        self.root.after(0, self.progress_var.set, pct)

                    if not gravando_tipo:
                        for assinatura, (tipo_base, configs) in assinaturas_ativas.items():
                            idx = chunk.find(assinatura)
                            if idx != -1:
                                if tipo_base == 'mft':
                                    self._analisar_mft(chunk, offset_chunk_atual, assinatura, destino)
                                    continue 

                                tipo_final = tipo_base
                                if tipo_base in ('office_moderno_ou_zip', 'office_antigo'):
                                    tipo_final = self._analisar_office(chunk[idx : idx + 2048], tipo_base)
                                    if not tipo_final: continue 
                                elif tipo_base == 'mp4':
                                    idx = max(0, idx - 4)

                                gravando_tipo = tipo_final
                                gravando_configs = configs
                                contagem_arquivos += 1
                                
                                # 9. Pré-visualização Hexadecimal do arquivo encontrado
                                hex_sample = " ".join(f"{b:02X}" for b in chunk[idx:idx+64])
                                self.root.after(0, self.atualizar_preview, hex_sample)

                                self.log(f"[+] Achado: {tipo_final.upper()}! Extraindo arquivo {contagem_arquivos}...")
                                buffer_leitura = chunk[idx:]
                                break
                    else:
                        buffer_leitura += chunk
                        finalizou = False
                        
                        if gravando_configs:
                            footer_hex = gravando_configs.get("footer", "")
                            if footer_hex:
                                footer_bytes = bytes.fromhex(footer_hex)
                                if footer_bytes in chunk:
                                    footer_idx = buffer_leitura.find(footer_bytes)
                                    buffer_leitura = buffer_leitura[:footer_idx + len(footer_bytes)]
                                    finalizou = True

                            if not finalizou and b'\x00' * 1024 in chunk:
                                null_idx = buffer_leitura.find(b'\x00' * 1024)
                                buffer_leitura = buffer_leitura[:null_idx]
                                finalizou = True
                                self.log("    -> [Smart Carving] Slack Space detectado (Corte de segurança).")

                            limite_tamanho = gravando_configs.get("max_size", 5242880)
                            if not finalizou and len(buffer_leitura) >= limite_tamanho:
                                finalizou = True

                        if finalizou:
                            nome_base = self._extrair_metadados(buffer_leitura, gravando_tipo, contagem_arquivos)
                            nome_arquivo = os.path.join(destino, f"{nome_base}.{gravando_tipo}")
                            with open(nome_arquivo, "wb") as f:
                                f.write(buffer_leitura)
                            
                            tamanho_kb = len(buffer_leitura) / 1024
                            self.log(f"    -> Salvo: {nome_arquivo} ({tamanho_kb:.1f} KB)")
                            gravando_tipo = None # Volta a caçar novas assinaturas
                            gravando_configs = None
                            buffer_leitura = b""

        except PermissionError:
            self.log("[ERRO FATAL] Permissão negada. Você precisa abrir o Python/Terminal como Administrador para ler o disco físico diretamente.")
        except Exception as e:
            self.log(f"[ERRO] {str(e)}")
        finally:
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.parar_recuperacao(silencioso=True))
            self.log("\n[*] Escaneamento e extração concluídos.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RecuperadorApp(root)
    root.mainloop()