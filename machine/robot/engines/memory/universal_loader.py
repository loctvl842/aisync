import langchain_community.document_loaders  as DocumentLoader

class UniversalLoader():
    """
    Universal loader for different file types
    """
    def __init__(self, file_type = 'txt'):
        self.file_type = file_type
        self.loader = None
        
        self.supported_file_type = {
                                    'txt': 'TextLoader'
                                    }
        
    def add_file_type(self, file_type):
        """
        Add a new file type to the supported file types
        Update later in the next MR
        """
        pass
        
    def choose_loader(self):
        """
        Choose the loader from langchain_community.document_loaders based on the file type
        """
        # TODO: Add more file types
        
        loader_name = self.supported_file_type.get(self.file_type)
        
        if loader_name:
            self.loader = getattr(DocumentLoader, loader_name, None)
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")
        
        return self.loader