"""
AI Agent Builder - Build, test, and deploy intelligent API agents
The POSTMAN KILLER feature - goes beyond Postman's capabilities
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import httpx
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool, StructuredTool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class AgentType(Enum):
    """Types of AI agents that can be created"""
    API_TESTER = "api_tester"
    DATA_PROCESSOR = "data_processor" 
    WORKFLOW_AUTOMATOR = "workflow_automator"
    SECURITY_SCANNER = "security_scanner"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    DOCUMENTATION_GENERATOR = "documentation_generator"
    MOCK_DATA_GENERATOR = "mock_data_generator"
    INTEGRATION_BUILDER = "integration_builder"
    CUSTOM = "custom"

class AgentCapability(Enum):
    """Capabilities that agents can have"""
    HTTP_REQUESTS = "http_requests"
    DATA_TRANSFORMATION = "data_transformation"
    FILE_OPERATIONS = "file_operations"
    DATABASE_QUERIES = "database_queries"
    CODE_GENERATION = "code_generation"
    NATURAL_LANGUAGE = "natural_language"
    SCHEDULING = "scheduling"
    NOTIFICATIONS = "notifications"
    CHAIN_APIS = "chain_apis"
    CONDITIONAL_LOGIC = "conditional_logic"

class AIAgent(BaseModel):
    """AI Agent configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: AgentType
    capabilities: List[AgentCapability]
    model: str = "gpt-4"  # or claude-3, gemini-pro, etc.
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: str
    tools: List[Dict[str, Any]] = []
    memory_enabled: bool = True
    auto_retry: bool = True
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Agent workflow
    workflow_steps: List[Dict[str, Any]] = []
    triggers: List[Dict[str, Any]] = []  # webhooks, schedules, events
    
    # Testing & validation
    test_cases: List[Dict[str, Any]] = []
    success_criteria: Dict[str, Any] = {}
    
    # Deployment
    deployed: bool = False
    endpoint: Optional[str] = None
    api_key: Optional[str] = None

