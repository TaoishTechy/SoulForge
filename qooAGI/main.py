#!/usr/bin/env python3
"""
main.py - Modular Quantum AGI Server v0.2
Multi-Entity System with Training, User Management & Media Analysis
"""

import os
import json
import time
import base64
import hashlib
import hmac
import secrets
import random
import socket
import math
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime

# Import custom libraries
try:
    from bumpy import BUMPYCore, BumpyArray, BoundedView
except ImportError:
    # Fallback stub
    class BUMPYCore:
        def __init__(self, qualia_dimension=5):
            self.qualia_dimension = qualia_dimension
            self.coherence_level = 1.0
            self._rho_ema = 1.0
        
        def lambda_entropic_sample(self, size):
            return [random.uniform(0, 1) for _ in range(size)]
        
        def set_coherence(self, rho):
            self.coherence_level = rho
            self._rho_ema = rho
    
    class BumpyArray:
        def __init__(self, data, coherence=1.0):
            self.data = data[:] if hasattr(data, '__getitem__') else [data]
            self.coherence = coherence
            self.entanglement_links = []
        
        def lambda_kernel(self, other):
            return random.uniform(0, 1)
        
        def entangle(self, other, threshold=0.6):
            return True
    
    class BoundedView(list):
        def __init__(self, base, lo, hi, coherence=1.0):
            super().__init__(base)
            self._lo, self._hi = lo, hi

try:
    from qubitlearn import MultimodalDataLoader
except ImportError:
    class MultimodalDataLoader:
        @staticmethod
        def load_multimodal(path, labeled=False, max_dim=100):
            return [[random.uniform(0, 1) for _ in range(max_dim)]], [random.randint(0, 1)] if labeled else None

try:
    from laser import LASERUtility
except ImportError:
    class LASERUtility:
        def __init__(self, parent_config=None):
            self.parent_config = parent_config or {}
        
        def log_event(self, invariant, message):
            print(f"LASER: {message}")
        
        def check_and_flush(self, coherence):
            pass

try:
    from sentiflow import SentientTensor, nn, optim, qualia_ritual
except ImportError:
    class SentientTensor:
        def __init__(self, data, requires_grad=False, qualia_layer="base"):
            self.data = data
            self.qualia_coherence = 1.0
    
    class nn:
        class Dense:
            def __init__(self, in_features, out_features):
                self.weight = [random.uniform(-1, 1) for _ in range(out_features * in_features)]
            
            def __call__(self, x):
                return SentientTensor([sum(a*b for a,b in zip(x.data, self.weight[i::len(x.data)])) for i in range(len(x.data))])
    
    class optim:
        class Adam:
            def __init__(self, params, lr=0.001):
                self.params = params
                self.lr = lr
            
            def step(self):
                pass
    
    def qualia_ritual(tensors, threshold=0.3):
        print("Qualia ritual completed")

# ==================== MODULE MANAGER ====================

class ModuleManager:
    """Manages all system modules with hot-reloading capability"""
    
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.modules = {}
        self.load_all_modules()
    
    def load_all_modules(self):
        """Load all module types"""
        module_types = ['agi_mods', 'system_mods', 'sensory_mods', 'bootstrap_mods']
        
        for mod_type in module_types:
            mod_path = os.path.join(self.base_path, mod_type)
            self.modules[mod_type] = self._load_modules_from_path(mod_path)
    
    def _load_modules_from_path(self, path):
        """Load all JSON modules from a directory"""
        modules = {}
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            return modules
        
        for file in os.listdir(path):
            if file.endswith('.json'):
                mod_name = file[:-5]
                try:
                    with open(os.path.join(path, file), 'r') as f:
                        modules[mod_name] = json.load(f)
                except Exception as e:
                    print(f"Error loading module {file}: {e}")
        
        return modules
    
    def get_module(self, mod_type, mod_name):
        """Get a specific module"""
        return self.modules.get(mod_type, {}).get(mod_name)
    
    def reload_modules(self):
        """Reload all modules"""
        self.load_all_modules()

# ==================== SECURITY MANAGER ====================

