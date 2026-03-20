import os
import time
import subprocess
import threading
import requests
import asyncio
import zipfile
import shutil
from tqdm.auto import tqdm
from huggingface_hub import hf_hub_download, list_repo_files
import fnmatch

class InstallerEngine:
    current_tries: int = 0
    max_tries: int = 3
    def __init__(self, target_dir, update_callback):
        self.target_dir = target_dir
        self.update_callback = update_callback
        self.is_cancelled = False
        self.loop = asyncio.get_event_loop()

    def start(self):
        global ACTIVE_ENGINE
        ACTIVE_ENGINE = self
        threading.Thread(target=self._run_sequence, daemon=True).start()
    
    def update_ui_callback(self, step_index, status, progress = None, description = None):
        future = asyncio.run_coroutine_threadsafe(
            self.update_callback(step_index, status, progress, description),
            self.loop
        )

        future.result()

    def _run_sequence(self):
        try:
            # SET UP ENV

            self.current_step = 0
            self.update_ui_callback(
                step_index=self.current_step, 
                status="running",
                progress=-1,
                description=f"Setting up Python Environment."
            )
            self._prepare_environment()
            self.update_ui_callback(
                step_index=self.current_step, 
                status="done",
                progress=-1,
                description=f"Python Environment created."
            )

            # SET UP PROVENANCE

            self.current_step = 1
            self.update_ui_callback(
                step_index=self.current_step, 
                status="running",
                progress=-1,
                description=f"Downloading Deepfake Detection Model."
            )
            self._download_provenance_models()
            self.update_ui_callback(
                step_index=self.current_step, 
                status="done",
                progress=100,
                description=f"Downloaded Deepfake Detection Model."
            )

            # SET UP STT/TTS/Wake Word

            self.current_step = 2
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Downloading Faster-Whisper Speech-to-Text Model"
            )
            self._download_hf_model(
                "Systran/faster-whisper-small",
                "models/stt",
                [
                    "config.json",
                    "preprocessor_config.json",
                    "model.bin",
                    "tokenizer.json",
                    "vocabulary.*",
                ]
            )
            # print("Downloading Kokoro-onnx Text-to-Speech model")
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description="Downloading Kokoro-onnx Text-to-Speech model"
            )
            self._download_kokoro_onnx()
            print("DONE ONNX")
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Downloading 'Hey_Iris' openWakeWord model"
            )
            self._download_wakeword()
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Downloaded Transcription/Narration Models"
            )
            # print("DONE WAKEWORD")

            # Download Qwen3-VL and MMPROJ

            self.current_step = 3
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Downloading Qwen3-VL model"
            )
            self._download_using_requests(
                "models\\vlm",
                "https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/Qwen3VL-2B-Instruct-Q4_K_M.gguf",
                "Qwen3VL-2B-Instruct-Q4_K_M.gguf"
            )
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Downloaded Qwen3-VL model"
            )

            self.current_step = 4
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Downloading Qwen3-VL multimodal projector (MMPROJ)"
            )
            self._download_using_requests(
                "models\\vlm",
                "https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/mmproj-Qwen3VL-2B-Instruct-F16.gguf",
                "mmproj-Qwen3VL-2B-Instruct-F16.gguf"
            )
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Downloaded Qwen3-VL multimodal projector (MMPROJ)"
            )
            # print("DONE QWEN")

            # DL All other files

            self.current_step = 5
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Downloading Assets, Databases, and Scripts"
            )
            self._download_using_requests(
                "git",
                "https://github.com/deepfake-dev/IRIS_system/archive/refs/heads/main.zip",
                "main.zip"
            )
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Decompressing Package."
            )
            self.decompress_main()
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Moving Avatar Assets."
            )
            self.move_avatar_assets()
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Moving Databases."
            )
            self.move_databases()
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Moving Scripts."
            )
            self.move_scripts()
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Cleaning up cloned git"
            )
            self.clean_git()
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Downloaded Assets, Databases, and Scripts"
            )
            # print("DONE ASSETS")

            # Install Deps

            self.current_step = 6
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Install LLM Server"
            )
            self._install_vlm_server()
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Installed LLM Server"
            )

            # Install VLM Server

            self.current_step = 7
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Installing Python Dependencies"
            )
            self._install_python_dependencies()
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Installed Python Dependencies"
            )

            # Check everything

            self.current_step = 8
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Checking if everything is in place"
            )
            self._verify_working()
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"Checked everything"
            )

            self.current_step = 9
            self.update_ui_callback(
                step_index=self.current_step,
                status="done",
                progress=-1,
                description=f"IRIS System was installed!"
            )

        except Exception as e:
            print(f"Installation failed: {e}")
            # You could add an 'error' status to your callback here

    # ---------------------------------------------------------
    # ACTUAL INSTALLATION SCRIPTS
    # ---------------------------------------------------------

    def _prepare_environment(self):
        """Creates the main folders and optionally a Python Virtual Environment."""

        if os.path.exists(self.target_dir):
            try:
                shutil.rmtree(self.target_dir)
            except OSError as e:
                print(f"Error: {e.strerror}. Could not delete directory '{self.target_dir}'.")

        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "scripts"), exist_ok=True)
        
        venv_dir = os.path.join(self.target_dir, ".venv")
        if not os.path.exists(venv_dir):
            subprocess.run(
                [
                    "winget", "install", 
                    "--id", "Python.Python.3.12", 
                    "-e", 
                    "--accept-package-agreements", 
                    "--accept-source-agreements"
                ], 
                check=True
            )
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Installing Python 3.12"
            )
            subprocess.run(["py", "-3.12", "-m", "venv", venv_dir], check=True)
            self.update_ui_callback(
                step_index=self.current_step,
                status="running",
                progress=-1,
                description=f"Creating Python 3.12 Environment"
            )
            self.venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    
    def clean_git(self):
        dirs = ["git", "main_zip"]
        for folder in dirs:
            dir = os.path.join(self.target_dir, folder)
            if os.path.exists(dir):
                try:
                    shutil.rmtree(dir)
                except OSError as e:
                    print(f"Error: {e.strerror}. Could not delete directory '{self.target_dir}'.")
    
    def decompress_main(self):
        if not os.path.exists(os.path.join(self.target_dir, "git", "main.zip")):
            print("main.zip does not exist.")
            return
        
        extract_dir = os.path.join(self.target_dir, "main_zip")

        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(os.path.join(self.target_dir, "git", "main.zip"), 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
    def move_avatar_assets(self):
        decompressed_folder = os.path.join(self.target_dir, "main_zip")
        if not os.path.exists(decompressed_folder):
            print("no decompressed folder hahaha")
            return

        avatar_dir = os.path.join(self.target_dir, "avatar")
        
        try:
            shutil.copytree(
                os.path.join(decompressed_folder, "IRIS_System-main", "avatar"),
                avatar_dir
            )
        except shutil.SameFileError:
            print("Source and destination represent the same file.")
        except PermissionError:
            print("Permission denied.")
        except IsADirectoryError:
            print("Destination is a directory, please provide a file name.")
        except FileNotFoundError:
            print("Source file not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def move_databases(self):
        decompressed_folder = os.path.join(self.target_dir, "main_zip")
        if not os.path.exists(decompressed_folder):
            print("no decompressed folder hahaha")
            return

        databases_dir = os.path.join(self.target_dir, "databases")
        
        try:
            shutil.copytree(
                os.path.join(decompressed_folder, "IRIS_System-main", "databases"),
                databases_dir
            )
        except shutil.SameFileError:
            print("Source and destination represent the same file.")
        except PermissionError:
            print("Permission denied.")
        except IsADirectoryError:
            print("Destination is a directory, please provide a file name.")
        except FileNotFoundError:
            print("Source file not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def move_scripts(self):
        decompressed_folder = os.path.join(self.target_dir, "main_zip")
        if not os.path.exists(decompressed_folder):
            print("no decompressed folder hahaha")
            return
        
        folders = ['provenance_checker', 'assistant']

        for folder in folders:
            folder_path = os.path.join(self.target_dir, "scripts", folder)

            try:
                shutil.copytree(
                    os.path.join(decompressed_folder, "IRIS_System-main", "scripts", folder),
                    folder_path
                )
            except shutil.SameFileError:
                print("Source and destination represent the same file.")
            except PermissionError:
                print("Permission denied.")
            except IsADirectoryError:
                print("Destination is a directory, please provide a file name.")
            except FileNotFoundError:
                print("Source file not found.")
            except Exception as e:
                print(f"An error occurred: {e}")
        
        if os.path.exists(os.path.join(decompressed_folder, "IRIS_System-main", "scripts", "requirements.txt")):
            with open(os.path.join(decompressed_folder, "IRIS_System-main", "scripts", "requirements.txt"), 'r') as f:
                contents = f.read()
            
            with open(os.path.join(self.target_dir, "scripts", "requirements.txt"), 'x') as f:
                f.write(contents)
    
    def _download_provenance_models(self):
        os.makedirs(os.path.join(self.target_dir, "models/provenance"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "scripts/provenance"), exist_ok=True)

        links = [
            "https://github.com/deepfake-dev/IRIS_System/releases/download/ProvenanceModel/deepfake_detector_feb26.onnx",
            "https://github.com/deepfake-dev/IRIS_System/releases/download/ProvenanceModel/deepfake_detector_feb26.onnx.data"
        ]

        outs = [
            "deepfake_detector_model.onnx",
            "deepfake_detector_feb26.onnx.data",
        ]

        for i in range(2):
            self._download_using_requests("models/provenance", links[i], outs[i])
    
    def _download_kokoro_onnx(self):
        if not self.venv_python:
            print("SADDDD")
            return
        
        os.makedirs(os.path.join(self.target_dir, "models", "tts"), exist_ok=True)

        self.update_ui_callback(
            step_index=self.current_step,
            status="downloading",
            progress=-1,
            description="Installing Kokoro-onnx[GPU]"
        )
        
        subprocess.run([self.venv_python, "-m", "pip", "install", "-U", "kokoro-onnx[gpu]"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = subprocess.run([self.venv_python, "-m", "pip", "show", "kokoro-onnx"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "WARNING: Package(s) not found:" in result.stdout.strip():
            print("HINDI NAGINSTALL!!!!")
        self.update_ui_callback(
            step_index=self.current_step,
            status="downloading",
            progress=-1,
            description="Installed Kokoro-onnx[GPU]. Downloading extra Kokoro-onnx files"
        )

        self._download_using_requests("models\\tts", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx", "kokoro-v1.0.onnx")
        self._download_using_requests("models\\tts", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin", "voices-v1.0.bin")
    
    def _download_wakeword(self):
        os.makedirs(os.path.join(self.target_dir, "models", "wakeword"), exist_ok=True)
        self._download_using_requests("models\\wakeword", "https://github.com/deepfake-dev/IRIS_System/releases/download/WakeWordModel/hey_iris.onnx", "hey_iris.onnx")
    
    def _download_using_requests(self, subfolder, link, filename):
        os.makedirs(os.path.join(self.target_dir, subfolder), exist_ok=True)

        response = requests.get(link, stream=True)
        response.raise_for_status() # Throw an error if the URL is dead/404

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        last_ui_update = 0

        with open(os.path.join(self.target_dir, subfolder, filename), 'wb') as file:

            for data in response.iter_content(chunk_size=8192):
                size = file.write(data)
                downloaded_size += size

                # Calculate progress and update UI
                if total_size > 0:
                    now = time.time()
                    
                    # THROTTLE: Only update the UI every 0.1 seconds or when 100% finished
                    if now - last_ui_update > 0.1 or downloaded_size == total_size:
                        progress_val = downloaded_size / total_size
                        
                        # Send to Flet UI using the exact same format as the HuggingFace patch
                        self.update_ui_callback(
                            step_index=self.current_step,
                            status="downloading",
                            progress=progress_val,
                            description=f"Downloading {filename}"
                        )
                        last_ui_update = now

    def _download_hf_model(self, repo_id, subfolder, allow_patterns=None):
        save_path = os.path.join(self.target_dir, subfolder)
        os.makedirs(save_path, exist_ok=True)

        # Get the list of files to download
        all_files = list(list_repo_files(repo_id))
        if allow_patterns:
            files = [
                f for f in all_files
                if any(fnmatch.fnmatch(f, p) for p in allow_patterns)
            ]
        else:
            files = all_files

        for i, filename in enumerate(files):
            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=i / len(files),
                description=f"Downloading {filename}"
            )

            # Downloads one file at a time with a real progress callback
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=save_path,
            )

            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=(i + 1) / len(files),
                description=f"Downloaded {filename}"
            )

    def _install_python_dependencies(self):
        """Runs pip install inside the newly created virtual environment."""
        req_file = os.path.join(self.target_dir, "scripts", "requirements.txt")
        
        try:
            if os.path.exists(req_file):
                subprocess.run([self.venv_python, "-m", "pip", "install", "-r", req_file], check=True)
            
                return
        except:
            if self.current_tries < self.max_tries:
                self.update_ui_callback(
                    step_index=self.current_step,
                    status="downloading",
                    progress=-1,
                    description=f"Download failed. Retrying..."
                )
                self.current_tries += 1
                self._install_python_dependencies()
        
        print("MALAS sorry")
    
    def _install_vlm_server(self):
        cudart_link = "https://github.com/ggml-org/llama.cpp/releases/download/b8429/cudart-llama-bin-win-cuda-12.4-x64.zip"
        llama_cpp_link = "https://github.com/ggml-org/llama.cpp/releases/download/b8429/llama-b8429-bin-win-cuda-12.4-x64.zip"
        self.update_ui_callback(
            step_index=self.current_step,
            status="downloading",
            progress=-1,
            description=f"Download CUDA-RT for the Server"
        )
        self._download_using_requests(
            "server",
            cudart_link,
            "cudart.zip"
        )
        self.update_ui_callback(
            step_index=self.current_step,
            status="downloading",
            progress=-1,
            description=f"Download Llama-cpp Server"
        )
        self._download_using_requests(
            "server",
            llama_cpp_link,
            "llama_cpp.zip"
        )

        if os.path.exists(os.path.join(self.target_dir, "server", "cudart.zip")) and os.path.exists(os.path.join(self.target_dir, "server", "llama_cpp.zip")):
            llama_cpp_zip_path = os.path.join(self.target_dir, "server", 'llama_cpp.zip')
            cudart_zip_path = os.path.join(self.target_dir, "server", 'cudart.zip')
            destination_directory = os.path.join(self.target_dir, "server")
            
            if not os.path.exists(destination_directory):
                os.makedirs(destination_directory)

            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=-1,
                description=f"Unzipping Llama-cpp"
            )

            with zipfile.ZipFile(llama_cpp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(destination_directory)

            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=-1,
                description=f"Unzipped Llama-cpp, unzipping CUDA-RT"
            )
            
            with zipfile.ZipFile(cudart_zip_path, 'r') as zip_ref:
                zip_ref.extractall(destination_directory)
            
            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=-1,
                description=f"Unzipped CUDA-RT"
            )
        else:
            print("AYAWWWW")

    
    def _verify_working(self):
        if all([
            # AVATAR STUFF
            os.path.exists(os.path.join(self.target_dir, "avatar", "css", "kiosk.css")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "css", "style.css")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "animation.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "audio.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "main.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "scene.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "signal.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "js", "websocket.js")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "bsu_girl.vrm")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "icon.png")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "index.html")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "kist-1.webp")),
            os.path.exists(os.path.join(self.target_dir, "avatar", "logo.png")),

            # DATABASE
            os.path.exists(os.path.join(self.target_dir, "databases", "Citizens_Charter_Handbook_2025.db")),
            os.path.exists(os.path.join(self.target_dir, "databases", "Citizens_Charter_Handbook_2025.faiss")),

            # MODELS (PROVENANCE)
            os.path.exists(os.path.join(self.target_dir, "models", "provenance", "deepfake_detector_model.onnx")),
            os.path.exists(os.path.join(self.target_dir, "models", "provenance", "deepfake_detector_feb26.onnx.data")),

            # MODELS (STT)
            os.path.exists(os.path.join(self.target_dir, "models", "stt", "config.json")),
            os.path.exists(os.path.join(self.target_dir, "models", "stt", "model.bin")),
            os.path.exists(os.path.join(self.target_dir, "models", "stt", "tokenizer.json")),
            os.path.exists(os.path.join(self.target_dir, "models", "stt", "vocabulary.txt")),

            # MODELS (TTS)

            os.path.exists(os.path.join(self.target_dir, "models", "tts", "kokoro-v1.0.onnx")),
            os.path.exists(os.path.join(self.target_dir, "models", "tts", "voices-v1.0.bin")),

            # MODELS (VLM)

            os.path.exists(os.path.join(self.target_dir, "models", "vlm", "mmproj-Qwen3VL-2B-Instruct-F16.gguf")),
            os.path.exists(os.path.join(self.target_dir, "models", "vlm", "Qwen3VL-2B-Instruct-Q4_K_M.gguf")),

            # MODELS (WAKEWORD)

            os.path.exists(os.path.join(self.target_dir, "models", "wakeword", "hey_iris.onnx")),

            # SCRIPTS

            os.path.exists(os.path.join(self.target_dir, "scripts", "requirements.txt")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "assistant", "avatar.py")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "assistant", "vlm_handler.py")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "provenance_checker", "main.py")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "provenance_checker", "deepfake_detector.py")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "provenance_checker", "metadata_scanner.py")),
            os.path.exists(os.path.join(self.target_dir, "scripts", "provenance_checker", "vlm_classifier.py")),

            # SERVER
            os.path.exists(os.path.join(self.target_dir, "server", "llama-server.exe")),
        ]):
            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=-1,
                description=f"ALL IS WELL!"
            )
        else:
            self.update_ui_callback(
                step_index=self.current_step,
                status="downloading",
                progress=-1,
                description=f"We encountered some problems!"
            )