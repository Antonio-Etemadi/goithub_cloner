import os
import gc
import requests
import json
import time
import sys
import mip
import ntptime
try:
    import logging
except :
    mip.install("logging",mpy=False)
import logging

class Ota_github:
    def __init__(self, url,directory="/",json_path="/",json_name="github_version.json",ota_cloner_name="Ota_github.py",log_name="github_cloner.log",console_log_level="INFO",file_log_level="INFO"):
        self.log_name=log_name
        self.console_log_level=console_log_level
        self.file_log_level=file_log_level
        self.setup_logging()
        self.url = url
        self.all_content_list = []
        self.directory=directory
        self.all_entries_list = []
        self.json_path=json_path
        self.json_name=json_name
        self.json_SHA_list=[]
        self.update_list=[]
        self.download_list=[]
        self.ota_cloner_name=ota_cloner_name
       
#============================================
    def setup_logging(self):
#         print(":setup_logging:")
        current_time = time.localtime()
        asctime = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*current_time)
        formatter = logging.Formatter(f'{asctime} - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        self.logger_console = logging.getLogger(__name__ + '.console')
        self.logger_console.setLevel(getattr(logging, self.console_log_level.upper()))
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.console_log_level.upper()))
        console_handler.setFormatter(formatter)
        self.logger_console.addHandler(console_handler)


        self.logger = logging.getLogger(__name__ + '.file')
        self.logger.setLevel(getattr(logging, self.file_log_level.upper()))
        file_handler = logging.FileHandler(self.log_name)
        file_handler.setLevel(getattr(logging, self.file_log_level.upper()))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
#=========================================================        
    def mkdir(self,path):
#         print(":mkdir:")
        base_directory = "/" 
        path_elements = []
        while path:
            path, folder = path.rsplit('/', 1)
            if folder:
                path_elements.insert(0, folder)
        for subdirectory in path_elements:
            file_path=os.chdir(f"{base_directory}") 
            base_directory += f"{subdirectory}/"
            try :
                os.mkdir(subdirectory)
            except:
                pass
        
#======================================================        
    def download_repository_list(self):
#         print(":download_repository_list:")
        if not self.url.startswith("https://api.github.com/"):
            index = self.url.find("github.com/" )+len("github.com/")
            repo = self.url[index:] 
            self.url = "https://api.github.com/repos/"   + repo + "/contents"
            
        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
                    }

        response = requests.get(f"{self.url}", headers=headers)    
        content_list = response.json()
        
        for item in content_list:
            if item["type"] == "dir":
                path = "/" + item["path"] + "/"
                self.url=item['url']
                self.download_repository_list()
            else:
                path = "/" + item["path"]
            entry = {"name": item["name"], "path": path, "sha": item["sha"], "type": item["type"], "download_url": item["download_url"]}
            self.all_content_list.append(entry)
        return 


#===========================================================

    def list_directory_entries(self):
#         print(":list_directory_entries:")
        os.chdir("/"+self.directory)
        entries = os.ilistdir()
        all_entries = []
        for entry in entries:
            name, entry_type, inode, size = entry
            if entry_type == 32768:
                item = {"path": self.directory + name, "type": entry_type, "inode": inode, "size": size}
                self.all_entries_list.append(item)
            elif entry_type == 16384:
                item = {"path":self.directory + name, "type": entry_type, "inode": inode, "size": size}
                self.all_entries_list.append(item)
                item["path"] += "/"
                self.directory=item['path']
                subdir_entries = self.list_directory_entries()
                self.directory="/"
        return 


#=======================================================

    def read_SHA_json(self):
#         print(":read_SHA_json:")
        
        # self.logger.info("Checking if the SHA JSON file exists.")
        try:
            os.chdir(self.json_path)
            with open(self.json_name, 'r') as file:
                self.json_SHA_list = json.load(file)
                file.close()
        except :
#             print(f"not found {self.json_name}")
            # self.logger.warning("SHA JSON file not found.")
            return False


#=======================================================================

    def download_repository_contents(self):
#         print(":download_repository_contents:")
        for item in self.download_list:
            
            if item['type'] == "dir":
#                 print(item['type'],item['path'],item['download_url'])
                self.mkdir(item['path'])
        for item in self.download_list:
            
            if item['type'] == "file":
#                 print(item['type'],item['path'],item['download_url'])
                file_url = item['download_url']
#                 print("##",self.directory)
                file_path=os.chdir(f"{self.directory}" )
                response = requests.get(item['download_url'])
