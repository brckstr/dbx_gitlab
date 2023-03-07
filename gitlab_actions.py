# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # Gitlab Actions
# MAGIC 
# MAGIC This notebook is used to execute git actions to interact with a remote git repository. It accepts parameters from the above widgets and uses them to execute the according actions.
# MAGIC 
# MAGIC **Before executing any commands**, you must first create the folder where you will sync the remote repository and clone this notebook to that folder.
# MAGIC 
# MAGIC  1. Click on the "Workspace" icon from the pullout menu on the left.
# MAGIC  2. Navigate to the parent folder where you will create the repository folder.
# MAGIC  3. Click on the caret next to the parent folder name and select "Create", then "Folder".
# MAGIC  4. Enter your desired folder name and click "Create Folder".
# MAGIC  5. Now back in the notebook, go to the "File" menu above and select "Clone."
# MAGIC  6. Select your newly created folder, remove the " (1)" that is added to the notebook name and click "Clone".
# MAGIC  
# MAGIC You're all set! You can now execute the following git actions to interact with your remote repository:

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pulling an existing repository
# MAGIC 
# MAGIC Required Parameters:
# MAGIC  - __action__: "pull"
# MAGIC  - __repo__: The url of the gitlab repository that you'd like to sync.
# MAGIC  - __branch__: The branch that you'd like to start working on.
# MAGIC  
# MAGIC Once you've entered these parameters, you can click the "Run all" button at the upper right to execute the action.
# MAGIC 
# MAGIC ### Committing to a repository
# MAGIC
# MAGIC Required Parameters:
# MAGIC  - __action__: "commit"
# MAGIC  - __repo__: The url of the gitlab repository that you'd like to commit to.
# MAGIC  - __branch__: The branch that you'd like to start working on.
# MAGIC  - __commit_message__: Commit message to log with your commit.
# MAGIC
# MAGIC Optional Parameters:
# MAGIC  - __files_to_add__: A list of new and modified files to include in the commit. Default is "--All--"
# MAGIC 
# MAGIC ### Change your working branch
# MAGIC
# MAGIC Required Parameters:
# MAGIC  - __action__: "branch"
# MAGIC  - __repo__: The url of the gitlab repository that you'd like to commit to.
# MAGIC  - __branch__: The branch that you'd like to start working on.
# MAGIC 
# MAGIC ### See the status of your changes
# MAGIC
# MAGIC Required Parameters:
# MAGIC  - __action__: "status"
# MAGIC  - __repo__: The url of the gitlab repository that you'd like to commit to.
# MAGIC  - __branch__: The branch that you'd like to start working on.

# COMMAND ----------

from dbx_gitlab import GitConnection

g = GitConnection().run()

# COMMAND ----------

g.cleanup()
