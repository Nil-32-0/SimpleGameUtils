from datetime import datetime

class Logger():
    def __init__(self):
        self.open_time = datetime.now()
    
    def openFile(self):
        fName = 'logs/{:%Y-%m-%d_%H:%M:%S}'.format(self.open_time)
        return open(fName, "a")
    
    def writeToFile(self, message: str):
        with self.openFile() as file:
            file.write(message+"\n")

    def addPrefix(self, message: str, source: str) -> str:
        t = datetime.now()
        return '[{:%H:%M:%S}] [{}] {}'.format(t, source, message)
    
    def addPrefixColor(self, message: str, source: str, color: int) -> str:
        return f"\033[{color}m{self.addPrefix(message, source)}\033[00m"

    def debug(self, message: str, console: bool):
        """
        Write a message to the debug output.
        """
        self.writeToFile(self.addPrefix(message, "DEBUG"))
        if console:
            print(self.addPrefixColor(message, "DEBUG", 96))

    def error(self, message: str, console: bool):
        """
        Write a message to the error output.
        """
        self.writeToFile(self.addPrefix(message, "ERROR"))
        if console:
            print(self.addPrefixColor(message, "ERROR", 91))

    def info(self, message: str, console: bool):
        """
        Write a message to the info output.
        """
        self.writeToFile(self.addPrefix(message, "INFO"))
        if console:
            print(self.addPrefix(message, "INFO"))

    def warn(self, message: str, console: bool):
        """
        Write a message to the warning output.
        """
        self.writeToFile(self.addPrefix(message, "WARN"))
        if console:
            print(self.addPrefixColor(message, "WARN", 33))