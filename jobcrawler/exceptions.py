class ScrapingException(Exception):
    def __init__(self, url, message, code):
        self.url = url
        self.message = message
        self.code = code

    def __str__(self):
        return f"Getting {self.url} returned status code 404."

class CompanyExistsException(Exception):
    def __init__(self, name):
        self.name = name
        self.code = 400

    def __str__(self):
        return f"A company called {self.name} already exists."

