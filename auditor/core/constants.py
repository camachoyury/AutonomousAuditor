from decimal import Decimal

# Categorías de documentos
DOC_TYPE_PL = 'pl'
DOC_TYPE_BALANCE = 'balance'

# Formatos de archivo
FORMAT_MARKDOWN = 'markdown'
FORMAT_CSV = 'csv'

# Categorías financieras
CATEGORY_REVENUE = 'revenue'
CATEGORY_EXPENSE = 'expense'
CATEGORY_ASSET = 'asset'
CATEGORY_LIABILITY = 'liability'
CATEGORY_EQUITY = 'equity'

# Umbrales de validación
MIN_AMOUNT = Decimal('-999999999.99')
MAX_AMOUNT = Decimal('999999999.99')
TOLERANCE = Decimal('0.01')

# Configuración de GitHub
GITHUB_LABELS = ['auditoría', 'finanzas', 'automático']
GITHUB_DEFAULT_BRANCH = 'main'

# Patrones de búsqueda de archivos
PL_FILE_PATTERNS = ['pl', 'income', 'profit']
BALANCE_FILE_PATTERNS = ['balance', 'bs']
FILE_EXTENSIONS = ['.md', '.csv'] 