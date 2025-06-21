# src/core/exceptions.py
"""
Custom exception classes for the HR Q&A system.
Provides specific error types for better error handling and debugging.
"""

class HRQAException(Exception):
    """Base exception class for HR Q&A system"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "HRQA_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }

# Database Exceptions
class DatabaseException(HRQAException):
    """Base exception for database-related errors"""
    
    def __init__(self, message: str, operation: str = None, collection: str = None):
        self.operation = operation
        self.collection = collection
        details = {}
        if operation:
            details["operation"] = operation
        if collection:
            details["collection"] = collection
        super().__init__(message, "DB_ERROR", details)

class DatabaseConnectionException(DatabaseException):
    """Exception for database connection failures"""
    
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message, "connection", None)
        self.error_code = "DB_CONNECTION_ERROR"

class DocumentNotFoundException(DatabaseException):
    """Exception for when a document is not found"""
    
    def __init__(self, collection: str, filter_criteria: dict):
        message = f"Document not found in collection '{collection}'"
        super().__init__(message, "find", collection)
        self.error_code = "DOC_NOT_FOUND"
        self.details["filter"] = filter_criteria

class DocumentInsertException(DatabaseException):
    """Exception for document insertion failures"""
    
    def __init__(self, collection: str, error_details: str = None):
        message = f"Failed to insert document in collection '{collection}'"
        if error_details:
            message += f": {error_details}"
        super().__init__(message, "insert", collection)
        self.error_code = "DOC_INSERT_ERROR"

class DocumentUpdateException(DatabaseException):
    """Exception for document update failures"""
    
    def __init__(self, collection: str, document_id: str, error_details: str = None):
        message = f"Failed to update document '{document_id}' in collection '{collection}'"
        if error_details:
            message += f": {error_details}"
        super().__init__(message, "update", collection)
        self.error_code = "DOC_UPDATE_ERROR"
        self.details["document_id"] = document_id

class DocumentDeleteException(DatabaseException):
    """Exception for document deletion failures"""
    
    def __init__(self, collection: str, document_id: str, error_details: str = None):
        message = f"Failed to delete document '{document_id}' from collection '{collection}'"
        if error_details:
            message += f": {error_details}"
        super().__init__(message, "delete", collection)
        self.error_code = "DOC_DELETE_ERROR"
        self.details["document_id"] = document_id

# Search Exceptions
class SearchException(HRQAException):
    """Base exception for search-related errors"""
    
    def __init__(self, message: str, search_type: str = None, query: str = None):
        self.search_type = search_type
        self.query = query
        details = {}
        if search_type:
            details["search_type"] = search_type
        if query:
            details["query"] = query
        super().__init__(message, "SEARCH_ERROR", details)

class SearchServiceException(SearchException):
    """Exception for Azure Search service errors"""
    
    def __init__(self, message: str, service_error: str = None):
        super().__init__(message, "azure_search", None)
        self.error_code = "SEARCH_SERVICE_ERROR"
        if service_error:
            self.details["service_error"] = service_error

class SearchIndexException(SearchException):
    """Exception for search index related errors"""
    
    def __init__(self, message: str, index_name: str, operation: str = None):
        super().__init__(message, "index_operation", None)
        self.error_code = "SEARCH_INDEX_ERROR"
        self.details["index_name"] = index_name
        if operation:
            self.details["operation"] = operation

class EmbeddingException(SearchException):
    """Exception for embedding generation errors"""
    
    def __init__(self, message: str, text: str = None):
        super().__init__(message, "embedding", None)
        self.error_code = "EMBEDDING_ERROR"
        if text:
            self.details["text_length"] = len(text)

class VectorSearchException(SearchException):
    """Exception for vector search errors"""
    
    def __init__(self, message: str, vector_dimension: int = None):
        super().__init__(message, "vector_search", None)
        self.error_code = "VECTOR_SEARCH_ERROR"
        if vector_dimension:
            self.details["vector_dimension"] = vector_dimension

# Query Processing Exceptions
class QueryException(HRQAException):
    """Base exception for query processing errors"""
    
    def __init__(self, message: str, query: str = None, intent: str = None):
        self.query = query
        self.intent = intent
        details = {}
        if query:
            details["query"] = query
        if intent:
            details["intent"] = intent
        super().__init__(message, "QUERY_ERROR", details)

class IntentDetectionException(QueryException):
    """Exception for intent detection failures"""
    
    def __init__(self, message: str, query: str):
        super().__init__(message, query, None)
        self.error_code = "INTENT_DETECTION_ERROR"

class EntityExtractionException(QueryException):
    """Exception for entity extraction failures"""
    
    def __init__(self, message: str, query: str, entities: dict = None):
        super().__init__(message, query, None)
        self.error_code = "ENTITY_EXTRACTION_ERROR"
        if entities:
            self.details["extracted_entities"] = entities

class ResponseGenerationException(QueryException):
    """Exception for response generation failures"""
    
    def __init__(self, message: str, query: str, context: str = None):
        super().__init__(message, query, None)
        self.error_code = "RESPONSE_GENERATION_ERROR"
        if context:
            self.details["context_length"] = len(context)

# API Exceptions
class APIException(HRQAException):
    """Base exception for API-related errors"""
    
    def __init__(self, message: str, status_code: int = 500, endpoint: str = None):
        self.status_code = status_code
        self.endpoint = endpoint
        details = {"status_code": status_code}
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(message, "API_ERROR", details)

class ValidationException(APIException):
    """Exception for request validation errors"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message, 400, None)
        self.error_code = "VALIDATION_ERROR"
        if field:
            self.details["field"] = field
        if value:
            self.details["invalid_value"] = value

