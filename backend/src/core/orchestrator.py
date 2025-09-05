import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from enum import Enum

class AgentType(Enum):
    DISCOVERY = "discovery"
    SPEC_GENERATOR = "spec_generator"
    TEST_GENERATOR = "test_generator"
    MOCK_SERVER = "mock_server"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    VERSION_MANAGER = "version_manager"
    AI_INTELLIGENCE = "ai_intelligence"

@dataclass
class APIEndpoint:
    path: str
    method: str
    handler_name: str
    parameters: List[Dict]
    response_schema: Optional[Dict] = None
    description: Optional[str] = None
    auth_required: bool = False
    rate_limit: Optional[int] = None

@dataclass
class AgentMessage:
    sender: AgentType
    receiver: AgentType
    action: str
    payload: Dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class APIOrchestrator:
    def __init__(self):
        self.agents = {}
        self.api_registry: Dict[str, APIEndpoint] = {}
        self.message_queue: List[AgentMessage] = []
        self.is_running = False
        
    def register_agent(self, agent_type: AgentType, agent_instance):
        """Register an agent with the orchestrator"""
        self.agents[agent_type] = agent_instance
        print(f"✓ Registered {agent_type.value} agent")
        
    async def discover_apis(self, source_path: str) -> List[APIEndpoint]:
        """Discover all APIs in a codebase"""
        if AgentType.DISCOVERY not in self.agents:
            raise ValueError("Discovery agent not registered")
            
        discovery_agent = self.agents[AgentType.DISCOVERY]
        apis = await discovery_agent.scan(source_path)
        
        # Register discovered APIs
        for api in apis:
            key = f"{api.method}:{api.path}"
            self.api_registry[key] = api
            
        print(f"✓ Discovered {len(apis)} API endpoints")
        return apis
    
    async def generate_specs(self, apis: List[APIEndpoint]) -> Dict:
        """Generate OpenAPI specifications"""
        if AgentType.SPEC_GENERATOR not in self.agents:
            raise ValueError("Spec generator agent not registered")
            
        spec_agent = self.agents[AgentType.SPEC_GENERATOR]
        specs = await spec_agent.generate(apis)
        print(f"✓ Generated OpenAPI spec with {len(specs.get('paths', {}))} paths")
        return specs
    
    async def generate_tests(self, specs: Dict) -> List[Dict]:
        """Generate test suites from specifications"""
        if AgentType.TEST_GENERATOR not in self.agents:
            raise ValueError("Test generator agent not registered")
            
        test_agent = self.agents[AgentType.TEST_GENERATOR]
        tests = await test_agent.create_tests(specs)
        print(f"✓ Generated {len(tests)} test cases")
        return tests
    
    async def process_message(self, message: AgentMessage):
        """Process inter-agent messages"""
        receiver = self.agents.get(message.receiver)
        if receiver:
            await receiver.handle_message(message)
    
    async def orchestrate(self, source_path: str) -> Dict:
        """Main orchestration flow"""
        self.is_running = True
        results = {
            "started_at": datetime.now().isoformat(),
            "source_path": source_path,
            "apis": [],
            "specs": {},
            "tests": [],
            "errors": []
        }
        
        try:
            # Step 1: Discovery
            print("\n🔍 Starting API Discovery...")
            apis = await self.discover_apis(source_path)
            results["apis"] = [api.__dict__ for api in apis]
            
            # Step 2: Generate Specs
            print("\n📝 Generating OpenAPI Specifications...")
            specs = await self.generate_specs(apis)
            results["specs"] = specs
            
            # Step 3: Generate Tests
            print("\n🧪 Generating Test Suites...")
            tests = await self.generate_tests(specs)
            results["tests"] = tests
            
            # Process any queued messages
            while self.message_queue:
                message = self.message_queue.pop(0)
                await self.process_message(message)
                
        except Exception as e:
            print(f"❌ Orchestration error: {str(e)}")
            results["errors"].append(str(e))
        finally:
            self.is_running = False
            results["completed_at"] = datetime.now().isoformat()
            
        return results
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            "is_running": self.is_running,
            "registered_agents": list(self.agents.keys()),
            "discovered_apis": len(self.api_registry),
            "queued_messages": len(self.message_queue)
        }