"""
Unit tests for AI Intelligence Agent
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.agents.ai_agent import AIIntelligenceAgent
from src.core.orchestrator import AgentMessage, AgentType
import httpx


class TestAIIntelligenceAgent:
    """Test cases for AI Intelligence Agent"""

    def setup_method(self):
        """Setup for each test"""
        self.agent = AIIntelligenceAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct attributes"""
        assert self.agent.name == "ai_intelligence"
        assert hasattr(self.agent, 'anthropic_api_key')
        assert hasattr(self.agent, 'analysis_results')
        assert self.agent.analysis_results == {}

    @pytest.mark.asyncio
    @patch('src.agents.ai_agent.os.getenv')
    async def test_analyze_with_anthropic_key(self, mock_getenv):
        """Test analysis with Anthropic API key"""
        mock_getenv.return_value = "test-api-key"
        
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        # Mock the Anthropic client
        with patch('src.agents.ai_agent.AsyncAnthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="Security: High\nPerformance: Good")]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client
            
            # Reinitialize agent to pick up mocked API key
            agent = AIIntelligenceAgent()
            result = await agent.analyze(spec_data)
            
            assert "ai_analysis" in result
            assert mock_client.messages.create.called

    @pytest.mark.asyncio
    @patch('src.agents.ai_agent.os.getenv')
    async def test_analyze_without_api_key(self, mock_getenv):
        """Test analysis without API key falls back to basic analysis"""
        mock_getenv.return_value = None
        
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {"get": {}},
                "/admin": {"post": {}},
                "/api/v1/data": {"get": {}}
            }
        }
        
        agent = AIIntelligenceAgent()
        result = await agent.analyze(spec_data)
        
        assert "summary" in result
        assert result["summary"]["total_endpoints"] == 3
        assert result["summary"]["total_paths"] == 3
        assert "security_analysis" in result
        assert "performance_analysis" in result

    @pytest.mark.asyncio
    async def test_basic_analysis_security_checks(self):
        """Test basic security analysis"""
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/admin": {"post": {}},
                "/public": {"get": {}},
                "/users": {
                    "delete": {},
                    "get": {"security": [{"bearerAuth": []}]}
                }
            },
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"}
                }
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "security_analysis" in result
        security = result["security_analysis"]
        assert security["has_authentication"]
        assert "/admin" in security["sensitive_endpoints"]
        assert "delete" in [m.lower() for m in security["dangerous_operations"]]

    @pytest.mark.asyncio
    async def test_basic_analysis_performance_metrics(self):
        """Test basic performance analysis"""
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {"get": {}},
                "/users/{id}": {"get": {}, "put": {}, "delete": {}},
                "/posts": {"get": {}, "post": {}},
                "/posts/{id}": {"get": {}, "patch": {}}
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "performance_analysis" in result
        perf = result["performance_analysis"]
        assert perf["total_endpoints"] == 7
        assert perf["average_operations_per_path"] > 1
        assert "complexity_score" in perf

    @pytest.mark.asyncio
    async def test_analyze_with_rate_limiting(self):
        """Test detection of rate limiting in spec"""
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/api/data": {
                    "get": {
                        "x-rate-limit": "100 per hour",
                        "responses": {"429": {"description": "Rate limited"}}
                    }
                }
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "performance_analysis" in result
        assert "has_rate_limiting" in result["performance_analysis"]

    @pytest.mark.asyncio
    async def test_analyze_with_pagination(self):
        """Test detection of pagination support"""
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "parameters": [
                            {"name": "page", "in": "query"},
                            {"name": "limit", "in": "query"}
                        ]
                    }
                }
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "performance_analysis" in result
        perf = result["performance_analysis"]
        assert perf["has_pagination"]

    @pytest.mark.asyncio
    async def test_compliance_analysis(self):
        """Test compliance analysis"""
        spec_data = {
            "openapi": "3.0.0",
            "paths": {
                "/users/{id}": {
                    "delete": {
                        "summary": "Delete user data",
                        "description": "GDPR compliant deletion"
                    }
                },
                "/health": {
                    "get": {
                        "summary": "HIPAA compliant health check"
                    }
                }
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "compliance_hints" in result
        compliance = result["compliance_hints"]
        assert compliance["has_data_deletion"]
        assert any("gdpr" in hint.lower() for hint in compliance["potential_compliance"])

    @pytest.mark.asyncio
    async def test_business_value_estimation(self):
        """Test business value estimation"""
        spec_data = {
            "openapi": "3.0.0",
            "info": {"title": "User API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {}, "post": {}},
                "/orders": {"get": {}, "post": {}},
                "/payments": {"post": {}},
                "/analytics": {"get": {}}
            }
        }
        
        result = await self.agent.analyze(spec_data)
        
        assert "business_value" in result
        bv = result["business_value"]
        assert "estimated_complexity" in bv
        assert "resource_types" in bv
        assert len(bv["resource_types"]) > 0

    @pytest.mark.asyncio
    async def test_process_message_analyze_action(self):
        """Test process_message with analyze action"""
        message = AgentMessage(
            type=AgentType.AI_INTELLIGENCE,
            action="analyze",
            data={"spec": {"openapi": "3.0.0", "paths": {}}}
        )
        
        with patch.object(self.agent, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"analysis": "complete"}
            
            result = await self.agent.process_message(message)
            
            assert result["status"] == "success"
            assert "data" in result
            mock_analyze.assert_called_once_with({"openapi": "3.0.0", "paths": {}})

    @pytest.mark.asyncio
    async def test_process_message_unknown_action(self):
        """Test process_message with unknown action"""
        message = AgentMessage(
            type=AgentType.AI_INTELLIGENCE,
            action="unknown_action",
            data={}
        )
        
        result = await self.agent.process_message(message)
        
        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    @pytest.mark.asyncio
    @patch('src.agents.ai_agent.httpx.AsyncClient')
    async def test_analyze_with_openai_fallback(self, mock_httpx):
        """Test fallback to OpenAI when Anthropic fails"""
        # Set both API keys
        with patch('src.agents.ai_agent.os.getenv') as mock_getenv:
            def getenv_side_effect(key, default=None):
                if key == "ANTHROPIC_API_KEY":
                    return None
                if key == "OPENAI_API_KEY":
                    return "openai-test-key"
                return default
            
            mock_getenv.side_effect = getenv_side_effect
            
            # Mock OpenAI response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json = Mock(return_value={
                "choices": [{
                    "message": {
                        "content": "Analysis: Good API design"
                    }
                }]
            })
            mock_response.raise_for_status = Mock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_httpx.return_value.__aexit__ = AsyncMock()
            
            agent = AIIntelligenceAgent()
            result = await agent.analyze({"openapi": "3.0.0", "paths": {}})
            
            assert "ai_analysis" in result

    def test_extract_method_operations(self):
        """Test extraction of HTTP methods from paths"""
        spec_data = {
            "paths": {
                "/users": {"get": {}, "post": {}, "options": {}},
                "/users/{id}": {"get": {}, "put": {}, "delete": {}, "patch": {}}
            }
        }
        
        result = self.agent.analyze(spec_data)
        
        # Since analyze is async, we need to run it properly
        import asyncio
        result = asyncio.run(self.agent.analyze(spec_data))
        
        assert result["summary"]["total_endpoints"] == 7
        security = result["security_analysis"]
        assert "DELETE" in security["dangerous_operations"]

    def test_sensitive_endpoint_detection(self):
        """Test detection of sensitive endpoints"""
        spec_data = {
            "paths": {
                "/admin/users": {"post": {}},
                "/api/password-reset": {"post": {}},
                "/public/info": {"get": {}},
                "/auth/login": {"post": {}},
                "/payment/process": {"post": {}}
            }
        }
        
        import asyncio
        result = asyncio.run(self.agent.analyze(spec_data))
        
        sensitive = result["security_analysis"]["sensitive_endpoints"]
        assert "/admin/users" in sensitive
        assert "/api/password-reset" in sensitive
        assert "/auth/login" in sensitive
        assert "/payment/process" in sensitive
        assert "/public/info" not in sensitive