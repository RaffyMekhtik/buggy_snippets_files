    def to_dict(self):
        return {
            "Action": "InventoryRetrieval",
            "ArchiveId": self.archive_id,
            "ArchiveSizeInBytes": 0,
            "ArchiveSHA256TreeHash": None,
            "Completed": True,
            "CompletionDate": "2013-03-20T17:03:43.221Z",
            "CreationDate": "2013-03-20T17:03:43.221Z",
            "InventorySizeInBytes": "0",
            "JobDescription": None,
            "JobId": self.job_id,
            "RetrievalByteRange": None,
            "SHA256TreeHash": None,
            "SNSTopic": None,
            "StatusCode": "Succeeded",
            "StatusMessage": None,
            "VaultARN": None,
        }