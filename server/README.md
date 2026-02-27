# Setup

### Prerequisites:
Python 3.14+
Pip
You must also have a PostgreSQL server running that has a user with the ability to create tables, and knowledge of the login information for that user.

### Running:
On linux, you will first need to run "chmod +x run.sh".
Run install.sh or install.bat depending on your operating system. This will run a setup script that allows you to determine what you wish to set up. On a first install, you typically should answer yes to all parts. You will need to include a library file for whatever game you are setting the server up for in the /library/ folder in the same directory as the installer, and provide the name of that library when prompted for it.

### Future Launches:
To start the server in the future, use run.sh/run.bat.

### Stopping the server:
To stop the server, press Ctrl+C in the terminal it is running in. At the moment it does not shut down gracefully; this functionality will be added later.