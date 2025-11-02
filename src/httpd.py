# httpd.py - ASS_HTTPd v0.8: Alice Side Script Custom HTTPd
# Complete ASS Protocol Implementation with Full Module Integration

import asyncio
import ssl
import json
import time
import hashlib
import hmac
import secrets
import logging
import re
from typing import Dict, Any, Optional, Callable, Tuple, List
from datetime import datetime, timedelta, timezone
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature
from cryptography import x509
from cryptography.x509.oid import NameOID

# Frontend static content directory
PUBLIC_DIR = "public"
ASS_SCRIPTS_DIR = "ass_scripts"
os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(ASS_SCRIPTS_DIR, exist_ok=True)
os.makedirs(os.path.join(PUBLIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(PUBLIC_DIR, "js"), exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
audit_log = []

# Post-Quantum Crypto Simulator
class PQCSimulator:
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return priv_pem, pub_pem

    @staticmethod
    def sign(data: bytes, private_key_pem: bytes) -> bytes:
        private_key = load_pem_private_key(private_key_pem, password=None)
        return private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())

    @staticmethod
    def verify(signature: bytes, data: bytes, public_key_pem: bytes) -> bool:
        try:
            public_key = load_pem_public_key(public_key_pem)
            public_key.verify(signature, data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
            return True
        except InvalidSignature:
            return False

def sign_audit_event(event: Dict) -> Dict:
    data = json.dumps(event).encode()
    priv_pem, _ = PQCSimulator.generate_keypair()
    signature = PQCSimulator.sign(data, priv_pem)
    event['signature'] = base64.b64encode(signature).decode()
    event['timestamp'] = time.time()
    return event

class QuantumEntropy:
    @staticmethod
    def generate_bytes(length: int) -> bytes:
        return os.urandom(length)

def generate_self_signed_cert(keyfile: str, certfile: str):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Quantum"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "AGI"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ASS Protocol"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
    ).sign(key, hashes.SHA256())
    
    with open(keyfile, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(certfile, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

class SecurityManager:
    def __init__(self, secret_key: bytes = None):
        self.secret_key = secret_key or QuantumEntropy.generate_bytes(32)
        self.rate_limits = {}
        self.sessions = {}
        self.api_keys = {}
        self.certificates = {}
        self.nonce_cache = set()
        self.coherence_threshold = 0.8
        self.host_priv, self.host_pub = PQCSimulator.generate_keypair()
        self.cert_rotator_task = None

    async def start_background_tasks(self):
        async def rotator():
            while True:
                await asyncio.sleep(600)
                self.host_priv, self.host_pub = PQCSimulator.generate_keypair()
                logger.info("Host cert rotated")
        self.cert_rotator_task = asyncio.create_task(rotator())

    def rate_limit_check(self, ip: str, endpoint: str, limit: int = 100, window: int = 60) -> bool:
        now = time.time()
        key = f"{ip}:{endpoint}"
        if key not in self.rate_limits:
            self.rate_limits[key] = [0, now + window]
            return True
        count, reset = self.rate_limits[key]
        if now > reset:
            count = 0
            reset = now + window
        if count >= limit:
            self._audit_event({'type': 'rate_limit_exceeded', 'ip': ip, 'endpoint': endpoint})
            return False
        self.rate_limits[key] = [count + 1, reset]
        return True

    def generate_session(self, user: str, capabilities: list, expiry_hours: int = 24) -> str:
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        payload = f"{user}:{expiry.isoformat()}:{','.join(capabilities)}:1.0".encode()
        signature = hmac.new(self.secret_key, payload, hashlib.sha256).digest()
        session_id = base64.urlsafe_b64encode(payload + b':' + signature).decode().rstrip('=')
        self.sessions[session_id] = (user, expiry, capabilities, 1.0)
        return session_id

    def validate_session(self, session_id: str, required_capability: str = None) -> Tuple[Optional[str], float]:
        if session_id not in self.sessions:
            return None, 0.0
        user, expiry, caps, coherence = self.sessions[session_id]
        if datetime.now() > expiry:
            del self.sessions[session_id]
            return None, 0.0
        if required_capability and required_capability not in caps:
            return None, coherence
        new_coherence = max(0.0, coherence - 0.01)
        if new_coherence < self.coherence_threshold:
            self._audit_event({'type': 'coherence_low', 'session': session_id, 'user': user})
            del self.sessions[session_id]
            return None, 0.0
        self.sessions[session_id] = (user, expiry, caps, new_coherence)
        return user, new_coherence

    def security_headers(self) -> Dict[str, str]:
        return {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'",
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'X-ASS-Version': '1.0',
        }

    def _audit_event(self, event: Dict):
        signed_event = sign_audit_event(event)
        audit_log.append(signed_event)
        logger.info(f"Audit: {event['type']}")

class ASSParser:
    """ASS Template Parser with Quantum Context"""
    
    @staticmethod
    def parse(content: str, context: Dict[str, Any]) -> str:
        # Process loops first (they might contain conditionals and placeholders)
        content = ASSParser._process_loops(content, context)
        
        # Process conditionals
        content = ASSParser._process_conditionals(content, context)
        
        # Replace simple placeholders (after loops to handle nested replacements)
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (list, dict)):
                # Skip complex objects that should be handled by loops
                continue
            content = content.replace(placeholder, str(value))
        
        # Process quantum functions
        content = ASSParser._process_quantum_functions(content, context)
        
        return content
    
    @staticmethod
    def _process_conditionals(content: str, context: Dict) -> str:
        # {{#if CONDITION}}...{{/if}}
        pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_conditional(match):
            condition, block = match.groups()
            condition = condition.strip()
            
            # Handle different condition types
            if '==' in condition:
                var, value = condition.split('==', 1)
                var = var.strip()
                value = value.strip().strip('"\'')
                result = str(context.get(var, '')) == value
            elif '!=' in condition:
                var, value = condition.split('!=', 1)
                var = var.strip()
                value = value.strip().strip('"\'')
                result = str(context.get(var, '')) != value
            elif '>' in condition:
                var, value = condition.split('>', 1)
                var = var.strip()
                value = float(value.strip())
                result = float(context.get(var, 0)) > value
            elif '<' in condition:
                var, value = condition.split('<', 1)
                var = var.strip()
                value = float(value.strip())
                result = float(context.get(var, 0)) < value
            elif '>=' in condition:
                var, value = condition.split('>=', 1)
                var = var.strip()
                value = float(value.strip())
                result = float(context.get(var, 0)) >= value
            elif '<=' in condition:
                var, value = condition.split('<=', 1)
                var = var.strip()
                value = float(value.strip())
                result = float(context.get(var, 0)) <= value
            else:
                # Simple truthy check
                value = context.get(condition)
                if isinstance(value, bool):
                    result = value
                elif isinstance(value, (int, float)):
                    result = value != 0
                elif isinstance(value, (list, dict, str)):
                    result = bool(value)
                else:
                    result = False
            
            return block if result else ''
        
        return re.sub(pattern, replace_conditional, content, flags=re.DOTALL)
    
    @staticmethod
    def _process_loops(content: str, context: Dict) -> str:
        # {{#each ARRAY}}...{{/each}}
        pattern = r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}'
        
        def replace_loop(match):
            array_name, block = match.groups()
            array = context.get(array_name, [])
            
            if not isinstance(array, list):
                logger.warning(f"Expected list for {array_name}, got {type(array)}")
                return ''
            
            result = []
            for item in array:
                item_block = block
                # Replace placeholders within the loop block
                if isinstance(item, dict):
                    for key, value in item.items():
                        # Replace {{this.key}} and {{key}} patterns
                        placeholder_this = f"{{{{this.{key}}}}}"
                        placeholder_direct = f"{{{{{key}}}}}"
                        item_block = item_block.replace(placeholder_this, str(value))
                        item_block = item_block.replace(placeholder_direct, str(value))
                else:
                    # Handle simple array items
                    item_block = item_block.replace('{{this}}', str(item))
                result.append(item_block)
            
            return ''.join(result)
        
        return re.sub(pattern, replace_loop, content, flags=re.DOTALL)
    
    @staticmethod
    def _process_quantum_functions(content: str, context: Dict) -> str:
        # {{QUANTUM_COMPUTE: function, params: {...}}}
        pattern = r'\{\{QUANTUM_COMPUTE:\s*(\w+),\s*params:\s*\{([^}]+)\}\}\}'
        
        def replace_function(match):
            func_name, params_str = match.groups()
            # Parse params
            params = {}
            for param in params_str.split(','):
                if ':' in param:
                    k, v = param.split(':', 1)
                    params[k.strip()] = v.strip().strip('"\'')
            
            # Execute quantum function (stub)
            return f'[QUANTUM_RESULT: {func_name}({params})]'
        
        return re.sub(pattern, replace_function, content)

class ASSContentGenerator:
    def __init__(self, agi_core):
        self.agi_core = agi_core
        self.script_cache = {}

    async def generate_ass_response(self, path: str, user: str = None, session_coherence: float = 1.0) -> Tuple[str, str, int]:
        """Returns (content, content_type, status_code)"""
        
        # Serve static assets first (CSS, JS, images)
        if path.startswith('/public/') or path.endswith(('.css', '.js', '.png', '.jpg', '.svg', '.html')):
            return await self._serve_static_file(path)
        
        # Serve ASS templates from ass_scripts directory
        if path in ['/', '/index', '/dashboard']:
            return await self._serve_ass_file('/index.ass', user, session_coherence)
        elif path == '/admin':
            return await self._serve_ass_file('/admin.ass', user, session_coherence)
        elif path == '/training':
            return await self._serve_ass_file('/training.ass', user, session_coherence)
        elif path == '/entities':
            return await self._serve_ass_file('/entity.ass', user, session_coherence)
        elif path == '/userdash':
            return await self._serve_ass_file('/userdash.ass', user, session_coherence)
        elif path == '/auth':
            return await self._serve_ass_file('/auth.ass', user, session_coherence)
        
        # API endpoints
        if path == '/api/entities':
            return await self._serve_entity_data()
        elif path == '/api/metrics':
            return await self._serve_metrics_data()
        
        # Dynamic ASS generation for unknown paths
        return await self._generate_dynamic_ass(path, user, session_coherence)

    async def _serve_ass_file(self, ass_file: str, user: str, coherence: float) -> Tuple[str, str, int]:
        """Serve ASS template files from ass_scripts directory"""
        file_path = os.path.join(ASS_SCRIPTS_DIR, ass_file.lstrip('/'))
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Build quantum context
                context = await self._build_quantum_context(user, coherence)
                
                # Parse ASS template
                try:
                    processed = ASSParser.parse(content, context)
                except Exception as parse_error:
                    logger.error(f"ASS parsing error: {parse_error}")
                    processed = content  # Return unparsed if parsing fails
                
                return processed, 'text/html; charset=utf-8', 200
            else:
                logger.error(f"ASS file not found: {file_path}")
                return self._error_template(f"ASS template not found: {ass_file}"), 'text/html; charset=utf-8', 404
        except Exception as e:
            logger.error(f"Error serving ASS file {ass_file}: {e}", exc_info=True)
            return self._error_template(f"Error: {e}"), 'text/html; charset=utf-8', 500

    async def _serve_static_file(self, path: str) -> Tuple[str, str, int]:
        """Serve static files from public directory"""
        # Map URL paths to file paths in public directory
        if path.startswith('/public/'):
            file_path = path[1:]  # Remove leading slash -> public/css/style.css
        elif path.startswith('/css/') or path.startswith('/js/'):
            file_path = 'public' + path  # /css/style.css -> public/css/style.css
        else:
            file_path = 'public' + path  # /styles.css -> public/styles.css
        
        # Determine content type
        content_type = 'text/plain'
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        elif path.endswith('.html'):
            content_type = 'text/html'
        
        try:
            if os.path.exists(file_path):
                mode = 'rb' if content_type.startswith('image/') else 'r'
                encoding = None if content_type.startswith('image/') else 'utf-8'
                
                with open(file_path, mode, encoding=encoding) as f:
                    content = f.read()
                
                return content, content_type, 200
            else:
                logger.warning(f"Static file not found: {file_path}")
                if content_type == 'text/css':
                    return "/* File not found */", content_type, 404
                elif content_type == 'application/javascript':
                    return "// File not found", content_type, 404
                else:
                    return f"File not found: {path}", content_type, 404
                    
        except Exception as e:
            logger.error(f"Error serving static file {path}: {e}")
            if content_type == 'text/css':
                return "/* Error serving file */", content_type, 500
            elif content_type == 'application/javascript':
                return "// Error serving file", content_type, 500
            else:
                return f"Error: {e}", content_type, 500

    async def _serve_entity_data(self) -> Tuple[str, str, int]:
        """Serve entity data as JSON for API calls"""
        try:
            entities = []
            for entity in self.agi_core.entity_swarm:
                entities.append({
                    'entity_id': entity.entity_id,
                    'name': entity.name,
                    'archetype': entity.archetype,
                    'coherence': round(entity.coherence, 3),
                    'training_level': entity.training_level
                })
            return json.dumps(entities), 'application/json', 200
        except Exception as e:
            logger.error(f"Error serving entity data: {e}")
            return json.dumps({'error': str(e)}), 'application/json', 500

    async def _serve_metrics_data(self) -> Tuple[str, str, int]:
        """Serve metrics data as JSON for API calls"""
        try:
            metrics = await self.agi_core.get_system_metrics()
            return json.dumps(metrics), 'application/json', 200
        except Exception as e:
            logger.error(f"Error serving metrics data: {e}")
            return json.dumps({'error': str(e)}), 'application/json', 500

    async def _build_quantum_context(self, user: str, coherence: float) -> Dict[str, Any]:
        """Build context for ASS template rendering"""
        try:
            # Get system metrics for context
            metrics = await self.agi_core.get_system_metrics()
            
            context = {
                'SYSTEM_COHERENCE': round(coherence, 3),
                'QUANTUM_ENTROPY': round(self.agi_core.bumpy.lambda_entropic_sample(1)[0] if hasattr(self.agi_core, 'bumpy') and self.agi_core.bumpy else 0.5, 3),
                'ACTIVE_ENTITIES': len(self.agi_core.entity_swarm),
                'TIMESTAMP': int(time.time()),
                'USER': user or 'guest',
                'SESSION_ID': 'quantum_session',
                'ASS_VERSION': '1.0',
                'COHERENCE_STATUS': 'Stable' if coherence > 0.9 else 'Degraded' if coherence > 0.7 else 'Critical',
            }
            
            # Add metrics data
            context.update({
                'SYSTEM_UPTIME': metrics.get('system_uptime', '5m 23s'),
                'TOTAL_MEMORY': metrics.get('total_memory', 128),
                'ACTIVE_SESSIONS': metrics.get('active_sessions', 1),
                'TOTAL_ENTANGLEMENTS': metrics.get('total_entanglements', 12),
            })
            
            # Entity list - ensure proper data structure
            entities = []
            for entity in self.agi_core.entity_swarm:
                entities.append({
                    'id': entity.entity_id,
                    'name': entity.name,
                    'archetype': entity.archetype,
                    'coherence': round(entity.coherence, 3),
                    'training_level': entity.training_level
                })
            context['ENTITIES'] = entities
            
            # User entities - ensure proper data structure
            if user and user in self.agi_core.user_manager:
                user_entities = self.agi_core.user_manager[user].get('entities', [])
                context['USER_ENTITIES'] = user_entities
            else:
                context['USER_ENTITIES'] = []
            
            logger.debug(f"Built context for user {user}: {len(entities)} entities, {len(context['USER_ENTITIES'])} user entities")
            return context
            
        except Exception as e:
            logger.error(f"Error building quantum context: {e}")
            # Return basic context even if there's an error
            return {
                'SYSTEM_COHERENCE': round(coherence, 3),
                'ACTIVE_ENTITIES': 0,
                'TIMESTAMP': int(time.time()),
                'USER': user or 'guest',
                'SESSION_ID': 'quantum_session',
                'ASS_VERSION': '1.0',
                'COHERENCE_STATUS': 'Stable',
                'ENTITIES': [],
                'USER_ENTITIES': [],
            }

    async def _generate_dynamic_ass(self, path: str, user: str, coherence: float) -> Tuple[str, str, int]:
        context = await self._build_quantum_context(user, coherence)
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ASS Dynamic - {path}</title>
    <link rel="stylesheet" href="/public/css/style.css">
</head>
<body>
    <div class="quantum-container">
        <header class="quantum-header">
            <h1>Alice Side Script Dynamic Content</h1>
        </header>
        <div class="card">
            <p>Path: {path}</p>
            <p>Coherence: {context['SYSTEM_COHERENCE']}</p>
            <p>Entities: {context['ACTIVE_ENTITIES']}</p>
            <p>User: {context['USER']}</p>
        </div>
    </div>
</body>
</html>"""
        return content, 'text/html; charset=utf-8', 200

    def _error_template(self, message: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>ASS Error</title>
    <link rel="stylesheet" href="/public/css/style.css">
</head>
<body>
    <div class="quantum-container">
        <div class="card" style="text-align: center; background: #ff4444; color: white;">
            <h1>🔴 Quantum Decoherence Detected</h1>
            <p>{message}</p>
            <button onclick="location.reload()" class="btn-primary">Restore Coherence</button>
        </div>
    </div>
</body>
</html>"""

class ASSHTTPHandler:
    def __init__(self, agi_core, security_manager: SecurityManager, content_gen: ASSContentGenerator):
        self.agi_core = agi_core
        self.sec = security_manager
        self.content_gen = content_gen
        self.routes = {
            'GET': {
                '/': self.handle_dashboard,
                '/dashboard': self.handle_dashboard,
                '/admin': self.handle_admin,
                '/training': self.handle_training,
                '/entities': self.handle_entities,
                '/userdash': self.handle_userdash,
                '/auth': self.handle_auth,
                '/metrics': self.handle_metrics,
                '/api/entities': self.handle_api_entities,
                '/api/metrics': self.handle_api_metrics,
            },
            'POST': {
                '/login': self.handle_login,
                '/logout': self.handle_logout,
                '/register': self.handle_register,
                '/chat': self.handle_chat,
                '/collective_chat': self.handle_collective_chat,
                '/train': self.handle_train,
                '/assign_entity': self.handle_assign_entity,
            }
        }

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info('peername')
        ip = peer[0] if peer else '0.0.0.0'
        
        if not self.sec.rate_limit_check(ip, '/'):
            self._send_error(writer, 429, "Rate limited")
            return

        try:
            data = await reader.read(16384)
            if not data:
                return
            request = self._parse_request(data.decode('utf-8', errors='ignore'))
            if not request:
                self._send_error(writer, 400, "Bad Request")
                return

            method, path, headers, body = request['method'], request['path'], request['headers'], request['body']
            
            # Authentication
            user, coherence = None, 1.0
            auth_header = headers.get('authorization', '')
            
            if auth_header.startswith('Bearer '):
                session_id = auth_header.replace('Bearer ', '')
                user, coherence = self.sec.validate_session(session_id)
            
            # Public paths - no auth required
            public_paths = ['/', '/dashboard', '/auth', '/public/', '/css/', '/js/', '/login', '/register']
            require_auth = method == 'POST' and not any(path.startswith(p) for p in public_paths)
            
            if require_auth and not user:
                self._send_error(writer, 401, "Unauthorized")
                return
            
            # Admin check
            if path.startswith('/admin') and user:
                _, _, caps, _ = self.sec.sessions.get(auth_header.replace('Bearer ', ''), (None, None, [], 0))
                if 'admin' not in caps:
                    self._send_error(writer, 403, "Forbidden")
                    return

            # Route the request
            response = await self._route_request(method, path, headers, body, user, coherence)
            self._send_response(writer, response)

        except Exception as e:
            logger.error(f"Handler error: {e}", exc_info=True)
            self._send_error(writer, 500, "Internal Server Error")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def _route_request(self, method: str, path: str, headers: Dict, body: bytes, user: str, coherence: float) -> Dict:
        method_routes = self.routes.get(method, {})
        
        # Exact match
        if path in method_routes:
            return await method_routes[path](path, headers, body, user, coherence)
        
        # Pattern match
        for route_pattern, handler in method_routes.items():
            if '{' in route_pattern:
                base = route_pattern.split('{')[0]
                if path.startswith(base):
                    return await handler(path, headers, body, user, coherence)
        
        # Default ASS handler for static files and ASS templates
        content, content_type, status = await self.content_gen.generate_ass_response(path, user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_dashboard(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_admin(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/admin', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_training(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/training', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_entities(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/entities', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_userdash(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/userdash', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_auth(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen.generate_ass_response('/auth', user, coherence)
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': {**self.sec.security_headers(), 'X-Coherence': str(coherence)}
        }

    async def handle_metrics(self, path, headers, body, user, coherence):
        metrics = await self.agi_core.get_system_metrics()
        return {
            'content': json.dumps(metrics), 
            'content_type': 'application/json', 
            'status': 200,
            'headers': self.sec.security_headers()
        }

    async def handle_api_entities(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen._serve_entity_data()
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': self.sec.security_headers()
        }

    async def handle_api_metrics(self, path, headers, body, user, coherence):
        content, content_type, status = await self.content_gen._serve_metrics_data()
        return {
            'content': content,
            'content_type': content_type,
            'status': status,
            'headers': self.sec.security_headers()
        }

    async def handle_login(self, path, headers, body, user, coherence):
        try:
            data = json.loads(body.decode())
            username = data.get('username', '')
            password = data.get('password', '')
            
            result = await self.agi_core.user_login(username, password)
            
            if result['success']:
                # Determine capabilities
                caps = ['read', 'write', 'chat', 'train']
                if username == 'admin':
                    caps.append('admin')
                
                session_id = self.sec.generate_session(username, caps, expiry_hours=24)
                result['session_id'] = session_id
                result['capabilities'] = caps
                
                # Log
                if hasattr(self.agi_core, 'laser') and self.agi_core.laser:
                    self.agi_core.laser.log_event(1.0, f"USER_LOGIN {username}")
            
            return {
                'content': json.dumps(result), 
                'content_type': 'application/json', 
                'status': 200 if result['success'] else 401,
                'headers': self.sec.security_headers()
            }
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                'content': json.dumps({'success': False, 'message': 'Login failed'}), 
                'content_type': 'application/json', 
                'status': 500,
                'headers': self.sec.security_headers()
            }

    async def handle_logout(self, path, headers, body, user, coherence):
        auth_header = headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            session_id = auth_header.replace('Bearer ', '')
            if session_id in self.sec.sessions:
                del self.sec.sessions[session_id]
        
        return {
            'content': json.dumps({'success': True}), 
            'content_type': 'application/json', 
            'status': 200,
            'headers': self.sec.security_headers()
        }

    async def handle_register(self, path, headers, body, user, coherence):
        data = json.loads(body.decode())
        username = data['username']
        password = data['password']
        
        if username in self.agi_core.user_manager:
            return {
                'content': json.dumps({'success': False, 'message': 'User exists'}), 
                'content_type': 'application/json', 
                'status': 400,
                'headers': self.sec.security_headers()
            }
        
        self.agi_core.user_manager[username] = {
            'hashed_pass': hashlib.sha256(password.encode()).hexdigest(),
            'entities': ['quantum_01'],
            'training_sessions': 0
        }
        
        return {
            'content': json.dumps({'success': True}), 
            'content_type': 'application/json', 
            'status': 200,
            'headers': self.sec.security_headers()
        }

    async def handle_chat(self, path, headers, body, user, coherence):
        data = json.loads(body.decode())
        response = await self.agi_core.generate_response(data['input'], entity_id=data.get('entity_id'))
        
        entity_name = "Collective"
        if data.get('entity_id'):
            entity = self.agi_core._get_isolated_entity(data['entity_id'])
            if entity:
                entity_name = entity.name
        
        return {
            'content': json.dumps({'response': response, 'entity_name': entity_name, 'coherence': coherence}), 
            'content_type': 'application/json', 
            'status': 200,
            'headers': self.sec.security_headers()
        }

    async def handle_collective_chat(self, path, headers, body, user, coherence):
        data = json.loads(body.decode())
        entity_ids = data.get('entity_ids', [])
        
        individual = []
        for eid in entity_ids:
            resp = await self.agi_core.generate_response(data['input'], entity_id=eid)
            entity = self.agi_core._get_isolated_entity(eid)
            individual.append({'entity_id': eid, 'entity_name': entity.name if entity else eid, 'response': resp})
        
        synthesis = await self.agi_core.generate_response(f"Synthesize: {[r['response'] for r in individual]}")
        
        return {
            'content': json.dumps({'individual_responses': individual, 'collective_synthesis': synthesis}), 
            'content_type': 'application/json', 
            'status': 200,
            'headers': self.sec.security_headers()
        }

    async def handle_train(self, path, headers, body, user, coherence):
        data = json.loads(body.decode())
        result = await self.agi_core.train_entity(data['entity_id'], data['training_data'])
        return {
            'content': json.dumps(result), 
            'content_type': 'application/json', 
            'status': 200 if result.get('success') else 400,
            'headers': self.sec.security_headers()
        }

    async def handle_assign_entity(self, path, headers, body, user, coherence):
        if not user:
            return {
                'content': json.dumps({'success': False}), 
                'content_type': 'application/json', 
                'status': 401,
                'headers': self.sec.security_headers()
            }
        
        data = json.loads(body.decode())
        entity_id = data['entity_id']
        
        if user in self.agi_core.user_manager:
            user_entities = self.agi_core.user_manager[user].get('entities', [])
            if entity_id not in user_entities and len(user_entities) < 3:
                user_entities.append(entity_id)
                self.agi_core.user_manager[user]['entities'] = user_entities
                return {
                    'content': json.dumps({'success': True}), 
                    'content_type': 'application/json', 
                    'status': 200,
                    'headers': self.sec.security_headers()
                }
        
        return {
            'content': json.dumps({'success': False}), 
            'content_type': 'application/json', 
            'status': 400,
            'headers': self.sec.security_headers()
        }

    def _parse_request(self, raw: str) -> Optional[Dict]:
        lines = raw.split('\r\n')
        if len(lines) < 1 or not re.match(r'^[A-Z]+ \S+ HTTP/\d\.\d$', lines[0]):
            return None
        parts = lines[0].split()
        if len(parts) < 3:
            return None
        method, path = parts[0], parts[1]
        headers = {}
        i = 1
        while i < len(lines) and lines[i]:
            if ':' in lines[i]:
                k, v = lines[i].split(':', 1)
                headers[k.strip().lower()] = v.strip()
            i += 1
        body = '\r\n'.join(lines[i:]).encode() if i < len(lines) else b''
        return {'method': method, 'path': path, 'headers': headers, 'body': body}

    def _send_response(self, writer, response: Dict):
        status = response.get('status', 200)
        content_type = response.get('content_type', 'text/plain')
        content = response['content']
        extra_headers = response.get('headers', {})

        status_text = {
            200: "OK", 400: "Bad Request", 401: "Unauthorized", 
            403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 
            429: "Too Many Requests", 500: "Internal Server Error"
        }.get(status, "Unknown")
        
        resp = f"HTTP/1.1 {status} {status_text}\r\n"
        resp += f"Content-Type: {content_type}\r\n"
        
        # Handle binary content (images)
        if isinstance(content, bytes):
            resp += f"Content-Length: {len(content)}\r\n"
        else:
            resp += f"Content-Length: {len(content.encode('utf-8'))}\r\n"
            
        for k, v in extra_headers.items():
            resp += f"{k}: {v}\r\n"
        resp += "\r\n"
        
        if isinstance(content, bytes):
            writer.write(resp.encode() + content)
        else:
            writer.write(resp.encode() + content.encode('utf-8'))

    def _send_error(self, writer, status: int, message: str):
        self._send_response(writer, {
            'content': message, 
            'status': status, 
            'content_type': 'text/plain',
            'headers': {}
        })

class ASSHTTPServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8443, agi_core=None, certfile: str = 'server.crt', keyfile: str = 'server.key'):
        self.host = host
        self.port = port
        self.agi_core = agi_core
        self.sec = SecurityManager()
        self.content_gen = ASSContentGenerator(agi_core)
        self.handler = ASSHTTPHandler(agi_core, self.sec, self.content_gen)
        
        if not (os.path.exists(certfile) and os.path.exists(keyfile)):
            logger.info("Generating self-signed certs...")
            generate_self_signed_cert(keyfile, certfile)
        
        self.tls_context = self._create_tls_context(certfile, keyfile)

    def _create_tls_context(self, certfile: str, keyfile: str) -> ssl.SSLContext:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile, keyfile)
        return context

    async def start(self):
        await self.sec.start_background_tasks()
        server = await asyncio.start_server(self.handler.handle_request, self.host, self.port, ssl=self.tls_context)
        addr = server.sockets[0].getsockname()
        logger.info(f"🚀 ASS_HTTPd v0.8 listening on https://{self.host}:{addr[1]}")
        logger.info(f"🌌 Quantum AGI Ready | Alice Side Script Protocol Active")
        self.sec._audit_event({'type': 'server_start'})
        async with server:
            await server.serve_forever()

def run_server(host='0.0.0.0', port=8443, agi_core=None, certfile='server.crt', keyfile='server.key'):
    server = ASSHTTPServer(host, port, agi_core, certfile, keyfile)
    asyncio.run(server.start())