class AgentBuilder:
    """Build and manage AI agents for API automation"""
    
    def __init__(self):
        self.agents: Dict[str, AIAgent] = {}
        self.running_agents: Dict[str, AgentExecutor] = {}
        
    async def create_agent(
        self,
        name: str,
        description: str,
        agent_type: AgentType,
        capabilities: List[AgentCapability],
        custom_prompt: Optional[str] = None
    ) -> AIAgent:
        """Create a new AI agent with specified capabilities"""
        
        # Generate system prompt based on agent type
        system_prompt = custom_prompt or self._generate_system_prompt(agent_type, capabilities)
        
        # Create agent configuration
        agent = AIAgent(
            name=name,
            description=description,
            type=agent_type,
            capabilities=capabilities,
            system_prompt=system_prompt
        )
        
        # Add default tools based on capabilities
        agent.tools = self._create_tools_for_capabilities(capabilities)
        
        # Store agent
        self.agents[agent.id] = agent
        
        return agent
    
    def _generate_system_prompt(self, agent_type: AgentType, capabilities: List[AgentCapability]) -> str:
        """Generate a system prompt based on agent type and capabilities"""
        
        prompts = {
            AgentType.API_TESTER: """You are an expert API testing agent. Your role is to:
1. Execute API requests and validate responses
2. Check status codes, response times, and data formats
3. Run automated test suites and report results
4. Identify potential issues and suggest fixes
5. Generate comprehensive test reports""",
            
            AgentType.DATA_PROCESSOR: """You are a data processing agent specialized in:
1. Transforming API responses into desired formats
2. Extracting and aggregating data from multiple sources
3. Cleaning and validating data quality
4. Performing calculations and analytics
5. Exporting processed data to various formats""",
            
            AgentType.WORKFLOW_AUTOMATOR: """You are a workflow automation expert that:
1. Chains multiple API calls in sequence
2. Handles conditional logic and branching
3. Manages data flow between APIs
4. Implements retry logic and error handling
5. Orchestrates complex multi-step processes""",
            
            AgentType.SECURITY_SCANNER: """You are a security scanning agent focused on:
1. Identifying API vulnerabilities (OWASP Top 10)
2. Testing authentication and authorization
3. Detecting data exposure and injection flaws
4. Checking rate limiting and DOS protection
5. Generating security compliance reports""",
            
            AgentType.PERFORMANCE_OPTIMIZER: """You are a performance optimization agent that:
1. Measures API response times and throughput
2. Identifies performance bottlenecks
3. Suggests caching strategies
4. Recommends query optimizations
5. Monitors resource utilization patterns"""
        }
        
        base_prompt = prompts.get(agent_type, "You are an intelligent API agent.")
        
        # Add capability-specific instructions
        capability_prompts = {
            AgentCapability.HTTP_REQUESTS: "\n- Execute HTTP requests (GET, POST, PUT, DELETE, etc.)",
            AgentCapability.DATA_TRANSFORMATION: "\n- Transform data between formats (JSON, XML, CSV, etc.)",
            AgentCapability.CODE_GENERATION: "\n- Generate code snippets and SDKs",
            AgentCapability.CONDITIONAL_LOGIC: "\n- Apply conditional logic based on response data",
            AgentCapability.CHAIN_APIS: "\n- Chain multiple API calls using output from previous calls"
        }
        
        for cap in capabilities:
            if cap in capability_prompts:
                base_prompt += capability_prompts[cap]
                
        return base_prompt
    
    def _create_tools_for_capabilities(self, capabilities: List[AgentCapability]) -> List[Dict[str, Any]]:
        """Create LangChain tools based on agent capabilities"""
        tools = []
        
        if AgentCapability.HTTP_REQUESTS in capabilities:
            tools.append({
                "name": "http_request",
                "description": "Make HTTP requests to APIs",
                "parameters": {
                    "method": "HTTP method (GET, POST, etc.)",
                    "url": "API endpoint URL",
                    "headers": "Request headers",
                    "body": "Request body"
                }
            })
        
        if AgentCapability.DATA_TRANSFORMATION in capabilities:
            tools.append({
                "name": "transform_data",
                "description": "Transform data between formats",
                "parameters": {
                    "input_data": "Data to transform",
                    "input_format": "Current format",
                    "output_format": "Desired format"
                }
            })
            
        if AgentCapability.CODE_GENERATION in capabilities:
            tools.append({
                "name": "generate_code",
                "description": "Generate code for API integration",
                "parameters": {
                    "language": "Programming language",
                    "api_spec": "API specification",
                    "template": "Code template to use"
                }
            })
            
        return tools
    
    async def add_workflow_step(
        self,
        agent_id: str,
        step_type: str,
        config: Dict[str, Any],
        conditions: Optional[Dict[str, Any]] = None
    ):
        """Add a workflow step to an agent"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        step = {
            "id": str(uuid.uuid4()),
            "type": step_type,
            "config": config,
            "conditions": conditions,
            "order": len(self.agents[agent_id].workflow_steps)
        }
        
        self.agents[agent_id].workflow_steps.append(step)
        
        return step
    
    async def test_agent(
        self,
        agent_id: str,
        test_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test an agent with sample input"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        
        # Initialize the appropriate LLM
        if "gpt" in agent.model:
            llm = ChatOpenAI(model=agent.model, temperature=agent.temperature)
        elif "claude" in agent.model:
            llm = ChatAnthropic(model=agent.model, temperature=agent.temperature)
        else:
            llm = ChatOpenAI(model="gpt-4", temperature=agent.temperature)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", agent.system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create tools
        tools = self._create_langchain_tools(agent.tools)
        
        # Create agent
        agent_executor = create_openai_tools_agent(llm, tools, prompt)
        
        # Add memory if enabled
        if agent.memory_enabled:
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            agent_executor = AgentExecutor(
                agent=agent_executor,
                tools=tools,
                memory=memory,
                verbose=True
            )
        else:
            agent_executor = AgentExecutor(agent=agent_executor, tools=tools, verbose=True)
        
        # Run test
        result = await agent_executor.ainvoke({"input": json.dumps(test_input)})
        
        return {
            "success": True,
            "agent_id": agent_id,
            "input": test_input,
            "output": result,
            "execution_time": datetime.now().isoformat()
        }
    
    def _create_langchain_tools(self, tool_configs: List[Dict[str, Any]]) -> List[Tool]:
        """Convert tool configurations to LangChain tools"""
        tools = []
        
        for config in tool_configs:
            if config["name"] == "http_request":
                tool = Tool(
                    name="http_request",
                    func=self._http_request_tool,
                    description="Make HTTP requests to APIs"
                )
                tools.append(tool)
            elif config["name"] == "transform_data":
                tool = Tool(
                    name="transform_data",
                    func=self._transform_data_tool,
                    description="Transform data between formats"
                )
                tools.append(tool)
                
        return tools
    
    async def _http_request_tool(self, params: str) -> str:
        """Tool for making HTTP requests"""
        try:
            params_dict = json.loads(params)
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=params_dict.get("method", "GET"),
                    url=params_dict["url"],
                    headers=params_dict.get("headers", {}),
                    json=params_dict.get("body")
                )
                return json.dumps({
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                })
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _transform_data_tool(self, params: str) -> str:
        """Tool for transforming data"""
        try:
            params_dict = json.loads(params)
            # Implement data transformation logic
            return json.dumps({"transformed": params_dict["input_data"]})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    async def deploy_agent(
        self,
        agent_id: str,
        endpoint_path: str = None
    ) -> Dict[str, Any]:
        """Deploy an agent as an API endpoint"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        
        # Generate API key for agent
        agent.api_key = str(uuid.uuid4())
        
        # Set endpoint
        agent.endpoint = endpoint_path or f"/api/agents/{agent.id}/execute"
        
        # Mark as deployed
        agent.deployed = True
        
        return {
            "success": True,
            "agent_id": agent_id,
            "endpoint": agent.endpoint,
            "api_key": agent.api_key,
            "status": "deployed"
        }
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """Execute a deployed agent"""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent = self.agents[agent_id]
        
        # Validate API key
        if agent.api_key != api_key:
            raise ValueError("Invalid API key")
            
        # Execute agent
        result = await self.test_agent(agent_id, input_data)
        
        return result

