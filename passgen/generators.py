import secrets
import string
from datetime import datetime
from math import log2
from typing import Dict, List, Union, Optional

class PasswordGenerator:
    """Enhanced secure password generator with multiple generation methods and security checks"""
    
    def __init__(self):
        # Use cryptographically secure random generator
        self.random = secrets.SystemRandom()
        
        # Character sets
        self.LOWERCASE = string.ascii_lowercase + "ñ"
        self.UPPERCASE = string.ascii_uppercase + "Ñ"
        self.ACCENTED_LOWER = "áéíóúñ"
        self.ACCENTED_UPPER = "ÁÉÍÓÚÑ"
        self.SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        self.NUMBERS = string.digits
        self.PRONOUNCEABLE_SYLLABLES = [
            'ba', 'be', 'bi', 'bo', 'bu', 'ca', 'ce', 'ci', 'co', 'cu',
            'da', 'de', 'di', 'do', 'du', 'fa', 'fe', 'fi', 'fo', 'fu'
        ]
        
        # Components dictionary
        self.components = {
            'a': self._lowercase,
            'A': self._uppercase,
            '!': self._symbols,
            'x': self._numbers,
            'd': self._date,
            'p': self._pronounceable
        }
        
        # Enhanced predefined patterns with security metadata
        self.PREDEFINED_PATTERNS = {
            'basic': {
                'pattern': "a:4|x:3|!:1",
                'description': "Letras + números + símbolo básico",
                'category': "Básico",
                'min_length': 8,
                'strength': "Media",
                'entropy': 45
            },
            'strong': {
                'pattern': "A:3|a:3|!:2|x:2",
                'description': "Mayúsculas, minúsculas, símbolos y números",
                'category': "Seguro", 
                'min_length': 10,
                'strength': "Alta",
                'entropy': 60
            },
            'pin': {
                'pattern': "x:6",
                'description': "PIN numérico de 6 dígitos",
                'category': "Numérico",
                'min_length': 6,
                'strength': "Baja",
                'entropy': 20
            },
            'phrase': {
                'pattern': "p:3|x:2",
                'description': "Frase pronunciable con números",
                'category': "Memorizable",
                'min_length': 8,
                'strength': "Media",
                'entropy': 35
            },
            'secure': {
                'pattern': "A:3:1|a:3:1|!:2|x:2|!:1",
                'description': "Máxima seguridad con acentos y símbolos",
                'category': "Seguro",
                'min_length': 12,
                'strength': "Muy Alta",
                'entropy': 75
            },
            'date_based': {
                'pattern': "a:2|d:ymd|!:1",
                'description': "Basado en fecha actual",
                'category': "Personalizado",
                'min_length': 10,
                'strength': "Media",
                'entropy': 40
            },
            'accented': {
                'pattern': "a:3:1|A:2:1|x:2",
                'description': "Incluye caracteres acentuados obligatorios",
                'category': "Internacional",
                'min_length': 8,
                'strength': "Alta",
                'entropy': 55
            }
        }
        
        # Security configuration
        self.MIN_LENGTH = 8
        self.MAX_LENGTH = 64
        self.MIN_ENTROPY = 60  # bits
        self.BANNED_CHARS = "'\"\\`"
        self.COMMON_PATTERNS = [
            '123', 'abc', 'qwe', 'asd', 'password', 'admin', 'qwerty'
        ]

    # Core generation methods ################################################

    def _lowercase(self, length: int = 4, accents: int = 0) -> str:
        """Generate lowercase letters with optional accents"""
        return self._generate_letters(length, accents, self.LOWERCASE, self.ACCENTED_LOWER)

    def _uppercase(self, length: int = 4, accents: int = 0) -> str:
        """Generate uppercase letters with optional accents"""
        return self._generate_letters(length, accents, self.UPPERCASE, self.ACCENTED_UPPER)

    def _generate_letters(self, length: int, min_accents: int, 
                         base_chars: str, accented_chars: str) -> str:
        """Base method for letter generation with accents"""
        length = max(int(length), 1)
        min_accents = max(int(min_accents), 0)
        
        # Ensure we have enough accented characters
        accented = [self.random.choice(accented_chars) for _ in range(min_accents)]
        remaining = [self.random.choice(base_chars) for _ in range(length - min_accents)]
        
        # Combine and shuffle
        result = accented + remaining
        self.random.shuffle(result)
        return ''.join(result)

    def _symbols(self, length: int = 1) -> str:
        """Generate random symbols"""
        return ''.join(self.random.choice(self.SYMBOLS) for _ in range(int(length)))

    def _numbers(self, length: int = 2) -> str:
        """Generate random numbers"""
        return ''.join(self.random.choice(self.NUMBERS) for _ in range(int(length)))

    def _date(self, format: str = "ymd") -> str:
        """Generate current date in specified format"""
        now = datetime.now()
        formats = {
            "ymd": now.strftime("%Y%m%d"),
            "dmy": now.strftime("%d%m%Y"),
            "mdy": now.strftime("%m%d%Y")
        }
        return formats.get(format, formats["ymd"])

    def _pronounceable(self, length: int = 8, complexity: int = 1) -> str:
        """Generate pronounceable passwords with configurable complexity"""
        syllables = []
        for _ in range(int(length) // 2):
            syllables.append(self.random.choice(self.PRONOUNCEABLE_SYLLABLES))
        
        password = ''.join(syllables)[:int(length)]
        
        # Add complexity
        if complexity >= 1:
            password = self._capitalize_random(password)
        if complexity >= 2:
            password = self._add_numbers(password)
        if complexity >= 3:
            password = self._add_symbols(password)
            
        return password

    # Public interface methods ###############################################

    def generate(self, pattern: str) -> Dict[str, Union[str, int, float]]:
        """Generate password based on pattern with security checks"""
        try:
            # Parse and validate pattern
            components = self._parse_pattern(pattern)
            
            # Generate password parts
            password_parts = []
            for comp in components:
                func = self.components[comp['type']]
                password_parts.append(func(**comp['params']))
            
            password = ''.join(password_parts)
            
            # Security checks
            self._validate_password(password)
            
            # Calculate metrics
            entropy = self.calculate_entropy(password)
            strength = self.estimate_strength(password)
            length = len(password)
            
            return {
                'password': password,
                'entropy': entropy,
                'strength': strength,
                'length': length,
                'pattern': pattern
            }
            
        except Exception as e:
            raise ValueError(f"Error generating password: {str(e)}")

    def generate_pronounceable(self, length: int = 10, 
                              complexity: int = 2) -> Dict[str, Union[str, int, float]]:
        """Generate memorable password with configurable complexity"""
        try:
            password = self._pronounceable(length, complexity)
            self._validate_password(password)
            
            return {
                'password': password,
                'entropy': self.calculate_entropy(password),
                'strength': self.estimate_strength(password),
                'length': len(password),
                'type': 'pronounceable'
            }
        except Exception as e:
            raise ValueError(f"Error generating pronounceable password: {str(e)}")

    # Security methods #######################################################

    def _validate_password(self, password: str) -> None:
        """Perform all security validations on generated password"""
        if len(password) < self.MIN_LENGTH:
            raise ValueError(f"Password too short (min {self.MIN_LENGTH} chars)")
        if len(password) > self.MAX_LENGTH:
            raise ValueError(f"Password too long (max {self.MAX_LENGTH} chars)")
        if any(c in self.BANNED_CHARS for c in password):
            raise ValueError("Password contains banned characters")
        if self._has_common_patterns(password):
            raise ValueError("Password contains common insecure patterns")
        if self.calculate_entropy(password) < self.MIN_ENTROPY:
            raise ValueError("Password entropy too low")

    def _has_common_patterns(self, password: str) -> bool:
        """Check for common insecure patterns"""
        lower_pass = password.lower()
        return any(p in lower_pass for p in self.COMMON_PATTERNS)

    def calculate_entropy(self, password: str) -> float:
        """Calculate password entropy in bits"""
        char_set = 0
        if any(c.islower() for c in password): char_set += 26
        if any(c.isupper() for c in password): char_set += 26
        if any(c.isdigit() for c in password): char_set += 10
        if any(c in self.SYMBOLS for c in password): char_set += len(self.SYMBOLS)
        
        if char_set == 0:
            return 0
        return len(password) * log2(char_set)

    def estimate_strength(self, password: str) -> str:
        """Estimate password strength based on multiple factors"""
        score = 0
        
        # Length score
        length = len(password)
        score += min(length // 4, 5)  # Up to 5 points for length
        
        # Character diversity
        char_types = 0
        if any(c.islower() for c in password): char_types += 1
        if any(c.isupper() for c in password): char_types += 1
        if any(c.isdigit() for c in password): char_types += 1
        if any(c in self.SYMBOLS for c in password): char_types += 1
        score += (char_types - 1) * 2  # 0-6 points
        
        # Entropy score
        entropy = self.calculate_entropy(password)
        score += min(int(entropy // 20), 4)  # Up to 4 points
        
        # Deductions for common patterns
        if self._has_common_patterns(password):
            score = max(0, score - 3)
        
        # Classify
        if score >= 10: return "Muy Alta"
        if score >= 7: return "Alta"
        if score >= 4: return "Media"
        return "Baja"

    # Helper methods #########################################################

    def _parse_pattern(self, pattern: str) -> List[Dict[str, Union[str, Dict]]]:
        """Parse pattern string into component instructions"""
        components = []
        
        # Check if it's a predefined pattern
        if pattern in self.PREDEFINED_PATTERNS:
            pattern = self.PREDEFINED_PATTERNS[pattern]['pattern']
        
        for token in [t.strip() for t in pattern.split("|") if t.strip()]:
            if ':' in token:
                parts = token.split(':')
                symbol = parts[0].strip()
                
                if symbol not in self.components:
                    raise ValueError(f"Invalid component: {symbol}")
                
                params = {}
                if symbol in ['a', 'A']:
                    params['length'] = int(parts[1]) if len(parts) > 1 else 4
                    params['accents'] = int(parts[2]) if len(parts) > 2 else 0
                elif symbol == 'p':
                    params['length'] = int(parts[1]) if len(parts) > 1 else 8
                    params['complexity'] = int(parts[2]) if len(parts) > 2 else 1
                elif symbol == 'd':
                    params['format'] = parts[1] if len(parts) > 1 else 'ymd'
                else:
                    params['length'] = int(parts[1]) if len(parts) > 1 else 1
                
                components.append({'type': symbol, 'params': params})
            else:
                symbol = token.strip()
                if symbol not in self.components:
                    raise ValueError(f"Invalid component: {symbol}")
                components.append({'type': symbol, 'params': {}})
        
        return components

    def _capitalize_random(self, s: str) -> str:
        """Capitalize random letters in string"""
        if not s:
            return s
        index = self.random.randint(0, len(s)-1)
        return s[:index] + s[index].upper() + s[index+1:]

    def _add_numbers(self, s: str) -> str:
        """Add random numbers to string"""
        return s + self.random.choice(self.NUMBERS)

    def _add_symbols(self, s: str) -> str:
        """Add random symbols to string"""
        return s + self.random.choice(self.SYMBOLS)

    # Metadata methods (unchanged from original) #############################

    def get_context_data(self) -> Dict:
        """Prepare all template data"""
        demo_password = self._safe_generate("a:3|x:2")
        
        predefined_patterns = []
        for key, data in self.PREDEFINED_PATTERNS.items():
            try:
                example = self.generate(data['pattern'])['password']
            except:
                example = self._safe_generate(data['pattern'])
            
            predefined_patterns.append({
                'name': key,
                'pattern': data['pattern'],
                'description': data['description'],
                'example': example,
                'category': data['category'],
                'strength': data['strength']
            })
        
        return {
            'demo_password': demo_password,
            'predefined_patterns': predefined_patterns,
            'categories': self.CATEGORIES
        }

    def _safe_generate(self, pattern: str) -> str:
        """Safe generation that never fails (for examples)"""
        try:
            return self.generate(pattern)['password']
        except:
            parts = []
            for token in [t.strip() for t in pattern.split("|") if t.strip()]:
                if ':' in token:
                    symbol = token.split(':')[0]
                    if symbol in self.components:
                        parts.append(self.components[symbol](1))
            return ''.join(parts)

    def get_pattern_info(self, pattern_name: str) -> Optional[Dict]:
        """Get detailed info about a specific pattern"""
        if pattern_name in self.PREDEFINED_PATTERNS:
            pattern_data = self.PREDEFINED_PATTERNS[pattern_name]
            try:
                example = self.generate(pattern_data['pattern'])['password']
            except:
                example = self._safe_generate(pattern_data['pattern'])
            
            return {
                'name': pattern_name,
                'pattern': pattern_data['pattern'],
                'description': pattern_data['description'],
                'example': example,
                'category': pattern_data['category'],
                'strength': pattern_data['strength'],
                'min_length': pattern_data.get('min_length', 8),
                'entropy': pattern_data.get('entropy', 0)
            }
        return None

    def get_pattern_choices(self) -> List[tuple]:
        """Get options for select/radio buttons"""
        return [
            (key, f"{data['description']} ({data['pattern']})") 
            for key, data in self.PREDEFINED_PATTERNS.items()
        ] + [('custom', 'Personalizado')]

    def get_initial_pattern(self, pattern_name: str) -> str:
        """Get initial pattern for a given name"""
        if pattern_name in self.PREDEFINED_PATTERNS:
            return self.PREDEFINED_PATTERNS[pattern_name]['pattern']
        return ""

# Example usage
if __name__ == "__main__":
    generator = PasswordGenerator()
    
    # Generate using pattern
    try:
        result = generator.generate("A:3:1|a:3:1|!:2|x:2")
        print(f"Generated password: {result['password']}")
        print(f"Strength: {result['strength']}")
        print(f"Entropy: {result['entropy']:.1f} bits")
    except ValueError as e:
        print(f"Error: {str(e)}")
    
    # Generate pronounceable password
    try:
        result = generator.generate_pronounceable(length=12, complexity=2)
        print(f"\nPronounceable password: {result['password']}")
        print(f"Strength: {result['strength']}")
        print(f"Entropy: {result['entropy']:.1f} bits")
    except ValueError as e:
        print(f"Error: {str(e)}")