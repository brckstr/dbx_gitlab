# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <p align="center" width="100%">
# MAGIC   <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaqtlHFs5x2qtMXMnBj8JELl45RJ1qexRdBn-PuXhs&s" />
# MAGIC </p>
# MAGIC 
# MAGIC # Your Gitlab Credentials
# MAGIC 
# MAGIC ## Clone this Notebook
# MAGIC 
# MAGIC The Git integration expects your credentials to be stored in the root of your user directory (ie. /Users/<user_id>/gitlab_creds)
# MAGIC 
# MAGIC  1. From the "File" menu above select "Clone"
# MAGIC  2. Select the "Users" folder and then your personal folder, which should be the first one at the top.
# MAGIC  3. Be sure to remove the " (1)" that is automatically added to the filename and click the "Clone" button.
# MAGIC  
# MAGIC ## Creating a Personal Access Token
# MAGIC 
# MAGIC You need to go to the Gitlab UI to generate a new personal access token.
# MAGIC 
# MAGIC 1. In the top-right corner, select your avatar.
# MAGIC 2. Select Edit profile.
# MAGIC 3. On the left sidebar, select Access Tokens.
# MAGIC 4. Enter a name and optional expiry date for the token.
# MAGIC 5. Select the desired scopes. (read_repository, write_repository)
# MAGIC 6. Select Create personal access token.
# MAGIC 7. Copy your personal access token for use in the next step.
# MAGIC 
# MAGIC ## Entering your Personal Access Token
# MAGIC 
# MAGIC Finally, you will encode your token before entering it in the notebook, so that it doesn't get stored in cleartext.
# MAGIC 
# MAGIC  1. Enter your token in the textbox in the cell below and click the "Encode" button.
# MAGIC  2. Copy the encoded value that is returned, and paste in the following cell over \_ENCODED_VALUE\_.
# MAGIC  
# MAGIC  You're all set! You can now start syncing repositories from Gitlab using the [gitlab_actions]() notebook.

# COMMAND ----------

displayHTML("""
<div>
<div>
<h2>Gitlab Credentials</h2>
  <form id="form">
  <label>Enter your Personal Access Token: <input type="text" id="token" /></label>
  <br /><br />
  <button type="submit">Encode</button>
  </form>
  <p id="log"></p>
</div>
<script>
  function logSubmit(event) {
  var tk = btoa(document.getElementById('token').value)
  log.textContent = `Encoded token: ${tk}`;
  event.preventDefault();
}

const form = document.getElementById('form');
const log = document.getElementById('log');
const token = document.getElementById('token');
form.addEventListener('submit', logSubmit);
  </script>
</div>""")

# COMMAND ----------

GITLAB_TOKEN = "_ENCODED_VALUE_"

# COMMAND ----------

dbutils.notebook.exit(GITLAB_TOKEN)

# COMMAND ----------

# No longer needed