class AgentTemplate(BaseModel):
    """Pre-built agent templates for common use cases"""
    name: str
    description: str
    type: AgentType
    capabilities: List[AgentCapability]
    workflow: List[Dict[str, Any]]
    
# Pre-built templates that beat Postman
AGENT_TEMPLATES = [
    AgentTemplate(
        name="API Health Monitor",
        description="Continuously monitor API health and alert on issues",
        type=AgentType.API_TESTER,
        capabilities=[AgentCapability.HTTP_REQUESTS, AgentCapability.NOTIFICATIONS],
        workflow=[
            {"type": "http_request", "config": {"method": "GET", "check_interval": 60}},
            {"type": "validate_response", "config": {"expected_status": 200}},
            {"type": "alert_on_failure", "config": {"channels": ["email", "slack"]}}
        ]
    ),
    AgentTemplate(
        name="Data Pipeline Builder",
        description="Extract, transform, and load data from multiple APIs",
        type=AgentType.DATA_PROCESSOR,
        capabilities=[AgentCapability.HTTP_REQUESTS, AgentCapability.DATA_TRANSFORMATION, AgentCapability.CHAIN_APIS],
        workflow=[
            {"type": "fetch_data", "config": {"sources": ["api1", "api2"]}},
            {"type": "transform", "config": {"format": "normalized_json"}},
            {"type": "aggregate", "config": {"group_by": "category"}},
            {"type": "export", "config": {"destination": "database"}}
        ]
    ),
    AgentTemplate(
        name="Security Audit Bot",
        description="Automatically scan APIs for security vulnerabilities",
        type=AgentType.SECURITY_SCANNER,
        capabilities=[AgentCapability.HTTP_REQUESTS, AgentCapability.CONDITIONAL_LOGIC],
        workflow=[
            {"type": "scan_endpoints", "config": {"tests": ["sql_injection", "xss", "auth_bypass"]}},
            {"type": "check_headers", "config": {"required": ["X-Frame-Options", "CSP"]}},
            {"type": "test_rate_limiting", "config": {"threshold": 100}},
            {"type": "generate_report", "config": {"format": "pdf", "compliance": ["OWASP", "PCI-DSS"]}}
        ]
    ),
    AgentTemplate(
        name="Customer Support Bot",
        description="Handle customer API queries and provide solutions",
        type=AgentType.CUSTOM,
        capabilities=[AgentCapability.NATURAL_LANGUAGE, AgentCapability.HTTP_REQUESTS],
        workflow=[
            {"type": "parse_query", "config": {"nlp_model": "gpt-4"}},
            {"type": "search_knowledge_base", "config": {"sources": ["docs", "tickets"]}},
            {"type": "generate_response", "config": {"tone": "friendly"}},
            {"type": "create_ticket", "config": {"if_unresolved": True}}
        ]
    ),
    AgentTemplate(
        name="Performance Optimizer",
        description="Analyze and optimize API performance automatically",
        type=AgentType.PERFORMANCE_OPTIMIZER,
        capabilities=[AgentCapability.HTTP_REQUESTS, AgentCapability.CODE_GENERATION],
        workflow=[
            {"type": "benchmark_endpoints", "config": {"metrics": ["latency", "throughput"]}},
            {"type": "identify_bottlenecks", "config": {"threshold_ms": 500}},
            {"type": "suggest_optimizations", "config": {"areas": ["caching", "queries", "pagination"]}},
            {"type": "generate_code", "config": {"optimizations": True}}
        ]
    )
]

# Global agent builder instance
agent_builder = AgentBuilder()