#                 print("@===",item['path'])
                with open(item['path'], 'wb') as file:
                    file.write(response.content)
                    file.close()
                self.logger.info(f'downloaded {item['path']}')
                self.logger_console.info(f'\033[94mdownloaded:------------ {item["path"]}\033[0m ')

        return    
    

#==============================================================
    def find_update(self):
#         print(":find_update:")

        for a in self.all_content_list:
            for b in self.json_SHA_list:
                if a["path"] == b["path"] and a["sha"] != b["sha"]  :
                    self.logger_console.info(f'\033[33mchenged content::------------{a["path"]}\033[0m')
                    self.logger.info(f'chengeed content::------------{a["path"]}🗸')
                    self.download_list.append(a)
                    break
                if a["path"] == b["path"] and a["sha"] == b["sha"]  :
                    for c in self.all_entries_list:
                        if a["path"] == c["path"]:
                            self.logger_console.info(f'\033[92mUp to date:------------ {a["path"]}✅\033[0m ')                            
                            break
                    else:
                        self.logger_console.info(f'\033[91mmising file:------------{a["path"]}⚠\033[0m')
                        self.logger.warning(f'mising file:------------{a["path"]} ⚠')
                        self.download_list.append(a)
                    break
            else:
                self.logger_console.info(f'\033[93mnew file:------------{a["path"]}✔\033[0m')
                self.logger.info(f'new file:------------{a["path"]} ✔')
                self.download_list.append(a)

#==============================================================
    def extract_name_and_sha_from_repo(self):
#         print(":extract_name_and_sha_from_repo:")
        name_and_sha = [
            {"name": self.json_name, "path": f"/{self.json_name}", "sha": 0, "type": "file"},
            {"name": "/logging.py", "path": f"/lib/logging.py", "sha": 0, "type": "file"},
            {"name": self.log_name, "path": f"/{self.log_name}", "sha": 0, "type": "file"},
            {"name": "lib", "path": "/lib/", "sha": 0, "type": "dir"}
        ]
        name_and_sha.extend([
            {"name": item["name"], "path": item["path"], "sha": item["sha"], "type": item["type"]}
            for item in self.all_content_list
        ])

        file_path = os.chdir(f"{self.json_path}")
        with open(self.json_name, 'w') as file:
            json.dump(name_and_sha, file)
#             self.logger.info("file name_and_sha.json created")
        return

#========================================================================
    def remove_dir(self,rm_dir):  # Remove file or tree
#         print(":remove_dir:")
        try:
            if os.stat(rm_dir)[0] & 0x4000:  # Dir
                for file in os.ilistdir(rm_dir):
                    if file[0] not in ('.', '..'):
                        self.remove_dir("/".join((rm_dir, file[0])))  # File or Dir
                self.logger_console.warning(f"\033[31mremove dir:{rm_dir}❎\033[0m")
                self.logger.warning(f"remove dir:{rm_dir}")
                os.rmdir(rm_dir)
            else:  # File
                self.logger_console.warning(f"\033[31mremove file:{rm_dir}❎\033[0m")
                self.logger.warning(f"remove file:{rm_dir}")
                os.remove(rm_dir)
        except Exception as e:
            if not isinstance(e, FileNotFoundError):
                self.logger.error(f"Failed to remove {rm_dir}: {e}")
                self.logger_console.error("\033[91Failed to remove {rm_dir}: {e}\033[0m" )

                
#=====================================================================

# #⚠✔⛔❎
    def remove_deleted_file_in_repo(self ):
#         print(":remove_deleted_file_in_repo:")
        self.read_SHA_json()
        name_set = set(item['path'] for item in self.json_SHA_list)
        for file_info in self.all_entries_list:
            
            if file_info["path"] not  in name_set:
                try:
                    self.remove_dir(file_info["path"])
                except :
                        continue
#====================================================

    def run_ota(self):
        self.logger_console.info(f"\033[45m.........connecting..........\033[0m")
        self.download_repository_list()
        self.list_directory_entries()
        self.read_SHA_json()
        self.find_update()
        self.download_repository_contents()
        self.extract_name_and_sha_from_repo()
        self.remove_deleted_file_in_repo()
        initial_memory = gc.mem_alloc()
        gc.collect()
        memory_after_gc = gc.mem_alloc()
        cleaned_memory=(initial_memory-memory_after_gc)/1000
        self.logger_console.info(f"\033[41mcleaned memory {cleaned_memory} KB\033[0m")
#============================================================
if __name__ == "__main__":
    url = "https://github.com/Antonio-Etemadi/github_cloner"
    ota_instance = Ota_github(url)
    ota_instance.run_ota()

