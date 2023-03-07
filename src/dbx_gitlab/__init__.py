import os
import re
from base64 import b64decode
from shutil import copytree, rmtree
import subprocess
from zipfile import ZipFile

from databricks_cli.sdk import ApiClient
from databricks_cli.workspace.api import WorkspaceApi

from io import StringIO 
import sys

class capture_out(list):
  def __enter__(self):
    self._stdout = sys.stdout
    sys.stdout = self._stringio = StringIO()
    return self
  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio
    sys.stdout = self._stdout

class GitConnection:
  def __init__(self):
    notebook_context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    self.USERNAME = notebook_context.userName().get()
    self.UNAME = self.USERNAME.split("@")[0]
    HOST = notebook_context.apiUrl().get()
    DBX_TOKEN = notebook_context.apiToken().get()
    self.NOTEBOOK_WS_PATH = notebook_context.notebookPath().get()
    path_segments = self.NOTEBOOK_WS_PATH.split("/")
    self.FOLDER_WS_PATH = "/".join(path_segments[0:-1])
    self.TARGET_PATH = "/".join(path_segments[2:-1])
    self.ROOT_WS_PATH = "/".join(path_segments[2:-2])
    self.FOLDER_FILE_PATH = f"/tmp/{self.TARGET_PATH}"
    self.ROOT_FILE_PATH = f"/tmp/{self.ROOT_WS_PATH}" # .replace(" ","\ ")
    self.ROOT_FOLDER = self.FOLDER_WS_PATH.split("/")[-1]
    self.GITLAB_TOKEN = dbutils.notebook.run(f"/Users/{self.USERNAME}/gitlab_creds", 60, {})
    dbutils.widgets.text("repo","https://gitlab.blueorigin.com/test")
    dbutils.widgets.dropdown("action","commit",["commit","status","pull"])
    dbutils.widgets.text("branch","main")
    dbutils.widgets.text("commit_message","")
    dbutils.widgets.multiselect("files_to_add","--All---",["--All---"])

    self.repo = dbutils.widgets.get("repo")
    self.action = dbutils.widgets.get("action")
    self.branch = dbutils.widgets.get("branch")
    self.commit_message = dbutils.widgets.get("commit_message")
    self.files_to_add = dbutils.widgets.get("files_to_add").split(",")

    self.api_client = ApiClient(host=HOST, token=DBX_TOKEN)
    self.output = {}
    
  def check_target_dir(self):
    if not os.path.exists(self.ROOT_FILE_PATH):
      os.makedirs(self.ROOT_FILE_PATH, mode=0o777)
    os.chdir(self.ROOT_FILE_PATH)
      
  def pull_from_workspace(self):
    bundle_filename = "workspace_bundle.zip"
    target_filepath = f"{self.ROOT_FILE_PATH}/{bundle_filename}"
    WorkspaceApi(self.api_client).export_workspace(self.FOLDER_WS_PATH, target_filepath, "SOURCE", True)
    os.chdir(self.ROOT_FILE_PATH)
    with ZipFile('workspace_bundle.zip', 'r') as zipObj:
      zipObj.extractall()
    os.remove("workspace_bundle.zip")
    os.remove("manifest.mf")
    os.chdir(self.FOLDER_FILE_PATH)

  def pull_repo(self):
    folder_name = self.FOLDER_WS_PATH.split("/")[-1]
    gtoken = b64decode(self.GITLAB_TOKEN).decode("utf-8")
    repo_url_wtoken = f"//{gtoken}@".join(self.repo.split("//"))
    result = subprocess.run(["git", "clone", repo_url_wtoken, folder_name])
#     print(result)
    print("Pulled remote repository!", end='\x1b[2K\r')
    os.chdir(self.FOLDER_FILE_PATH)
      
  def commit_push(self):
    gtoken = b64decode(self.GITLAB_TOKEN).decode("utf-8")
    repo_url_wtoken = f"//gitlab-ci-token:{gtoken}@".join(self.repo.split("//"))
    if "--All--" in self.files_to_add:
      commit_files = ["."]
    else:
      commit_files = self.files_to_add.split(",")
    proc = subprocess.run(["git", "add", "."], capture_output=True, text=True)
    print(proc.stdout)
    output = subprocess.run(["git", "status"], capture_output=True, text=True)
    print(output.stdout)
    proc = subprocess.run(["git", "-c", f"user.email={self.USERNAME}", "-c", f"user.name={self.UNAME}", "commit", "-m", self.commit_message], capture_output=True, text=True)
    print(proc.stdout)
    proc = subprocess.run(["git", "push", "--set-upstream", repo_url_wtoken, self.branch], capture_output=True, text=True)
    print(proc.stdout)

  def get_status(self):
    output = subprocess.run(["git", "status"], capture_output=True, text=True)
    self.parse_status(output.stdout)
#     print(output.stdout)
    displayHTML("<p><pre>%s</pre></p>" % output.stdout)
#     print(output.stderr)
    
  def parse_status(self, status_output):
    pattern = re.compile(r'\t(new file|modified)?(:\s+)?(?P<files>\S.+)')
    new_files = pattern.finditer(status_output)
    self.output["files"] = [f.group("files") for f in new_files]

  def update_branch_name(self):
    branch_file = [f for f in os.listdir() if f.startswith("branch_")]
    if branch_file:
      os.remove(branch_file[0])
    with open(f"branch_{self.branch}","a") as bfile:
      bytes_out = bfile.write(f"BRANCH = \"{self.branch}\"")

  def update_workspace(self):
    with capture_out() as output:
      WorkspaceApi(self.api_client).import_workspace_dir(self.FOLDER_FILE_PATH, self.FOLDER_WS_PATH, True, True)

  def action_commit(self):
    self.check_target_dir()
    self.pull_repo()
    self.pull_from_workspace()
    self.commit_push()
    rmtree(self.ROOT_FILE_PATH)

  def action_status(self):
    self.check_target_dir()
    self.pull_repo()
    self.pull_from_workspace()
    self.get_status()
    rmtree(self.ROOT_FILE_PATH)

  def action_pull(self):
    self.check_target_dir()
    self.pull_repo()
    self.update_workspace()
    print("Updated workspace", end='\x1b\r')
    rmtree(self.ROOT_FILE_PATH)
    print("Removed Folders", end='\x1b\r')

  def action_branch(self):
    self.check_target_dir()
    self.pull_repo()
    self.checkout_branch() ######
    self.update_workspace()
    print("Updated workspace", end='\x1b\r')
    rmtree(self.ROOT_FILE_PATH)
    print("Removed Folders", end='\x1b\r')

  def run(self):
    if self.action == "commit":
      self.action_commit()
    elif self.action == "status":
      self.action_status()
    elif self.action == "pull":
      self.action_pull()
    elif self.action == "branch":
      self.action_branch()
    return self
      
  def cleanup(self):
    file_list = ["--All--"]
    file_list.extend(self.output.get("files",[]))
    print(file_list)
    dbutils.widgets.remove("files_to_add")
    print("Removed Widget")
    dbutils.widgets.multiselect("files_to_add","--All--", file_list)