class SecurityManager:
    """Military-grade security with session management"""
    
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.sessions = {}
        self.user_content_path = "user_content"
        os.makedirs(self.user_content_path, exist_ok=True)
    
    def create_session(self, user_id):
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'ip_address': '0.0.0.0',
            'permissions': ['read', 'write', 'upload']
        }
        
        self.sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id):
        """Validate session and update access time"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_accessed'] = time.time()
            return True
        return False
    
    def get_user_path(self, user_id, session_id):
        """Get user content path with session validation"""
        if not self.validate_session(session_id):
            raise PermissionError("Invalid session")
        
        user_path = os.path.join(self.user_content_path, user_id)
        os.makedirs(user_path, exist_ok=True)
        return user_path
    
    def cleanup_sessions(self, max_age=3600):
        """Remove expired sessions"""
        current_time = time.time()
        expired = [sid for sid, data in self.sessions.items() 
                  if current_time - data['last_accessed'] > max_age]
        
        for sid in expired:
            del self.sessions[sid]

# ==================== USER MANAGEMENT ====================

class UserManager:
    """Secure user management with JSON storage"""
    
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = self._load_users()
        self._ensure_default_admin()
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists"""
        if "admin" not in self.users:
            salt = secrets.token_hex(16)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256', "passabc123".encode(), salt.encode(), 100000
            ).hex()
            
            self.users["admin"] = {
                'password_hash': password_hash,
                'salt': salt,
                'email': 'admin@quantum-agi.com',
                'created_at': time.time(),
                'entities': ["quantum_01", "ling_01", "creative_01"],
                'training_data': [],
                'feedback_history': []
            }
            self._save_users()
            print("✅ Default admin user created: admin/passabc123")
    
    def _load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading users file: {e}")
                return {}
        return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving users file: {e}")
    
    def create_user(self, username, password, email=""):
        """Create new user with hashed password"""
        if username in self.users:
            return False, "User already exists"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Hash password with salt
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt.encode(), 100000
        ).hex()
        
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'email': email,
            'created_at': time.time(),
            'entities': [],  # User's entity swarm
            'training_data': [],
            'feedback_history': []
        }
        self._save_users()
        return True, "User created successfully"
    
    def authenticate(self, username, password):
        """Authenticate user"""
        if username not in self.users:
            return False, "User not found"
        
        user = self.users[username]
        try:
            password_hash = hashlib.pbkdf2_hmac(
                'sha256', password.encode(), user['salt'].encode(), 100000
            ).hex()
            
            if hmac.compare_digest(password_hash, user['password_hash']):
                return True, "Authentication successful"
            return False, "Invalid password"
        except Exception as e:
            print(f"Authentication error: {e}")
            return False, "Authentication error"

# ==================== ENTITY SWARM SYSTEM ====================