class AuthenticationException(APIException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, None)
        self.error_code = "AUTH_ERROR"

class AuthorizationException(APIException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Access denied", resource: str = None):
        super().__init__(message, 403, None)
        self.error_code = "AUTHZ_ERROR"
        if resource:
            self.details["resource"] = resource

class RateLimitException(APIException):
    """Exception for rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, 429, None)
        self.error_code = "RATE_LIMIT_ERROR"
        if retry_after:
            self.details["retry_after_seconds"] = retry_after

# Configuration Exceptions
class ConfigurationException(HRQAException):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, "CONFIG_ERROR", details)

class MissingConfigException(ConfigurationException):
    """Exception for missing configuration values"""
    
    def __init__(self, config_key: str):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, config_key)
        self.error_code = "MISSING_CONFIG"

class InvalidConfigException(ConfigurationException):
    """Exception for invalid configuration values"""
    
    def __init__(self, config_key: str, value: str, expected: str = None):
        message = f"Invalid configuration value for '{config_key}': {value}"
        if expected:
            message += f" (expected: {expected})"
        super().__init__(message, config_key)
        self.error_code = "INVALID_CONFIG"
        self.details["value"] = value
        if expected:
            self.details["expected"] = expected

# Processing Exceptions
class ProcessingException(HRQAException):
    """Base exception for data processing errors"""
    
    def __init__(self, message: str, process_type: str = None, file_path: str = None):
        self.process_type = process_type
        self.file_path = file_path
        details = {}
        if process_type:
            details["process_type"] = process_type
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, "PROCESSING_ERROR", details)

class ETLException(ProcessingException):
    """Exception for ETL process errors"""
    
    def __init__(self, message: str, stage: str, source: str = None):
        super().__init__(message, "etl", source)
        self.error_code = "ETL_ERROR"
        self.details["stage"] = stage

class DataValidationException(ProcessingException):
    """Exception for data validation errors"""
    
    def __init__(self, message: str, field: str = None, value: str = None, rule: str = None):
        super().__init__(message, "validation", None)
        self.error_code = "DATA_VALIDATION_ERROR"
        if field:
            self.details["field"] = field
        if value:
            self.details["value"] = value
        if rule:
            self.details["validation_rule"] = rule

class FileProcessingException(ProcessingException):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, file_path: str, file_type: str = None):
        super().__init__(message, "file_processing", file_path)
        self.error_code = "FILE_PROCESSING_ERROR"
        if file_type:
            self.details["file_type"] = file_type

# Utility functions for exception handling
def handle_database_error(func):
    """Decorator to handle database errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "connection" in str(e).lower():
                raise DatabaseConnectionException(str(e))
            elif "not found" in str(e).lower():
                raise DocumentNotFoundException("unknown", {})
            else:
                raise DatabaseException(str(e))
    return wrapper

def handle_search_error(func):
    """Decorator to handle search errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "index" in str(e).lower():
                raise SearchIndexException(str(e), "unknown")
            elif "embedding" in str(e).lower():
                raise EmbeddingException(str(e))
            else:
                raise SearchException(str(e))
    return wrapper

def handle_api_error(func):
    """Decorator to handle API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationException:
            raise
        except Exception as e:
            raise APIException(str(e))
    return wrapper