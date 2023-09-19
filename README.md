# dbx_gitlab
Gitlab integration for private Databricks deployments

## Core Setup

 1. Upload the dbx_gitlab-x.whl python wheel file to DBFS via the Data Explorer UI.
 2. Include installation of the wheel in a global init script so that is available on all clusters in the workspace.
 3. Place the gitlab_actions.py and gitlab_credentials.py files in the root folder of the workspace. Ensure that all users have permissions to read the file.

## Set up User Authentication

 1. Each user will need to clone the gitlab_credentials.py file into the root of their user folder. After cloning, ensure that permissions to this file are restricted to their user.
 2. The user will need to create a personal access token in their User Settings.
 3. Returning to the cloned notebook, enter the token into the text box and click the button to encode the token value.
 4. Replace the _ENCODED_VALUE_ string with the encoded token value.

## Working with Gitlab Repos

 1. Create a new folder where you want to begin a project.
 2. Clone the "gitlab_actions" notebook from the workspace root into your new project folder.
 3. Update the values in the provided input boxes to select the git action you want to execute, the target repository you want to interact with, and other options relevant to your chosen action.
 4. Click the "Run all" button to execute the git action. 

Testing
