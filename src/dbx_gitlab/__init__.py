import os
import re
from base64 import b64decode
from shutil import copytree, rmtree
import subprocess
from zipfile import ZipFile

from databricks_cli.sdk import ApiClient
from databricks_cli.workspace.api import WorkspaceApi
from databricks_cli.workspace.types import WorkspaceLanguage

from io import StringIO 
import sys

class capture_out(list):
  def __enter__(self):
    self._stdout = sys.stdout
    sys.stdout = self._stringio = StringIO()
    return self
  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio    # free up some memory
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
    self.GITLAB_TOKEN = dbutils.notebook.run(f"/Users/{self.USERNAME}/gitlab_credentials", 60, {})
    dbutils.widgets.text("repo","https://gitlab.com/brckstr/git_test.git")
    dbutils.widgets.dropdown("action","status",["commit","change branch","new branch","status","pull"])
    dbutils.widgets.combobox("branch","main",["main"])
    dbutils.widgets.text("commit_message","")
    dbutils.widgets.multiselect("files_to_add","--All---",["--All---"])

    self.repo = dbutils.widgets.get("repo")
    self.action = dbutils.widgets.get("action")
    self.branch = dbutils.widgets.get("branch")
    self.commit_message = dbutils.widgets.get("commit_message")
    self.files_to_add = dbutils.widgets.get("files_to_add").split(",")

    self.api_client = ApiClient(host=HOST, token=DBX_TOKEN)
    self.output = {}
    # print(self.USERNAME, HOST, DBX_TOKEN, self.NOTEBOOK_WS_PATH, self.ROOT_WS_PATH, self.ROOT_FOLDER, self.ROOT_FILE_PATH, self.GITLAB_TOKEN)
    
  def check_target_dir(self):
    if not os.path.exists(self.ROOT_FILE_PATH):
      os.makedirs(self.ROOT_FILE_PATH, mode=0o777)
    os.chdir(self.ROOT_FILE_PATH)
      
  def pull_from_workspace(self):
    bundle_filename = "workspace_bundle.zip"
    target_filepath = f"{self.ROOT_FILE_PATH}/{bundle_filename}"
    WorkspaceApi(self.api_client).export_workspace(self.FOLDER_WS_PATH, target_filepath, "SOURCE", True)
    os.chdir(self.ROOT_FILE_PATH)
    with ZipFile(bundle_filename, 'r') as zipObj:
      zipObj.extractall()
    os.remove(bundle_filename)
    try:
      os.remove("manifest.mf")
    except:
      pass
    os.chdir(self.FOLDER_FILE_PATH)
    return True

  def pull_repo(self):
    folder_name = self.FOLDER_WS_PATH.split("/")[-1]
    gtoken = b64decode(self.GITLAB_TOKEN).decode("utf-8")
    repo_url_wtoken = f"//gitlab-ci-token:{gtoken}@".join(self.repo.split("//"))
    result = subprocess.run(["git", "clone", repo_url_wtoken, folder_name])
    # print(result.stdout)
    print("Pulled remote repository!", end='\x1b \r')
    os.chdir(self.FOLDER_FILE_PATH)
      
  def commit_push(self):
    gtoken = b64decode(self.GITLAB_TOKEN).decode("utf-8")
    repo_url_wtoken = f"//gitlab-ci-token:{gtoken}@".join(self.repo.split("//"))
    if "--All--" in self.files_to_add:
      commit_files = ["."]
    else:
      commit_files = self.files_to_add
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
    # print(output.stdout)
    displayHTML("<p><pre>%s</pre></p>" % output.stdout)
    # print(output.stderr)
    
  def parse_status(self, status_output):
    pattern = re.compile(r'\t(new file|modified)?(:\s+)?(?P<files>\S.+)')
    new_files = pattern.finditer(status_output)
    self.output["files"] = [f.group("files") for f in new_files]

  def check_gitignore(self):
    gitignore_file = [f for f in os.listdir() if f == ".gitignore"]
    if gitignore_file:
      file_handle = open(gitignore_file[0], "r+")
      contents = file_handle.read()
      notebook_match = re.search("gitlab_actions.py", contents)
      branchfile_match = re.search(".branch_\*", contents)
      if not notebook_match:
        file_handle.write("\ngitlab_actions.py\n")
      if not branchfile_match:
        file_handle.write("\n.branch_*\n")
    else:
      with open(f".gitignore","a") as bfile:
        bytes_out = bfile.write(f".branch_*\ngitlab_actions.py\n")

  def checkout_branch(self):
    if self.action in ['create branch', 'status', 'commit']:
      if (branch_name := self.output.get("current_branch", None)):
        result = subprocess.run(["git", "checkout", self.output["current_branch"]])
    else:
      result = subprocess.run(["git", "checkout", self.branch])
    # print(result.stdout)

  def create_branch(self):
    result = subprocess.run(["git", "branch", self.branch])
    result = subprocess.run(["git", "push", "origin", self.branch])
    self.list_branches()

  def list_branches(self):
    result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)
    self.parse_branches(result.stdout)

  def parse_current_branch(self):
    object_list = WorkspaceApi(self.api_client).list_objects(self.FOLDER_WS_PATH)
    branch_file = [f.basename for f in object_list if f.basename.startswith(".branch_")]
    if branch_file:
      pattern = re.compile(r'\.branch_(?P<branch>\w+)')
      branch = pattern.finditer(branch_file[0])
      self.output["current_branch"] = [f.group("branch") for f in branch][0]
      return True
    else:
      return False

  def parse_branches(self, branch_output):
    pattern = re.compile(r'/(?P<branch>\w+)(\n|$)')
    branches = pattern.finditer(branch_output)
    self.output["branches"] = {b.group("branch") for b in branches} 

  def update_branch_name(self):
    self.parse_current_branch()
    if (branch := self.output.get("current_branch", None)):
      WorkspaceApi(self.api_client).delete(f"{self.FOLDER_WS_PATH}/.branch_{branch}", False)
    with open(f".branch_{self.branch}.py","a") as bfile:
      bytes_out = bfile.write(f"# DO NOT EDIT!!!\nBRANCH = \"{self.branch}\"")

  def update_workspace(self):
    with capture_out() as output:
      workspace = WorkspaceApi(self.api_client)
      filenames = os.listdir(self.FOLDER_FILE_PATH)
      for filename in filenames:
        if filename != 'gitlab_actions.py':
          cur_src = os.path.join(self.FOLDER_FILE_PATH, filename)
          cur_dst = os.path.join(self.FOLDER_WS_PATH, filename)
          if os.path.isdir(cur_src) and not filename.startswith('.'):
            workspace.import_workspace_dir(cur_src, cur_dst, True, True)
          elif os.path.isfile(cur_src):
            ext = WorkspaceLanguage.get_extension(cur_src)
            if ext != '':
              cur_dst = cur_dst[:-len(ext)]
              (language, file_format) = WorkspaceLanguage.to_language_and_format(cur_src)
              workspace.import_workspace(cur_src, cur_dst, language, file_format, True)
            else:
              pass

  def action_commit(self):
    self.check_target_dir()
    self.pull_repo()
    if self.parse_current_branch():
      self.checkout_branch()
      self.pull_from_workspace()
      self.check_gitignore()
      self.commit_push()
      self.list_branches()
    rmtree(self.ROOT_FILE_PATH)

  def action_status(self):
    self.check_target_dir()
    self.pull_repo()
    self.list_branches()
    if self.parse_current_branch():
      self.checkout_branch()
      self.check_gitignore()
      self.pull_from_workspace()
      self.get_status()
    else:
      print("This repo has not been initialized. Please execute the pull action to initialize the repo.")
    rmtree(self.ROOT_FILE_PATH)

  def action_pull(self):
    self.check_target_dir()
    self.pull_repo()
    self.list_branches()
    self.update_branch_name()
    self.update_workspace()
    print("Updated workspace", end='\x1b \r')
    rmtree(self.ROOT_FILE_PATH)
    print("Removed Folders", end='\x1b \r')

  def action_checkout(self):
    self.check_target_dir()
    self.pull_repo()
    self.checkout_branch() ######
    self.list_branches()
    self.update_branch_name()
    self.update_workspace()
    print("Updated workspace", end='\x1b \r')
    rmtree(self.ROOT_FILE_PATH)
    print("Removed Folders", end='\x1b \r')

  def action_branch(self):
    self.check_target_dir()
    self.pull_repo()
    self.checkout_branch() ######
    self.create_branch()
    self.list_branches()
    print("Updated workspace", end='\x1b \r')
    rmtree(self.ROOT_FILE_PATH)
    print("Removed Folders", end='\x1b \r')

  def run(self):
    if self.action == "commit":
      self.action_commit()
    elif self.action == "status":
      self.action_status()
    elif self.action == "pull":
      self.action_pull()
    elif self.action == "new branch":
      self.action_branch()
    elif self.action == "change branch":
      self.action_checkout()
    return self
      
  def cleanup(self):
    file_list = ["--All--"]
    file_list.extend(self.output.get("files",[])) 
    dbutils.widgets.remove("files_to_add")
    dbutils.widgets.remove("branch")
    print("Removed Widget")
    dbutils.widgets.multiselect("files_to_add","--All--", file_list)
    dbutils.widgets.combobox("branch", self.branch, list(self.output.get("branches",[self.branch])))