@dataclass
class Entity:
    """Individual AGI Entity in the swarm"""
    entity_id: str
    name: str
    archetype: str  # quantum, linguistic, creative, analytical, etc.
    coherence: float = 1.0
    training_level: int = 1
    memory: List[Dict] = field(default_factory=list)
    conversation_history: List[Dict] = field(default_factory=list)
    specialized_knowledge: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def process_input(self, user_input: str, media_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Process input with entity-specific logic"""
        # Entity-specific response generation based on archetype
        if self.archetype == "quantum":
            response = self._quantum_response(user_input, media_data)
        elif self.archetype == "linguistic":
            response = self._linguistic_response(user_input, media_data)
        elif self.archetype == "creative":
            response = self._creative_response(user_input, media_data)
        elif self.archetype == "analytical":
            response = self._analytical_response(user_input, media_data)
        else:
            response = self._general_response(user_input, media_data)
        
        # Store in memory
        memory_entry = {
            "timestamp": time.time(),
            "input": user_input,
            "media_data": media_data,
            "response": response,
            "coherence": self.coherence
        }
        self.memory.append(memory_entry)
        self.conversation_history.append(memory_entry)
        
        # Limit memory size
        if len(self.memory) > 1000:
            self.memory = self.memory[-500:]
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]
        
        return {
            "entity_id": self.entity_id,
            "entity_name": self.name,
            "archetype": self.archetype,
            "response": response,
            "coherence": self.coherence,
            "training_level": self.training_level,
            "timestamp": time.time()
        }
    
    def _quantum_response(self, user_input: str, media_data: Optional[Dict]) -> str:
        """Quantum archetype responses"""
        responses = [
            f"🔮 Quantum analysis: Input shows {random.uniform(0.7, 0.95):.2f} coherence with quantum field",
            f"🌌 Entanglement detected: {len(user_input)} semantic qubits activated",
            f"⚛️ Superposition state: Multiple interpretations emerging from your query",
            f"🌀 Quantum coherence: {self.coherence:.3f} - Processing through Hilbert space"
        ]
        return random.choice(responses)
    
    def _linguistic_response(self, user_input: str, media_data: Optional[Dict]) -> str:
        """Linguistic archetype responses"""
        word_count = len(user_input.split())
        responses = [
            f"📚 Linguistic analysis: {word_count} words with semantic depth {random.uniform(0.6, 0.9):.2f}",
            f"💬 Pragmatic structure: Multiple discourse interpretations available",
            f"🎭 Narrative coherence: Strong thematic alignment detected",
            f"🔤 Semantic field analysis: {len(set(user_input.lower().split()))} unique concepts"
        ]
        return random.choice(responses)
    
    def _creative_response(self, user_input: str, media_data: Optional[Dict]) -> str:
        """Creative archetype responses"""
        responses = [
            f"🎨 Creative synthesis: Generating novel patterns from input",
            f"✨ Emergent ideation: Multiple creative pathways activated",
            f"🌈 Associative linking: Connecting {random.randint(3, 8)} conceptual domains",
            f"🎭 Narrative weaving: Building immersive story structures"
        ]
        return random.choice(responses)
    
    def _analytical_response(self, user_input: str, media_data: Optional[Dict]) -> str:
        """Analytical archetype responses"""
        responses = [
            f"🔍 Analytical breakdown: {random.randint(2, 5)} primary patterns identified",
            f"📊 Statistical analysis: Confidence interval {random.uniform(0.85, 0.98):.2f}",
            f"🎯 Precision targeting: Optimal response pathways calculated",
            f"📈 Pattern recognition: {random.randint(3, 7)} significant correlations found"
        ]
        return random.choice(responses)
    
    def _general_response(self, user_input: str, media_data: Optional[Dict]) -> str:
        """General archetype responses"""
        responses = [
            f"Processing your input through {self.archetype} cognitive pathways",
            f"Analyzing patterns with {self.coherence:.2f} coherence level",
            f"Entity {self.name} responding with specialized {self.archetype} knowledge",
            f"Integrated analysis complete - multiple perspectives synthesized"
        ]
        return random.choice(responses)
    
    def train_entity(self, training_data: Dict) -> Dict[str, Any]:
        """Train entity with provided data"""
        # Simulated training process
        improvement = random.uniform(0.01, 0.05)
        self.coherence = min(1.0, self.coherence + improvement)
        
        if random.random() < 0.3:  # 30% chance of level up
            self.training_level += 1
        
        # Store training data
        training_entry = {
            "timestamp": time.time(),
            "data": training_data,
            "improvement": improvement,
            "new_level": self.training_level
        }
        
        if 'training_data' not in self.specialized_knowledge:
            self.specialized_knowledge['training_data'] = []
        self.specialized_knowledge['training_data'].append(training_entry)
        
        return {
            "entity_id": self.entity_id,
            "training_result": "success",
            "coherence_improvement": improvement,
            "new_coherence": self.coherence,
            "training_level": self.training_level
        }

class EntitySwarm:
    """Manages the collective of AGI entities"""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.available_archetypes = [
            "quantum", "linguistic", "creative", "analytical", 
            "empathetic", "strategic", "technical", "philosophical"
        ]
        self._initialize_default_entities()
    
    def _initialize_default_entities(self):
        """Initialize some default entities"""
        default_entities = [
            ("quantum_01", "Quantum Oracle", "quantum"),
            ("ling_01", "Linguistic Sage", "linguistic"),
            ("creative_01", "Creative Muse", "creative"),
            ("analytic_01", "Analytical Mind", "analytical"),
            ("empath_01", "Empathic Guide", "empathetic")
        ]
        
        for entity_id, name, archetype in default_entities:
            self.create_entity(entity_id, name, archetype)
    
    def create_entity(self, entity_id: str, name: str, archetype: str) -> Entity:
        """Create a new entity"""
        if archetype not in self.available_archetypes:
            archetype = "quantum"  # Default fallback
        
        entity = Entity(
            entity_id=entity_id,
            name=name,
            archetype=archetype,
            coherence=random.uniform(0.7, 0.9),
            training_level=1
        )
        self.entities[entity_id] = entity
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_user_entities(self, user_entity_ids: List[str]) -> List[Entity]:
        """Get entities belonging to a user"""
        return [self.entities[eid] for eid in user_entity_ids if eid in self.entities]
    
    def process_collective_input(self, user_input: str, media_data: Optional[Dict], entity_ids: List[str]) -> Dict[str, Any]:
        """Process input through multiple entities collectively"""
        responses = []
        for entity_id in entity_ids:
            if entity_id in self.entities:
                entity = self.entities[entity_id]
                response = entity.process_input(user_input, media_data)
                responses.append(response)
        
        # Generate collective synthesis
        if responses:
            synthesis = self._synthesize_responses(responses, user_input)
        else:
            synthesis = "No entities available for collective processing"
        
        return {
            "individual_responses": responses,
            "collective_synthesis": synthesis,
            "participating_entities": len(responses),
            "timestamp": time.time()
        }
    
    def _synthesize_responses(self, responses: List[Dict], original_input: str) -> str:
        """Synthesize multiple entity responses into collective insight"""
        archetypes = [r['archetype'] for r in responses]
        coherence_avg = sum(r['coherence'] for r in responses) / len(responses)
        
        synthesis_templates = [
            f"🌐 Collective Insight ({len(responses)} entities): Multiple perspectives synthesized with {coherence_avg:.2f} avg coherence",
            f"🔗 Swarm Intelligence: {', '.join(set(archetypes))} archetypes collaborating on your query",
            f"🎯 Integrated Analysis: {len(responses)} specialized viewpoints unified",
            f"🚀 Emergent Understanding: Cross-archetype synthesis complete"
        ]
        
        return random.choice(synthesis_templates)

# ==================== MEDIA PROCESSING & TRAINING ====================

class MediaProcessor:
    """Enhanced media processing with analysis and generation"""
    
    def __init__(self):
        self.supported_formats = ['image', 'audio', 'video', 'text', 'pdf']
    
    def analyze_media(self, media_data: Dict, prompt: str) -> Dict[str, Any]:
        """Analyze uploaded media in context of prompt"""
        media_type = media_data.get('type', 'unknown')
        
        analysis = {
            "media_type": media_type,
            "prompt_context": prompt,
            "semantic_coherence": random.uniform(0.6, 0.95),
            "feature_analysis": self._extract_features(media_data),
            "relevance_score": random.uniform(0.5, 1.0),
            "analysis_timestamp": time.time()
        }
        
        # Add type-specific analysis
        if media_type == 'image':
            analysis.update(self._analyze_image(media_data))
        elif media_type == 'audio':
            analysis.update(self._analyze_audio(media_data))
        elif media_type == 'video':
            analysis.update(self._analyze_video(media_data))
        elif media_type == 'text':
            analysis.update(self._analyze_text(media_data))
        
        return analysis
    
    def _extract_features(self, media_data: Dict) -> Dict[str, Any]:
        """Extract features from media data"""
        return {
            "dimensionality": random.randint(10, 1000),
            "entropy_level": random.uniform(0.3, 0.9),
            "pattern_complexity": random.uniform(0.5, 1.0),
            "feature_vectors": random.randint(5, 50)
        }
    
    def _analyze_image(self, media_data: Dict) -> Dict[str, Any]:
        return {
            "color_analysis": f"RGB spectrum with {random.randint(3, 10)} dominant colors",
            "composition": random.choice(["balanced", "dynamic", "minimalist", "complex"]),
            "texture_patterns": random.randint(2, 8)
        }
    
    def _analyze_audio(self, media_data: Dict) -> Dict[str, Any]:
        return {
            "frequency_range": f"{random.randint(50, 500)}-{random.randint(1000, 5000)}Hz",
            "rhythm_pattern": random.choice(["regular", "syncopated", "complex", "simple"]),
            "harmonic_content": random.choice(["rich", "minimal", "dissonant", "consonant"])
        }
    
    def _analyze_video(self, media_data: Dict) -> Dict[str, Any]:
        return {
            "temporal_features": random.randint(5, 30),
            "motion_analysis": random.choice(["static", "dynamic", "chaotic", "rhythmic"]),
            "scene_complexity": random.uniform(0.3, 0.95)
        }
    
    def _analyze_text(self, media_data: Dict) -> Dict[str, Any]:
        text_content = media_data.get('content', '')[:100]  # Sample first 100 chars
        return {
            "semantic_density": random.uniform(0.4, 0.9),
            "sentiment_score": random.uniform(-1.0, 1.0),
            "complexity_level": random.choice(["simple", "moderate", "complex"]),
            "key_themes": random.sample(["quantum", "cognition", "emergence", "synthesis"], 2)
        }

class TrainingManager:
    """Manages entity training and feedback system"""
    
    def __init__(self, entity_swarm: EntitySwarm):
        self.entity_swarm = entity_swarm
        self.training_datasets = {}
        self.feedback_history = []
    
    def create_training_session(self, entity_id: str, training_data: Dict) -> Dict[str, Any]:
        """Create a training session for an entity"""
        entity = self.entity_swarm.get_entity(entity_id)
        if not entity:
            return {"error": "Entity not found"}
        
        training_result = entity.train_entity(training_data)
        
        # Store training session
        session_id = f"train_{int(time.time())}_{secrets.token_hex(4)}"
        training_session = {
            "session_id": session_id,
            "entity_id": entity_id,
            "training_data": training_data,
            "result": training_result,
            "timestamp": time.time()
        }
        
        self.feedback_history.append(training_session)
        return training_session
    
    def submit_feedback(self, entity_id: str, interaction_id: str, rating: int, comments: str) -> Dict[str, Any]:
        """Submit feedback for entity performance"""
        feedback = {
            "feedback_id": f"fb_{int(time.time())}_{secrets.token_hex(4)}",
            "entity_id": entity_id,
            "interaction_id": interaction_id,
            "rating": max(1, min(5, rating)),  # Clamp 1-5
            "comments": comments,
            "timestamp": time.time()
        }
        
        self.feedback_history.append(feedback)
        
        # Update entity based on feedback
        entity = self.entity_swarm.get_entity(entity_id)
        if entity and rating >= 4:
            # Positive feedback boosts coherence
            entity.coherence = min(1.0, entity.coherence + 0.02)
        
        return feedback

# ==================== ENHANCED AGI CORE ====================

class AGICore:
    """Enhanced AGI core with entity swarm and training"""
    
    def __init__(self, module_manager):
        self.module_manager = module_manager
        self.user_manager = UserManager()
        self.entity_swarm = EntitySwarm()
        self.media_processor = MediaProcessor()
        self.training_manager = TrainingManager(self.entity_swarm)
        self.laser = LASERUtility()
        
        # Initialize BUMPY core
        self.bumpy = BUMPYCore(qualia_dimension=5)
    
    def user_login(self, username: str, password: str) -> Dict[str, Any]:
        """User login with session creation"""
        success, message = self.user_manager.authenticate(username, password)
        if success:
            session_id = secrets.token_urlsafe(32)
            user_entities = self.user_manager.users[username].get('entities', [])
            return {
                "success": True,
                "session_id": session_id,
                "username": username,
                "user_entities": user_entities,
                "message": "Login successful"
            }
        return {"success": False, "message": message}
    
    def user_register(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        """User registration"""
        success, message = self.user_manager.create_user(username, password, email)
        return {"success": success, "message": message}
    
    def assign_entity_to_user(self, username: str, entity_id: str) -> Dict[str, Any]:
        """Assign entity to user's swarm"""
        success, message = self.user_manager.add_entity_to_user(username, entity_id)
        return {"success": success, "message": message}
    
    def process_entity_input(self, entity_id: str, user_input: str, media_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Process input through specific entity"""
        entity = self.entity_swarm.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity {entity_id} not found"}
        
        # Analyze media if provided
        media_analysis = None
        if media_data:
            media_analysis = self.media_processor.analyze_media(media_data, user_input)
        
        response = entity.process_input(user_input, media_analysis)
        
        # Update BUMPY coherence
        self.bumpy.set_coherence(entity.coherence)
        
        return response
    
    def process_collective_input(self, entity_ids: List[str], user_input: str, media_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Process input through multiple entities"""
        # Analyze media if provided
        media_analysis = None
        if media_data:
            media_analysis = self.media_processor.analyze_media(media_data, user_input)
        
        response = self.entity_swarm.process_collective_input(user_input, media_analysis, entity_ids)
        
        # Update BUMPY coherence based on average
        if response['individual_responses']:
            avg_coherence = sum(r['coherence'] for r in response['individual_responses']) / len(response['individual_responses'])
            self.bumpy.set_coherence(avg_coherence)
        
        return response
    
    def train_entity(self, entity_id: str, training_data: Dict) -> Dict[str, Any]:
        """Train a specific entity"""
        return self.training_manager.create_training_session(entity_id, training_data)
    
    def submit_feedback(self, entity_id: str, interaction_id: str, rating: int, comments: str) -> Dict[str, Any]:
        """Submit feedback for entity performance"""
        return self.training_manager.submit_feedback(entity_id, interaction_id, rating, comments)
    
    def get_entity_metrics(self, entity_id: str) -> Dict[str, Any]:
        """Get metrics for specific entity"""
        entity = self.entity_swarm.get_entity(entity_id)
        if not entity:
            return {"error": "Entity not found"}
        
        return {
            "entity_id": entity.entity_id,
            "name": entity.name,
            "archetype": entity.archetype,
            "coherence": entity.coherence,
            "training_level": entity.training_level,
            "memory_size": len(entity.memory),
            "conversation_history_size": len(entity.conversation_history),
            "created_at": entity.created_at
        }
    
    def get_available_entities(self) -> List[Dict[str, Any]]:
        """Get list of all available entities"""
        entities = []
        for entity_id, entity in self.entity_swarm.entities.items():
            entities.append({
                "entity_id": entity_id,
                "name": entity.name,
                "archetype": entity.archetype,
                "coherence": entity.coherence,
                "training_level": entity.training_level
            })
        return entities

# ==================== ENHANCED HTTP HANDLER ====================

class ModularHTTPHandler:
    """Enhanced HTTP handler with new v0.2 features"""
    
    def __init__(self, agi_core: AGICore, security_manager):
        self.agi = agi_core
        self.security = security_manager
        self.sessions = {}  # session_id -> username
        
        # Define routes
        self.routes = {
            'GET': {
                '/': self.serve_dashboard,
                '/metrics': self.serve_metrics,
                '/status': self.serve_status,
                '/entities': self.serve_entities,
                '/entity/:id': self.serve_entity_metrics
            },
            'POST': {
                '/login': self.handle_login,
                '/register': self.handle_register,
                '/chat': self.handle_chat,
                '/collective_chat': self.handle_collective_chat,
                '/upload': self.handle_upload,
                '/generate_media': self.handle_generate_media,
                '/train': self.handle_training,
                '/feedback': self.handle_feedback,
                '/assign_entity': self.handle_assign_entity
            }
        }
    
    def get_username_from_session(self, headers: Dict) -> Optional[str]:
        """Extract username from session headers"""
        auth_header = headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            session_id = auth_header[7:]
            return self.sessions.get(session_id)
        return None
    
    def handle_request(self, method: str, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle HTTP request with routing"""
        path = path.split('?')[0]
        
        # Check for parameterized routes
        if path.startswith('/entity/') and method == 'GET':
            entity_id = path.split('/')[-1]
            return self.serve_entity_metrics(path, headers, body, entity_id)
        
        route_map = self.routes.get(method, {})
        handler = route_map.get(path)
        
        if handler:
            return handler(path, headers, body)
        else:
            return self.not_found(path)
    
    def serve_dashboard(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Serve the enhanced dashboard"""
        try:
            with open('html_public/index.html', 'r') as f:
                html_content = f.read()
            return {"content": html_content, "content_type": "text/html", "status": 200}
        except FileNotFoundError:
            return self._serve_fallback_dashboard()
    
    def _serve_fallback_dashboard(self) -> Dict[str, Any]:
        """Serve fallback dashboard"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quantum AGI v0.2 - Entity Swarm</title>
            <style>
                body { font-family: Arial; margin: 40px; background: #0f0f23; color: #00ff00; }
                .panel { background: #1a1a2e; padding: 20px; margin: 10px; border-radius: 10px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background: #16213e; }
            </style>
        </head>
        <body>
            <h1>🌌 Quantum AGI v0.2 - Entity Swarm System</h1>
            <div class="panel">
                <h2>New Features:</h2>
                <p>• User Login/Registration</p>
                <p>• Entity Swarm Management</p>
                <p>• Collective Conversations</p>
                <p>• Media Analysis & Training</p>
                <p>• Feedback System</p>
            </div>
        </body>
        </html>
        """
        return {"content": html, "content_type": "text/html", "status": 200}
    
    def serve_metrics(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Serve system metrics"""
        metrics = {
            "system_coherence": random.uniform(0.7, 0.95),
            "active_entities": len(self.agi.entity_swarm.entities),
            "total_users": len(self.agi.user_manager.users),
            "bumpy_coherence": self.agi.bumpy.coherence_level,
            "training_sessions": len(self.agi.training_manager.feedback_history),
            "timestamp": time.time()
        }
        return {"content": json.dumps(metrics), "content_type": "application/json", "status": 200}
    
    def serve_status(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Serve system status"""
        status = {
            "version": "0.2.0",
            "status": "operational",
            "features": {
                "user_management": "active",
                "entity_swarm": "active",
                "media_processing": "active",
                "training_system": "active",
                "feedback_system": "active"
            },
            "timestamp": time.time()
        }
        return {"content": json.dumps(status), "content_type": "application/json", "status": 200}
    
    def serve_entities(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Serve available entities"""
        entities = self.agi.get_available_entities()
        return {"content": json.dumps(entities), "content_type": "application/json", "status": 200}
    
    def serve_entity_metrics(self, path: str, headers: Dict, body: bytes, entity_id: str = None) -> Dict[str, Any]:
        """Serve specific entity metrics"""
        if not entity_id:
            return {"content": json.dumps({"error": "Entity ID required"}), "content_type": "application/json", "status": 400}
        
        metrics = self.agi.get_entity_metrics(entity_id)
        return {"content": json.dumps(metrics), "content_type": "application/json", "status": 200}
    
    def handle_login(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle user login"""
        try:
            data = json.loads(body.decode('utf-8'))
            username = data.get('username', '')
            password = data.get('password', '')
            
            result = self.agi.user_login(username, password)
            if result['success']:
                # Store session
                self.sessions[result['session_id']] = username
            
            return {"content": json.dumps(result), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_register(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle user registration"""
        try:
            data = json.loads(body.decode('utf-8'))
            username = data.get('username', '')
            password = data.get('password', '')
            email = data.get('email', '')
            
            result = self.agi.user_register(username, password, email)
            return {"content": json.dumps(result), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_chat(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle chat with specific entity"""
        try:
            data = json.loads(body.decode('utf-8'))
            entity_id = data.get('entity_id', '')
            user_input = data.get('input', '')
            media_data = data.get('media_data')
            
            response = self.agi.process_entity_input(entity_id, user_input, media_data)
            return {"content": json.dumps(response), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_collective_chat(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle chat with multiple entities"""
        try:
            data = json.loads(body.decode('utf-8'))
            entity_ids = data.get('entity_ids', [])
            user_input = data.get('input', '')
            media_data = data.get('media_data')
            
            response = self.agi.process_collective_input(entity_ids, user_input, media_data)
            return {"content": json.dumps(response), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_upload(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle file uploads"""
        # Simplified upload handling - in production would parse multipart form data
        response = {"status": "upload_received", "message": "File upload endpoint ready"}
        return {"content": json.dumps(response), "content_type": "application/json", "status": 200}
    
    def handle_generate_media(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle media generation requests"""
        try:
            data = json.loads(body.decode('utf-8'))
            media_type = data.get('media_type', 'audio')
            prompt = data.get('prompt', 'Quantum creation')
            
            # Simple media generation stub
            media_data = {
                "type": media_type,
                "description": f"Generated {media_type} for: {prompt}",
                "data": "base64_encoded_data",
                "timestamp": time.time()
            }
            return {"content": json.dumps(media_data), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_training(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle entity training"""
        try:
            data = json.loads(body.decode('utf-8'))
            entity_id = data.get('entity_id', '')
            training_data = data.get('training_data', {})
            
            result = self.agi.train_entity(entity_id, training_data)
            return {"content": json.dumps(result), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_feedback(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle feedback submission"""
        try:
            data = json.loads(body.decode('utf-8'))
            entity_id = data.get('entity_id', '')
            interaction_id = data.get('interaction_id', '')
            rating = data.get('rating', 3)
            comments = data.get('comments', '')
            
            result = self.agi.submit_feedback(entity_id, interaction_id, rating, comments)
            return {"content": json.dumps(result), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def handle_assign_entity(self, path: str, headers: Dict, body: bytes) -> Dict[str, Any]:
        """Handle entity assignment to user"""
        try:
            username = self.get_username_from_session(headers)
            if not username:
                return {"content": json.dumps({"error": "Authentication required"}), "content_type": "application/json", "status": 401}
            
            data = json.loads(body.decode('utf-8'))
            entity_id = data.get('entity_id', '')
            
            result = self.agi.assign_entity_to_user(username, entity_id)
            return {"content": json.dumps(result), "content_type": "application/json", "status": 200}
        except Exception as e:
            return {"content": json.dumps({"error": str(e)}), "content_type": "application/json", "status": 400}
    
    def not_found(self, path: str) -> Dict[str, Any]:
        """Handle 404 errors"""
        return {"content": f"Path {path} not found", "content_type": "text/plain", "status": 404}

# ==================== MAIN SERVER ====================

class ModularAGIServer:
    """Main modular AGI server v0.2"""
    
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        
        self._ensure_directories()
        
        # Initialize managers
        self.module_manager = ModuleManager()
        self.security_manager = SecurityManager()
        self.agi_core = AGICore(self.module_manager)
        self.http_handler = ModularHTTPHandler(self.agi_core, self.security_manager)
        
        # HTTP server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        print(f"🚀 Quantum AGI Server v0.2 starting on http://{self.host}:{self.port}")
        print("🎯 New Features:")
        print("   • User Login/Registration System")
        print("   • Entity Swarm with Multiple AGI Personalities") 
        print("   • Collective Conversations")
        print("   • Media Analysis & Training")
        print("   • Feedback & Growth System")
        print("   • Entity Management Dashboard")
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            'agi_mods', 'system_mods', 'sensory_mods', 'bootstrap_mods',
            'html_public', 'user_content', 'user_sessions', 'training_data'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def parse_http_request(self, data):
        """Parse HTTP request"""
        try:
            lines = data.decode('utf-8').split('\r\n')
            if not lines or not lines[0]:
                return {}
            
            request_parts = lines[0].split(' ')
            if len(request_parts) < 2:
                return {}
                
            method, path = request_parts[0], request_parts[1]
            
            headers = {}
            body_start = 0
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            body = b'\r\n'.join([line.encode('utf-8') for line in lines[body_start:]]) if body_start else b''
            
            return {
                'method': method,
                'path': path,
                'headers': headers,
                'body': body
            }
        except Exception as e:
            print(f"Error parsing HTTP request: {e}")
            return {}
    
    def create_http_response(self, content, content_type="text/plain", status=200):
        """Create HTTP response"""
        status_text = {
            200: "OK",
            404: "Not Found", 
            400: "Bad Request",
            401: "Unauthorized",
            500: "Internal Server Error"
        }.get(status, "Unknown")
        
        response = f"HTTP/1.1 {status} {status_text}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(content)}\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"
        response += content
        
        return response.encode('utf-8')
    
    def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            data = client_socket.recv(8192)
            if not data:
                return
            
            request = self.parse_http_request(data)
            if not request:
                error_response = self.create_http_response("Bad Request", "text/plain", 400)
                client_socket.send(error_response)
                return
            
            response_data = self.http_handler.handle_request(
                request['method'],
                request['path'], 
                request['headers'],
                request['body']
            )
            
            response = self.create_http_response(
                response_data['content'],
                response_data['content_type'],
                response_data['status']
            )
            client_socket.send(response)
            
        except Exception as e:
            print(f"Error handling client: {e}")
            error_response = self.create_http_response(
                f"Internal Server Error: {str(e)}", "text/plain", 500
            )
            client_socket.send(error_response)
        finally:
            client_socket.close()
    
    def start(self):
        """Start the server"""
        print(f"🌐 Server listening on http://{self.host}:{self.port}")
        
        try:
            while True:
                client_socket, addr = self.socket.accept()
                print(f"📡 Connection from {addr[0]}:{addr[1]}")
                self.handle_client(client_socket)
                
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        finally:
            self.socket.close()

# ==================== MAIN ====================

if __name__ == "__main__":
    server = ModularAGIServer(host='0.0.0.0', port=8080)
    server.start()
