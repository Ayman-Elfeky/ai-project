class Settings:
    """Configuration settings for the Cultural Algorithm Scheduler."""
    
    # Algorithm Parameters
    DEFAULT_POPULATION_SIZE = 50
    DEFAULT_GENERATIONS = 100
    DEFAULT_ACCEPTANCE_RATE = 0.3
    DEFAULT_MUTATION_RATE = 0.1
    
    # Constraint Weights
    HARD_CONSTRAINT_WEIGHT = 1000
    SOFT_CONSTRAINT_WEIGHT = 1
    
    # Time Constraints
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    START_HOUR = 8
    END_HOUR = 18
    
    # K-Fold Validation / Testing
    DEFAULT_K_FOLDS = 5
    
    # File Upload
    ALLOWED_FILE_TYPES = ['csv', 'xlsx', 'json']
    MAX_FILE_SIZE_MB = 10